#!/usr/bin/env python3
import sys
sys.path.insert(0, '/usr/lib/python3.10')
from Rosmaster_Lib import Rosmaster
import time

bot = Rosmaster(debug=False)
bot.create_receive_threading()
bot.set_car_type(2)
time.sleep(1)

print("Test 1 — set_motor(50, 50, 50, 50)")
input("Premi INVIO...")
bot.set_motor(50, 50, 50, 50)
time.sleep(2)
bot.set_motor(0, 0, 0, 0)
time.sleep(1)

print("Test 2 — set_car_motion(0, 0.3, 0)")
input("Premi INVIO...")
bot.set_car_motion(0, 0.3, 0)
time.sleep(2)
bot.set_car_motion(0, 0, 0)
time.sleep(1)

print("Test 3 — set_car_run(1, 50)  stato=1 avanti")
input("Premi INVIO...")
bot.set_car_run(1, 50)
time.sleep(2)
bot.set_car_run(0, 0)

del bot
