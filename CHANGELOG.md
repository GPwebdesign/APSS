# CHANGELOG — rosmaster_project

---

## [v2.2.0] — 2026-06-06

### Added
- `test_files/discharge_logger.py`: logger INA219 standalone per caratterizzazione scarica LiFePO4. CSV append con campionamento adattivo (>11.5V=300s, 11.2–11.5V=60s, <11.2V=10s), marker RESTART/STOP, prompt misura morsetti all'avvio.
- `test_files/morsetti_logger.py`: one-shot logger misure manuali al tester in note_morsetti.csv. Correlabile per timestamp con discharge_*.csv per calcolo offset V_ina vs V_reale.
- `test_files/discharge_20260528_2137.csv`: dati ciclo scarica completo 28/05–04/06/2026 (273 campioni). Curva LiFePO4 documentata: plateau ~11.84V → ginocchio ~10.0V V_ina.
- `test_files/note_morsetti.csv`: misure manuali ai morsetti batteria correlate al ciclo di scarica. Offset INA219 hawk vs terminali reali: +1.5V medio.

### Changed
- Nessuna modifica al codice principale in questa sessione.

---

## [v2.1.0] — 2026-05-24

### Batteria — sostituzione YTZ10S → ECO-WORTHY LiFePO4

- Sostituita batteria Yuasa YTZ10S AGM 12V 8.6Ah con **ECO-WORTHY LiFePO4 12.8V 8Ah** (ECO-LFPYZ1208, ASIN B0CCJ8JJV3)
- Dimensioni fisiche: 152×65×96mm — terminali F2 — peso 1.05kg (-2.15kg rispetto a YTZ10S)
- Batteria installata nel robot, cablaggio T-plug con interruttore sul positivo

### Circuito di ricarica docking — ricalibrazione LiFePO4

- **XL4016** ricalibrato: CV 14.82V → **14.40V**, CC 0.9A → **1.5A**
  - 2A generava spike alla chiusura relay che facevano scattare erroneamente XHM603 — 1.5A è il valore ottimale verificato sperimentalmente
- **Fusibile** sostituito: T1.5A slow-blow → **T3.15A slow-blow** 250V
- **XHM603** soglie aggiornate per LiFePO4: STOP **14.4V** display (scatta a 14.5V) / START **13.1V** display
  - Soglia STOP confermata corretta: OCV stabile post-carica = 13.40V (~95% SoC) — non modificare
  - Comportamento verificato: XHM603 scatta al **superamento** del valore impostato (14.4V → effettivo 14.5V)
- Offset catena misurati fisicamente: display XHM603 vs terminali = +0.70V, INA219 docking vs terminali = +0.34V

### Firmware ESP32 docking — v2.1

- **Fix 1 — Debounce IRQ reed/microswitch (GPIO18):** debounce software 2000ms via `utime.ticks_diff()` — spike dalla chiusura relay XHM603 non provocano più apertura erronea del relay ESP32
- **Fix 2 — Relay automatico:** logica nel loop principale ogni 2s — relay si chiude automaticamente se switch=1 e rete presente, senza intervento manuale da webapp
- **Fix 3 — Watchdog CAL INA219:** in `leggi_sensori()` — se V>12V e A=0 reinizializza automaticamente registro CAL azzerato da reset a caldo ESP32
- **Fix 4 — config.json aggiornato:** `max_expected_amps` 3.0→2.0, `tensione_min_v` 11.5→12.5, `tensione_max_v` 15.0→14.7, aggiunta sezione `ricarica` con valori START/STOP di riferimento
- **Branding:** dashboard `http://192.168.1.193` aggiornata da "Docking Station — Rosmaster R2" a "Docking Station — APSS"
- Reed switch sostituito con **microswitch meccanico NC** (comportamento reed erratico verificato) — attualmente fissato aperto → GPIO18 pull-up = 1 costante → relay chiude automaticamente al boot con rete presente
- Documentazione firmware: `docs/doc_firmware.md` aggiunto al repo APSS

### battery_node.py — v2.0 (LiFePO4)

