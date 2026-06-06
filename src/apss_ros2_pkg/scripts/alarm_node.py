#!/usr/bin/env python3
# coding=utf-8
# APSS — Alarm Node
# Riceve /apss/alarm, gestisce voce (piper-tts), storico e /apss/oled_alert
# Versione: 1.1 — Giugno 2026

import rclpy
import yaml
import json
import os
import subprocess
import threading
import time
from rclpy.node import Node
from std_msgs.msg import String
from collections import deque
from datetime import datetime
from pathlib import Path
from ament_index_python.packages import get_package_share_directory

PRIORITY = ["EMERGENCY", "CRITICAL", "ERROR", "LOW"]


class VoiceManager:

    def __init__(self, cfg, node):
        self._logger = node.get_logger()
        self._templates = cfg.get('templates', {})
        self._source_labels = cfg.get('source_labels', {})
        self._lang = cfg.get('language', 'it')
        self._alsa = cfg.get('alsa_device', 'default')
        self._enabled = cfg.get('voice_enabled', True)
        models = cfg.get('voice_models', {})
        self._model = os.path.expanduser(models.get(self._lang, ''))
        beep_patterns = cfg.get('beep_patterns', {})
        self._repeat = {lv: p.get('repeat_s', 30) for lv, p in beep_patterns.items()}
        self._last_spoken = {}
        self._speaking_flags = {}
        self._lock = threading.Lock()

    def _render(self, alarm):
        level = alarm.get('level', 'LOW')
        tmpl = self._templates.get(self._lang, {}).get(level, '{source_label}. {message}.')
        value = alarm.get('value', -1.0)
        value_str = 'N/A' if value == -1.0 else f'{value:.2f}'
        source = alarm.get('source', '')
        source_label = self._source_labels.get(self._lang, {}).get(source, source)
        message = '' if alarm.get('type') == 'watchdog' else alarm.get('message', '')
        return tmpl.format(source_label=source_label, message=message, value=value_str)

    def should_speak(self, level):
        repeat_s = self._repeat.get(level, 30)
        if repeat_s == 0:
            return True
        last = self._last_spoken.get(level, 0)
        return (time.time() - last) >= repeat_s

    def is_speaking(self, level):
        with self._lock:
            return self._speaking_flags.get(level, False)

    def speak_alarm(self, alarm):
        """Sintetizza e riproduce un singolo allarme. Bloccante."""
        if not self._enabled:
            return
        text = self._render(alarm)
        self._logger.info(f'[VOICE] {text}')
        wav = '/tmp/apss_alarm.wav'
        subprocess.run(
            ['bash', '-c', f'echo "{text}" | piper --model {self._model} --output_file {wav}'],
            stderr=subprocess.DEVNULL,
        )
        subprocess.run(
            ['aplay', '-D', self._alsa, wav],
            stderr=subprocess.DEVNULL,
        )
        time.sleep(0.8)

    def speak_alarms(self, alarms_list):
        """Parla tutti gli allarmi della lista in sequenza. Gestisce il flag per livello."""
        if not alarms_list:
            return
        level = alarms_list[0].get('level', 'LOW')
        with self._lock:
            self._speaking_flags[level] = True
        try:
            for alarm in alarms_list:
                self.speak_alarm(alarm)
            self._last_spoken[level] = time.time()
        finally:
            with self._lock:
                self._speaking_flags[level] = False


class OledAlertPublisher:

    def __init__(self, node):
        self._pub = node.create_publisher(String, '/apss/oled_alert', 10)

    def update(self, alarms):
        if not alarms:
            payload = json.dumps({'messages': [], 'scroll': False})
        else:
            messages = []
            for a in alarms:
                level = a.get('level', '')
                source = a.get('source', '')
                value = a.get('value', -1.0)
                if source == 'battery' and value != -1.0:
                    messages.append(f'{level} {source} {value:.2f}V')
                else:
                    messages.append(f'{level} {source}')
            payload = json.dumps({'messages': messages, 'scroll': True})
        self._pub.publish(String(data=payload))


class AlarmHistory:

    def __init__(self, log_path, max_entries):
        self._path = Path(os.path.expanduser(log_path))
        self._max = max_entries
        self._entries = deque(maxlen=max_entries)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._load()

    def _load(self):
        if self._path.exists():
            try:
                with open(self._path) as f:
                    data = json.load(f)
                for entry in data[-self._max:]:
                    self._entries.append(entry)
            except Exception:
                pass

    def _save(self):
        try:
            with open(self._path, 'w') as f:
                json.dump(list(self._entries), f, indent=2)
        except Exception:
            pass

    def record(self, alarm, state):
        entry = {
            'ts': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'level': alarm.get('level'),
            'source': alarm.get('source'),
            'message': alarm.get('message'),
            'state': state,
        }
        self._entries.append(entry)
        self._save()


class AlarmNode(Node):

    def __init__(self):
        super().__init__('alarm_node')

        pkg_share = get_package_share_directory('apss_ros2_pkg')
        yaml_path = os.path.join(pkg_share, 'config', 'safety_rules.yaml')
        with open(yaml_path) as f:
            cfg = yaml.safe_load(f)

        acfg = cfg.get('alarm_node', {})

        self._voice = VoiceManager(acfg, self)
        self._oled = OledAlertPublisher(self)
        self._history = AlarmHistory(
            acfg.get('log_path', '~/alarm_history.json'),
            acfg.get('log_max_entries', 20),
        )

        self._active_alarms = {}

        self.create_subscription(String, '/apss/alarm', self._alarm_cb, 10)

        lang = acfg.get('language', 'it')
        model = acfg.get('voice_models', {}).get(lang, 'N/A')
        log_path = acfg.get('log_path', '~/alarm_history.json')
        self.get_logger().info(f'[ALARM] lingua={lang} modello={model} log={log_path}')

    def _alarm_cb(self, msg):
        try:
            payload = json.loads(msg.data)
        except Exception as e:
            self.get_logger().error(f'[ALARM] JSON parse error: {e}')
            return

        charging = payload.get('charging', False)
        raw_alarms = payload.get('alarms', [])

        # Filtra allarmi TOF se in carica
        if charging:
            raw_alarms = [a for a in raw_alarms if 'tof' not in a.get('source', '').lower()]

        current = {a['source']: a for a in raw_alarms}

        # Onset: allarmi nuovi
        for src, alarm in current.items():
            if src not in self._active_alarms:
                self._history.record(alarm, 'onset')
                self.get_logger().warn(f'[ALARM] onset {src}:{alarm["level"]}')

        # Clear: allarmi risolti
        for src, alarm in self._active_alarms.items():
            if src not in current:
                self._history.record(alarm, 'clear')
                self.get_logger().info(f'[ALARM] clear {src}:{alarm["level"]}')

        self._active_alarms = current
        self._oled.update(list(current.values()))

        if not current:
            return

        # Trova il livello più grave tra gli allarmi attivi
        worst_level = min(
            (a['level'] for a in current.values() if a['level'] in PRIORITY),
            key=lambda lv: PRIORITY.index(lv),
            default=None,
        )
        if worst_level is None:
            return

        # Tutti gli allarmi con quel livello
        worst_alarms = [a for a in current.values() if a['level'] == worst_level]

        if self._voice.should_speak(worst_level) and not self._voice.is_speaking(worst_level):
            t = threading.Thread(
                target=self._voice.speak_alarms,
                args=(worst_alarms,),
                daemon=True,
            )
            t.start()


def main(args=None):
    rclpy.init(args=args)
    node = AlarmNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
