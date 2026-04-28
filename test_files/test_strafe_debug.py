#!/usr/bin/env python3
import sys
sys.path.insert(0, '/usr/lib/python3.10')
from Rosmaster_Lib import Rosmaster
import time

bot = Rosmaster(debug=False)
bot.create_receive_threading()
bot.set_car_type(2)
time.sleep(1)

# Strafe destra Mecanum corretto:
# M1 (ant.sx) avanti +, M2 (ant.dx) indietro -, M3 (post.sx) indietro -, M4 (post.dx) avanti +
print("Strafe destra manuale: M1+, M2-, M3-, M4+")
bot.set_motor(50, -50, -50, 50)
time.sleep(2)
bot.set_motor(0, 0, 0, 0)
time.sleep(1)

print("Strafe sinistra manuale: M1-, M2+, M3+, M4-")
bot.set_motor(-50, 50, 50, -50)
time.sleep(2)
bot.set_motor(0, 0, 0, 0)
time.sleep(1)

print("Rotazione destra manuale: tutti positivi sx, negativi dx")
bot.set_motor(50, -50, 50, -50)
time.sleep(2)
bot.set_motor(0, 0, 0, 0)

del bot
