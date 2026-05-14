# main.py — firmware docking station v2.0
# Dashboard: http://192.168.1.193
# NTP sync all'avvio — orario reale nel log e nella dashboard

import json, time, network, socket, ntptime
from machine import Pin, I2C, RTC
from ina219 import INA219

# ── Configurazione ────────────────────────────────────────────────
with open("config.json") as f:
    cfg = json.load(f)

# ── GPIO ──────────────────────────────────────────────────────────
relay = Pin(cfg["pin"]["relay_ch1"], Pin.OUT, value=1)
reed  = Pin(cfg["pin"]["reed_switch"], Pin.IN, Pin.PULL_UP)
grid  = Pin(cfg["pin"]["grid_detect"], Pin.IN)

# ── INA219 ────────────────────────────────────────────────────────
i2c = I2C(0,
          sda=Pin(cfg["pin"]["ina219_sda"]),
          scl=Pin(cfg["pin"]["ina219_scl"]),
          freq=100_000)
sensore = INA219(i2c,
                 address=cfg["ina219"]["i2c_address"],
                 shunt_ohms=cfg["ina219"]["shunt_ohms"])
ina_ok = sensore.ok()
if ina_ok:
    sensore.configura(max_amps=cfg["ina219"]["max_expected_amps"])
    print("[INA219] OK — addr 0x40")
else:
    print("[INA219] NON TROVATO — verifica cablaggio")

# ── RTC e NTP ─────────────────────────────────────────────────────
rtc = RTC()
ntp_ok = False

def sync_ntp():
    global ntp_ok
    try:
        ntptime.host = cfg.get("ntp_host", "pool.ntp.org")
        ntptime.settime()   # imposta UTC sull'RTC
        ntp_ok = True
        t = rtc.datetime()
        print("[NTP] Sync OK — UTC {:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(
              t[0], t[1], t[2], t[4], t[5], t[6]))
    except Exception as e:
        ntp_ok = False
        print("[NTP] Fallito: {}".format(e))

def ora_str():
    """Ora locale CET/CEST (UTC+1 / UTC+2) in formato HH:MM:SS."""
    t = rtc.datetime()          # (year, month, day, weekday, hour, min, sec, subsec)
    if not ntp_ok:
        # Se NTP non disponibile usa uptime
        up = int(stato["uptime"])
        return "{:02d}:{:02d}:{:02d}".format(up//3600, (up%3600)//60, up%60)
    # Offset Italia: +1 standard, +2 ora legale
    # Stima semplificata: ora legale da ultima domenica marzo a ultima domenica ottobre
    mese = t[1]
    ora_utc = t[4]
    offset = 2 if (3 < mese < 10) or (mese == 3 and t[2] >= 25) or \
                  (mese == 10 and t[2] < 25) else 1
    ora_loc = (ora_utc + offset) % 24
    return "{:02d}:{:02d}:{:02d}".format(ora_loc, t[5], t[6])

def data_str():
    """Data in formato DD/MM/YYYY."""
    if not ntp_ok:
        return "--/--/----"
    t = rtc.datetime()
    return "{:02d}/{:02d}/{:04d}".format(t[2], t[1], t[0])

# ── Stato globale ─────────────────────────────────────────────────
stato = {
    "relay":   1,
    "reed":    0,
    "grid":    0,
    "v":       0.0,
    "a":       0.0,
    "w":       0.0,
    "ina_ok":  ina_ok,
    "ntp_ok":  False,
    "log":     [],
    "uptime":  0,
}

def log(msg):
    entry = "{} {}".format(ora_str(), msg)
    stato["log"].append(entry)
    if len(stato["log"]) > 12:
        stato["log"].pop(0)
    print("[{}] {}".format(ora_str(), msg))

# ── IRQ Reed switch ───────────────────────────────────────────────
def irq_reed(pin):
    v = pin.value()
    stato["reed"] = v
    log("Reed AGGANCIATO" if v else "Reed sganciato")
    if v == 0 and stato["relay"] == 0:
        relay.value(1)
        stato["relay"] = 1
        log("Relay aperto — sicurezza")

reed.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING, handler=irq_reed)
stato["reed"] = reed.value()

