#!/usr/bin/env python3
# coding=utf-8
"""
CameraScreen — stream video + controllo pan/tilt.
"""
import os
import urllib.request
import threading
import io
import platform
from datetime import datetime
from kivy.clock import Clock
from kivy.graphics.texture import Texture
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
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
        if platform.system() == 'Linux' and 'ANDROID_ARGUMENT' in os.environ:
            self._save_dir = '/sdcard/DCIM/APSSystem'
        else:
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
        if self._last_jpg is None:
            return
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        path = os.path.join(self._save_dir, f'photo_{ts}.jpg')
        with open(path, 'wb') as f:
            f.write(self._last_jpg)
        self._notify_media_store(path)
        self._show_photo_popup(path)

    def _notify_media_store(self, path):
        """Notifica Android MediaStore del nuovo file per renderlo visibile in galleria."""
        try:
            if 'ANDROID_ARGUMENT' in os.environ:
                from jnius import autoclass
                MediaScannerConnection = autoclass('android.media.MediaScannerConnection')
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                context = PythonActivity.mActivity
                MediaScannerConnection.scanFile(context, [path], None, None)
        except Exception:
            pass

    def _show_photo_popup(self, path):
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        lbl = Label(text=f'Foto salvata:\n{os.path.basename(path)}',
                    halign='center', text_size=(None, None))
        layout.add_widget(lbl)
        btn = Button(text='OK', size_hint_y=None, height=44)
        layout.add_widget(btn)
        popup = Popup(title='Foto salvata', content=layout,
                      size_hint=(0.85, 0.35), auto_dismiss=False)
        btn.bind(on_release=popup.dismiss)
        popup.open()

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
        else:
            self._recording = False
            if hasattr(self.ids, 'btn_record'):
                self.ids.btn_record.icon = 'record-circle'
                self.ids.btn_record.theme_icon_color = 'Custom'
                self.ids.btn_record.icon_color = (1, 1, 1, 1)
            if self._record_dir:
                self._show_video_popup(self._record_dir, self._record_count)

    def _show_video_popup(self, record_dir, frame_count):
        default_name = os.path.basename(record_dir)
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        layout.add_widget(Label(
            text=f'Fermata — {frame_count} frame\nCartella: {os.path.basename(os.path.dirname(record_dir))}',
            halign='center'))
        layout.add_widget(Label(text='Nome cartella:', size_hint_y=None, height=30))
        txt = TextInput(text=default_name, multiline=False, size_hint_y=None, height=40)
        layout.add_widget(txt)
        btn_layout = BoxLayout(size_hint_y=None, height=44, spacing=10)
        btn_ok = Button(text='Salva')
        btn_cancel = Button(text='Annulla')
        btn_layout.add_widget(btn_ok)
        btn_layout.add_widget(btn_cancel)
        layout.add_widget(btn_layout)
        popup = Popup(title='Video salvato', content=layout,
                      size_hint=(0.85, 0.55), auto_dismiss=False)

        def on_ok(instance):
            new_name = txt.text.strip()
            if new_name and new_name != default_name:
                new_path = os.path.join(os.path.dirname(record_dir), new_name)
                try:
                    os.rename(record_dir, new_path)
                    self._notify_media_store(new_path)
                except Exception:
                    pass
            else:
                self._notify_media_store(record_dir)
            popup.dismiss()

        def on_cancel(instance):
            import shutil
            try:
                shutil.rmtree(record_dir)
            except Exception:
                pass
            popup.dismiss()

        btn_ok.bind(on_release=on_ok)
        btn_cancel.bind(on_release=on_cancel)
        popup.open()

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
