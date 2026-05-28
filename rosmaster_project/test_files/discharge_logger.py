#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
APSS - discharge_logger.py
Logger di caratterizzazione della scarica della batteria LiFePO4 ECO-WORTHY.

Scopo: produrre un dataset V/I/P con timestamp dell'INA219 (0x40, a valle del
DD32AJ4B) lungo un ciclo di scarica completo, per tarare empiricamente la
mappatura V_ina <-> SoC e le soglie voltage-based di safety_node.

NON e' battery_node. NON fa coulomb counting ne' interpreta i dati.
L'interpretazione si fa in analisi off-line su discharge_*.csv.

ASSUNZIONI DI QUESTO PRIMO CICLO (sessione 27/05/2026):
  - Robot FERMO IDLE durante la scarica -> corrente quasi costante (~0.6A).
    Si usa la V ISTANTANEA grezza per il campionamento adattivo, senza gate
    sulla corrente. Se un domani si logga SOTTO CARICO, rivedere questa
    semplificazione: gli spunti motore abbassano momentaneamente la V per
    via della load regulation del DD32AJ4B e falserebbero l'infittimento.
  - battery_node NON in esecuzione durante la cattura (evita doppio accesso
    I2C 0x40). apss-oled.service in fallback legge anch'esso l'INA219:
    letture concorrenti sono tollerate (transazioni I2C atomiche) ma se
    noti glitch fermalo temporaneamente.

REGOLA OPERATIVA:
  Durante UNA scarica, tra una sessione e l'altra NON caricare la batteria.
  Se carichi, al prossimo avvio scegli [N]uovo ciclo (file nuovo).
  Una scarica spezzata su piu' sessioni resta ricostruibile SOLO se tra
  le sessioni non c'e' stata carica (il log INA non vede la carica a
  robot spento).

