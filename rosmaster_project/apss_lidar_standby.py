#!/usr/bin/env python3
"""
APSS — RPLIDAR A1M8 standby al boot
Per A1M8: DTR=True = motore OFF, DTR=False = motore ON
"""
import serial
import time
import sys

PORT     = '/dev/ttyUSB1'
BAUDRATE = 115200
TIMEOUT  = 1.0

def lidar_standby():
    try:
        ser = serial.Serial(PORT, BAUDRATE, timeout=TIMEOUT)
        time.sleep(1.0)

        # A1M8: DTR=True → motore OFF
        ser.dtr = True
        print(f"[APSS] RPLIDAR standby OK — DTR=True — {PORT}")

        while True:
            ser.dtr = True
            time.sleep(2.0)

    except serial.SerialException as e:
        print(f"[APSS] RPLIDAR standby FAIL: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        ser.close()
        sys.exit(0)

if __name__ == '__main__':
    lidar_standby()