# This file is executed on every boot (including wake-boot from deepsleep)
#import esp
#esp.osdebug(None)
#import webrepl
#webrepl.start()
# boot.py — eseguito prima di main.py
# CRITICO: relay aperto (HIGH) come prima istruzione
import machine, json, webrepl

with open("config.json") as f:
    cfg = json.load(f)

relay = machine.Pin(cfg["pin"]["relay_ch1"], machine.Pin.OUT, value=1)
machine.freq(240_000_000)

print("=" * 40)
print("[BOOT] ESP32 WROOM-32D — firmware test")
print(f"[BOOT] GPIO{cfg['pin']['relay_ch1']} relay = HIGH (aperto)")
print(f"[BOOT] CPU = {machine.freq()//1_000_000} MHz")
print("=" * 40)

webrepl.start(password="1234")
print("[BOOT] WebREPL attivo — ws://192.168.1.193:8266")
