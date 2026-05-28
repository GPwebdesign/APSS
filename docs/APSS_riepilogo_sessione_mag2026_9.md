# APSS — Autonomous Patrol and Surveillance System
## Riepilogo sessione per nuova chat — Maggio 2026

Contesto: Robot autonomo APSS su Yahboom Rosmaster R2 + Raspberry Pi 4 (hawk, 192.168.1.158,
Ubuntu 22.04, ROS2 Humble). VM sviluppo: gp68-vmware. VM Buildozer: VMware-Ubuntu24-04-4.
Repo: `rosmaster_project` e `ros2_py_ws` (GitHub GPwebdesign privati).
Workflow: modifiche codice su VM → push GitHub → pull hawk → test.
Doc solo su PC `D:\_claudecodeproject\APSS\` → push APSS.

---

## Completati in questa sessione 26/05/2026

- ✅ **Batteria LiFePO4 installata:** YTZ10S → ECO-WORTHY 12.8V 8Ah
  (B0CCJ8JJV3, 50€, 152×65×96mm, terminali F2, 1.05kg). Installata
  nel robot. XL4016: CV=14.40V, CC=1.5A (2A causava spike su XHM603).
  Fusibile T3.15A slow-blow. XHM603: STOP=14.4V(scatta a 14.5V),
  START=13.1V. OCV post-carica stabile: 13.40V (~95% SoC). Offset
  catena: display-terminali=+0.70V, INA219docking-terminali=+0.34V.

- ✅ **Firmware ESP32 docking v2.1:** Fix debounce reed 2000ms (spike
  non aprono più relay), relay automatico (chiude se switch=1+grid=1),
  watchdog CAL INA219. Microswitch NC sostituisce reed (erratico).
  Attualmente fissato aperto → relay chiude automaticamente al boot.
  Config.json aggiornato LiFePO4. Dashboard "Docking Station — APSS".

- ✅ **battery_node.py v2.0:** Coulomb counting come metodo SoC primario
  (INA219 hawk misura tensione regolata DD32AJ4B ~12.10V stabili, non
  tensione batteria reale). SOC_INITIAL=0.85, BATTERY_CAPACITY=8Ah.
  serial_number='ECO-LFPYZ1208', design_capacity=8.0, LIPO technology.
  Log con tag [coulomb]. Deployato su hawk, build OK.

- ✅ **Documentazione aggiornata:** architecture.md v2.1 (sezione INA219
  robot con nota DD32AJ4B, docking definitivo con dati ciclo reali),
  CHANGELOG v2.1.0, doc_firmware.md creato in docs/,
  APSS_Documentazione_Tecnica_v2_4.docx generata (NON toccare v2.3).

- ✅ **Script generazione docx:** gen_doc_apss.mjs (858 righe, Node.js)
  salvato in D:\_claudecodeproject\APSS\docs\scripts\. Per aggiornare
  la doc tecnica: delegare SEMPRE a Claude Code (zero token in chat).
  Setup: npm install docx. Run: node gen_doc_apss.mjs.

- ✅ **Skill allinea-apss v1.1:** Step 3 aggiornato — docx NON si genera
  in chat (costa 70%+ token Pro), si delega a Claude Code con prompt
  mirato a gen_doc_apss.mjs.

- ✅ **apss-oled.service:** installato, enabled, funzionante al boot su
  hawk (Main PID operativo). Package udemy_ros2_pkg rinominato
  apss_ros2_pkg. Build pulita, 7 packages finished.

### Aggiornamento architettura ROS importante

1. safety_node.py — orchestratore sensori
    - Subscriber: /battery (BatteryState), futuri /tof/front|left|right, encoder fault, ecc.
Logica soglie: confronta valori con soglie configurate
Publisher: /apss/alarm (std_msgs/String) quando una soglia è superata
2. alarm_node.py — dispatcher allarmi
    -Subscriber: /apss/alarm
Azioni: beeper Yahboom, messaggio OLED, futuri: notifica Android, log, ecc.
Nessuna logica di soglia — solo reazione agli allarmi ricevuti

Separazione di responsabilità pulita: safety_node sa cosa sta succedendo, alarm_node sa come reagire.
Aggiungere un nuovo sensore tocca solo safety_node; aggiungere un nuovo tipo di allarme tocca solo alarm_node.

### Thread aperti (prossima sessione)

1. **alarm_node.py** — nodo allarmi batteria: segnale acustico beeper
   Yahboom + messaggio OLED a due soglie:
   - 🟡 LOW: 11.50V INA219 (~30% SoC) — "completa task, rientra"
   - 🟠 CRITICAL: 11.20V INA219 (~15% SoC) — "rientra subito + beeper"
   Publisher /apss/alarm (std_msgs/String). Subscriber /battery.

2. **Brainstorming obstacle avoidance TOF** (no codice) — 3x VL53L1X
   (frontale CH2, sx CH3, dx CH4), soglie 50cm/40cm già definite.
   Valutare architettura tof_node + avoidance_node + /cmd_vel subscriber
   in rosmaster_main.py.

3. **Fase D batteria — pendenti:**
   - battery_node.py: soglie START/STOP in config.json ESP32 da rivedere
     dopo ciclo completo con dati empirici LiFePO4
   - Microswitch meccanico su dochking (ora fissato
     con scotch in posizione aperta) che sostituisce reed switch
   - Firmware v2.2 roadmap: relay_chiudi/apri devono loggare V/A/W
     INA219 al momento esatto di avvio/stop ricarica

4. **RPLIDAR A1M8:** in reso (linea TX morta). Sostituto in arrivo.
   Quando arriva: test Python protocollo + lancio driver ROS2.

5. **ros-humble-slam-toolbox:** da reinstallare su hawk (perso post
   restore SD) — obbligatorio prima della prima sessione SLAM.

### Note operative importanti

- XHM603 scatta al **superamento**: STOP=14.4V → effettivo a 14.5V
- Misurare terminali batteria IN ricarica fa scattare relay → riarmare da webapp http://192.168.1.193
- INA219 hawk misura tensione DOPO DD32AJ4B (~12.10V stabili) — NON la tensione reale della batteria ECO-WORTHY
- NON generare docx in chat Claude — sempre Claude Code su gen_doc_apss.mjs
- Patch Rosmaster_Lib.py riga 20 (/dev/yahboom) da riapplicare se la libreria viene reinstallata via apt/pip

---

## Completati in questa sessione 23/05/2026

- ✅ Bug video MainScreen risolto: TCP server bind `0.0.0.0` invece di IP specifico
- ✅ App Android funzionante su S23 Ultra: connessione, video, CameraScreen, cambio schermata
- ✅ `filetype` aggiunto ai requirements buildozer — crash Android risolto
- ✅ `camera_screen.py`: salvataggio foto/video in `/sdcard/DCIM/APSSystem/` visibile in galleria
- ✅ Popup conferma foto + popup Salva/Annulla/Rinomina video con notifica MediaStore
- ✅ Icona app personalizzata `icon.png` configurata in `buildozer.spec`
- ✅ `static_img/` aggiunta al repo APSS (logo black/white + sorgenti)
- ✅ `buildozer.spec` e `.gitignore` aggiornati e nel repo
- ✅ Verifica I2C post-scarica statica: tutti i sensori OK

### Hardware robot

- RPLIDAR A1M8: **in reso** (linea TX morta). Sostituto in arrivo.
- TOF400C VL53L1X: tutti e 3 verificati OK post-scarica statica (CH2/CH3/CH4 → 0x29) ✅
- INA219 0x40: operativo ✅
- OLED SSD1306: funzionante via `apss-oled.service` al boot ✅
- TCA9548A 0x70: operativo ✅

### Stack ROS2

| Nodo | Comando | Stato |
|------|---------|-------|
| `oled_node` | `ros2 run apss_ros2_pkg oled_node.py` | ✅ funzionante + service boot |
| `battery_node` | `ros2 run apss_ros2_pkg battery_node.py` | ✅ funzionante |
| `safety_node` | `ros2 run apss_ros2_pkg safety_node.py` | 🔲 pianificato |

### App Android

- APK `apssystem-2.1` — testato e funzionante su S23 Ultra ✅
- Salvataggio: `/sdcard/DCIM/APSSystem/` (foto `.jpg`, video cartella frame)
- Icona personalizzata APSS configurata
- Bug connessione risolto (TCP bind `0.0.0.0`)

### Soglie ricarica (Fase 1 — voltage based)

| Livello | Tensione | SoC stimato | Azione |
|---------|----------|-------------|--------|
| 🟡 LOW | 11.50V | ~30% | Completa task, rientra |
| 🟠 CRITICAL | 11.20V | ~15% | Interrompe task, rientra — trigger SOS beeper |
| 🔴 EMERGENCY | 10.80V | ~5% | Stop ovunque, attende recupero |

### Prossimi step (in ordine)

1. Reinstallare `ros-humble-slam-toolbox` su hawk
2. `battery_node` + `oled_node` nel launch file + test integrato (asterisco scompare)
3. Verifica pacchetti pip post-restore SD
4. Test RPLIDAR sostituto al ricevimento
5. Progettazione e implementazione `safety_node.py`
6. `tof_node.py` + `avoidance_node.py` + subscriber `/cmd_vel`
7. Fase D batteria LiFePO4 (fusibile T3A, CC 2A, soglie XHM603)

### Pending items

| Item | Priorità | Note |
|------|----------|------|
| ⚠️ RPLIDAR A1M8 in reso | Alta | Sostituto in arrivo |
| Reinstallare `ros-humble-slam-toolbox` | Alta | Pre-SLAM obbligatorio |
| Test asterisco OLED scompare con battery_node | Media | `battery_node` nel launch file |
| Verificare pacchetti pip post-restore | Media | `adafruit-circuitpython-*`, `picamera2`, ecc. |
| Fase D batteria | Media | Fusibile T3A, CC 2A, soglie XHM603 |
| Bug `[ODOM] publisher's context is invalid` | Bassa | Cosmetico, non bloccante |
| Log rumore `Camera Init Error!` | Bassa | Handler legacy Yahboom, non funzionale |
