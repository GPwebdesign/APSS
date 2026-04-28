#!/usr/bin/env python3
# coding=utf-8
"""
APSS — OLED Display Node
Mostra su display SSD1306 128x64 I2C:
  - Nome sistema + IP
  - Stato batteria
  - Modalita operativa
  - Sensori ambientali (DHT-11, gas)
Subscribers:
  /apss/mode    (std_msgs/String)
  /apss/battery (std_msgs/String — JSON)
  /apss/sensors/env (std_msgs/String — JSON)
"""
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import json
import socket
import threading
import time

try:
    from luma.core.interface.serial import i2c
    from luma.oled.device import ssd1306
    from luma.core.render import canvas
    from PIL import ImageFont
    OLED_AVAILABLE = True
except ImportError:
    OLED_AVAILABLE = False


def get_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "no network"


class OledNode(Node):

    def __init__(self):
        super().__init__('oled_node')

        # Stato display
        self._ip      = get_ip()
        self._mode    = "STANDBY"
        self._batt_v  = "--.-V"
        self._batt_pct= "--%"
        self._temp    = "--"
        self._hum     = "--"
        self._gas     = "--"
        self._lock    = threading.Lock()

        # Inizializza display
        if OLED_AVAILABLE:
            try:
                serial = i2c(port=1, address=0x3C)
                self._device = ssd1306(serial, width=128, height=64)
                try:
                    self._font_large = ImageFont.truetype(
                        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 14)
                    self._font_small = ImageFont.truetype(
                        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 11)
                except Exception:
                    self._font_large = ImageFont.load_default()
                    self._font_small = ImageFont.load_default()
                self._oled_ok = True
                self.get_logger().info('Display OLED SSD1306 inizializzato!')
            except Exception as e:
                self._oled_ok = False
                self.get_logger().warn(f'OLED non disponibile: {e}')
        else:
            self._oled_ok = False
            self.get_logger().warn('luma.oled non installato — display disabilitato')

        # Subscribers
        self.create_subscription(String, '/apss/mode',
                                 self._mode_cb, 10)
        self.create_subscription(String, '/apss/battery',
                                 self._battery_cb, 10)
        self.create_subscription(String, '/apss/sensors/env',
                                 self._env_cb, 10)

        # Timer aggiornamento display 2Hz
        self.create_timer(0.5, self._update_display)

        self.get_logger().info('OLED Node avviato!')

    # ── Callbacks ────────────────────────────────────────────────────────
    def _mode_cb(self, msg: String):
        with self._lock:
            self._mode = msg.data[:10].upper()

    def _battery_cb(self, msg: String):
        try:
            data = json.loads(msg.data)
            v   = data.get('voltage', 0.0)
            pct = data.get('percent', 0)
            with self._lock:
                self._batt_v   = f"{v:.1f}V"
                self._batt_pct = f"{pct:.0f}%"
        except Exception:
            pass

    def _env_cb(self, msg: String):
        try:
            data = json.loads(msg.data)
            with self._lock:
                self._temp = f"{data.get('temperature', '--'):.0f}"
                self._hum  = f"{data.get('humidity', '--'):.0f}"
        except Exception:
            pass

    # ── Aggiornamento display ─────────────────────────────────────────────
    def _update_display(self):
        if not self._oled_ok:
            return
        with self._lock:
            ip      = self._ip
            mode    = self._mode
            batt_v  = self._batt_v
            batt_pct= self._batt_pct
            temp    = self._temp
            hum     = self._hum
            gas     = self._gas

        try:
            with canvas(self._device) as draw:
                # Riga 1 — "APSS" centrato
                text_width = draw.textlength("APSS", font=self._font_large)
                x = (128 - text_width) // 2
                draw.text((x, 0), "APSS", font=self._font_large, fill="white")
                # Separatore
                draw.line([(0, 17), (128, 17)], fill="white", width=1)
                # Riga 3 — IP centrato
                text_width = draw.textlength(ip, font=self._font_small)
                x = (128 - text_width) // 2
                draw.text((x, 20), ip, font=self._font_small, fill="white")
                # Riga 4 — modalita
                draw.text((0, 29), f"Mode:{mode}",
                          font=self._font_small, fill="white")
                # Riga 5 — sensori
                draw.text((0, 41), f"T:{temp}C H:{hum}%",
                          font=self._font_small, fill="white")
                # Riga 6 — gas
                draw.text((0, 52), f"Gas:{gas}",
                          font=self._font_small, fill="white")
        except Exception as e:
            self.get_logger().warn(f'Errore display: {e}')

    def destroy_node(self):
        if self._oled_ok:
            self._device.cleanup()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = OledNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
