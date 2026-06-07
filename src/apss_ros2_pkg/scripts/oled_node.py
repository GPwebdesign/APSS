#!/usr/bin/env python3
# coding=utf-8
"""
APSS — OLED Display Node
Mostra su display SSD1306 128x64 I2C:
  - Nome sistema + IP
  - Stato batteria (con fallback INA219 diretto se /battery e' stale)
  - Modalita operativa (riservato a usi futuri)
  - Sensori ambientali (riservato a usi futuri)
Subscribers:
  /apss/mode        (std_msgs/String)
  /apss/sensors/env (std_msgs/String — JSON)
  /battery          (sensor_msgs/BatteryState)
  /apss/oled_alert  (std_msgs/String — JSON {"messages": [...]})
"""
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from sensor_msgs.msg import BatteryState
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

try:
    import board
    import adafruit_ina219
    INA219_LIB_AVAILABLE = True
except ImportError:
    INA219_LIB_AVAILABLE = False


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
        self._ip               = get_ip()
        self._mode             = "STANDBY"
        self._batt_volts       = None   # float o None
        self._batt_amps        = None
        self._batt_watts       = None
        self._battery_source   = 'none'  # 'ros' | 'direct' | 'none'
        self._last_battery_msg_ts = 0.0
        self._temp             = "--"
        self._hum              = "--"
        self._gas              = "--"
        self._alert_messages   = []
        self._alert_scroll_x   = 128
        self._alert_scroll_text = ""
        self._alert_text_width  = 0
        self._lock             = threading.Lock()

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
                    self._font_xl = ImageFont.truetype(
                        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 18)
                except Exception:
                    self._font_large = ImageFont.load_default()
                    self._font_small = ImageFont.load_default()
                    self._font_xl    = ImageFont.load_default()
                self._oled_ok = True
                self.get_logger().info('Display OLED SSD1306 inizializzato!')
            except Exception as e:
                self._oled_ok = False
                self.get_logger().warn(f'OLED non disponibile: {e}')
        else:
            self._oled_ok = False
            self.get_logger().warn('luma.oled non installato — display disabilitato')

        # Inizializza INA219 diretto (fallback se /battery e' stale)
        self._ina    = None
        self._ina_ok = False
        if INA219_LIB_AVAILABLE:
            try:
                self._ina    = adafruit_ina219.INA219(board.I2C())
                self._ina_ok = True
                self.get_logger().info('INA219 diretto inizializzato su 0x40')
            except Exception as e:
                self.get_logger().warn(f'INA219 diretto non disponibile: {e}')

        # Subscribers
        self.create_subscription(String, '/apss/mode',
                                 self._mode_cb, 10)
        self.create_subscription(BatteryState, '/battery',
                                 self._battery_state_cb, 10)
        self.create_subscription(String, '/apss/sensors/env',
                                 self._env_cb, 10)
        self.create_subscription(String, '/apss/oled_alert',
                                 self._oled_alert_cb, 10)

        # Timer aggiornamento display 2Hz
        self.create_timer(0.5, self._update_display)

        self.get_logger().info('OLED Node avviato!')

    # ── Lettura diretta INA219 ────────────────────────────────────────────
    def _read_ina219_direct(self):
        """Legge tensione, corrente e potenza direttamente dall'INA219.
        Ritorna (V, A, W) con corrente positiva = scarica, o None in caso di errore.
        """
        if not self._ina_ok:
            return None
        try:
            volts = self._ina.bus_voltage          # V
            amps  = self._ina.current / 1000.0     # mA → A (positivo = scarica)
            watts = volts * abs(amps)
            return (volts, amps, watts)
        except Exception as e:
            self.get_logger().warn(f'Errore lettura INA219 diretto: {e}')
            return None

    # ── Callbacks ────────────────────────────────────────────────────────
    def _mode_cb(self, msg: String):
        with self._lock:
            self._mode = msg.data[:10].upper()

    def _battery_state_cb(self, msg: BatteryState):
        """Callback da battery_node — sensor_msgs/BatteryState (fonte dati reale INA219)."""
        try:
            volts = msg.voltage
            # BatteryState ROS2: positivo = carica; invertiamo per positivo = scarica
            amps  = -msg.current
            watts = volts * abs(amps)
            with self._lock:
                self._batt_volts          = volts
                self._batt_amps           = amps
                self._batt_watts          = watts
                self._last_battery_msg_ts = time.monotonic()
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

    def _oled_alert_cb(self, msg: String):
        try:
            self.get_logger().info(f'[OLED] alert ricevuto: {msg.data[:50]}')
            data = json.loads(msg.data)
            messages = data.get('messages', [])
            new_text = "APSS  |  " + "  |  ".join(messages) if messages else ""
            with self._lock:
                if new_text != self._alert_scroll_text:
                    self._alert_scroll_x   = 128
                    self._alert_text_width = 0
                self._alert_scroll_text = new_text
                self._alert_messages    = messages
        except Exception as e:
            self.get_logger().warning(f'[OLED] oled_alert parse error: {e}')

    # ── Aggiornamento display ─────────────────────────────────────────────
    def _update_display(self):
        if not self._oled_ok:
            return
        with self._lock:
            ip                = self._ip
            last_ts           = self._last_battery_msg_ts
            volts             = self._batt_volts
            amps              = self._batt_amps
            watts             = self._batt_watts
            alert_messages    = list(self._alert_messages)
            alert_scroll_x    = self._alert_scroll_x
            alert_scroll_text = self._alert_scroll_text
            alert_text_width  = self._alert_text_width

        # Watchdog 5s su /battery: se stale usa lettura diretta INA219
        now = time.monotonic()
        if last_ts > 0.0 and (now - last_ts) <= 5.0:
            batt_source = 'ros'
            batt_v, batt_a, batt_w = volts, amps, watts
        else:
            direct = self._read_ina219_direct()
            if direct is not None:
                batt_source = 'direct'
                batt_v, batt_a, batt_w = direct
            else:
                batt_source = 'none'
                batt_v = batt_a = batt_w = None

        with self._lock:
            self._battery_source = batt_source

        # Componi stringhe di visualizzazione
        if batt_v is not None:
            prefix   = '*' if batt_source == 'direct' else ''
            volt_str = f"{prefix}{batt_v:.2f}V"
        else:
            volt_str = "--.--V"

        if batt_a is not None and batt_w is not None:
            curr_str = f"{batt_a:.2f}A  {batt_w:.2f}W"
        else:
            curr_str = "--.--A  --.--W"

        try:
            with canvas(self._device) as draw:
                # Riga 0 — scrolling alert o "APSS" centrato (font_large 14) a y=0
                if alert_messages:
                    if alert_text_width == 0:
                        alert_text_width = int(draw.textlength(
                            alert_scroll_text, font=self._font_large))
                        with self._lock:
                            self._alert_text_width = alert_text_width
                    draw.text((alert_scroll_x, 0),
                              alert_scroll_text,
                              font=self._font_large, fill="white")
                    if alert_scroll_x < -alert_text_width:
                        alert_scroll_x = 128
                    else:
                        alert_scroll_x -= 8
                else:
                    text_width = draw.textlength("APSS", font=self._font_large)
                    x = (128 - text_width) // 2
                    draw.text((x, 0), "APSS", font=self._font_large, fill="white")
                # Separatore
                draw.line([(0, 17), (128, 17)], fill="white", width=1)
                # Riga 1 — IP centrato (font_small 11) a y=20
                text_width = draw.textlength(ip, font=self._font_small)
                x = (128 - text_width) // 2
                draw.text((x, 20), ip, font=self._font_small, fill="white")
                # Riga 2 — voltaggio (font_xl 18) a y=33
                draw.text((0, 33), volt_str, font=self._font_xl, fill="white")
                # Riga 3 — corrente e potenza (font_small 11) a y=53
                draw.text((0, 53), curr_str, font=self._font_small, fill="white")
        except Exception as e:
            self.get_logger().warn(f'Errore display: {e}')

        with self._lock:
            self._alert_scroll_x = alert_scroll_x

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