# ── Lettura sensori ───────────────────────────────────────────────
def leggi_sensori():
    stato["grid"] = grid.value()
    if stato["ina_ok"]:
        dati = sensore.leggi_tutto()
        stato["v"] = dati["v"]
        stato["a"] = dati["a"]
        stato["w"] = dati["w"]

# ── Comandi ───────────────────────────────────────────────────────
def relay_chiudi():
    relay.value(0)
    stato["relay"] = 0
    log("Relay CHIUSO — ricarica abilitata")

def relay_apri():
    relay.value(1)
    stato["relay"] = 1
    log("Relay APERTO — ricarica bloccata")

def r1(): relay_chiudi()
def r0(): relay_apri()

def stato_txt():
    print("Relay={} Reed={} Grid={} V={:.2f}V I={:.4f}A {}".format(
        "CH" if stato["relay"]==0 else "AP",
        "AGG" if stato["reed"] else "---",
        "OK" if stato["grid"] else "BLK",
        stato["v"], stato["a"], ora_str()))

# ── WiFi ──────────────────────────────────────────────────────────
def connetti_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if wlan.isconnected():
        return wlan.ifconfig()[0]
    print("[WIFI] Connessione a {}...".format(cfg["wifi"]["ssid"]))
    wlan.connect(cfg["wifi"]["ssid"], cfg["wifi"]["password"])
    t = cfg["wifi"]["timeout_s"] * 10
    while not wlan.isconnected() and t > 0:
        time.sleep_ms(100)
        t -= 1
    if wlan.isconnected():
        ip = wlan.ifconfig()[0]
        print("[WIFI] Connesso — IP: {}".format(ip))
        return ip
    print("[WIFI] Fallito")
    return None

# ── Dashboard HTML ────────────────────────────────────────────────
# HTML diviso in 3 parti per non saturare la RAM — servito in chunks
_HTML_HEAD = b"""<!DOCTYPE html>
<html><head>
<meta charset=UTF-8>
<meta name=viewport content="width=device-width,initial-scale=1">
<meta http-equiv=refresh content=5>
<title>Docking Station</title>
<style>
body{font-family:Arial;background:#eef2f7;margin:0;padding:10px}
h2{color:#1a3a5c;margin:0 0 3px;font-size:16px}
.sub{font-size:10px;color:#888;margin-bottom:9px}
.grid{display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;margin-bottom:9px}
.card{background:white;border-radius:8px;padding:10px;box-shadow:0 1px 3px #0001}
.lbl{font-size:9px;color:#888;text-transform:uppercase;margin-bottom:2px}
.val{font-size:19px;font-weight:bold;color:#2c3e50}
.badge{display:inline-block;padding:2px 10px;border-radius:10px;font-size:12px;font-weight:bold;color:white}
.btns{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:9px}
a.btn{padding:8px 14px;border-radius:6px;font-size:12px;font-weight:bold;color:white;text-decoration:none}
.br{background:#e74c3c}.bg{background:#27ae60}.bb{background:#2980b9}.bv{background:#8e44ad}
.log{background:#1e1e2e;border-radius:8px;padding:9px;font-family:monospace;font-size:10px;color:#a8e6cf}
.lr{padding:2px 0;border-bottom:1px solid #ffffff10}
.ft{text-align:center;font-size:9px;color:#aaa;margin-top:6px}
</style></head><body>
"""

