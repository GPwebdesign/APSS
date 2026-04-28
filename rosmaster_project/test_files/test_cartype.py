#!/usr/bin/env python3
import sys
sys.path.insert(0, '/usr/lib/python3.10')
from Rosmaster_Lib import Rosmaster
import time

bot = Rosmaster(debug=True)
bot.create_receive_threading()
time.sleep(1)

# Prova senza impostare car_type — usa il valore di default della scheda
print("Test AVANTI senza set_car_type...")
input("Premi INVIO...")
bot.set_car_motion(0, 0.3, 0)
time.sleep(2)
bot.set_car_motion(0, 0, 0)

del bot
