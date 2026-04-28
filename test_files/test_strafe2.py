#!/usr/bin/env python3
import sys
sys.path.insert(0, '/usr/lib/python3.10')
from Rosmaster_Lib import Rosmaster
import time

bot = Rosmaster(debug=False)
bot.create_receive_threading()
bot.set_car_type(2)
time.sleep(1)

print("Strafe destra alternativo: M1- M2+ M3+ M4-")
input("Premi INVIO...")
bot.set_motor(-50, 50, 50, -50)
time.sleep(2)
bot.set_motor(0, 0, 0, 0)
time.sleep(1)

print("Strafe sinistra alternativo: M1+ M2- M3- M4+")
input("Premi INVIO...")
bot.set_motor(50, -50, -50, 50)
time.sleep(2)
bot.set_motor(0, 0, 0, 0)

del bot
