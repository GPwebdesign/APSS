# APSS — Documentazione Firmware ESP32 Docking Station
> Versione firmware: v2.1 — Maggio 2026  
> Hardware: ESP32 WROOM-32D  
> Linguaggio: MicroPython  
> Dashboard: http://192.168.1.193

---

## 1. Architettura generale

Il firmware gestisce la docking station di ricarica autonoma del robot APSS.
È composto da 4 file che lavorano insieme:

```
boot.py       ← eseguito PRIMA di main.py ad ogni avvio
config.json   ← parametri configurabili (WiFi, pin, soglie, INA219)
ina219.py     ← driver I2C per il sensore di corrente/tensione INA219
main.py       ← logica principale: webserver, loop sensori, gestione relay
```

### Sequenza di avvio

```
Power ON / Reset
    ↓
boot.py     → GPIO5 relay HIGH (aperto) come prima istruzione
            → CPU a 240MHz
            → WebREPL attivo (ws://192.168.1.193:8266, password: 1234)
    ↓
main.py     → carica config.json
            → inizializza GPIO (relay, reed/microswitch, grid)
            → inizializza INA219 via I2C
            → connette WiFi
            → sync NTP (pool.ntp.org)
            → avvia webserver HTTP porta 80
            → entra nel loop principale (relay si chiude automaticamente
              entro 2s se rete presente e switch agganciato)
```

---

## 2. File: `boot.py`

### Funzione
Eseguito automaticamente da MicroPython ad ogni avvio, prima di `main.py`.
Contiene solo operazioni critiche di sicurezza e configurazione hardware iniziale.

### Operazioni eseguite
1. **Relay GPIO5 → HIGH** (aperto) come prima istruzione assoluta — garantisce
   che il relay di ricarica sia sempre aperto all'avvio, indipendentemente
   dallo stato precedente
2. **CPU a 240MHz** — massima frequenza per risposta webserver ottimale
3. **WebREPL attivo** — accesso REPL remoto via browser per debug e comandi

### Perché il relay viene aperto in boot.py e non in main.py
Se `main.py` dovesse crashare durante l'inizializzazione, il relay rimarrebbe
comunque aperto (sicuro). Aprirlo in `boot.py` garantisce la sicurezza anche
in scenari di fault software.

### Codice
```python
import machine, json, webrepl

with open("config.json") as f:
    cfg = json.load(f)

relay = machine.Pin(cfg["pin"]["relay_ch1"], machine.Pin.OUT, value=1)
machine.freq(240_000_000)
webrepl.start(password="1234")
```

---

## 3. File: `config.json`

### Funzione
File di configurazione centralizzato. Tutti i parametri modificabili
sono qui — nessun valore hardcoded in `main.py` o `ina219.py`.

### Struttura e valori attuali (v2.1)
```json
{
    "wifi": {
        "ssid": "...",
        "password": "...",
        "timeout_s": 20
    },
    "webserver": {
        "port": 80
    },
    "ntp_host": "pool.ntp.org",
    "pin": {
        "relay_ch1":   5,    ← Relay ricarica (LOW=chiuso, HIGH=aperto)
        "ina219_sda":  21,   ← I2C SDA
        "ina219_scl":  22,   ← I2C SCL
        "reed_switch": 18,   ← Microswitch NC (sostituisce reed switch)
        "grid_detect": 34    ← Partitore tensione rilevamento 230V (input-only)
    },
    "ina219": {
        "i2c_address":       64,   ← 0x40 (A0=A1=GND)
        "shunt_ohms":        0.1,  ← R100 shunt onboard HW-831B
        "max_expected_amps": 2.0   ← Range corrente (CC calibrata a 1.5A)
    },
    "soglie": {
        "tensione_min_v": 12.5,   ← Soglia allarme bassa LiFePO4
        "tensione_max_v": 14.7    ← Soglia allarme alta LiFePO4
    },
    "ricarica": {
        "start_v":          13.1,  ← Soglia START display XHM603 (riferimento)
        "stop_v":           14.4,  ← Soglia STOP display XHM603 (riferimento)
        "debounce_reed_ms": 2000   ← Debounce IRQ microswitch
    },
    "test": {
        "lettura_intervallo_s": 2  ← Frequenza lettura INA219 e loop logica
    }
}
```

