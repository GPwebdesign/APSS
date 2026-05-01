# TCP Yahboom — Algoritmo Checksum

## Regola base

```
checksum = sum(payload) % 256
```

`payload` = tutti i byte del pacchetto **esclusi** `$`, `#` e il checksum stesso.  
Include: `cartype` + `cmd` + `len` + tutti i byte `data`.

---

## Passo per passo

Esempio: costruzione pacchetto stop `0x1A` (tutti i motori a zero)

```
Byte posizione:  [0]   [1]   [2]   [3]   [4]   [5]   [6]   [7]
Valore hex:      02    1A    0C    00    00    00    00    00
Significato:     car   cmd   len   M1    M2    M3    M4    pad

sum = 0x02 + 0x1A + 0x0C + 0x00 + 0x00 + 0x00 + 0x00 + 0x00
    = 2 + 26 + 12 + 0 + 0 + 0 + 0 + 0
    = 40 = 0x28

checksum = 40 % 256 = 40 = 0x28

Pacchetto finale: $021a0c000000000028#
```

---

## Valori negativi (motori in retromarcia)

I valori motore sono **signed** nel range `-100..+100` ma vengono trasmessi
come **unsigned** a 1 byte in complemento a 2:

```python
def to_byte(val: int) -> int:
    """Converte valore signed (-100..+100) in byte unsigned (0..255)"""
    return val & 0xFF

# Esempi:
to_byte(100)   # → 0x64  (avanti piena velocità)
to_byte(0)     # → 0x00  (fermo)
to_byte(-100)  # → 0x9C  (indietro piena velocità)
to_byte(-1)    # → 0xFF
to_byte(-50)   # → 0xCE
```

Il checksum si calcola **sui byte unsigned** — dopo la conversione:

```python
m1, m2, m3, m4 = -50, 50, 50, -50   # valori motore signed
data = [to_byte(m1), to_byte(m2), to_byte(m3), to_byte(m4), 0x00]

payload = [0x02, 0x1A, 0x0C] + data
checksum = sum(payload) % 256
```

---

## Calcolo manuale — verifica rapida

```python
def verify_packet(packet_str: str) -> bool:
    """
    Verifica checksum di un pacchetto Yahboom.
    Input: stringa tipo '$021a0c000000000028#'
    """
    inner = packet_str.strip('$#')
    # Tutti i byte tranne l'ultimo (checksum)
    payload_hex = inner[:-2]
    checksum_hex = inner[-2:]

    payload_bytes = [int(payload_hex[i:i+2], 16)
                     for i in range(0, len(payload_hex), 2)]
    expected = sum(payload_bytes) % 256
    actual = int(checksum_hex, 16)

    return expected == actual

# Test:
verify_packet('$021a0c000000000028#')  # → True
verify_packet('$020f040116#')          # → True
```

---

## Casi limite noti

| Caso | Problema | Soluzione |
|------|----------|-----------|
| `len` errato su `0x1A` | Usare `0x0A` invece di `0x0C` → errore `10 != 12` in `parse_data` | Usare sempre `0x0C` per `0x1A` con 4 motori + padding |
| Sum > 255 | Nessun problema — `% 256` gestisce overflow automaticamente | — |
| Valori motore fuori range | Valori oltre ±100 producono byte errati | Clampare a `max(-100, min(100, val))` prima di `to_byte()` |
| Pacchetto senza init | `parse_data` riceve comandi validi ma `g_car_type` non è impostato | Inviare sempre `$020f040116#` dopo connessione |

---

## Riferimento rapido checksum pacchetti fissi

| Pacchetto | Hex | Checksum |
|-----------|-----|----------|
| Init | `$020f040116#` | `0x16` = 22 |
| Stop | `$021a0c000000000028#` | `0x28` = 40 |
| Pan home 100° | `$02110602647f#` | `0x7f` = 127 |
| Tilt home 95° | `$021106015f79#` | `0x79` = 121 |

→ Script interattivo in `@scripts/validate.py`