def _html_body():
    """Genera solo la parte dinamica — stringa breve."""
    s = stato
    rc  = "#e74c3c" if s["relay"] == 0 else "#27ae60"
    rt  = "CHIUSO" if s["relay"] == 0 else "APERTO"
    rec = "#27ae60" if s["reed"] == 1 else "#95a5a6"
    ret = "AGGANCIATO" if s["reed"] == 1 else "libero"
    gc  = "#27ae60" if s["grid"] == 1 else "#e74c3c"
    gt  = "RETE OK" if s["grid"] == 1 else "BLACKOUT"
    vc  = "#e74c3c" if (s["v"] < 11.5 or s["v"] > 15.0) and s["v"] > 0.5 else "#2c3e50"
    ic  = "#27ae60" if s["ina_ok"] else "#e74c3c"
    it  = "OK" if s["ina_ok"] else "ERR"
    nc  = "#27ae60" if s["ntp_ok"] else "#e67e22"
    nt  = "NTP OK" if s["ntp_ok"] else "NTP --"
    up  = int(s["uptime"])
    ora = ora_str()
    dat = data_str()
    log_html = "".join("<div class=lr>{}</div>".format(e) for e in reversed(s["log"]))

    h  = "<h2>Docking Station — Rosmaster R2</h2>"
    h += "<div class=sub>"
    h += "<b style='color:#1a3a5c;font-size:13px'>{} {}</b>".format(dat, ora)
    h += " &nbsp;|&nbsp; Uptime {:d}s".format(up)
    h += " &nbsp;|&nbsp; INA219 <b style='color:{}'>{}</b>".format(ic, it)
    h += " &nbsp;|&nbsp; <b style='color:{}'>{}</b>".format(nc, nt)
    h += "</div>"
    h += "<div class=grid>"
    h += "<div class=card><div class=lbl>Tensione</div>"
    h += "<div class=val style='color:{}'>{:.2f} V</div></div>".format(vc, s["v"])
    h += "<div class=card><div class=lbl>Corrente</div>"
    h += "<div class=val>{:.4f} A</div></div>".format(s["a"])
    h += "<div class=card><div class=lbl>Potenza</div>"
    h += "<div class=val>{:.3f} W</div></div>".format(s["w"])
    h += "<div class=card><div class=lbl>Relay CH1</div>"
    h += "<div class=val><span class=badge style='background:{}'>{}</span></div></div>".format(rc, rt)
    h += "<div class=card><div class=lbl>Reed switch</div>"
    h += "<div class=val><span class=badge style='background:{}'>{}</span></div></div>".format(rec, ret)
    h += "<div class=card><div class=lbl>Rete 230V</div>"
    h += "<div class=val><span class=badge style='background:{}'>{}</span></div></div>".format(gc, gt)
    h += "</div>"
    h += "<div class=btns>"
    h += "<a href=/relay/on  class='btn br'>Relay ON</a>"
    h += "<a href=/relay/off class='btn bg'>Relay OFF</a>"
    h += "<a href=/leggi     class='btn bb'>Leggi INA219</a>"
    h += "<a href=/scan_i2c  class='btn bv'>Scan I2C</a>"
    h += "</div>"
    h += "<div class=log>"
    h += "<div style='color:white;font-weight:bold;margin-bottom:4px'>Log eventi</div>"
    h += log_html if log_html else "<div class=lr>nessun evento</div>"
    h += "</div>"
    h += "<div class=ft>ESP32 WROOM-32D — MicroPython — Docking v2.0</div>"
    h += "</body></html>"
    return h

# ── Webserver ─────────────────────────────────────────────────────
def send_redirect(conn, loc="/"):
    conn.send("HTTP/1.1 302 Found\r\nLocation: {}\r\nConnection: close\r\n\r\n".format(loc).encode())

