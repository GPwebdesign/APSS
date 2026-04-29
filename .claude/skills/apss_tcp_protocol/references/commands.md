# TCP Yahboom — Comandi Implementati

## Struttura generale

```
$ [cartype] [cmd] [len] [data...] [checksum] #
  2hex       2hex  2hex  Nhex      2hex

cartype = 02  (X3_PLUS Mecanum — fisso per APSS)
len     = (numero byte data) + 2
checksum = sum(tutti i byte del payload) % 256
```

---

## 0x0F — Inizializzazione

**Obbligatorio** dopo ogni connessione TCP. Senza questo il server ignora i comandi.

```
$ 02 0F 04 01 16 #
  |  |  |  |  |
  |  |  |  |  checksum = (02+0F+04+01) % 256 = 16
  |  |  |  g_mode = 01 (Standard)
  |  |  len = 04
  |  cmd = 0F
  cartype = 02
```

Pacchetto pronto: `$020f040116#`

---

## 0x1A — Set Motor Diretto ✓ PREFERITO

Controlla i 4 motori individualmente. Usare **sempre questo** al posto di `0x10`.

```
$ 02 1A 0C [m1] [m2] [m3] [m4] 00 [cs] #
  |  |  |   |    |    |    |   |   |
  |  |  |   |    |    |    |   |   checksum
  |  |  |   |    |    |    |   byte padding
  |  |  |   M1   M2   M3   M4  (valori signed, range -100..+100, in hex 2 compl.)
  |  |  len = 0C  ← CRITICO: 0x0C non 0x0A
  |  cmd = 1A
  cartype = 02
```

**Mappatura motori APSS:**

| Variabile | Motore | Posizione | Formula |
|-----------|--------|-----------|---------|
| M1 | ant. sinistro | polarità invertita | `vx - vy + vz` |
| M2 | ant. destro | normale | `vx + vy - vz` |
| M3 | post. sinistro | normale | `vx + vy + vz` |
| M4 | post. destro | polarità invertita | `vx - vy - vz` |

Conversione valore → hex (signed, 1 byte):
```python
def to_hex_byte(val: float) -> int:
    return int(val) & 0xFF  # gestisce i negativi in complemento a 2
```

Stop (tutti a zero): `$021a0c000000000028#`

---

## 0x11 — Servo PWM

Controlla un servo singolo per posizione angolare.

```
$ 02 11 06 [id] [angle] [cs] #
  |  |  |   |    |       |
  |  |  |   |    |       checksum
  |  |  |   |    angolo in gradi (0-180) → hex
  |  |  |   id servo
  |  |  len = 06
  |  cmd = 11
  cartype = 02
```

**ID servo APSS** (swap fisico rispetto a denominazione Yahboom):

| id | Servo fisico | Home |
|----|-------------|------|
| 1  | S1 = Tilt   | 95°  |
| 2  | S2 = Pan    | 100° |

Esempio — Pan a 90°: `$ 02 11 06 02 5A [cs] #`  
checksum = (02+11+06+02+5A) % 256 = `75` → pacchetto: `$021106025a75#`

---

## 0x10 — Movimento Base (legacy)

Usato dall'app Yahboom originale. **Preferire 0x1A** per controllo Mecanum preciso.

```
$ 02 10 08 [num_x] [num_y] 00 00 [cs] #
  |  |  |   |       |
  |  |  |   laterale (-vy*100) & 0xFF
  |  |  |   avanti/indietro (vx*100) & 0xFF
  |  |  len = 08
  |  cmd = 10
  cartype = 02
```

---

## Algoritmo checksum — Python

```python
def checksum(payload: list[int]) -> int:
    """payload = tutti i byte PRIMA del checksum (cartype incluso)"""
    return sum(payload) % 256

def build_cmd(cmd_id: int, data: list[int]) -> bytes:
    car_type = 0x02
    length = len(data) + 2
    payload = [car_type, cmd_id, length] + data
    cs = checksum(payload)
    hex_str = "".join(f"{b:02x}" for b in payload)
    return f"${hex_str}{cs:02x}#".encode()
```

→ Esempi pratici in `@examples/basic-usage.md` e `@examples/advanced.md`  
→ Script di validazione in `@scripts/validate.py`
