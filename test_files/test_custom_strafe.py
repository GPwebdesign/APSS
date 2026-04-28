#!/usr/bin/env python3
# coding=utf-8
"""
APSS — Test custom strafe left/right
Tasto 6: toggle custom strafe left
Tasto 7: toggle custom strafe right
Q: esci

Custom strafe left:  M1=-45 M2=+45 M3=-45 M4=+45
Custom strafe right: M1=+45 M2=-45 M3=+45 M4=-45
speed=50 speed_factor=0.9 → speed_out=45
"""
import sys
import os
import socket
import time
import tty
import termios

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

ROBOT_IP  = '192.168.1.158'
TCP_PORT  = 6000
SPEED_OUT = int(50 * 0.9)  # 45

def build_motor_cmd(m1, m2, m3, m4):
    data = [0x02, 0x1A, 0x0C,
            m1 & 0xFF, m2 & 0xFF, m3 & 0xFF, m4 & 0xFF, 0x00]
    cs = sum(data) % 256
    return ('$' + ''.join(f'{b:02x}' for b in data) + f'{cs:02x}' + '#').encode()

def send_stop(sock):
    sock.sendall(build_motor_cmd(0, 0, 0, 0))
    print('[STOP]')

def send_custom_strafe_left(sock):
    s = SPEED_OUT
    sock.sendall(build_motor_cmd(-s-10, s, -s-10, s))
    print(f'[CUSTOM STRAFE LEFT] M1={-s} M2={s} M3={-s} M4={s}')

def send_custom_strafe_right(sock):
    s = SPEED_OUT
    sock.sendall(build_motor_cmd(s, -s, s, -s))
    print(f'[CUSTOM STRAFE RIGHT] M1={s} M2={-s} M3={s} M4={-s}')

def getch():
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        return sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)

def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((ROBOT_IP, TCP_PORT))
    sock.sendall(b'$020f040116#')
    time.sleep(0.5)
    print('Connesso al robot')
    print('Tasto 6: toggle custom strafe LEFT')
    print('Tasto 7: toggle custom strafe RIGHT')
    print('Tasto Q: esci')

    state = 'stop'  # stop / strafe_left / strafe_right

    while True:
        key = getch()

        if key == 'q' or key == 'Q':
            send_stop(sock)
            break

        elif key == '6':
            if state == 'strafe_left':
                send_stop(sock)
                state = 'stop'
            else:
                send_custom_strafe_left(sock)
                state = 'strafe_left'

        elif key == '7':
            if state == 'strafe_right':
                send_stop(sock)
                state = 'stop'
            else:
                send_custom_strafe_right(sock)
                state = 'strafe_right'

    sock.close()
    print('Disconnesso')

if __name__ == '__main__':
    main()
