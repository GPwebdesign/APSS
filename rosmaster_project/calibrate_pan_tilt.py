#!/usr/bin/env python3
"""
calibrate_pan_tilt.py — Calibrazione interattiva servomotori pan/tilt
Robot: Yahboom Rosmaster R2
Canali: S1 = Tilt, S2 = Pan  (swap verificato fisicamente)

Controlli (nessun INVIO necessario):
  ← →     Pan  sinistra / destra  ±5°
  ↑ ↓     Tilt su / giù           ±5°
  INVIO   Ritorna a home 90°/90°
  1       Memorizza HOME
  2       Memorizza PAN MAX sinistra
  3       Memorizza PAN MAX destra
  4       Memorizza TILT MAX su
  5       Memorizza TILT MAX giù
  s       Salva preset su JSON
  r       Vai a HOME memorizzato
  q       Esci

Eseguire SOLO su Raspberry Pi (hawk) con robot acceso.
"""

import sys
import time
import json
import tty
import termios
import select

try:
    from Rosmaster_Lib import Rosmaster
except ImportError:
    print("[ERRORE] Rosmaster_Lib non trovata.")
    sys.exit(1)

# --- Costanti ---
SERVO_PAN   = 2
SERVO_TILT  = 1
STEP        = 5
ANGLE_MIN   = 0
ANGLE_MAX   = 180
OUTPUT_FILE = "pan_tilt_presets.json"

# Sequenze escape frecce
KEY_UP    = '\x1b[A'
KEY_DOWN  = '\x1b[B'
KEY_RIGHT = '\x1b[C'
KEY_LEFT  = '\x1b[D'
KEY_ENTER = '\r'


def read_key() -> str:
    """Legge un tasto singolo senza INVIO.
    Distingue INVIO (\r) dalle sequenze freccia (\x1b[X).
    Drena l'input residuo per garantire 5° per singola pressione.
    """
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = sys.stdin.read(1)
        if ch == '\x1b':
            ready, _, _ = select.select([sys.stdin], [], [], 0.05)
            if ready:
                ch2 = sys.stdin.read(1)
                ch3 = sys.stdin.read(1)
                result = ch + ch2 + ch3
            else:
                result = ch
        else:
            result = ch
        # Drena eventuali byte residui nel buffer (ripetizioni da key repeat)
        while True:
            ready, _, _ = select.select([sys.stdin], [], [], 0.02)
            if ready:
                sys.stdin.read(1)
            else:
                break
        return result
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


def clamp(v):
    return max(ANGLE_MIN, min(ANGLE_MAX, v))


def apply(bot, pan, tilt):
    bot.set_pwm_servo(SERVO_PAN,  pan)
    bot.set_pwm_servo(SERVO_TILT, tilt)
    time.sleep(0.05)


def print_status(pan, tilt, presets):
    print("\033[2J\033[H", end="")  # clear screen
    print("=" * 52)
    print("  CALIBRAZIONE PAN/TILT — Rosmaster R2")
    print("=" * 52)
    print(f"  Posizione corrente:  Pan={pan:4d}°   Tilt={tilt:4d}°")
    print()
    print("  Controlli:")
    print("    ← →     Pan   ±5°        ↑ ↓    Tilt  ±5°")
    print("    INVIO   Home 90°/90°      r      Home memorizzato")
    print("    1  HOME              2  Pan MAX sinistra")
    print("    3  Pan MAX destra    4  Tilt MAX su")
    print("    5  Tilt MAX giù      s  Salva JSON     q  Esci")
    print()
    print("  Preset memorizzati:")
    labels = {
        "home":       "1  HOME            ",
        "scan_left":  "2  Pan MAX sinistra",
        "scan_right": "3  Pan MAX destra  ",
        "tilt_up":    "4  Tilt MAX su     ",
        "tilt_down":  "5  Tilt MAX giù    ",
    }
    for key, label in labels.items():
        if key in presets:
            p = presets[key]
            print(f"    {label}  Pan={p['pan']:4d}°  Tilt={p['tilt']:4d}°  ✓")
        else:
            print(f"    {label}  —")
    print()


def save_presets(presets):
    with open(OUTPUT_FILE, "w") as f:
        json.dump(presets, f, indent=2)
    print(f"  [SALVATO] → {OUTPUT_FILE}")
    time.sleep(1.0)


def main():
    print("[INIT] Connessione a Rosmaster_Lib...")
    try:
        bot = Rosmaster()
        bot.create_receive_threading()
        time.sleep(1.0)
        print("[INIT] OK")
    except Exception as e:
        print(f"[ERRORE] {e}")
        sys.exit(1)

    pan     = 90
    tilt    = 90
    presets = {}

    apply(bot, pan, tilt)
    print_status(pan, tilt, presets)

    try:
        while True:
            key = read_key()

            if key in ('q', '\x03'):       # q o Ctrl+C
                break

            elif key in (KEY_ENTER, '\n'): # INVIO — home 90/90
                pan, tilt = 90, 90

            elif key == KEY_LEFT:
                pan = clamp(pan + STEP)   # invertito fisicamente
            elif key == KEY_RIGHT:
                pan = clamp(pan - STEP)   # invertito fisicamente
            elif key == KEY_UP:
                tilt = clamp(tilt - STEP)
            elif key == KEY_DOWN:
                tilt = clamp(tilt + STEP)

            elif key == '1':
                presets["home"] = {"pan": pan, "tilt": tilt}
            elif key == '2':
                presets["scan_left"] = {"pan": pan, "tilt": tilt}
            elif key == '3':
                presets["scan_right"] = {"pan": pan, "tilt": tilt}
            elif key == '4':
                presets["tilt_up"] = {"pan": pan, "tilt": tilt}
            elif key == '5':
                presets["tilt_down"] = {"pan": pan, "tilt": tilt}

            elif key == 's':
                save_presets(presets)

            elif key == 'r':
                if "home" in presets:
                    pan  = presets["home"]["pan"]
                    tilt = presets["home"]["tilt"]
                else:
                    pan, tilt = 90, 90

            else:
                continue  # tasto non gestito — non aggiornare

            apply(bot, pan, tilt)
            print_status(pan, tilt, presets)

    except KeyboardInterrupt:
        pass

    finally:
        print("\n[EXIT] Posizione finale mantenuta.")
        if presets:
            fd = sys.stdin.fileno()
            old = termios.tcgetattr(fd)
            termios.tcsetattr(fd, termios.TCSADRAIN, old)
            risposta = input("  Salvare i preset prima di uscire? [s/N] ").strip().lower()
            if risposta == "s":
                save_presets(presets)
        print("[EXIT] Done.")


if __name__ == "__main__":
    main()