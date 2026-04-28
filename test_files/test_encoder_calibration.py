#!/usr/bin/env python3
# coding=utf-8
"""
APSS — Test calibrazione encoder motori
Misura i valori encoder di M1-M4 durante movimento avanti
per calcolare i fattori di correzione.
Tasti:
  SPAZIO: start/stop test (3 secondi avanti a speed_out fisso)
  +/-: aumenta/diminuisce speed_out
  Q: esci
"""
import sys
import os
import time
import tty
import termios
import threading

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Rosmaster_Lib import Rosmaster

SPEED_OUT = 50
TEST_DURATION = 3.0  # secondi

def getch():
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        return sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)

def run_test(bot, speed_out):
    print(f'\n--- TEST AVANTI speed_out={speed_out} per {TEST_DURATION}s ---')

    # Reset encoder leggendo i valori attuali come baseline
    time.sleep(0.2)
    e1_start, e2_start, e3_start, e4_start = bot.get_motor_encoder()
    print(f'Encoder start: M1={e1_start} M2={e2_start} M3={e3_start} M4={e4_start}')

    # Movimento avanti
    s = speed_out
    bot.set_motor(s, s, s, s)
    time.sleep(TEST_DURATION)
    bot.set_motor(0, 0, 0, 0)
    time.sleep(0.2)

    # Leggi encoder finali
    e1_end, e2_end, e3_end, e4_end = bot.get_motor_encoder()
    print(f'Encoder end:   M1={e1_end} M2={e2_end} M3={e3_end} M4={e4_end}')

    # Calcola delta
    d1 = abs(e1_end - e1_start)
    d2 = abs(e2_end - e2_start)
    d3 = abs(e3_end - e3_start)
    d4 = abs(e4_end - e4_start)
    print(f'Delta encoder: M1={d1} M2={d2} M3={d3} M4={d4}')

    # Calcola fattori di correzione
    max_enc = max(d1, d2, d3, d4)
    if max_enc > 0:
        f1 = round(max_enc / d1, 3) if d1 > 0 else 1.0
        f2 = round(max_enc / d2, 3) if d2 > 0 else 1.0
        f3 = round(max_enc / d3, 3) if d3 > 0 else 1.0
        f4 = round(max_enc / d4, 3) if d4 > 0 else 1.0
        print(f'\nFattori correzione (motore più lento = 1.0):')
        print(f'  M1 (ant.sx): {f1}')
        print(f'  M2 (ant.dx): {f2}')
        print(f'  M3 (post.sx): {f3}')
        print(f'  M4 (post.dx): {f4}')

        # Calcola speed corretti
        print(f'\nSpeed corretti per speed_out={speed_out}:')
        print(f'  M1: {int(speed_out * f1)}')
        print(f'  M2: {int(speed_out * f2)}')
        print(f'  M3: {int(speed_out * f3)}')
        print(f'  M4: {int(speed_out * f4)}')

def main():
    global SPEED_OUT
    bot = Rosmaster(debug=False)
    bot.create_receive_threading()
    time.sleep(0.5)

    print('Test calibrazione encoder APSS')
    print('SPAZIO: esegui test | +/-: speed | Q: esci')
    print(f'speed_out corrente: {SPEED_OUT}')

    while True:
        key = getch()
        if key == 'q' or key == 'Q':
            bot.set_motor(0, 0, 0, 0)
            break
        elif key == ' ':
            run_test(bot, SPEED_OUT)
        elif key == '+':
            SPEED_OUT = min(100, SPEED_OUT + 5)
            print(f'speed_out={SPEED_OUT}')
        elif key == '-':
            SPEED_OUT = max(10, SPEED_OUT - 5)
            print(f'speed_out={SPEED_OUT}')

    del bot
    print('Fine test')

if __name__ == '__main__':
    main()
