# TCP Yahboom — Esempi Avanzati

---

## Cinematica Mecanum completa — da (vx, vy, vz) a pacchetto 0x1A

La formula è verificata fisicamente sul robot APSS. M1 e M4 hanno polarità
invertita (fili scambiati sul connettore) — la formula compensa già questo.

```python
def mecanum_to_motors(vx: float, vy: float, vz: float, speed: int = 60):
    """
    vx : avanti (+) / indietro (-)   range -1.0..+1.0
    vy : destra  (+) / sinistra (-)  range -1.0..+1.0
    vz : orario  (+) / antiorario(-) range -1.0..+1.0
    speed : velocità base 0-100

    Ritorna (m1, m2, m3, m4) valori signed -100..+100
    """
    m1 = int((vx - vy + vz) * speed)   # ant. sinistro — polarità inv.
    m2 = int((vx + vy - vz) * speed)   # ant. destro
    m3 = int((vx + vy + vz) * speed)   # post. sinistro
    m4 = int((vx - vy - vz) * speed)   # post. destro — polarità inv.

    # Clamp -100..+100
    clamp = lambda v: max(-100, min(100, v))
    return clamp(m1), clamp(m2), clamp(m3), clamp(m4)


def build_0x1A(m1: int, m2: int, m3: int, m4: int) -> bytes:
    """Costruisce pacchetto 0x1A da 4 valori motore signed."""
    def to_byte(v): return v & 0xFF
    payload = [0x02, 0x1A, 0x0C,
               to_byte(m1), to_byte(m2), to_byte(m3), to_byte(m4), 0x00]
    cs = sum(payload) % 256
    return ("$" + "".join(f"{b:02x}" for b in payload) + f"{cs:02x}#").encode()


# Uso:
m1, m2, m3, m4 = mecanum_to_motors(0.8, 0.2, 0.0, speed=55)
packet = build_0x1A(m1, m2, m3, m4)
sock.sendall(packet)
```

**Tabella movimenti di riferimento (speed=60):**

| Movimento | vx | vy | vz | M1 | M2 | M3 | M4 |
|-----------|----|----|----|----|----|----|-----|
| Avanti | +1 | 0 | 0 | +60 | +60 | +60 | +60 |
| Indietro | -1 | 0 | 0 | -60 | -60 | -60 | -60 |
| Strafe dx | 0 | +1 | 0 | -60 | +60 | +60 | -60 |
| Strafe sx | 0 | -1 | 0 | +60 | -60 | -60 | +60 |
| Rot oraria | 0 | 0 | +1 | +60 | -60 | +60 | -60 |
| Rot antioraria | 0 | 0 | -1 | -60 | +60 | -60 | +60 |
| Curva avanti dx | +1 | 0 | +0.4 | +84 | +36 | +84 | +36 |

---

## Integrazione in tcp_client.py (Kivy app)

Pattern usato in `rosmaster_kivy/network/tcp_client.py`:

```python
class TcpClient:
    INIT    = b"$020f040116#"
    STOP    = b"$021a0c000000000028#"
    PAN_HOME  = b"$02110602647f#"   # Pan  id=2 angle=100
    TILT_HOME = b"$021106015f79#"   # Tilt id=1 angle=95

    def send_motion(self, vx: float, vy: float, vz: float, speed: int = 55):
        m1 = int((vx - vy + vz) * speed)
        m2 = int((vx + vy - vz) * speed)
        m3 = int((vx + vy + vz) * speed)
        m4 = int((vx - vy - vz) * speed)
        clamp = lambda v: max(-100, min(100, v))
        m1, m2, m3, m4 = clamp(m1), clamp(m2), clamp(m3), clamp(m4)
        def tb(v): return v & 0xFF
        payload = [0x02, 0x1A, 0x0C, tb(m1), tb(m2), tb(m3), tb(m4), 0x00]
        cs = sum(payload) % 256
        pkt = ("$" + "".join(f"{b:02x}" for b in payload) + f"{cs:02x}#").encode()
        self._sock.sendall(pkt)

    def send_stop(self):
        self._sock.sendall(self.STOP)   # stop sempre immediato, nessun delay

    def send_servo(self, servo_id: int, angle: int):
        """servo_id: 1=Tilt, 2=Pan — angle: 0-180"""
        angle = max(0, min(180, angle))
        payload = [0x02, 0x11, 0x06, servo_id, angle]
        cs = sum(payload) % 256
        pkt = ("$" + "".join(f"{b:02x}" for b in payload) + f"{cs:02x}#").encode()
        self._sock.sendall(pkt)
```

---

## parse_data — lato server (rosmaster_main.py)

Come il server decodifica i pacchetti in entrata:

```python
def parse_data(client, data):
    # data = stringa tipo "$021a0c3c3c3c3c0018#"
    car_type = int(data[1:3], 16)   # byte [0]
    cmd      = data[3:5].upper()    # byte [1] — .upper() OBBLIGATORIO
    length   = int(data[5:7], 16)   # byte [2]
    # data bytes iniziano da posizione 7 della stringa (indice 3 del payload)

    if cmd == "1A":
        m1 = int(data[7:9],   16)
        m2 = int(data[9:11],  16)
        m3 = int(data[11:13], 16)
        m4 = int(data[13:15], 16)
        # conversione signed
        def to_signed(b): return b if b < 128 else b - 256
        set_motor(to_signed(m1), to_signed(m2), to_signed(m3), to_signed(m4))

    elif cmd == "11":
        servo_id = int(data[7:9],  16)
        angle    = int(data[9:11], 16)
        set_pwm_servo(servo_id, angle)
```

> ⚠️ Senza `.upper()` su `cmd`, i pacchetti inviati in minuscolo (`1a`, `0f`, `11`)
> vengono silenziosamente ignorati dal server — bug già corretto in APSS.

---

## Sequenza pattugliamento — esempio strutturato

```python
import time, socket
from scripts.validate import build_mecanum, build_servo

INIT = b"$020f040116#"
STOP = b"$021a0c000000000028#"

def patrol_square(sock, speed=50, side_sec=1.5):
    """Percorre un quadrato: avanti → rot dx → avanti → rot dx → ..."""
    sock.sendall(INIT)
    sock.sendall(STOP)
    time.sleep(0.2)

    for _ in range(4):
        # Lato
        sock.sendall(build_mecanum(1.0, 0.0, 0.0, speed).encode())
        time.sleep(side_sec)
        sock.sendall(STOP)
        time.sleep(0.3)

        # Rotazione 90° (durata empirica ~0.8s a speed=50)
        sock.sendall(build_mecanum(0.0, 0.0, 1.0, speed).encode())
        time.sleep(0.8)
        sock.sendall(STOP)
        time.sleep(0.3)

    # Camera home
    sock.sendall(build_servo(2, 100).encode())  # Pan
    time.sleep(0.3)
    sock.sendall(build_servo(1, 95).encode())   # Tilt


with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect(("192.168.1.158", 6000))
    patrol_square(s)
```

---

## Verifica pacchetti a runtime con validate.py

```python
from scripts.validate import verify, build_mecanum

pkt = build_mecanum(0.8, 0.2, 0.0, 55)
result = verify(pkt)

if not result["valid"]:
    raise ValueError(f"Pacchetto non valido: {pkt}")

d = result["decoded"]
print(f"M1={d['M1_ant_sx']} M2={d['M2_ant_dx']} M3={d['M3_post_sx']} M4={d['M4_post_dx']}")
sock.sendall(pkt.encode())
```

→ Riferimento completo protocollo in `@references/commands.md`  
→ Algoritmo checksum in `@references/checksum.md`
