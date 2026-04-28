#!/usr/bin/env python3
# coding=utf-8
"""
MainScreen — controllo robot + stream video.
"""
import urllib.request
import threading
import time
import io
from kivy.clock import Clock
from kivy.graphics.texture import Texture
from kivy.uix.image import Image
from kivymd.uix.screen import MDScreen


class MainScreen(MDScreen):
    """Schermata principale con stream video e pad di controllo."""

    # URL stream MJPEG dalla camera OV5647
    STREAM_URL = "http://192.168.1.158:6500/video_feed"
    STREAM_FPS  = 15  # frame al secondo da richiedere

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._stream_thread = None
        self._stream_running = False
        self._tcp = None  # impostato dall'app principale
        self._speed_factor = 0.5

    def set_tcp_client(self, tcp_client):
        """Collega il client TCP alla schermata."""
        self._tcp = tcp_client

    # ── Stream video ─────────────────────────────────────────────────────
    def start_stream(self):
        """Avvia lo stream video in un thread separato."""
        if self._stream_running:
            return
        self._stream_running = True
        self._stream_thread = threading.Thread(
            target=self._stream_worker, daemon=True)
        self._stream_thread.start()

    def stop_stream(self):
        """Ferma lo stream video."""
        self._stream_running = False

    def _stream_worker(self):
        """Thread che legge i frame MJPEG dalla camera."""
        try:
            stream = urllib.request.urlopen(self.STREAM_URL, timeout=5)
            bytes_buf = b""
            while self._stream_running:
                chunk = stream.read(4096)
                if not chunk:
                    break
                bytes_buf += chunk
                # Cerca i marker JPEG start/end
                start = bytes_buf.find(b'\xff\xd8')
                end   = bytes_buf.find(b'\xff\xd9')
                if start != -1 and end != -1 and end > start:
                    jpg = bytes_buf[start:end + 2]
                    bytes_buf = bytes_buf[end + 2:]
                    Clock.schedule_once(
                        lambda dt, j=jpg: self._update_texture(j))
        except Exception:
            pass

    def _update_texture(self, jpg_bytes):
        """Aggiorna la texture del widget Image con il frame ricevuto."""
        try:
            from PIL import Image as PILImage
            img = PILImage.open(io.BytesIO(jpg_bytes))
            img = img.convert("RGB")
            w, h = img.size
            tex = Texture.create(size=(w, h), colorfmt="rgb")
            tex.blit_buffer(img.tobytes(), colorfmt="rgb", bufferfmt="ubyte")
            tex.flip_vertical()
            # Aggiorna il widget camera_view definito nel .kv
            if hasattr(self.ids, "camera_view"):
                self.ids.camera_view.texture = tex
        except Exception:
            pass

    # ── Controllo motori ──────────────────────────────────────────────────
    def send_motion(self, vx, vy, vz):
        if self._tcp:
            self._tcp.send_motion(vx, vy, vz, speed_factor=self._speed_factor)

    def on_speed_change(self, value):
        self._speed_factor = round(value, 1)

    def on_btn_forward_press(self):
        self.send_motion(1.0, 0.0, 0.0)

    def on_btn_forward_release(self):
        if self._tcp:
            self._tcp.send_stop()

    def on_btn_backward_press(self):
        self.send_motion(-1.0, 0.0, 0.0)

    def on_btn_backward_release(self):
        if self._tcp:
            self._tcp.send_stop()

    def on_btn_left_press(self):
        if self._tcp:
            self._tcp.send_motion(0.0, 0.0, -1.0, speed_factor=0.8)

    def on_btn_left_release(self):
        if self._tcp:
            self._tcp.send_stop()

    def on_btn_right_press(self):
        if self._tcp:
            self._tcp.send_motion(0.0, 0.0, 1.0, speed_factor=0.8)

    def on_btn_right_release(self):
        if self._tcp:
            self._tcp.send_stop()

    def on_btn_stop_press(self):
        if self._tcp:
            self._tcp.send_stop()

    def on_btn_strafe_left_press(self):
        if self._tcp:
            self._tcp.send_motion(0.6, 0.0, -0.4, speed_factor=0.9)

    def on_btn_strafe_left_release(self):
        if self._tcp: self._tcp.send_stop()

    def on_btn_strafe_right_press(self):
        if self._tcp:
            self._tcp.send_motion(0.6, 0.0, 0.4, speed_factor=0.9)

    def on_btn_strafe_right_release(self):
        if self._tcp: self._tcp.send_stop()

    # ── Lifecycle ─────────────────────────────────────────────────────────
    def on_enter(self):
        """Chiamata quando la schermata diventa attiva."""
        if self._tcp and self._tcp.connected and not self._stream_running:
            self.start_stream()

    def on_robot_connected(self):
        """Chiamato da main.py dopo send_init, avvia lo stream."""
        self.start_stream()

    def on_leave(self):
        """Chiamata quando si lascia la schermata."""
        self.stop_stream()
        if self._tcp:
            self._tcp.send_stop()
