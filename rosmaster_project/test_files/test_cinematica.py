#!/usr/bin/env python3
import sys
sys.path.insert(0, '/usr/lib/python3.10')
from Rosmaster_Lib import Rosmaster
import time

bot = Rosmaster(debug=False)
bot.create_receive_threading()
time.sleep(1)

def mecanum_move(vx, vy, vz, speed=50):
    """
    Cinematica Mecanum wheel.
    vx: avanti/indietro (+avanti)
    vy: laterale (+destra)
    vz: rotazione (+orario)
    """
    m1 = vx - vy + vz  # anteriore sinistra  (vz invertito)
    m2 = vx + vy - vz  # anteriore destra    (vz invertito)
    m3 = vx + vy + vz  # posteriore sinistra (vz invertito)
    m4 = vx - vy - vz  # posteriore destra   (vz invertito)
    # Normalizza e scala
    max_val = max(abs(m1), abs(m2), abs(m3), abs(m4), 1)
    m1 = int(m1 / max_val * speed)
    m2 = int(m2 / max_val * speed)
    m3 = int(m3 / max_val * speed)
    m4 = int(m4 / max_val * speed)
    print(f"M1={m1} M2={m2} M3={m3} M4={m4}")
    bot.set_motor(m1, m2, m3, m4)

tests = [
    ("AVANTI",           ( 1,  0,  0)),
    ("INDIETRO",         (-1,  0,  0)),
    ("ROTAZIONE DX",     ( 0,  0,  1)),
    ("ROTAZIONE SX",     ( 0,  0, -1)),
]

for label, args in tests:
    input(f"\n{label} — premi INVIO...")
    mecanum_move(*args)
    time.sleep(2)
    bot.set_motor(0, 0, 0, 0)
    time.sleep(0.5)

del bot