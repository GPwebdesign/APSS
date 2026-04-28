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
    ("AVANTI          set_car_motion( 0,  0.3,  0)", (0,  0.3,  0)),
    ("INDIETRO        set_car_motion( 0, -0.3,  0)", (0, -0.3,  0)),
    ("ROTAZIONE DX    set_car_motion( 0,  0,   -1)", (0,  0,   -1)),
    ("ROTAZIONE SX    set_car_motion( 0,  0,    1)", (0,  0,    1)),
]

for label, args in tests:
    input(f"\n{label}\nPremi INVIO per eseguire...")
    bot.set_car_motion(*args)
    time.sleep(2)
    bot.set_car_motion(0, 0, 0)
    time.sleep(0.5)

print("\nTest completato.")
del bot