### Note sulla sezione "ricarica"
I valori `start_v` e `stop_v` sono documentazione di riferimento — la logica
START/STOP è gestita **hardware** dall'XHM603, non dal firmware ESP32.
Il firmware usa `tensione_min_v` e `tensione_max_v` solo per colorare la
tensione in rosso sulla dashboard in caso di anomalia.

---

## 4. File: `ina219.py`

### Funzione
Driver I2C per il sensore INA219 HW-831B. Gestisce lettura di tensione,
corrente e potenza. Non dipende da librerie esterne MicroPython.

### Convenzione corrente (CRITICA)
```
Corrente POSITIVA → ricarica attiva (XHM603 eroga corrente verso batteria)
Corrente NEGATIVA → flusso inverso (batteria alimenta XHM603 a relay aperto)
```
Questa convenzione è verificata fisicamente sul cablaggio HW-831B:
- VIN+ ← XHM603 BAT+ (sorgente)
- VIN- → pogo pin+ (carico/batteria robot)

### Cablaggio fisico INA219 HW-831B
```
Pin header anteriori: SDA(21) / SCL(22) / VCC(3.3V) / GND / A0(GND) / A1(GND)
Morsetti a vite posteriori: VIN+(←XHM603) / VIN-(→pogo pin)
Indirizzo I2C: 0x40 (A0=A1=GND)
```

### Metodi pubblici
| Metodo | Ritorna | Descrizione |
|---|---|---|
| `configura(max_amps)` | — | Imposta registro CAL — chiamare dopo init |
| `tensione_v()` | float (V) | Tensione bus lato VIN- (lato pogo pin) |
| `corrente_a()` | float (A) | Corrente con segno (+ ricarica, - inverso) |
| `potenza_w()` | float (W) | V × I calcolata |
| `leggi_tutto()` | dict {v,a,w} | Lettura unica ottimizzata |
| `ok()` | bool | Verifica presenza sul bus I2C |

### ⚠️ Nota su `configura()` e reset a caldo
Il registro CAL dell'INA219 si azzera se l'ESP32 viene resettato a caldo.
In v2.1 è stato aggiunto un watchdog in `leggi_sensori()` che rileva
automaticamente la condizione (V>12V, A=0) e reinizializza il registro CAL.

---

## 5. File: `main.py`

