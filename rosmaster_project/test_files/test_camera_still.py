#!/usr/bin/env python3
# coding=utf-8
"""
APSS — Test calibrazione camera in modalità still (foto singola)
Scatta una foto con i parametri correnti e la salva in test_files/
Modifica i parametri nel dizionario params e rilancia per confrontare.
"""
from picamera2 import Picamera2
import time
import os
import json
from datetime import datetime

# Parametri da testare — modifica qui
params = {
    "AwbEnable":   True,
    "ColourGains": (0.9, 1.1),
    "AeEnable":    True,
    "Sharpness":   3.0,
    "Contrast":    1.2,
    "Saturation":  1.3,
    "Brightness":  0.1,
}

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))

cam = Picamera2()
config = cam.create_still_configuration(
    main={"size": (1920, 1080), "format": "RGB888"},
    controls=params)
cam.configure(config)
cam.start()
time.sleep(2)  # attendi stabilizzazione AE

ts = datetime.now().strftime('%Y%m%d_%H%M%S')
path = os.path.join(OUTPUT_DIR, f'test_still_{ts}.jpg')
cam.capture_file(path)
cam.stop()
cam.close()
print(f"Salvato: {path}")
print(f"Parametri usati: {json.dumps(params, indent=2)}")
