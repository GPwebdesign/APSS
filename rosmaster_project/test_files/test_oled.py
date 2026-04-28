#!/usr/bin/env python3
# coding=utf-8
"""
APSS — Test display OLED SSD1306 128x64 I2C
Verifica funzionamento base prima di integrare in ROS2
"""
import time
from luma.core.interface.serial import i2c
from luma.oled.device import ssd1306
from luma.core.render import canvas
from PIL import ImageFont

# Inizializzazione I2C e display
serial = i2c(port=1, address=0x3C)
device = ssd1306(serial, width=128, height=64)

print("Display OLED SSD1306 inizializzato!")

# Font default (bitmap)
try:
    font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 14)
    font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 11)
except:
    font_large = ImageFont.load_default()
    font_small = ImageFont.load_default()

# Schermata di test
with canvas(device) as draw:
    # Titolo
    draw.text((0, 0),  "APSS Robot",        font=font_large, fill="white")
    draw.line([(0, 15), (128, 15)],          fill="white", width=1)
    # Info
    draw.text((0, 17), "IP: 192.168.1.158", font=font_small, fill="white")
    draw.text((0, 29), "Batt: 12.4V  85%",  font=font_small, fill="white")
    draw.text((0, 41), "Mode: STANDBY",      font=font_small, fill="white")
    draw.text((0, 52), "T:23 H:45% Gas:OK", font=font_small, fill="white")

print("Schermata test visualizzata — attendo 10s...")
time.sleep(10)

# Schermata animata
print("Test animazione...")
for i in range(5):
    with canvas(device) as draw:
        draw.text((0, 0),  "APSS Robot",    font=font_large, fill="white")
        draw.line([(0, 15), (128, 15)],     fill="white", width=1)
        draw.text((0, 25), f"Test {i+1}/5", font=font_large, fill="white")
        draw.rectangle([(0, 50), (int(128*(i+1)/5), 62)], fill="white")
    time.sleep(1)

device.cleanup()
print("Test completato!")
