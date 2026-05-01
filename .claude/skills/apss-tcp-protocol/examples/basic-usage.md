# TCP Yahboom — Esempi Base

Pacchetti pronti all'uso, tutti verificati con `validate.py`.

---

## Sequenza minima obbligatoria

Ogni sessione TCP deve iniziare con questi due comandi nell'ordine:

```python
import socket

HOST = "192.168.1.158"  # hawk
PORT = 6000

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((HOST, PORT))

# 1. Init — obbligatorio, senza questo i comandi vengono ignorati
sock.sendall(b"$020f040116#")

# 2. Stop — stato sicuro di partenza
sock.sendall(b"$021a0c000000000028#")
```

---

## Stop

```python
sock.sendall(b"$021a0c000000000028#")
```

---

## Movimento avanti / indietro

```python
# Avanti — speed ~60%
sock.sendall(b"$021a0c3c3c3c3c0018#")

# Indietro — speed ~60%
sock.sendall(b"$021a0cc4c4c4c40038#")
```

Generare pacchetti a velocità personalizzata:

```python
from scripts.validate import build_mecanum

sock.sendall(build_mecanum(1.0, 0.0, 0.0, speed=55).encode())   # avanti
sock.sendall(build_mecanum(-1.0, 0.0, 0.0, speed=55).encode())  # indietro
```

---

## Rotazione sul posto

```python
# Rotazione oraria (destra)
sock.sendall(build_mecanum(0.0, 0.0, 1.0, speed=60).encode())

# Rotazione antioraria (sinistra)
sock.sendall(build_mecanum(0.0, 0.0, -1.0, speed=60).encode())
```

---

## Traslazione laterale (strafe)

```python
# Strafe destra
sock.sendall(build_mecanum(0.0, 1.0, 0.0, speed=60).encode())

# Strafe sinistra
sock.sendall(build_mecanum(0.0, -1.0, 0.0, speed=60).encode())
```

---

## Controllo servo

```python
from scripts.validate import build_servo

# Pan a 90°
sock.sendall(build_servo(2, 90).encode())

# Tilt a 90°
sock.sendall(build_servo(1, 90).encode())

# Home (valori fisici APSS)
sock.sendall(build_servo(2, 100).encode())  # Pan home = 100°
sock.sendall(build_servo(1, 95).encode())   # Tilt home = 95°
```

Pacchetti home pre-calcolati:

```python
PAN_HOME  = b"$02110602647f#"   # Pan  id=2 angle=100
TILT_HOME = b"$021106015f79#"   # Tilt id=1 angle=95
```

---

## Pattern di movimento completo con stop finale

```python
import time
from scripts.validate import build_mecanum, build_servo

INIT = b"$020f040116#"
STOP = b"$021a0c000000000028#"

sock.sendall(INIT)
sock.sendall(STOP)
time.sleep(0.1)

# Avanti 1 secondo
sock.sendall(build_mecanum(1.0, 0.0, 0.0, 55).encode())
time.sleep(1.0)

# Stop — sempre immediato, nessun smorzamento
sock.sendall(STOP)
time.sleep(0.1)

# Pan home
sock.sendall(build_servo(2, 100).encode())
time.sleep(0.5)

sock.close()
```

> ⚠️ Lo stop deve essere sempre immediato — non applicare smoothing ai comandi di stop.
> Il `MotionSmoother` (quando implementato) deve escludere i comandi stop.

---

→ Casi più complessi in `@examples/advanced.md`
