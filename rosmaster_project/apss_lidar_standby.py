#!/usr/bin/env python3
"""
APSS — RPLIDAR A1M8 standby al boot
Manda il comando STOP (0xA5 0x25) via seriale per fermare il motore.
Il driver ROS2 (rplidar_composition) lo riavvierà quando necessario.

Eseguito da systemd PRIMA del launch file ROS2.
"""
import serial
import time
import sys

PORT     = '/dev/ttyUSB1'
BAUDRATE = 115200
TIMEOUT  = 1.0

CMD_STOP = bytes([0xA5, 0x25])   # RPLIDAR stop scan + motore

def lidar_standby():
    try:
        ser = serial.Serial(PORT, BAUDRATE, timeout=TIMEOUT)
        time.sleep(0.1)          # attendi apertura porta
        ser.write(CMD_STOP)
        ser.flush()
        time.sleep(0.5)          # lascia tempo al motore di ricevere cmd
        ser.close()
        print(f"[APSS] RPLIDAR standby OK — {PORT}")
        sys.exit(0)
    except serial.SerialException as e:
        print(f"[APSS] RPLIDAR standby FAIL: {e}", file=sys.stderr)
        sys.exit(1)   # il service fallisce silenziosamente, non blocca il boot

if __name__ == '__main__':
    lidar_standby()
