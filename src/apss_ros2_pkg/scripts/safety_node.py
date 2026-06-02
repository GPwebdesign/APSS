#!/usr/bin/env python3
# coding=utf-8
# APSS — Safety Node
# Monitora topic ROS2 via regole dichiarative YAML e pubblica /apss/alarm
# Versione: 1.0 — Giugno 2026

import os
import rclpy
import yaml
import json
import time
from rclpy.node import Node
from std_msgs.msg import String
from sensor_msgs.msg import BatteryState, Range
from collections import deque
from datetime import datetime
from ament_index_python.packages import get_package_share_directory

MSG_TYPE_MAP = {
    'sensor_msgs/BatteryState': BatteryState,
    'sensor_msgs/Range': Range,
}


class ThresholdEvaluator:
    """Valuta soglie low/high — restituisce il match più critico o None."""

    def __init__(self, rule_cfg):
        self._rule = rule_cfg
        self._type = rule_cfg['type']
        thresholds = rule_cfg.get('thresholds', [])
        if self._type == 'threshold_low':
            # Ordine ascending: valore più basso = più critico → primo match restituito
            self._thresholds = sorted(thresholds, key=lambda t: t['value'])
        else:
            # threshold_high: ordine descending: valore più alto = più critico
            self._thresholds = sorted(thresholds, key=lambda t: t['value'], reverse=True)

    def evaluate(self, value):
        for t in self._thresholds:
            if self._type == 'threshold_low' and value < t['value']:
                return {
                    'source': self._rule['source'],
                    'level': t['level'],
                    'type': self._type,
                    'value': float(value),
                    'threshold': float(t['value']),
                    'message': t['message'],
                }
            elif self._type == 'threshold_high' and value > t['value']:
                return {
                    'source': self._rule['source'],
                    'level': t['level'],
                    'type': self._type,
                    'value': float(value),
                    'threshold': float(t['value']),
                    'message': t['message'],
                }
        return None


class FrozenEvaluator:
    """Allarme se il valore non cambia per frozen_samples campioni consecutivi."""

    def __init__(self, rule_cfg):
        self._rule = rule_cfg
        self._tolerance = rule_cfg['frozen_tolerance']
        self._buffer = deque(maxlen=rule_cfg['frozen_samples'])

    def evaluate(self, value):
        self._buffer.append(value)
        if len(self._buffer) < self._buffer.maxlen:
            return None  # buffer non ancora pieno — attesa dati, non errore
        if (max(self._buffer) - min(self._buffer)) < self._tolerance:
            return {
                'source': self._rule['source'],
                'level': self._rule['level'],
                'type': 'frozen',
                'value': float(value),
                'threshold': -1.0,
                'message': self._rule['message'],
            }
        return None


class BooleanEvaluator:
    """Allarme se il campo è True."""

    def __init__(self, rule_cfg):
        self._rule = rule_cfg

    def evaluate(self, value):
        if value:
            return {
                'source': self._rule['source'],
                'level': self._rule['level'],
                'type': 'boolean',
                'value': -1.0,
                'threshold': -1.0,
                'message': self._rule['message'],
            }
        return None


class TopicMonitor:
    """Subscriber dinamici per tutti i topic nelle regole.

    Stato per topic: {last_ts, ever_received, values: {field: last_value}}
    I sample_buffer per frozen vivono nei FrozenEvaluator, non qui.
    """

    def __init__(self, node, rules, global_cfg):
        self._node = node
        self._global = global_cfg
        self._state = {}

        # Raccogli (topic → {fields, msg_type}) dalle regole
        topic_fields = {}
        for rule in rules:
            topic = rule['topic']
            if topic not in topic_fields:
                topic_fields[topic] = {'fields': set(), 'msg_type': rule['msg_type']}
            topic_fields[topic]['fields'].add(rule['field'])

        # Aggiungi charging_field allo stesso topic (trattato come qualsiasi altro campo)
        c_topic = global_cfg['charging_topic']
        c_field = global_cfg['charging_field']
        if c_topic in topic_fields:
            topic_fields[c_topic]['fields'].add(c_field)
        else:
            topic_fields[c_topic] = {
                'fields': {c_field},
                'msg_type': 'sensor_msgs/BatteryState',
            }

        # Inizializza stato e crea subscriber
        for topic, info in topic_fields.items():
            fields = frozenset(info['fields'])
            self._state[topic] = {
                'last_ts': None,
                'ever_received': False,
                'values': {f: None for f in fields},
            }
            msg_cls = MSG_TYPE_MAP[info['msg_type']]

            def _make_cb(t, fs):
                def cb(msg):
                    ts = time.time()
                    self._state[t]['last_ts'] = ts
                    self._state[t]['ever_received'] = True
                    for f in fs:
                        self._state[t]['values'][f] = getattr(msg, f)
                return cb

            node.create_subscription(msg_cls, topic, _make_cb(topic, fields), 10)

    def get_state(self, topic, field):
        if topic not in self._state:
            return {'last_value': None, 'last_ts': None, 'ever_received': False}
        s = self._state[topic]
        return {
            'last_value': s['values'].get(field),
            'last_ts': s['last_ts'],
            'ever_received': s['ever_received'],
        }

    def is_charging(self):
        c_topic = self._global['charging_topic']
        c_field = self._global['charging_field']
        c_thresh = self._global['charging_threshold']
        state = self.get_state(c_topic, c_field)
        if state['last_value'] is None:
            return False
        return state['last_value'] < c_thresh