def gestisci(conn):
    try:
        conn.settimeout(3)
        req = conn.recv(512).decode("utf-8", "ignore")
        if not req:
            return
        rl   = req.split("\r\n")[0]
        path = rl.split(" ")[1] if len(rl.split(" ")) > 1 else "/"
        qpath = path.split("?")[0]

        if qpath in ("/", "/index.html"):
            # Serve dashboard in due chunk: head statico + body dinamico
            body = _html_body().encode()
            hdr = ("HTTP/1.1 200 OK\r\n"
                   "Content-Type: text/html; charset=utf-8\r\n"
                   "Cache-Control: no-cache\r\n"
                   "Connection: close\r\n\r\n").encode()
            conn.send(hdr)
            conn.send(_HTML_HEAD)
            # Body a chunks da 512 byte
            mv = memoryview(body)
            for i in range(0, len(body), 512):
                conn.send(mv[i:i+512])

        elif qpath == "/relay/on":
            relay_chiudi()
            send_redirect(conn)

        elif qpath == "/relay/off":
            relay_apri()
            send_redirect(conn)

        elif qpath == "/leggi":
            leggi_sensori()
            log("Lettura: {:.2f}V {:.4f}A".format(stato["v"], stato["a"]))
            send_redirect(conn)

        elif qpath == "/scan_i2c":
            try:
                res = i2c.scan()
                msg = "I2C: " + (", ".join("0x{:02X}".format(a) for a in res) if res else "nessun disp.")
            except Exception as e:
                msg = "I2C err: {}".format(e)
            log(msg)
            send_redirect(conn)

        elif qpath == "/stato.json":
            leggi_sensori()
            stato["ntp_ok"] = ntp_ok
            body = json.dumps(stato).encode()
            conn.send(b"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n"
                      b"Cache-Control: no-cache\r\nConnection: close\r\n\r\n")
            conn.send(body)

        else:
            conn.send(b"HTTP/1.1 404 Not Found\r\nConnection: close\r\n\r\nnot found")

    except Exception as e:
        print("[WEB] {}".format(e))
    finally:
        try: conn.close()
        except: pass

# ── Avvio ─────────────────────────────────────────────────────────
leggi_sensori()
ip = connetti_wifi()

# Sync NTP dopo connessione WiFi
if ip:
    sync_ntp()
    stato["ntp_ok"] = ntp_ok

if ip:
    srv = socket.socket()
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("", cfg["webserver"]["port"]))
    srv.listen(2)
    srv.settimeout(0.05)
    log("Dashboard: http://{}".format(ip))
else:
    srv = None
    print("[WEB] Non attivo — solo seriale")

print("\n[MAIN] r1() r0() stato_txt()\n")
stato_txt()

# ── Loop principale ───────────────────────────────────────────────
t_start    = time.time()
t_lettura  = time.time()
t_ntp_sync = time.time()       # risync NTP ogni ora
INTERVALLO = cfg["test"]["lettura_intervallo_s"]
NTP_INTERVALLO = 3600
grid_prec  = stato["grid"]

while True:
    adesso = time.time()
    stato["uptime"] = adesso - t_start

    # Richiesta HTTP
    if srv:
        try:
            conn, _ = srv.accept()
            gestisci(conn)
        except OSError:
            pass

    # Lettura periodica sensori
    if adesso - t_lettura >= INTERVALLO:
        t_lettura = adesso
        leggi_sensori()
        if stato["grid"] != grid_prec:
            grid_prec = stato["grid"]
            log("Rete OK" if stato["grid"] else "BLACKOUT")
            if stato["grid"] == 0 and stato["relay"] == 0:
                relay_apri()
        print("[{}] V={:.2f}V I={:+.4f}A Reed={} Grid={} Relay={}".format(
            ora_str(), stato["v"], stato["a"],
            "AGG" if stato["reed"] else "---",
            "OK" if stato["grid"] else "BLK",
            "CH" if stato["relay"]==0 else "AP"))

    # Risync NTP ogni ora
    if ip and adesso - t_ntp_sync >= NTP_INTERVALLO:
        t_ntp_sync = adesso
        sync_ntp()
        stato["ntp_ok"] = ntp_ok

    time.sleep_ms(50)
