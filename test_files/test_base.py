#!/usr/bin/env python3
import sys
sys.path.insert(0, '/usr/lib/python3.10')
from Rosmaster_Lib import Rosmaster
import time

bot = Rosmaster(debug=False)
bot.create_receive_threading()
time.sleep(1)

print("Test M1+ M2+ M3+ M4+ — devono girare tutti AVANTI")
input("Premi INVIO...")
bot.set_motor(50, 50, 50, 50)
time.sleep(2)
bot.set_motor(0, 0, 0, 0)

del bot
