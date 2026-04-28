#!/usr/bin/env python3
"""
control_pan_tilt.py — Controllo interattivo pan/tilt con tour automatici
Robot: Yahboom Rosmaster R2
Canali: S1 = Tilt, S2 = Pan  (swap verificato fisicamente)

Preset caricati da: pan_tilt_presets.json

Controlli (nessun INVIO necessario):
  ← →     Pan  sinistra / destra  ±5°
  ↑ ↓     Tilt su / giù           ±5°
  INVIO   Vai a HOME (dal preset JSON)
  1       Tour PAN  (scan_left → scan_right → home)  passi 3°
  2       Tour TILT (tilt_up   → tilt_down  → home)  passi 3°
  3       Tour combinato PAN + TILT                   passi 3°
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
SERVO_PAN    = 2
SERVO_TILT   = 1
STEP_MANUAL  = 5    # gradi per freccia manuale
STEP_TOUR    = 3    # gradi per ogni passo dei tour
ANGLE_MIN    = 0
ANGLE_MAX    = 180
TOUR_DELAY   = 0.05  # secondi tra un passo e l'altro del tour
SLOW_STEP    = 5     # gradi per passo nei movimenti lenti (home, posiz. iniziale)
SLOW_DELAY   = 0.1   # secondi tra un passo lento e l'altro
PRESET_FILE  = "pan_tilt_presets.json"

KEY_UP    = '\x1b[A'
KEY_DOWN  = '\x1b[B'
KEY_RIGHT = '\x1b[C'
KEY_LEFT  = '\x1b[D'
KEY_ENTER = '\r'


# ---------------------------------------------------------------------------
# I/O
# ---------------------------------------------------------------------------

def read_key() -> str:
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
        # Drain buffer residuo
        while True:
            ready, _, _ = select.select([sys.stdin], [], [], 0.02)
            if ready:
                sys.stdin.read(1)
            else:
                break
        return result
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


# ---------------------------------------------------------------------------
# Servo
# ---------------------------------------------------------------------------

def clamp(v):
    return max(ANGLE_MIN, min(ANGLE_MAX, v))


def apply(bot, pan, tilt):
    bot.set_pwm_servo(SERVO_PAN,  pan)
    bot.set_pwm_servo(SERVO_TILT, tilt)
    time.sleep(0.05)


def go_to(bot, pan, tilt, delay=0.05):
    """Muove a posizione assoluta con delay configurabile."""
    bot.set_pwm_servo(SERVO_PAN,  clamp(pan))
    bot.set_pwm_servo(SERVO_TILT, clamp(tilt))
    time.sleep(delay)


def slow_move(bot, from_pan, from_tilt, to_pan, to_tilt):
    """Movimento graduale step 5° delay 0.1s — usato per HOME e posiz. iniziale tour."""
    pan  = from_pan
    tilt = from_tilt
    while pan != to_pan or tilt != to_tilt:
        if pan < to_pan:
            pan = min(pan + SLOW_STEP, to_pan)
        elif pan > to_pan:
            pan = max(pan - SLOW_STEP, to_pan)
        if tilt < to_tilt:
            tilt = min(tilt + SLOW_STEP, to_tilt)
        elif tilt > to_tilt:
            tilt = max(tilt - SLOW_STEP, to_tilt)
        bot.set_pwm_servo(SERVO_PAN,  pan)
        bot.set_pwm_servo(SERVO_TILT, tilt)
        time.sleep(SLOW_DELAY)


# ---------------------------------------------------------------------------
# Display
# ---------------------------------------------------------------------------

def print_status(pan, tilt, presets, message=""):
    print("\033[2J\033[H", end="")
    print("=" * 52)
    print("  CONTROLLO PAN/TILT — Rosmaster R2")
    print("=" * 52)
    print(f"  Posizione corrente:  Pan={pan:4d}°   Tilt={tilt:4d}°")
    if message:
        print(f"  {message}")
    print()
    print("  Controlli:")
    print("    ← →   Pan ±5°         ↑ ↓   Tilt ±5°")
    print("    INVIO  → HOME         1  Tour PAN")
    print("    2  Tour TILT          3  Tour PAN+TILT")
    print("    q  Esci")
    print()
    print("  Preset caricati:")
    labels = {
        "home":       "HOME            ",
        "scan_left":  "Pan MAX sinistra",
        "scan_right": "Pan MAX destra  ",
        "tilt_up":    "Tilt MAX su     ",
        "tilt_down":  "Tilt MAX giù    ",
    }
    for key, label in labels.items():
        if key in presets:
            p = presets[key]
            print(f"    {label}  Pan={p['pan']:4d}°  Tilt={p['tilt']:4d}°")
        else:
            print(f"    {label}  — (non presente nel JSON)")
    print()


# ---------------------------------------------------------------------------
# Tour
# ---------------------------------------------------------------------------

def sweep(bot, servo_id, from_angle, to_angle, fixed_other, other_servo_id, step=STEP_TOUR):
    """Sweep lineare di un asse, l'altro fermo."""
    direction = 1 if to_angle >= from_angle else -1
    angle = from_angle
    while (direction == 1 and angle <= to_angle) or (direction == -1 and angle >= to_angle):
        if servo_id == SERVO_PAN:
            go_to(bot, angle, fixed_other, TOUR_DELAY)
        else:
            go_to(bot, fixed_other, angle, TOUR_DELAY)
        angle += direction * step
    # Assicura che arrivi esattamente all'angolo finale
    if servo_id == SERVO_PAN:
        go_to(bot, to_angle, fixed_other, TOUR_DELAY)
    else:
        go_to(bot, fixed_other, to_angle, TOUR_DELAY)