DA VERIFICARE SULLA VM/HAWK contro battery_node.py:
  [1] Init bus + classe INA219 (sezione INIT INA219 sotto).
  [2] Convenzione segno corrente — verificata sulla logica coulomb counting
      di battery_node.py (fonte di verita', Mag2026):
      ina.current POSITIVO = DISCHARGING (robot assorbe dal circuito),
                  NEGATIVO = CHARGING   (docking eroga, batteria assorbe).
      Confermato da: delta_soc = (-current_a * dt) / C → current_a positivo
      abbassa il SoC → DISCHARGING. Il commento su msg.current nel codice
      ("negativo=discharge") e' un refuso e va ignorato.
      Scarica idle attesa: i_ina ~ +0.6A.
"""

import os
import sys
import csv
import glob
import time
import signal
import subprocess
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# INIT INA219  --  DA VERIFICARE [1] contro battery_node.py
# ---------------------------------------------------------------------------
import board
import busio
from adafruit_ina219 import INA219

INA219_ADDR = 0x40

def init_ina219():
    i2c = busio.I2C(board.SCL, board.SDA)
    return INA219(i2c, addr=INA219_ADDR)

def leggi_ina(sensor):
    """Ritorna (v, i, p) in V, A, W.
    bus_voltage = tensione lato carico (VIN-).
    current in mA -> A. Segno: vedi nota [2] sopra.
    Potenza calcolata come V*|I|: coerente con battery_node.py e oled_node.py.
    sensor.power NON usare: il registro riporta mW con shunt R100 e range
    default adafruit (es. 5.8mW invece di 5.8W)."""
    v = sensor.bus_voltage
    i = sensor.current / 1000.0
    p = v * abs(i)
    return v, i, p

# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------
LOG_DIR    = os.path.dirname(os.path.abspath(__file__))
PREFIX     = "discharge_"
NOTE_FILE  = os.path.join(LOG_DIR, "note_morsetti.csv")

# Bande campionamento adattivo sulla V istantanea INA219 (a valle DD32AJ4B).
# Valutate dall'alto verso il basso; primo match vince.
BANDE_V = [
    (11.5, 300),  # V >= 11.5  -> 300s / 5min  (plateau LiFePO4 — V piatta per ore)
    (11.2, 60),   # V >= 11.2  -> 60s           (inizio discesa)
    (0.0,  10),   # V <  11.2  -> 10s            (ginocchio finale — caduta rapida)
]

CONV_NOTE  = ("i_ina = grezzo adafruit (mA->A). "
              "Convenzione: POSITIVO=discharging, NEGATIVO=charging. "
              "Scarica idle attesa: i_ina ~ +0.6A.")
CSV_HEADER = ["timestamp_iso", "v_ina", "i_ina", "p_ina", "nota"]

# ---------------------------------------------------------------------------
# UTIL
# ---------------------------------------------------------------------------
def now_iso():
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")

def intervallo_per_v(v):
    for soglia, dt in BANDE_V:
        if v >= soglia:
            return dt
    return BANDE_V[-1][1]

def trova_ultimo():
    files = sorted(glob.glob(os.path.join(LOG_DIR, PREFIX + "*.csv")))
    return files[-1] if files else None

def nuovo_nome():
    stamp = datetime.now().strftime("%Y%m%d_%H%M")
    return os.path.join(LOG_DIR, f"{PREFIX}{stamp}.csv")

# ---------------------------------------------------------------------------
# PROMPT DI AVVIO
# ---------------------------------------------------------------------------
def scegli_file():
    ultimo = trova_ultimo()
    if ultimo is None:
        path = nuovo_nome()
        print(f"[avvio] Nessun ciclo esistente. Nuovo file: {os.path.basename(path)}")
        return path, True
    print(f"[avvio] Ultimo ciclo trovato: {os.path.basename(ultimo)}")
    scelta = input("        [N]uovo ciclo o [R]iprendi ultimo? [R]: ").strip().lower()
    if scelta == "n":
        path = nuovo_nome()
        print(f"[avvio] Nuovo file: {os.path.basename(path)}")
        return path, True
    print(f"[avvio] Riprendo: {os.path.basename(ultimo)}")
    return ultimo, False

def prompt_morsetti_reminder():
    """Reminder: suggerisce di registrare la lettura morsetti via script dedicato."""
    raw = input(
        "[avvio] Lettura morsetti al tester (V) [invio per saltare, "
        "oppure esegui morsetti_logger.py]: "
    ).strip()
    if not raw:
        return
    raw = raw.replace(",", ".")
    try:
        v = float(raw)
    except ValueError:
        print(f"[avvio] '{raw}' non valido, salto.")
        return
    # Delega la scrittura a morsetti_logger.py per coerenza del formato.
    script = os.path.join(LOG_DIR, "morsetti_logger.py")
    if os.path.exists(script):
        subprocess.run(
            [sys.executable, script, "--valore", str(v), "--nota", "avvio_discharge"],
            check=False
        )
    else:
        # Fallback: scrivi direttamente se lo script non e' presente.
        _scrivi_nota(v, "avvio_discharge")

def _scrivi_nota(v, nota=""):
    esiste = os.path.exists(NOTE_FILE) and os.path.getsize(NOTE_FILE) > 0
    with open(NOTE_FILE, "a", newline="") as f:
        w = csv.writer(f)
        if not esiste:
            f.write(f"# {CONV_NOTE}\n")
            w.writerow(["timestamp_iso", "v_morsetti", "nota"])
        w.writerow([now_iso(), f"{v:.3f}", nota])
    print(f"[avvio] Morsetti {v:.3f}V -> {os.path.basename(NOTE_FILE)}")

# ---------------------------------------------------------------------------
# LOOP DI LOGGING
# ---------------------------------------------------------------------------
_stop = False

def _on_signal(signum, frame):
    global _stop
    _stop = True

def apri_csv(path, is_new):
    serve_header = is_new or not os.path.exists(path) or os.path.getsize(path) == 0
    f = open(path, "a", newline="")
    w = csv.writer(f)
    if serve_header:
        f.write(f"# {CONV_NOTE}\n")
        w.writerow(CSV_HEADER)
    return f, w

def main():
    signal.signal(signal.SIGINT,  _on_signal)
    signal.signal(signal.SIGTERM, _on_signal)

    path, is_new = scegli_file()
    prompt_morsetti_reminder()

    try:
        sensor = init_ina219()
    except Exception as e:
        print(f"[errore] init INA219: {e}", file=sys.stderr)
        sys.exit(1)

    f, w = apri_csv(path, is_new)
    w.writerow([now_iso(), "", "", "", "RESTART"])
    f.flush()

    print(f"[run] Logging su {os.path.basename(path)}. Ctrl-C per fermare.")
    print(f"[run] Bande: {BANDE_V}")

    while not _stop:
        try:
            v, i, p = leggi_ina(sensor)
        except Exception as e:
            w.writerow([now_iso(), "", "", "", f"READ_ERR:{e}"])
            f.flush()
            time.sleep(5)
            continue

        w.writerow([now_iso(), f"{v:.3f}", f"{i:.4f}", f"{p:.3f}", ""])
        f.flush()
        os.fsync(f.fileno())

        dt = intervallo_per_v(v)
        slept = 0
        while slept < dt and not _stop:
            time.sleep(min(1, dt - slept))
            slept += 1

    w.writerow([now_iso(), "", "", "", "STOP"])
    f.flush()
    f.close()
    print("\n[stop] Log chiuso correttamente.")

if __name__ == "__main__":
    main()