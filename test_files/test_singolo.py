#!/usr/bin/env python3
import sys
sys.path.insert(0, '/usr/lib/python3.10')
from Rosmaster_Lib import Rosmaster
import time

bot = Rosmaster(debug=False)
bot.create_receive_threading()
bot.set_car_type(2)
time.sleep(1)

porta = input("Quale porta testare? (1/2/3/4): ").strip()
speeds = [0, 0, 0, 0]
speeds[int(porta)-1] = 50
print(f"Attivazione porta M{porta}...")
bot.set_motor(*speeds)
time.sleep(3)
bot.set_motor(0, 0, 0, 0)
del bot
