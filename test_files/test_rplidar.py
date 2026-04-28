# test_files/test_rplidar.py
from rplidar import RPLidar
import time

PORT = '/dev/ttyUSB1'

lidar = RPLidar(PORT, baudrate=115200)

try:
    info = lidar.get_info()
    print(f"Info: {info}")
    
    health = lidar.get_health()
    print(f"Health: {health}")
    
    print("\nAvvio scansione — 5 secondi...")
    for i, scan in enumerate(lidar.iter_scans()):
        print(f"Scan {i}: {len(scan)} misure — primo punto: {scan[0]}")
        if i >= 4:
            break

except Exception as e:
    print(f"Errore: {e}")

finally:
    lidar.stop()
    lidar.disconnect()
    print("LiDAR disconnesso.")