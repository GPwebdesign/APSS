---
name: apss-tcp-protocol
description: >
  Attiva quando il codice tocca: TCP, set_motor, parse_data, send_motion,
  0x1A, 0x11, 0x10, cmd hex, checksum, rosmaster_main.py, tcp_client.py.
  Regole critiche per costruire pacchetti Yahboom corretti senza errori.
version: 1.0
references:
  - references/commands.md   # tutti i comandi con formato hex completo
  - references/checksum.md   # algoritmo checksum + casi limite
examples:
  - examples/basic-usage.md  # stop, avanti, servo
  - examples/advanced.md     # cinematica Mecanum completa
---

# apss-tcp-protocol

## Formato pacchetto

```
$[cartype 2hex][cmd 2hex][len 2hex][data...][checksum 2hex]#
```
- Tutto ASCII hex minuscolo, delimitato da `$` e `#`
- `len` = `data_size − 8` (NON la lunghezza totale del pacchetto)
- `checksum` = `sum(tutti i byte del payload) % 256`
- `cartype` sempre `0x02` (Mecanum X3_PLUS)

## Costruzione pacchetto in Python

```python
def _build_cmd(car_type: int, cmd_id: int, data: list) -> bytes:
    length = len(data) + 2          # +2 per cartype e cmd
    payload = [car_type, cmd_id, length] + data
    checksum = sum(payload) % 256
    hex_str = "".join(f"{b:02x}" for b in payload)
    return f"${hex_str}{checksum:02x}#".encode()
```

## Comandi principali

`0x0F` init — `0x1A` set_motor (preferito) — `0x11` servo — `0x10` movimento base  
→ Formato completo in `@references/commands.md`

## Regola critica — parse_data

```python
cmd = data[3:5].upper()  # OBBLIGATORIO — senza .upper() i comandi minuscoli vengono ignorati
```

## ⚠️ Gotchas (errori noti da evitare)

> **Workflow PC:** il file `subtree-pull.bat` nella root di APSS controlla i file `.md`
> non committati all'avvio e chiede se committare e pushare su GitHub.
> Usarlo dopo ogni modifica a questa skill.

- **MAI usare `set_car_motion()`** dalla libreria Rosmaster_Lib — produce movimenti errati con il cablaggio fisico APSS
- **`len` field sbagliato** — il campo lunghezza è `data_size − 8`, non la lunghezza totale; per `0x1A` con 4 motori il valore corretto è `0x0C`
- **Init mancante** — senza `$020f040116#` dopo la connessione il server ignora i comandi successivi
- **Case sensitivity** — senza `.upper()` in `parse_data()` i comandi inviati in minuscolo vengono scartati silenziosamente
- **Servo id** — S1=Tilt (id=1), S2=Pan (id=2): swap fisico rispetto alla denominazione Yahboom
- **Motori M1/M4** — polarità fisica invertita (fili scambiati): la formula custom compensa già questo