- Aggiornato per batteria ECO-WORTHY LiFePO4 12.8V 8Ah (ECO-LFPYZ1208)
- `design_capacity`: 8.6 → **8.0** Ah
- `serial_number`: 'YTZ10S' → **'ECO-LFPYZ1208'**
- `power_supply_technology`: UNKNOWN → **LIPO** (enum ROS2 più vicino a LiFePO4)
- **Metodo SoC:** rimosso calcolo da tensione (INA219 hawk misura tensione regolata DD32AJ4B ~12.10V stabili, non la tensione reale della batteria) — introdotto **coulomb counting** come metodo primario
  - `SOC_INITIAL = 0.85` — SoC assunto al boot
  - `BATTERY_CAPACITY_AH = 8.0` → `BATTERY_CAPACITY_C = 28800.0` C
  - Reset SoC a 100% quando corrente scende sotto 0.05A durante ricarica (fine fase CV)
- **Tabella SoC LiFePO4** (`VOLTAGE_TABLE_LIFEPO4`) mantenuta come riferimento futuro — non usata attivamente per stima SoC
- Log aggiornato con tag `[coulomb]` per identificare il metodo di stima attivo

### Documentazione

- `docs/architecture.md` aggiornato:
  - Sezione INA219 robot: aggiunta nota architetturale critica su posizione dopo DD32AJ4B e inutilizzabilità stima SoC da tensione
  - Sezione Stack ROS2: aggiunta tabella dettagliata battery_node.py v2.0
  - Sezione Hardware docking station: completamente riscritta con dati reali misurati (parametri XL4016/XHM603 definitivi, tabella offset catena, dati ciclo completo, INA219 docking HW-831B, firmware v2.1 fix table e roadmap v2.2)
  - Stack tecnologico: firmware docking aggiornato a v2.1
- `docs/doc_firmware.md` aggiunto — documentazione completa firmware ESP32 docking v2.1: architettura, sequenza avvio, tutti i file, stato globale, catena potenza con offset misurati, fix applicati, note operative, roadmap

---

## [v0.20.0] — 2026-04-25

### Aggiunto
- Arducam OV5647 IR-cut motorizzato installato e testato
- IR-cut funzionante: commutazione automatica giorno/notte verificata
- test_camera_still.py: scatta foto in modalità still per calibrazione
- camera_params.json aggiornato per nuova camera IR-cut:
  - profilo streaming: ColourGains(1.3,1.4) Sharp=2.0 Cont=1.1 Sat=0.8
  - profilo vision: Sharp=3.0 Cont=1.1 Sat=0.3 per OpenCV

### Note
- Foto still: colori eccellenti con ColourGains(0.9,1.1) Sharp=3.0
- Stream video: colori accettabili — limitazione pipeline ISP OV5647
- Fuoco fisso ottimale fino a 1.5m

### Known Issues / TODO
- Foto dall'app salvate da frame MJPEG stream — colori pipeline video
- TODO: aggiungere endpoint /capture_still in rosmaster_main.py
  per foto in modalità still con colori eccellenti

---

## [v0.19.0] — 2026-04-25

