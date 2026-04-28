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
    ("M1 +50 — ruota ANTERIORE SINISTRA deve girare IN AVANTI",  [50,  0,  0,  0]),
    ("M2 +50 — ruota ANTERIORE DESTRA  deve girare IN AVANTI",   [ 0, 50,  0,  0]),
    ("M3 +50 — ruota POSTERIORE SINISTRA deve girare IN AVANTI", [ 0,  0, 50,  0]),
    ("M4 +50 — ruota POSTERIORE DESTRA  deve girare IN AVANTI",  [ 0,  0,  0, 50]),
]

for label, speeds in tests:
    print(f"\n{label}")
    input("Premi INVIO per eseguire...")
    bot.set_motor(*speeds)
    time.sleep(2)
    bot.set_motor(0, 0, 0, 0)
    time.sleep(0.5)

print("\nTest completato.")
del bot

