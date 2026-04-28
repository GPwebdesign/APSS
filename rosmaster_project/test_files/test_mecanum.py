#!/usr/bin/env python3
import sys
sys.path.insert(0, '/usr/lib/python3.10')
from Rosmaster_Lib import Rosmaster
import time

bot = Rosmaster(debug=False)
bot.create_receive_threading()
bot.set_car_type(2)
time.sleep(1)

tests = [
    ("AVANTI        M1+ M2+ M3+ M4+", [ 50,  50,  50,  50]),
    ("INDIETRO      M1- M2- M3- M4-", [-50, -50, -50, -50]),
    ("STRAFE DX     M1+ M2- M3- M4+", [ 50, -50, -50,  50]),
    ("STRAFE SX     M1- M2+ M3+ M4-", [-50,  50,  50, -50]),
    ("RUOTA DX      M1+ M2- M3+ M4-", [ 50, -50,  50, -50]),
    ("RUOTA SX      M1- M2+ M3- M4+", [-50,  50, -50,  50]),
]

for label, speeds in tests:
    input(f"\n{label} — premi INVIO...")
    bot.set_motor(*speeds)
    time.sleep(2)
    bot.set_motor(0, 0, 0, 0)
    time.sleep(0.5)

del bot