def tour_pan(bot, presets, home_pan, home_tilt, cur_pan, cur_tilt):
    """Tour pan: scan_left → scan_right → home."""
    p_left  = presets.get("scan_left",  {"pan": ANGLE_MIN, "tilt": home_tilt})
    p_right = presets.get("scan_right", {"pan": ANGLE_MAX, "tilt": home_tilt})

    # Posizionamento iniziale — lento
    slow_move(bot, cur_pan, cur_tilt, p_left["pan"], home_tilt)
    time.sleep(0.2)
    # Sweep sinistra → destra
    sweep(bot, SERVO_PAN, p_left["pan"], p_right["pan"], home_tilt, SERVO_TILT)
    time.sleep(0.2)
    # Ritorno HOME — lento
    slow_move(bot, p_right["pan"], home_tilt, home_pan, home_tilt)


def tour_tilt(bot, presets, home_pan, home_tilt, cur_pan, cur_tilt):
    """Tour tilt: tilt_up → tilt_down → home."""
    p_up   = presets.get("tilt_up",   {"pan": home_pan, "tilt": ANGLE_MIN})
    p_down = presets.get("tilt_down", {"pan": home_pan, "tilt": ANGLE_MAX})

    # Posizionamento iniziale — lento
    slow_move(bot, cur_pan, cur_tilt, home_pan, p_up["tilt"])
    time.sleep(0.2)
    # Sweep su → giù
    sweep(bot, SERVO_TILT, p_up["tilt"], p_down["tilt"], home_pan, SERVO_PAN)
    time.sleep(0.2)
    # Ritorno HOME — lento
    slow_move(bot, home_pan, p_down["tilt"], home_pan, home_tilt)


