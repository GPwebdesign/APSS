#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
APSS - morsetti_logger.py
Registra misure manuali al tester dei morsetti della batteria ECO-WORTHY
durante un ciclo di caratterizzazione della scarica.

Queste misure sono i punti di ancoraggio: correlano la V reale ai terminali
della batteria con la V letta dall'INA219 (a valle DD32AJ4B) nello stesso
istante, permettendo di stimare l'offset e la sua dipendenza dal carico.

Uso: python3 morsetti_logger.py
  oppure, da discharge_logger.py con args:
     python3 morsetti_logger.py --valore 12.84 --nota avvio_discharge

Il file note_morsetti.csv viene creato se non esiste, altrimenti si appende.
Ctrl-C in qualsiasi momento non corrompe i dati (e' one-shot, non ha loop).
"""

import os
import sys
import csv
import argparse
from datetime import datetime, timezone

LOG_DIR   = os.path.dirname(os.path.abspath(__file__))
NOTE_FILE = os.path.join(LOG_DIR, "note_morsetti.csv")
HEADER    = ["timestamp_iso", "v_morsetti", "nota"]
CONV_NOTE = ("Misure manuali al tester sui morsetti della batteria ECO-WORTHY. "
             "Correlare per timestamp con discharge_*.csv per stimare offset "
             "V_ina vs V_reale. Convenzione i_ina: POSITIVO=discharging, NEGATIVO=charging.")

def now_iso():
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")

def scrivi_riga(v, nota):
    esiste = os.path.exists(NOTE_FILE) and os.path.getsize(NOTE_FILE) > 0
    with open(NOTE_FILE, "a", newline="") as f:
        w = csv.writer(f)
        if not esiste:
            f.write(f"# {CONV_NOTE}\n")
            w.writerow(HEADER)
        w.writerow([now_iso(), f"{v:.3f}", nota])
    print(f"[ok] {v:.3f} V -> {os.path.basename(NOTE_FILE)}")

def chiedi_valore():
    while True:
        raw = input("Lettura morsetti al tester (V): ").strip().replace(",", ".")
        try:
            return float(raw)
        except ValueError:
            print(f"  '{raw}' non e' un numero valido. Riprova.")

def chiedi_nota():
    raw = input("Nota opzionale [invio per saltare]: ").strip()
    return raw if raw else ""

def main():
    parser = argparse.ArgumentParser(
        description="Registra una misura manuale ai morsetti della batteria."
    )
    parser.add_argument("--valore", type=float, default=None,
                        help="Tensione letta al tester (V)")
    parser.add_argument("--nota",   type=str,   default=None,
                        help="Nota descrittiva opzionale")
    args = parser.parse_args()

    # Se chiamato da discharge_logger con args, non chiede nulla.
    if args.valore is not None:
        v    = args.valore
        nota = args.nota if args.nota is not None else ""
    else:
        # Modalita' interattiva: prompt semplice, nessun loop lungo.
        print(f"[morsetti_logger] File: {os.path.basename(NOTE_FILE)}")
        v    = chiedi_valore()
        nota = chiedi_nota()

    scrivi_riga(v, nota)

if __name__ == "__main__":
    main()