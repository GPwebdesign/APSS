#!/usr/bin/env python3
# coding=utf-8
"""
CameraScreen — stream video + controllo pan/tilt.
"""
import os
import urllib.request
import threading
import io
from datetime import datetime
from kivy.clock import Clock
from kivy.graphics.texture import Texture
from kivymd.uix.screen import MDScreen

# Limiti angolo pan/tilt verificati fisicamente
PAN_MIN   = 0
PAN_MAX   = 180
PAN_HOME  = 100
TILT_MIN  = 0
TILT_MAX  = 180
TILT_HOME = 85
STEP      = 5   # gradi per ogni pressione pulsante

class CameraScreen(MDScreen):
    """Schermata camera con stream video e controllo pan/tilt."""

    STREAM_URL = "http://192.168.1.158:6500/video_feed"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._stream_thread = None
        self._stream_running = False
        self._tcp = None
        self._pan  = PAN_HOME
        self._tilt = TILT_HOME
        self._save_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'save')
        os.makedirs(self._save_dir, exist_ok=True)
        self._recording = False
        self._record_dir = None
        self._record_count = 0
        self._last_jpg = None

    def set_tcp_client(self, tcp_client):
        self._tcp = tcp_client

    def start_stream(self):
        if self._stream_running:
            return
        self._stream_running = True
        self._stream_thread = threading.Thread(
            target=self._stream_worker, daemon=True)
        self._stream_thread.start()

    def stop_stream(self):
        self._stream_running = False

    def _stream_worker(self):
        try:
            stream = urllib.request.urlopen(self.STREAM_URL, timeout=5)
            buf = b""
            while self._stream_running:
                chunk = stream.read(4096)
                if not chunk:
                    break
                buf += chunk
                start = buf.find(b'\xff\xd8')
                end   = buf.find(b'\xff\xd9')
                if start != -1 and end != -1 and end > start:
                    jpg = buf[start:end + 2]
                    buf = buf[end + 2:]
                    self._last_jpg = jpg
                    Clock.schedule_once(
                        lambda dt, j=jpg: self._update_texture(j))
        except Exception:
            pass

    def _update_texture(self, jpg_bytes):
        try:
            from PIL import Image as PILImage
            img = PILImage.open(io.BytesIO(jpg_bytes)).convert("RGB")
            w, h = img.size
            tex = Texture.create(size=(w, h), colorfmt="rgb")
            tex.blit_buffer(img.tobytes(), colorfmt="rgb", bufferfmt="ubyte")
            tex.flip_vertical()
            if hasattr(self.ids, "cam_view"):
                self.ids.cam_view.texture = tex
                if self._recording and self._record_dir:
                    self._record_count += 1
                    frame_path = os.path.join(
                        self._record_dir, f'frame_{self._record_count:04d}.jpg')
                    if self._last_jpg:
                        with open(frame_path, 'wb') as f:
                            f.write(self._last_jpg)
        except Exception:
            pass

    # ── Foto e registrazione ──────────────────────────────────────────────
    def take_photo(self):
        # TODO: migliorare qualità foto aggiungendo endpoint /capture_still
        # in rosmaster_main.py che scatta in modalità still (colori eccellenti)
        # vs attuale che salva frame MJPEG stream (colori pipeline video)
        if self._last_jpg is None:
            return
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        path = os.path.join(self._save_dir, f'photo_{ts}.jpg')
        with open(path, 'wb') as f:
            f.write(self._last_jpg)
        print(f'[CAMERA] Foto salvata: {path}')

    def toggle_record(self):
        if not self._recording:
            ts = datetime.now().strftime('%Y%m%d_%H%M%S')
            self._record_dir = os.path.join(self._save_dir, f'video_{ts}')
            os.makedirs(self._record_dir, exist_ok=True)
            self._record_count = 0
            self._recording = True
            if hasattr(self.ids, 'btn_record'):
                self.ids.btn_record.icon = 'record-circle'
                self.ids.btn_record.theme_icon_color = 'Custom'
                self.ids.btn_record.icon_color = (1, 0, 0, 1)
            print(f'[CAMERA] Registrazione avviata: {self._record_dir}')
        else:
            self._recording = False
            if hasattr(self.ids, 'btn_record'):
                self.ids.btn_record.icon = 'record-circle'
                self.ids.btn_record.theme_icon_color = 'Custom'
                self.ids.btn_record.icon_color = (1, 1, 1, 1)
            print(f'[CAMERA] Registrazione fermata — {self._record_count} frame salvati')

    # ── Controllo Pan ─────────────────────────────────────────────────────
    def pan_left(self):
        self._pan = min(PAN_MAX, self._pan + STEP)
        if self._tcp: self._tcp.send_pan(self._pan)
        self._update_labels()

    def pan_right(self):
        self._pan = max(PAN_MIN, self._pan - STEP)
        if self._tcp: self._tcp.send_pan(self._pan)
        self._update_labels()

    # ── Controllo Tilt ────────────────────────────────────────────────────
    def tilt_up(self):
        self._tilt = max(TILT_MIN, self._tilt - STEP)
        if self._tcp: self._tcp.send_tilt(self._tilt)
        self._update_labels()

    def tilt_down(self):
        self._tilt = min(TILT_MAX, self._tilt + STEP)
        if self._tcp: self._tcp.send_tilt(self._tilt)
        self._update_labels()

    def go_home(self):
        """Ritorno a home graduale — 5° per step ogni 0.05s."""
        threading.Thread(target=self._go_home_worker, daemon=True).start()

    def _go_home_worker(self):
        import time
        STEP_DEG = 5
        DELAY    = 0.05
        while self._pan != PAN_HOME or self._tilt != TILT_HOME:
            if self._pan < PAN_HOME:
                self._pan = min(PAN_HOME, self._pan + STEP_DEG)
            elif self._pan > PAN_HOME:
                self._pan = max(PAN_HOME, self._pan - STEP_DEG)
            if self._tilt < TILT_HOME:
                self._tilt = min(TILT_HOME, self._tilt + STEP_DEG)
            elif self._tilt > TILT_HOME:
                self._tilt = max(TILT_HOME, self._tilt - STEP_DEG)
            if self._tcp:
                self._tcp.send_pan(self._pan)
                self._tcp.send_tilt(self._tilt)
            Clock.schedule_once(lambda dt: self._update_labels(), 0)
            time.sleep(DELAY)

    def _update_labels(self):
        if hasattr(self.ids, "lbl_pan"):
            self.ids.lbl_pan.text  = f"Pan: {self._pan}°"
        if hasattr(self.ids, "lbl_tilt"):
            self.ids.lbl_tilt.text = f"Tilt: {self._tilt}°"

    # ── Lifecycle ─────────────────────────────────────────────────────────
    def on_enter(self):
        if self._tcp and self._tcp.connected:
            self.start_stream()
        self.go_home()

    def on_leave(self):
        self.stop_stream()
