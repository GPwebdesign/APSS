#!/usr/bin/env python3
import sys
sys.path.insert(0, '/usr/lib/python3.10')
from Rosmaster_Lib import Rosmaster
import time

bot = Rosmaster(debug=False)
bot.create_receive_threading()
bot.set_car_type(2)
time.sleep(1)

print("Rotazione destra — misura il tempo per 90°")
input("Premi INVIO per iniziare...")
bot.set_car_motion(0, 0, -1.0)
time.sleep(2.5)  # modifica questo valore
bot.set_car_motion(0, 0, 0)
print("Quanti gradi ha ruotato?")

del bot