class RuleEngine:
    """Carica YAML, istanzia valutatori, valuta tutte le regole ad ogni tick."""

    def __init__(self, cfg):
        self._global = cfg['global']
        self._rules = cfg['rules']
        self._start_time = time.time()
        self._evaluators = {}
        for rule in self._rules:
            t = rule['type']
            if t in ('threshold_low', 'threshold_high'):
                self._evaluators[rule['id']] = ThresholdEvaluator(rule)
            elif t == 'frozen':
                self._evaluators[rule['id']] = FrozenEvaluator(rule)
            elif t == 'boolean':
                self._evaluators[rule['id']] = BooleanEvaluator(rule)

    def evaluate_all(self, topic_monitor, now):
        alarms = []
        grace = self._global['grace_period_s']

        for rule in self._rules:
            topic = rule['topic']
            field = rule['field']
            staleness_s = rule.get('staleness_s', 10)
            active_when_charging = rule.get('active_when_charging', True)

            state = topic_monitor.get_state(topic, field)
            last_value = state['last_value']
            last_ts = state['last_ts']
            ever_received = state['ever_received']

            # Watchdog: topic mai ricevuto dopo il grace period
            if not ever_received and (now - self._start_time) > grace:
                alarms.append({
                    'source': rule['source'],
                    'level': 'ERROR',
                    'type': 'watchdog',
                    'value': -1.0,
                    'threshold': -1.0,
                    'message': f'topic never started: {topic}',
                })

            # Staleness: topic silenzioso da troppo tempo
            if ever_received and last_ts is not None and (now - last_ts) > staleness_s:
                alarms.append({
                    'source': rule['source'],
                    'level': 'ERROR',
                    'type': 'staleness',
                    'value': -1.0,
                    'threshold': -1.0,
                    'message': f'topic stale: {topic}',
                })

            # Salta valutazione valore se regola non attiva durante ricarica
            if not active_when_charging and topic_monitor.is_charging():
                continue

            # Valutazione valore se disponibile
            if last_value is not None:
                ev = self._evaluators.get(rule['id'])
                if ev:
                    alarm = ev.evaluate(last_value)
                    if alarm:
                        alarms.append(alarm)

        return alarms


class SafetyNode(Node):

    def __init__(self):
        super().__init__('safety_node')

        pkg_share = get_package_share_directory('apss_ros2_pkg')
        yaml_path = os.path.join(pkg_share, 'config', 'safety_rules.yaml')
        with open(yaml_path) as f:
            cfg = yaml.safe_load(f)

        self._engine = RuleEngine(cfg)
        self._monitor = TopicMonitor(self, cfg['rules'], cfg['global'])

        self._pub = self.create_publisher(String, '/apss/alarm', 10)

        rate = cfg['global']['publish_rate_hz']
        self.create_timer(1.0 / rate, self._timer_cb)

        for rule in cfg['rules']:
            self.get_logger().info(f"[SAFETY] Rule loaded: {rule['id']} ({rule['type']})")

    def _timer_cb(self):
        now = time.time()
        alarms = self._engine.evaluate_all(self._monitor, now)

        payload = {
            'ts': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'charging': self._monitor.is_charging(),
            'alarms': alarms,
        }

        self._pub.publish(String(data=json.dumps(payload)))

        if alarms:
            self.get_logger().warn(
                f'[SAFETY] {len(alarms)} alarm(s): '
                + ', '.join(f'{a["source"]}:{a["level"]}' for a in alarms)
            )


def main(args=None):
    rclpy.init(args=args)
    node = SafetyNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
