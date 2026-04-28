#!/usr/bin/env python3
# coding=utf-8
"""
Rosmaster R2 — App di controllo Kivy/KivyMD
"""
import os
os.environ["KIVY_NO_ENV_CONFIG"] = "1"

from kivymd.app import MDApp
from kivymd.uix.screenmanager import MDScreenManager
from kivy.lang import Builder
from kivy.core.window import Window
from kivy.clock import Clock

from network.tcp_client import TCPClient
from screens.main_screen import MainScreen
from screens.settings_screen import SettingsScreen
from screens.patrol_screen import PatrolScreen
from screens.alert_screen import AlertScreen
from screens.status_screen import StatusScreen
from screens.camera_screen import CameraScreen


class RosmasterApp(MDApp):

    def build(self):
        # Tema dark Material Design
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Blue"
        self.theme_cls.accent_palette = "Teal"
        self.title = "Autonomous Patrol and Surveillance System"

        # Orientamento portrait su mobile
        Window.softinput_mode = "below_target"

        # Carica il file .kv
        Builder.load_file("rosmaster.kv")

        # Screen manager
        self.sm = MDScreenManager()
        self.sm.add_widget(MainScreen(name="main"))
        self.sm.add_widget(PatrolScreen(name="patrol"))
        self.sm.add_widget(AlertScreen(name="alert"))
        self.sm.add_widget(SettingsScreen(name="settings"))
        self.sm.add_widget(StatusScreen(name="status"))
        self.sm.add_widget(CameraScreen(name="camera"))

        # Client TCP
        self.tcp = TCPClient(
            host="192.168.1.158",
            port=6000
        )
        self.tcp.on_connected    = self._on_robot_connected
        self.tcp.on_disconnected = self._on_robot_disconnected

        # Collega TCP alla MainScreen
        main = self.sm.get_screen("main")
        main.set_tcp_client(self.tcp)
        camera = self.sm.get_screen("camera")
        camera.set_tcp_client(self.tcp)

        return self.sm

    # ── Navigazione ───────────────────────────────────────────────────────
    def go_screen(self, name: str):
        self.sm.current = name

    # ── Connessione ───────────────────────────────────────────────────────
    def toggle_connection(self):
        if self.tcp.connected:
            self.tcp.disconnect()
        else:
            self.tcp.connect()

    def _on_robot_connected(self):
        self.tcp.send_init()
        main = self.sm.get_screen("main")
        Clock.schedule_once(lambda dt: main.on_robot_connected(), 0.5)
        camera = self.sm.get_screen("camera")
        Clock.schedule_once(lambda dt: camera.start_stream(), 0.5)
        Clock.schedule_once(lambda dt: self._update_conn_ui(True))

    def _on_robot_disconnected(self):
        Clock.schedule_once(lambda dt: self._update_conn_ui(False))

    def _update_conn_ui(self, connected: bool):
        main = self.sm.get_screen("main")
        if connected:
            main.ids.conn_icon.text_color  = (0, 0.85, 0.6, 1)
            main.ids.conn_label.text       = f"Connesso — {self.tcp.host}"
        else:
            main.ids.conn_icon.text_color  = (0.90, 0.25, 0.25, 1)
            main.ids.conn_label.text       = "Non connesso"

    # ── Impostazioni ──────────────────────────────────────────────────────
    def save_settings(self):
        s = self.sm.get_screen("settings")
        self.tcp.host = s.ids.robot_ip.text
        self.tcp.port = int(s.ids.tcp_port.text)
        stream_url = f"http://{s.ids.robot_ip.text}:{s.ids.stream_port.text}"
        main = self.sm.get_screen("main")
        main.STREAM_URL = stream_url
        self.go_screen("main")


if __name__ == "__main__":
    RosmasterApp().run()
