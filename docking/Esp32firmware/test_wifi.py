import network
import time

# Credenziali Wi-Fi
ssid = "W3Connettimy24"
password = "Arafion968!020"

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
if not wlan.isconnected():
    print("Connessione alla rete Wi-Fi...")
    wlan.connect(ssid, password)
    while not wlan.isconnected():
        time.sleep(1)
        print(".")
    print("Wi-Fi connesso!")
    print("Indirizzo IP:", wlan.ifconfig()[0])
else:
    print("-->Wi-Fi già connesso<--")
    print("Indirizzo IP:", wlan.ifconfig()[0])
    