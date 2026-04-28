#!/usr/bin/env python3
# coding=utf-8
"""
Client TCP per comunicazione con il robot Rosmaster R2.
Protocollo Yahboom ASCII hex: $[payload_hex][checksum_hex]#

Mappatura verificata dal log dell'app Yahboom originale:
  num_x (byte 4) → speed_y = -num_x/100  (laterale sx/dx)
  num_y (byte 5) → speed_x =  num_y/100  (avanti/indietro)

Quindi per inviare:
  avanti  (vx=+0.3) → num_x=0x00, num_y=int(+0.3*100)=0x1e
  indietro(vx=-0.3) → num_x=0x00, num_y=int(-0.3*100)&0xFF=0xe2
  str.sx  (vy=+0.3) → num_x=int(-0.3*100)&0xFF=0xe2, num_y=0x00
  str.dx  (vy=-0.3) → num_x=int(+0.3*100)=0x1e, num_y=0x00
"""
import socket
import threading
import logging

logger = logging.getLogger(__name__)


class TCPClient:
    """
    Client TCP che comunica con rosmaster_main.py sulla porta 6000.
    Thread-safe — i comandi possono essere inviati da qualsiasi thread.
    """

    def __init__(self, host="192.168.1.158", port=6000):
        self.host = host
        self.port = port
        self._sock = None
        self._connected = False
        self._lock = threading.Lock()
        self._recv_thread = None
        self._running = False

        self.on_connected = None
        self.on_disconnected = None
        self.on_data = None

    # ── Connessione ───────────────────────────────────────────────────────
    def connect(self):
        t = threading.Thread(target=self._connect_worker, daemon=True)
        t.start()

    def _connect_worker(self):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5.0)
            sock.connect((self.host, self.port))
            sock.settimeout(None)
            with self._lock:
                self._sock = sock
                self._connected = True
                self._running = True
            logger.info(f"Connesso a {self.host}:{self.port}")
            if self.on_connected:
                self.on_connected()
            self._recv_thread = threading.Thread(
                target=self._recv_worker, daemon=True)
            self._recv_thread.start()
        except Exception as e:
            logger.error(f"Errore connessione: {e}")
            self._connected = False
            if self.on_disconnected:
                self.on_disconnected()

    def disconnect(self):
        self._running = False
        self._connected = False
        with self._lock:
            if self._sock:
                try:
                    self._sock.close()
                except Exception:
                    pass
                self._sock = None
        if self.on_disconnected:
            self.on_disconnected()

    @property
    def connected(self):
        return self._connected

    # ── Ricezione ─────────────────────────────────────────────────────────
    def _recv_worker(self):
        while self._running:
            try:
                with self._lock:
                    sock = self._sock
                if not sock:
                    break
                data = sock.recv(4096)
                if not data:
                    break
                if self.on_data:
                    self.on_data(data)
            except Exception as e:
                if self._running:
                    logger.error(f"Errore ricezione: {e}")
                break
        self._connected = False
        if self.on_disconnected:
            self.on_disconnected()

    # ── Invio raw ─────────────────────────────────────────────────────────
    def send_raw(self, data: bytes) -> bool:
        with self._lock:
            if not self._connected or not self._sock:
                return False
            try:
                self._sock.sendall(data)
                return True
            except Exception as e:
                logger.error(f"Errore invio: {e}")
                self._connected = False
                return False

    # ── Costruzione comando ───────────────────────────────────────────────
    def _cmd(self, data_bytes: list) -> bytes:
        """
        Costruisce il comando nel formato Yahboom ASCII hex.
        Formato: $[data_bytes in hex][checksum hex]#
        Il checksum è la somma di tutti i byte % 256.
        """
        checksum = sum(data_bytes) % 256
        hex_str = "".join(f"{b:02x}" for b in data_bytes)
        return f"${hex_str}{checksum:02x}#".encode()

    # ── Inizializzazione ──────────────────────────────────────────────────
    def send_init(self) -> bool:
        """
        Invia il comando di inizializzazione modalita MecanumWheel.
        Obbligatorio subito dopo la connessione — imposta car_type=02
        e modalita=2 (MecanumWheel) sul server rosmaster_main.py.
        Comando fisso verificato dal log: $020f040116#
        """
        return self.send_raw(b"$020f040116#")

    # ── Movimento principale ──────────────────────────────────────────────
    def _mecanum(self, vx, vy, vz, speed=55, speed_factor=1.0):
        """
        Cinematica Mecanum verificata fisicamente sul robot.
        vx: avanti/indietro (+avanti)
        vy: laterale (+destra)
        vz: rotazione (+orario)
        Segni verificati con test_cinematica.py:
        m1 = vx - vy + vz  (anteriore sinistra)
        m2 = vx + vy - vz  (anteriore destra)
        m3 = vx + vy + vz  (posteriore sinistra)
        m4 = vx - vy - vz  (posteriore destra)
        """
        m1 = vx - vy + vz
        m2 = vx + vy - vz
        m3 = vx + vy + vz
        m4 = vx - vy - vz
        # Normalizza e scala a speed
        speed_out = int(speed * speed_factor)
        max_val = max(abs(m1), abs(m2), abs(m3), abs(m4), 1)
        m1 = int(m1 / max_val * speed_out)
        m2 = int(m2 / max_val * speed_out)
        m3 = int(m3 / max_val * speed_out)
        m4 = int(m4 / max_val * speed_out)
        return m1, m2, m3, m4

    def send_motion(self, vx, vy, vz=0.0, speed_factor=1.0, speed=55) -> bool:
        """Invia movimento usando cinematica Mecanum diretta — cmd 0x1A."""
        m1, m2, m3, m4 = self._mecanum(vx, vy, vz, speed=speed, speed_factor=speed_factor)
        # converti signed a unsigned byte
        data = [0x02, 0x1A, 0x0C,
                m1 & 0xFF, m2 & 0xFF, m3 & 0xFF, m4 & 0xFF, 0x00]
        checksum = sum(data) % 256
        hex_str = "".join(f"{b:02x}" for b in data)
        return self.send_raw(f"${hex_str}{checksum:02x}#".encode())

    # ── Comandi di movimento ──────────────────────────────────────────────
    def send_stop(self) -> bool:
        return self.send_motion(0.0, 0.0, 0.0)

    def send_forward(self, speed=0.5) -> bool:
        return self.send_motion(1.0, 0.0, 0.0)

    def send_backward(self, speed=0.5) -> bool:
        return self.send_motion(-1.0, 0.0, 0.0)

    def send_rotate_left(self, speed=0.5) -> bool:
        """Curva a sinistra — avanza con rotazione sinistra."""
        return self.send_motion(0.6, 0.0, -0.4)

    def send_rotate_right(self, speed=0.5) -> bool:
        """Curva a destra — avanza con rotazione destra."""
        return self.send_motion(0.6, 0.0, 0.4)

    def send_strafe_left(self, speed=0.5) -> bool:
        """Perno a sinistra — speculare a strafe destra."""
        return self.send_motion(0.0, 0.0, -1.0)

    def send_strafe_right(self, speed=0.5) -> bool:
        """Perno a destra."""
        return self.send_motion(0.0, 0.0, 1.0)

    def send_servo(self, servo_id: int, angle: int) -> bool:
        """
        Invia comando PWM servo — cmd 0x11.
        servo_id: 1=Tilt (S1), 2=Pan (S2)
        angle: 0-180 gradi
        """
        angle = max(0, min(180, angle))  # clamp 0-180
        data = [0x02, 0x11, 0x06, servo_id & 0xFF, angle & 0xFF]
        checksum = sum(data) % 256
        hex_str = "".join(f"{b:02x}" for b in data)
        return self.send_raw(f"${hex_str}{checksum:02x}#".encode())

    def send_pan(self, angle: int) -> bool:
        """Pan — S2 (servo_id=2)."""
        return self.send_servo(2, angle)

    def send_tilt(self, angle: int) -> bool:
        """Tilt — S1 (servo_id=1)."""
        return self.send_servo(1, angle)
