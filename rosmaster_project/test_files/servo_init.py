#!/usr/bin/env python3
# coding=utf-8
"""
APSS — Servo Init Helper
Centra i servo pan/tilt a 90°/90° prima di qualsiasi test.
Importa e chiama servo_home() all'inizio di ogni script di test.
"""
import sys
sys.path.insert(0, '/usr/lib/python3.10')
from Rosmaster_Lib import Rosmaster
import time
import json
import os


def servo_home(bot=None, delay=1.0):
    """
    Porta pan (S2) e tilt (S1) alla posizione home da pan_tilt_presets.json.
    Se bot=None crea una istanza temporanea.
    Ritorna il bot per riuso opzionale.
    """
    preset_path = os.path.join(
        os.path.dirname(__file__), '..', 'pan_tilt_presets.json')
    try:
        with open(preset_path) as f:
            presets = json.load(f)
        pan_home  = presets['home']['pan']
        tilt_home = presets['home']['tilt']
    except Exception:
        pan_home  = 100
        tilt_home = 95
        print("[servo_init] JSON non trovato — uso valori default")

    own_bot = bot is None
    if own_bot:
        bot = Rosmaster(debug=False)
        bot.create_receive_threading()
        time.sleep(0.5)

    print(f"[servo_init] Centratura pan={pan_home}° tilt={tilt_home}°...")
    bot.set_pwm_servo(1, tilt_home)  # Tilt S1
    time.sleep(0.1)
    bot.set_pwm_servo(2, pan_home)   # Pan S2
    time.sleep(delay)
    print("[servo_init] OK — pan/tilt centrati")

    if own_bot:
        del bot
        return None
    return bot