def tour_combined(bot, presets, home_pan, home_tilt, cur_pan, cur_tilt):
    """Tour combinato: pan a sinistra, sweep tilt; pan a destra, sweep tilt; home."""
    p_left  = presets.get("scan_left",  {"pan": ANGLE_MIN, "tilt": home_tilt})
    p_right = presets.get("scan_right", {"pan": ANGLE_MAX, "tilt": home_tilt})
    p_up    = presets.get("tilt_up",    {"pan": home_pan,  "tilt": ANGLE_MIN})
    p_down  = presets.get("tilt_down",  {"pan": home_pan,  "tilt": ANGLE_MAX})

    # Pan a sinistra, tilt su — lento
    slow_move(bot, cur_pan, cur_tilt, p_left["pan"], p_up["tilt"])
    time.sleep(0.2)
    # Sweep tilt su → giù (pan fermo a sinistra)
    sweep(bot, SERVO_TILT, p_up["tilt"], p_down["tilt"], p_left["pan"], SERVO_PAN)
    time.sleep(0.2)

    # Pan a destra, tilt su — lento
    slow_move(bot, p_left["pan"], p_down["tilt"], p_right["pan"], p_up["tilt"])
    time.sleep(0.2)
    # Sweep tilt su → giù (pan fermo a destra)
    sweep(bot, SERVO_TILT, p_up["tilt"], p_down["tilt"], p_right["pan"], SERVO_PAN)
    time.sleep(0.2)

    # Ritorno HOME — lento
    slow_move(bot, p_right["pan"], p_down["tilt"], home_pan, home_tilt)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    # Carica preset
    try:
        with open(PRESET_FILE) as f:
            presets = json.load(f)
        print(f"[PRESET] Caricati da {PRESET_FILE}")
    except FileNotFoundError:
        print(f"[ERRORE] File '{PRESET_FILE}' non trovato.")
        print("  Esegui prima calibrate_pan_tilt.py e salva i preset.")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"[ERRORE] JSON non valido: {e}")
        sys.exit(1)

    home_pan  = presets.get("home", {}).get("pan",  90)
    home_tilt = presets.get("home", {}).get("tilt", 90)

    # Init robot
    print("[INIT] Connessione a Rosmaster_Lib...")
    try:
        bot = Rosmaster()
        bot.create_receive_threading()
        time.sleep(1.0)
        print("[INIT] OK")
    except Exception as e:
        print(f"[ERRORE] {e}")
        sys.exit(1)

    pan  = home_pan
    tilt = home_tilt
    apply(bot, pan, tilt)
    print_status(pan, tilt, presets)

    try:
        while True:
            key = read_key()
            message = ""

            if key in ('q', '\x03'):
                break

            elif key in (KEY_ENTER, '\n'):
                slow_move(bot, pan, tilt, home_pan, home_tilt)
                pan, tilt = home_pan, home_tilt
                message = "→ HOME"

            elif key == KEY_LEFT:
                pan = clamp(pan + STEP_MANUAL)
            elif key == KEY_RIGHT:
                pan = clamp(pan - STEP_MANUAL)
            elif key == KEY_UP:
                tilt = clamp(tilt - STEP_MANUAL)
            elif key == KEY_DOWN:
                tilt = clamp(tilt + STEP_MANUAL)

            elif key == '1':
                print_status(pan, tilt, presets, "Tour PAN in corso...")
                tour_pan(bot, presets, home_pan, home_tilt, pan, tilt)
                pan, tilt = home_pan, home_tilt
                message = "Tour PAN completato"

            elif key == '2':
                print_status(pan, tilt, presets, "Tour TILT in corso...")
                tour_tilt(bot, presets, home_pan, home_tilt, pan, tilt)
                pan, tilt = home_pan, home_tilt
                message = "Tour TILT completato"

            elif key == '3':
                print_status(pan, tilt, presets, "Tour PAN+TILT in corso...")
                tour_combined(bot, presets, home_pan, home_tilt, pan, tilt)
                pan, tilt = home_pan, home_tilt
                message = "Tour PAN+TILT completato"

            else:
                continue

            apply(bot, pan, tilt)
            print_status(pan, tilt, presets, message)

    except KeyboardInterrupt:
        pass

    finally:
        print("\n[EXIT] Ritorno HOME...")
        slow_move(bot, pan, tilt, home_pan, home_tilt)
        print("[EXIT] Done.")


if __name__ == "__main__":
    main()