### Modificato
- Ruote Mecanum rimontate in configurazione X corretta (rulli formano X vista dall'alto)
- Motori e cablaggi invariati — polarità M1/M4 invertita fisicamente resta valida

### Testato e concluso
- Strafe laterale puro non ottenibile: né su tappeto né su parquet
- Problema fisico: attrito roller + peso robot impedisce scivolamento laterale
- Decisione: strafe_left/right mantenuti come rotazione stretta con perno ant.
- test_motor_calibration.py aggiornato con tasti 6/7/8/9 per test cinematica

### Prossimi step
- Riprendere calibrazione camera Arducam IR-cut (profilo vision)
- Riprendere mappatura Studio con procedura 5 fasi

---

## [v0.18.0] — 2026-04-21

### Modificato
- speed base aumentato da 50 a 55 per compensare depotenziamento M1 (m1=0.60)
- `send_motion()` e `_mecanum()` aggiornati con speed=55 come default
- Slider velocità 0.5-1.0 ora funzionante correttamente con speed=55

---

## [v0.17.0] — 2026-04-21

### Aggiunto
- motor_calibration.json — file JSON per calibrazione motori sul Pi
- Calibrazione applicata in rosmaster_main.py (non nell'app Kivy)
- test_encoder_calibration.py — misura delta encoder per calcolo fattori
- test_motor_calibration.py — test singoli motori e deriva

### Corretto
- Deriva avanti destra risolta: m1=0.60 — deriva ±1cm su 160cm
- Architettura calibrazione corretta: configurazione sul Pi, app stateless
- Rimossa calibrazione da tcp_client.py (incompatibile con Android)

### Note tecniche
- M1 (ant.sx) fisicamente più veloce degli altri — fattore 0.60
- Calibrazione ricaricata ad ogni comando da rosmaster_main.py
- motor_calibration.json modificabile sul Pi senza ricompilare l'app

---

## [v0.16.0] — 2026-04-20

### Aggiunto
- CameraScreen: pulsante foto — salva JPG con timestamp in rosmaster_kivy/save/
- CameraScreen: pulsante record — salva sequenza JPG in save/video_timestamp/frame_XXXX.jpg
- Script offline rosmaster_kivy/tools/frames_to_mp4.py per assemblaggio MP4 da sequenza JPG
- Cartella rosmaster_kivy/save/ creata automaticamente dall'app

### Corretto
- Fix stream video MainScreen: on_enter() avvia stream se TCP già connesso
- Slider velocità 0.5-1.0 applicato correttamente a forward/backward
- Rotate left/right: speed_factor=0.8 fisso
- Strafe left/right: speed_factor=0.9 fisso
- on_btn_*_press() ora passa attraverso send_motion() con speed_factor

### Note tecniche
- Foto salvate dal frame JPG grezzo dello stream (no flip Kivy)
- Video come sequenza JPG: cross-platform Linux e Android
- Assemblaggio MP4 offline con OpenCV via frames_to_mp4.py

---

## [v0.15.0] — 2026-04-19

### Aggiunto
- Cartella maps/ nel repository ros2_py_ws per versionamento mappe
- Documento step_mappatura.md con istruzioni complete per:
  - Avvio stack mappatura
  - Tecnica corretta di mappatura stanza per stanza
  - Salvataggio mappa con slam_toolbox service
  - Ripresa mappatura da sessione precedente
  - Checklist pre-mappatura
  - Naming convention mappe (apss_map_v1, v2, finale)

### Note
- Mappe salvate in ~/Workspaces/ros2_py_ws/maps/
- Prima mappatura da eseguire con robot a terra
- Mappa sul banco acquisita oggi da scartare

---

## [v0.14.0] — 2026-04-19

### Aggiunto
- oled_node.py: display OLED SSD1306 128x64 I2C operativo
  - APSS centrato con font large, linea separatore, IP centrato
  - Subscriber /apss/mode, /apss/battery, /apss/sensors/env
- URDF robot APSS: apss_robot.urdf.xml
  - Frame: base_footprint → base_link → laser (z=0.33m, offset 90°) + camera_link (x=0.16m, z=0.20m)
- Launch file apss_lidar.launch.py unificato:
  - RPLIDAR A1M8 + robot_state_publisher + tf statici + slam_toolbox + RViz2
- Configurazione RViz2 salvata: rviz/apss.rviz (Map + LaserScan + TF)
- slam_toolbox installato e operativo in modalita mapping

### Verificato
- tf tree completo: map → odom → base_footprint → base_link → laser/camera_link ✅
- slam_toolbox attivo con CeresSolver ✅
- RViz2 si apre automaticamente dal launch file con config APSS ✅

### Prossimi step
- Mappatura appartamento con teleoperazione manuale
- Salvataggio mappa apss_map.pgm + apss_map.yaml

---

## [v0.13.0] — 2026-04-19

### Aggiunto
- URDF robot APSS: apss_robot.urdf.xml con frame base_footprint, base_link, laser (z=0.33m, offset 90°), camera_link (x=0.16m, z=0.20m)
- Launch file apss_lidar.launch.py: avvia RPLIDAR + robot_state_publisher + tf statici map→odom→base_footprint in un solo comando
- tf tree completo verificato: map → odom → base_footprint → base_link → laser/camera_link

### Verificato
- Launch file avviato senza warning ✅
- tf tree completo e corretto ✅
- RPLIDAR attivo a 10Hz su /scan ✅

### Prossimi step
- slam_toolbox per mappatura appartamento

---

## [v0.12.0] — 2026-04-19

### Aggiunto
- Display OLED SSD1306 128x64 I2C integrato su Raspberry Pi (indirizzo 0x3C)
- oled_node.py — nodo ROS2 che mostra su display:
  - IP robot + nome APSS
  - Stato batteria (tensione + percentuale) via /apss/battery
  - Modalita operativa via /apss/mode
  - Sensori ambientali (temperatura, umidita) via /apss/sensors/env
- test_oled.py in test_files — test standalone display
- luma.oled installato su hawk

### Verificato
- Display OLED operativo a 0x3C ✅
- Aggiornamento display 2Hz ✅
- Subscriber /apss/mode e /apss/battery testati ✅

---

## [v0.10.0] — 2026-04-18

### Aggiunto
- RPLIDAR A1M8 integrato fisicamente su hawk (/dev/ttyUSB1)
- Test standalone Python con libreria rplidar-roboticia: info, health, scansione verificati
- Visualizzazione matplotlib polar plot in tempo reale (test_files/test_rplidar_viz.py)
  - Offset 90° compensato: fronte robot allineato a Nord nel plot
  - Colori RdYlGn: rosso=vicino, verde=lontano, range max 4m
- Driver ROS2 ros-humble-rplidar-ros v2.1.4 installato e messo in hold
- Topic /scan attivo e verificato: ~7.7 Hz, range 0.15-12m, copertura 360°
- Visualizzazione RViz2 con dati reali verificata

### Note tecniche
- LiDAR montato sul piano superiore del robot, visuale libera a 360°
- Offset fisico 90°: il fronte robot corrisponde a 90° nel sistema di riferimento LiDAR
- ttyUSB0 = scheda Yahboom, ttyUSB1 = RPLIDAR (ordine fisso verificato)
- tf tree incompleto (warning RViz2 atteso): verrà risolto con URDF nella fase successiva

### Prossimi step
- URDF robot con trasformazione base_link → laser (offset 90°)
- Launch file APSS unificato
- Integrazione slam_toolbox

---

## [v0.9.0] — 2026-04-16

### Modificato
- Documentazione tecnica v1.9: piattaforma mobile descritta come struttura proprietaria GPwebdesign
- Aggiunto RPLIDAR A1M8 Slamtec in sezione 4.1 componenti hardware
- Aggiunta sezione 10.1 sviluppo futuro: architettura hardware indipendente da Yahboom
  (ESP32 + driver motori L298N + PCA9685 come sostituto open hardware della scheda Yahboom)

---

## [v0.8.0] — 2026-04-16

### Modificato
- Obiettivi di progetto aggiornati alla versione definitiva:
  - Aggiunto RPLIDAR A1M8 come tecnologia primaria per obstacle avoidance
  - Aggiunto sistema sensori ambientali: DHT-11 (disponibile), microfono USB, gas MQ+ADS1115 (futuri)
  - Rilevamento fiamma/fumo via OpenCV invece di sensore hardware HW-072
  - Architettura sensori scalabile via MQTT per nodi fissi futuri
- Documentazione tecnica rinominata APSS_Documentazione_Tecnica_v1.8.docx

---

## [v0.7.0] — 2026-04-16

### Modificato
- Progetto rinominato: da "Rosmaster" ad APSS (Autonomous Patrol and Surveillance System)
- App Kivy: titolo finestra aggiornato a "Autonomous Patrol and Surveillance System"
- App Kivy: toolbar MainScreen aggiornata da "Rosmaster R2" a "APSSystem"
- App Kivy: toolbar CameraScreen aggiornata a "APSS — Camera Pan/Tilt"
- Fix: invertiti pulsanti pan sinistra/destra — direzione verificata fisicamente

### Note
- L'hardware sottostante rimane Yahboom Rosmaster R2
- APSS e il nome del sistema autonomo sviluppato su questa piattaforma
- Tutta la documentazione futura usera il nome APSS

---

## [v0.6.0] — 2026-04-16

### Aggiunto
- CameraScreen — schermata dedicata camera con stream video MJPEG e controllo pan/tilt
- camera_screen.py: stream MJPEG, controllo pan/tilt, labels angolo corrente
- send_servo(id, angle), send_pan(angle), send_tilt(angle) in tcp_client.py — cmd 0x11
- Pulsante camera nella toolbar MainScreen per navigare a CameraScreen
- Ritorno home graduale pan/tilt — 5°/step ogni 0.05s in thread separato

### Verificato
- Pan/tilt funzionante via app Kivy ✅
- Stream video attivo anche in CameraScreen ✅
- Movimento home graduale ✅

### Note tecniche
- S1=Tilt (servo_id=1), S2=Pan (servo_id=2) — swap fisico confermato
- Angolo range 0-180° con clamp software
- STEP=5° per pressione singola pulsante

---

## [v0.5.0] — 2026-04-16

### Aggiunto
- Stream video MJPEG funzionante in app Kivy — 31 FPS via WiFi
- Metodo on_robot_connected in main_screen.py — stream avviato solo dopo connessione TCP confermata e send_init
- Test locale flusso video: test_video_local.py — acquisisce frame OV5647 e mostra finestra OpenCV

### Corretto
- STREAM_URL aggiornato a http://192.168.1.158:6500/video_feed (mancava /video_feed)
- cmd.upper() in parse_data di rosmaster_main.py — fix case sensitivity che impediva cmd 0F di essere riconosciuto
- send_init corretto a $020f040116# (func=1=Standard) — imposta g_mode=Standard necessario per avviare lo stream
- IP default aggiornato a 192.168.1.158 in main.py, tcp_client.py, main_screen.py

### Verificato
- Stream video 31 FPS su app Kivy via WiFi ✅
- Controllo motori funzionante con stream video attivo ✅

---

## [2026-04-07] — Configurazione hold aggiornamenti sistema

### hawk (RPi) e gp68-vmware

- Kernel messo in hold (RPi: 5.15.0-1093-raspi, VM: 6.8.0-106-generic)
- Rimossi kernel vecchi (RPi: 1077, VM: 6.8.0-40)
- unattended-upgrades disabilitato su entrambi
- APT pinning kernel attivo (`/etc/apt/preferences.d/no-kernel-upgrade`)
- ROS2 Humble aggiornato e allineato a 16.0.19 su entrambi i sistemi
- Hold massivo su tutti i pacchetti ros-humble-*, gstreamer, colcon, librerie sistema
- TODO: ripristinare hold ROS2 quando necessario con:

  ```bash
  dpkg -l | grep "^ii  ros-humble-" | awk '{print $2}' | xargs sudo apt-mark unhold
  ```

---

## [v0.4.0] — 2026-04-06

### Aggiunto

- **App Kivy/KivyMD multiscreen** — struttura completa con 5 schermate:
  - `MainScreen` — controllo robot + stream video MJPEG
  - `PatrolScreen` — placeholder per Fase 5 (pattugliamento autonomo)
  - `AlertScreen` — placeholder per Fase 6 (rilevamento intrusi)
  - `SettingsScreen` — configurazione IP robot e porte TCP/stream
  - `StatusScreen` — placeholder per Fase 7 (stato sistema e batteria)
- **TCPClient** (`network/tcp_client.py`) — client TCP thread-safe con:
  - Connessione asincrona con callback `on_connected` / `on_disconnected`
  - Comando di inizializzazione `send_init()` — imposta car_type=2 MecanumWheel
  - Cinematica Mecanum custom calcolata in Python (`_mecanum()`)
  - Metodi: `send_forward`, `send_backward`, `send_stop`,
    `send_rotate_left`, `send_rotate_right`,
    `send_strafe_left`, `send_strafe_right`
- **Cinematica Mecanum custom** — bypass di `set_car_motion` tramite cmd TCP `0x1A`:
  - Calcolo velocità M1/M2/M3/M4 in Python con segni verificati fisicamente
  - Formula: `m1=vx-vy+vz`, `m2=vx+vy-vz`, `m3=vx+vy+vz`, `m4=vx-vy-vz`
- **Blocco `elif cmd in ("1A", "1a")`** aggiunto in `parse_data()` di `rosmaster_main.py`:
  - Riceve 4 velocità motore via TCP e chiama direttamente `g_bot.set_motor()`
- **Pad di controllo 3x3** — layout con icone Material Design centrate:
  - Riga 1: curva sinistra | avanti | curva destra
  - Riga 2: rotazione sinistra | stop | rotazione destra
  - Riga 3: vuoto | indietro | vuoto
  - Implementato con `BoxLayout` + `canvas.before` + `AnchorLayout` + `MDIcon`

### Modificato

- **Mappatura motori M1/M4** — invertita polarità fisica dei cavi su scheda espansione:
  - M1 (anteriore sinistro) e M4 (posteriore destro) avevano polarità invertita
  - Soluzione: scambio fisico dei fili M+/M- sui connettori M1 e M4
- **`rosmaster_main.py`** — aggiunto supporto cmd `0x1A` in `parse_data()`
- **Tema app** — KivyMD dark theme, primary Blue, accent Teal
- **Orientamento** — portrait, ottimizzato per smartphone

### Verificato fisicamente

- Tutti e 4 i motori girano in avanti con `set_motor(+50, +50, +50, +50)` ✅
- Avanti/indietro corretti ✅
- Rotazione sinistra/destra corrette ✅
- Curve sinistra/destra (avanzamento curvilineo) corrette ✅

### Struttura file aggiunta

```text
rosmaster_kivy/
├── main.py
├── rosmaster.kv
├── network/
│   ├── __init__.py
│   └── tcp_client.py
├── screens/
│   ├── __init__.py
│   ├── main_screen.py
│   ├── patrol_screen.py
│   ├── alert_screen.py
│   ├── settings_screen.py
│   └── status_screen.py
└── assets/
    └── icons/
        └── no_signal.png
```

### Problemi noti

- Stream video MJPEG non testato (camera CSI non collegata durante sviluppo)
- Strafe laterale puro non disponibile — le ruote Mecanum hanno orientamento
  rulli incompatibile con il firmware STM32 per traslazione pura
- I pulsanti strafe eseguono curve con `vx=0.6, vz=±0.4`
- Velocità motori da affinare (attualmente speed=50 fisso)

---

## [v0.3.0] — 2026-03-XX

### Aggiunto

- Stream video CSI OV5647 su porta 6500 con app Yahboom
- Integrazione camera CSI in `rosmaster_main.py` con `TYPE_CSI_CAMERA = 0x53`
- Nodo ROS2 `camera_publisher.py` — pubblica `/image_raw` a 30 FPS

### Modificato

- `Rosmaster_Camera` — aggiunto `TYPE_CSI_CAMERA = 0x53`
- Import `picamera2` spostato dentro `__init_csi_camera()` per compatibilità cross-platform

---

## [v0.2.0] — 2026-03-XX

### Aggiunto

- Configurazione due repository Git separati (`ros2_py_ws` e `rosmaster_project`)
- Ambiente di sviluppo VM Ubuntu 22.04 + VSCode
- Workflow Git: sviluppo VM → push → pull RPi → test

---

## [v0.1.0] — 2026-03-XX

### Aggiunto

- Prima emissione — struttura base `rosmaster_project`
- `rosmaster_main.py` — server TCP + Flask + controllo motori
- Integrazione Rosmaster-Lib 3.3.9
- Mappatura motori Mecanum: M1=ant.sx, M2=ant.dx, M3=post.sx, M4=post.dx
