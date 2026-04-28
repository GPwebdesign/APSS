#!/usr/bin/env python3
# coding=utf-8
"""
APSS — Test calibrazione motori
Testa ogni motore singolarmente per verificare velocità relativa.
Tasti:
  1: solo M1 avanti
  2: solo M2 avanti
  3: solo M3 avanti
  4: solo M4 avanti
  5: tutti avanti (verifica deriva)
  +/-: aumenta/diminuisce speed_out
  Q: esci
"""
import sys, os, socket, time, tty, termios

ROBOT_IP = '192.168.1.158'
TCP_PORT = 6000
speed_out = 50

def build_cmd(m1, m2, m3, m4):
    data = [0x02, 0x1A, 0x0C,
            m1 & 0xFF, m2 & 0xFF, m3 & 0xFF, m4 & 0xFF, 0x00]
    cs = sum(data) % 256
    return ('$' + ''.join(f'{b:02x}' for b in data) + f'{cs:02x}' + '#').encode()

def send(sock, m1, m2, m3, m4):
    sock.sendall(build_cmd(m1, m2, m3, m4))
    print(f'M1={m1:4d} M2={m2:4d} M3={m3:4d} M4={m4:4d}')

def getch():
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        return sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)

def main():
    global speed_out
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((ROBOT_IP, TCP_PORT))
    sock.sendall(b'$020f040116#')
    time.sleep(0.5)
    print(f'Connesso — speed_out={speed_out}')
    print('1-4: singolo motore | 5: tutti avanti | 6: strafe dx | 7: strafe sx | 8: custom-strafe sx | 9: custom-strafe dx | +/-: speed | Q: esci')

    while True:
        key = getch()
        s = speed_out
        if   key == 'q' or key == 'Q':
            send(sock, 0, 0, 0, 0); break
        elif key == '1': send(sock, 90, 0, 0, 0)
        elif key == '2': send(sock, 0, s, 0, 0)
        elif key == '3': send(sock, 0, 0, s, 0)
        elif key == '4': send(sock, 0, 0, 0, s)
        elif key == '5': send(sock, s, s, s, s)
        elif key == '6':  # strafe destra test
            send(sock, s, -s, -s, s)
            print("Strafe destra: M1=+s M2=-s M3=-s M4=+s")
        elif key == '7':  # strafe sinistra test
            send(sock, -s, s, s, -s)
            print("Strafe sinistra: M1=-s M2=+s M3=-s M4=+s")
        elif key == '8':
            send(sock, -90, 40, -90, 40)
            print("Tasto 8: M1=-90 M2=+40 M3=-90 M4=+40")
        elif key == '9':
            send(sock, 90, -40, 90, -40)
            print("Tasto 9: M1=+90 M2=-40 M3=+90 M4=-40")
        elif key == '0': send(sock, 0, 0, 0, 0)
        elif key == '+': speed_out = min(100, speed_out+5); print(f'speed_out={speed_out}')
        elif key == '-': speed_out = max(10,  speed_out-5); print(f'speed_out={speed_out}')

    sock.close()

if __name__ == '__main__':
    main()