### Funzione
Logica principale del firmware v2.1. Gestisce:
- Webserver HTTP (dashboard + API JSON)
- Loop sensori (INA219 ogni 2s, grid detection)
- IRQ microswitch con debounce 2000ms
- Relay automatico (chiude se switch agganciato + rete presente)
- Sync NTP (all'avvio + ogni ora)

### Struttura interna

```
main.py
├── Import
│   ├── json, time, network, socket, ntptime, utime
│   └── machine.Pin, machine.I2C, machine.RTC, INA219
│
├── Inizializzazione
│   ├── carica config.json
│   ├── GPIO: relay(GPIO5), microswitch(GPIO18 pull-up), grid(GPIO34)
│   ├── INA219 via I2C(SDA=21, SCL=22, addr=0x40)
│   ├── RTC + sync NTP
│   └── stato{} — dizionario stato globale
│
├── Funzioni di utilità
│   ├── ora_str()       — ora locale CET/CEST da RTC (UTC+1/+2)
│   ├── data_str()      — data DD/MM/YYYY
│   ├── log(msg)        — append log con timestamp (max 12 voci FIFO)
│   └── leggi_sensori() — aggiorna stato{} + watchdog CAL INA219
│
├── Gestione relay
│   ├── relay_chiudi() / r1() — relay ON  (GPIO5=LOW,  ricarica abilitata)
│   └── relay_apri()  / r0() — relay OFF (GPIO5=HIGH, ricarica bloccata)
│
├── IRQ Microswitch (GPIO18) — v2.1
│   └── irq_reed() — debounce 2000ms via utime.ticks_diff
│       Se sgancio reale (>2s) e relay chiuso → relay_apri() sicurezza
│
├── Dashboard HTML
│   ├── _HTML_HEAD (bytes literal statico ~1.2KB)
│   └── _html_body() — parte dinamica ~2.8KB
│       Separati per non saturare RAM MicroPython (>9KB causa crash)
│
├── Webserver HTTP — endpoint
│   ├── GET /           → dashboard HTML (auto-refresh 5s)
│   ├── GET /relay/on   → relay_chiudi() → redirect /
│   ├── GET /relay/off  → relay_apri()  → redirect /
│   ├── GET /leggi      → leggi_sensori() → redirect /
│   ├── GET /scan_i2c   → scan bus I2C   → redirect /
│   └── GET /stato.json → stato{} in JSON (API)
│
└── Loop principale (ogni 50ms)
    ├── accept() connessioni HTTP (timeout 50ms)
    ├── ogni 2s: leggi_sensori()
    ├── ogni 2s: rilevamento cambio stato grid (blackout)
    ├── ogni 2s: logica relay automatica (v2.1)
    │   ├── se switch=1, relay=1, grid=1 → relay_chiudi()
    │   └── se switch=0, relay=0         → relay_apri()
    └── ogni 3600s: risync NTP
```

### Stato globale `stato{}`
```python
stato = {
    "relay":  1,      # 0=chiuso (ricarica), 1=aperto (bloccata)
    "reed":   0,      # 0=sganciato/aperto, 1=agganciato
                      # ⚠️ reed rimosso fisicamente → GPIO18 pull-up → sempre 1
    "grid":   0,      # 0=blackout, 1=rete 230V presente
    "v":      0.0,    # tensione INA219 lato pogo pin (V)
    "a":      0.0,    # corrente INA219 con segno (A)
    "w":      0.0,    # potenza INA219 (W)
    "ina_ok": bool,   # True se INA219 risponde sul bus I2C
    "ntp_ok": bool,   # True se sync NTP riuscita
    "log":    [],     # lista eventi con timestamp (max 12 FIFO)
    "uptime": 0,      # secondi dall'avvio ESP32
}
```

### Comandi WebREPL/seriale
```python
r1()         # chiude relay manuale (abilita ricarica)
r0()         # apre relay manuale (blocca ricarica)
stato_txt()  # stampa stato compatto su seriale
```

---

## 6. Catena di potenza docking — riferimento

```
230VAC
    ↓
Alimentatore switching 20VDC / 3.25A
    ↓
Relay CH1 ESP32 GPIO5 (LOW=chiuso, HIGH=aperto)
    ↓
XL4016 CC/CV (CV=14.40V, CC=1.5A — calibrato Maggio 2026)
    ↓
Fusibile T3.15A 250V slow-blow
    ↓
XHM603 v1.0 (STOP=14.4V display / START=13.1V display)
    ↓
INA219 HW-831B (VIN+←XHM603, VIN-→pogo pin)
    ↓
Pogo pin docking → Pad rame robot → Batteria ECO-WORTHY LiFePO4 12.8V 8Ah
```

### Offset tensione catena (misurati fisicamente — Maggio 2026)
| Coppia | Offset | Condizione |
|---|---|---|
| Display XHM603 vs terminali batteria | **+0.70V** | Relay aperto (a vuoto) |
| INA219 vs terminali batteria | **+0.34V** | In ricarica attiva |
| Display XHM603 vs INA219 | **+0.40V** | In ricarica attiva |

### Comportamento XHM603 (verificato fisicamente)
- **STOP**: scatta al **superamento** — impostato 14.4V → scatta a 14.5V display
- **START**: riavvia quando tensione **scende sotto** il valore impostato
- ⚠️ Misurare con tester sui terminali batteria **durante la ricarica** può
  far scattare il relay per perturbazione — riarmare da webapp `/relay/on`

### Microswitch docking (sostituisce reed switch — Maggio 2026)
- Tipo: microswitch meccanico NC (normally closed)
- Cablaggio: COM → GPIO18 ESP32, NC → GND
- A riposo (robot non agganciato): NC chiuso → GPIO18 = GND = 0
- Premuto (robot agganciato): NC aperto → pull-up → GPIO18 = 1
- ⚠️ Attualmente fissato in posizione "aperto" (robot sempre "agganciato")
  in attesa di montaggio definitivo sul fronte della docking station,
  al centro tra le due barre di rame che coincidono con i pogo pin

---

## 7. Fix applicati in v2.1 (Maggio 2026)

### Fix 1 — Debounce IRQ microswitch
**Problema:** IRQ su GPIO18 senza debounce → spike dalla chiusura relay
XHM603 interpretati come sgancio → relay ESP32 aperto → ricarica interrotta.

**Soluzione:** debounce software 2000ms con `utime.ticks_diff()`.
Spike <2s ignorati. Sgancio reale (>2s) gestito correttamente.

```python
_last_reed_ms = 0
REED_DEBOUNCE_MS = 2000

def irq_reed(pin):
    global _last_reed_ms
    now = utime.ticks_ms()
    if utime.ticks_diff(now, _last_reed_ms) < REED_DEBOUNCE_MS:
        return  # spike ignorato
    _last_reed_ms = now
    v = pin.value()
    stato["reed"] = v
    log("Reed AGGANCIATO" if v else "Reed sganciato")
    if v == 0 and stato["relay"] == 0:
        relay_apri()
        log("Relay aperto — sicurezza")
```

### Fix 2 — Relay automatico all'aggancio
**Problema:** relay sempre aperto al boot → ricarica richiedeva intervento
manuale dalla webapp ad ogni avvio.

**Soluzione:** logica automatica nel loop ogni 2s.
Con microswitch rimosso/aperto (GPIO18 pull-up = 1 costante), il relay
si chiude automaticamente ad ogni boot quando la rete è presente.

```python
if stato["reed"] == 1 and stato["relay"] == 1 and stato["grid"] == 1:
    relay_chiudi()
    log("Relay chiuso auto — rete presente")
elif stato["reed"] == 0 and stato["relay"] == 0:
    relay_apri()
    log("Relay aperto auto — reed sganciato")
```

### Fix 3 — Watchdog CAL INA219
**Problema:** reset a caldo ESP32 azzera registro CAL INA219 → corrente
legge 0A con tensione corretta.

**Soluzione:** watchdog in `leggi_sensori()` — se V>12V e A=0 → reinizializza.

```python
if stato["v"] > 12.0 and stato["a"] == 0.0:
    sensore.configura(max_amps=cfg["ina219"]["max_expected_amps"])
    log("INA219 CAL reinizializzato")
```

### Fix 4 — config.json aggiornato per LiFePO4
- `ina219.max_expected_amps`: 3.0 → **2.0** (CC calibrata a 1.5A)
- `soglie.tensione_min_v`: 11.5 → **12.5** (soglia bassa LiFePO4)
- `soglie.tensione_max_v`: 15.0 → **14.7** (soglia alta LiFePO4)
- Aggiunta sezione `ricarica` con valori di riferimento XHM603

---

## 8. Note operative

| Situazione | Procedura |
|---|---|
| INA219 legge 0A con tensione corretta | Watchdog automatico (v2.1) — se persiste: reset ESP32 |
| Spike fa scattare relay durante ricarica | Debounce v2.1 previene — se accade: `/relay/on` da webapp |
| Tester sui terminali batteria fa scattare XHM603 | Riarmare relay da webapp dopo misura |
| Verifica bus I2C | `/scan_i2c` dalla dashboard |
| Debug da remoto | WebREPL ws://192.168.1.193:8266 (password: 1234) |
| Comandi rapidi da seriale | `r1()` `r0()` `stato_txt()` |
| API JSON per automazione | GET http://192.168.1.193/stato.json |

---

## 9. Roadmap firmware

| Item | Priorità | Note |
|---|---|---|
| Installazione microswitch meccanico (attualmente chiuso con scotch, contatto aperto) sul fronte della docking station, al centro tra le due barre di rame che coincidono con i pogo pin (attivi) sul paraurti del robot | Alta | Microswitch NC — montaggio fisico da completare |
| Aggiornare webapp docking: sostituire tutti i riferimenti a 'reed' con 'microswitch' | Bassa | `irq_reed()`→`irq_switch()`, `stato["reed"]`→`stato["switch"]`, log messages, HTML dashboard |
| Soglie XHM603 definitive post-ciclo completo | Media | In calibrazione — valori conservativi attuali |
| Aggiornamento `battery_node.py` con tabella SoC LiFePO4 | Media | Step 4 Fase D ancora da completare |
| Coulomb counting via INA219 hawk | Media | Per stima SoC accurata sul plateau |

---

*APSS — GPwebdesign — Maggio 2026 — Firmware docking v2.1*
