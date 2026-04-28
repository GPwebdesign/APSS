#!/usr/bin/env python3
import sys
sys.path.insert(0, '/usr/lib/python3.10')
from Rosmaster_Lib import Rosmaster
import time

bot = Rosmaster(debug=True)
bot.create_receive_threading()
time.sleep(1)

print("Test M1 (dovrebbe essere anteriore sinistro)")
bot.set_motor(50, 0, 0, 0)
time.sleep(2)
bot.set_motor(0, 0, 0, 0)
time.sleep(1)

print("Test M2 (dovrebbe essere anteriore destro)")
bot.set_motor(0, 50, 0, 0)
time.sleep(2)
bot.set_motor(0, 0, 0, 0)
time.sleep(1)

print("Test M3 (dovrebbe essere posteriore sinistro)")
bot.set_motor(0, 0, 50, 0)
time.sleep(2)
bot.set_motor(0, 0, 0, 0)
time.sleep(1)

print("Test M4 (dovrebbe essere posteriore destro)")
bot.set_motor(0, 0, 0, 50)
time.sleep(2)
bot.set_motor(0, 0, 0, 0)

bot.set_motor(0, 0, 0, 0)
del bot
