#!/usr/bin/env python3
"""
test_pan_tilt.py — Test standalone servomotori pan/tilt
Robot: Yahboom Rosmaster R2
Board: Expansion Board V3.0
Canali: S1 = Tilt, S2 = Pan  (swap verificato fisicamente)

Eseguire SOLO su Raspberry Pi (hawk) con robot acceso.
NON eseguire sulla VM di sviluppo.

Uso:
    python3 test_pan_tilt.py
"""

import time
import sys

# --- Import Rosmaster_Lib ---
try:
    from Rosmaster_Lib import Rosmaster
except ImportError:
    print("[ERRORE] Rosmaster_Lib non trovata.")
    print("  Verifica di essere su hawk (RPi) e che la libreria sia installata.")
    sys.exit(1)

# --- Costanti ---
SERVO_PAN  = 2   # S2 — asse orizzontale (swap verificato fisicamente)
SERVO_TILT = 1   # S1 — asse verticale  (swap verificato fisicamente)

DELAY_MOVE  = 1.0   # secondi di attesa dopo ogni movimento (per stabilizzazione servo)

# Preset angoli
PRESET_HOME       = (90, 90)    # centro
PRESET_SCAN_LEFT  = (45, 90)    # sinistra
PRESET_SCAN_RIGHT = (135, 90)   # destra
PRESET_ALERT      = (90, 60)    # leggermente in basso


def move(bot, pan_angle: int, tilt_angle: int, label: str = ""):
    """Muove entrambi i servo — chiede conferma INVIO prima di ogni movimento."""
    pan_angle  = max(0, min(180, pan_angle))
    tilt_angle = max(0, min(180, tilt_angle))
    tag = f"[{label}]" if label else ""
    input(f"  → INVIO per eseguire: {tag} Pan={pan_angle:3d}°  Tilt={tilt_angle:3d}°  ")
    bot.set_pwm_servo(SERVO_PAN,  pan_angle)
    bot.set_pwm_servo(SERVO_TILT, tilt_angle)
    time.sleep(DELAY_MOVE)


def test_preset(bot):
    """Verifica i preset definiti nel progetto."""
    print("\n=== TEST PRESET ===")
    move(bot, *PRESET_HOME,       "HOME")
    move(bot, *PRESET_SCAN_LEFT,  "SCAN_LEFT")
    move(bot, *PRESET_HOME,       "HOME")
    move(bot, *PRESET_SCAN_RIGHT, "SCAN_RIGHT")
    move(bot, *PRESET_HOME,       "HOME")
    move(bot, *PRESET_ALERT,      "ALERT")
    move(bot, *PRESET_HOME,       "HOME")


def test_range_pan(bot):
    """Sweep completo asse Pan: 0° → 180° → 0°."""
    print("\n=== TEST RANGE PAN (S2) ===")
    print("  Sweep 0° → 180°")
    for angle in range(0, 181, 30):
        move(bot, angle, 90, f"PAN {angle}")
    print("  Ritorno 180° → 0°")
    for angle in range(180, -1, -30):
        move(bot, angle, 90, f"PAN {angle}")


def test_range_tilt(bot):
    """Sweep completo asse Tilt: 0° → 180° → 0°."""
    print("\n=== TEST RANGE TILT (S1) ===")
    print("  Sweep 0° → 180°")
    for angle in range(0, 181, 30):
        move(bot, 90, angle, f"TILT {angle}")
    print("  Ritorno 180° → 0°")
    for angle in range(180, -1, -30):
        move(bot, 90, angle, f"TILT {angle}")


def main():
    print("=" * 50)
    print("  TEST PAN/TILT — Rosmaster R2")
    print("=" * 50)
    print(f"  Servo Pan  → S2 (servo_id={SERVO_PAN})  [swap verificato]")
    print(f"  Servo Tilt → S1 (servo_id={SERVO_TILT})  [swap verificato]")
    print("  Ogni movimento richiede INVIO da tastiera.")
    print()

    # --- Inizializzazione robot ---
    print("[INIT] Connessione a Rosmaster_Lib...")
    try:
        bot = Rosmaster()
        bot.create_receive_threading()
        time.sleep(1.0)   # attendi stabilizzazione
        print("[INIT] OK\n")
    except Exception as e:
        print(f"[ERRORE] Inizializzazione fallita: {e}")
        sys.exit(1)

    try:
        # Step 1 — porta in HOME per partire da posizione nota
        print("[STEP 1] Posizione HOME (90°/90°)")
        move(bot, *PRESET_HOME, "HOME")

        # Step 2 — test preset
        print("\n=== TEST PRESET ===")
        test_preset(bot)

        # Step 3 — sweep Pan
        test_range_pan(bot)

        # Step 4 — sweep Tilt
        test_range_tilt(bot)

        # Step 5 — ritorno HOME finale
        print("\n[FINE] Ritorno HOME...")
        move(bot, *PRESET_HOME, "HOME")
        print("[FINE] Test completato con successo.")

    except KeyboardInterrupt:
        print("\n[INTERRUPT] Interrotto dall'utente.")
        print("[INTERRUPT] Ritorno HOME di sicurezza...")
        bot.set_pwm_servo(SERVO_PAN,  90)
        bot.set_pwm_servo(SERVO_TILT, 90)

    finally:
        # Nessun metodo di shutdown necessario per i servo Yahboom,
        # rimangono nell'ultima posizione comandata.
        print("[EXIT] Done.")


if __name__ == "__main__":
    main()