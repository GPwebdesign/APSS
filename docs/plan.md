# APSS — Piano di Sviluppo

> Aggiornato: Maggio 2026 — v2.5  
> Spunta le checkbox man mano che completi ogni task.

---

## ✅ COMPLETATO

### Infrastruttura base
- [x] Progettazione architettura sistema
- [x] Circuito ricarica XL4016 + XHM603 calibrato e verificato
- [x] Firmware ESP32 MicroPython v2.0 — dashboard operativa
- [x] RPLIDAR A1M8 — driver installato, topic `/scan` attivo ~7.7Hz
- [x] URDF robot (`apss_robot.urdf.xml`) + TF tree completo
- [x] Launch file `apss_lidar.launch.py` — RPLIDAR + slam_toolbox + RViz2
- [x] Odometria encoder in `rosmaster_main.py` (`thread_odom`) — ENCODER_CPR=822
- [x] OLED SSD1306 operativo (`oled_node.py`)

### App Kivy
- [x] Controllo motori Mecanum custom (formula verificata fisicamente)
- [x] Stream video MJPEG 31 FPS a 640x480 — colori RGB corretti
- [x] Controllo pan/tilt via cmd `0x11` nativo Yahboom — movimento graduale home
- [x] Fix cmd.upper() in parse_data() — comandi case-sensitive
- [x] Calibrazione M1: `motor_calibration.json` → `m1=0.60`
- [x] Endpoint `/capture_still` — foto JPEG qualità 95 scaricabile su client

### Hardware verificato
- [x] Polarità M1/M4 invertita fisicamente (fili M+/M- scambiati)
- [x] Pan home=100°, Tilt home=85° — salvati in `pan_tilt_presets.json`
- [x] Package hold ROS2 — hawk e gp68-vmware (~290 pkg)

### Pulizia codebase (Maggio 2026)
- [x] Rimosso obstacle avoidance OpenCV da `rosmaster_main.py` — eliminati `thread_image_publisher`, `publish_image_frame`, `RosImage`, `g_image_pub`, `g_ros_node`
- [x] Semplificato `camera_params.json` — solo profilo streaming (vision rimosso)
- [x] Fix pipeline colore camera — RGB nativo picamera2, nessuna conversione intermedia
- [x] `camera_rosmaster.py` — `__load_streaming_params()` sostituisce `__load_vision_params()`
- [x] `test_camera_calibrate.py` — rimosso profilo vision, solo streaming

### Hardware sensori (Maggio 2026)
- [x] INA219 installato in serie al positivo — indirizzo 0x40, shunt R100
- [x] 3x TOF400C VL53L1X installati — frontale CH2, sinistro CH3, destro CH4
- [x] TCA9548A multiplexer I2C installato — indirizzo 0x70
- [x] CH2 e CH3 verificati OK — 0x29 su entrambi i canali
- [x] Fix TOF destro CH4 — sensore originale difettoso sostituito con scorta — tutti e 3 OK

### Monitor batteria ROS2 (Maggio 2026)
- [x] `battery_node.py` — legge INA219, pubblica `/battery` (BatteryState) ogni 2s
- [x] `BatteryStats.msg` custom — min/max V/I/P + sample_count
- [x] `/battery/stats` topic operativo — accumula statistiche da avvio nodo
- [x] Logica status corretta: corrente positiva=DISCHARGING, negativa=CHARGING
- [x] Tabella SoC AGM 12V integrata (12.70V=100% ... 11.50V=0%)
- [x] Test assorbimento reale (89 campioni): idle 0.63A/7.7W, picco 2.14A/25.7W
- [x] `oled_node.py` — aggiunto subscriber `/battery` (BatteryState) — allineato con battery_node ✅
- [ ] Aggiornare tabella SoC → LiFePO4 (plateau ~13.1-13.2V) in battery_node.py
- [ ] Aggiornare soglie START/STOP in ESP32 config.json per LiFePO4

### Batteria LiFePO4 (Maggio 2026)
- [x] ECO-WORTHY 12V 8Ah LiFePO4 (B0CCJ8JJV3) acquistata — 50€ Amazon.it
- [x] XL4016 ricalibrato: CV 14.82V → 14.40V — CC 0.9A confermata
- [x] XHM603 soglie conservative: STOP=14.2V / START=13.1V display
- [x] Prima ricarica parziale completata — OCV post-carica 13.27V (~85-90% SoC)
- [ ] Sostituire fusibile T1.5A → T3A slow-blow (per alzare CC a 2A)
- [ ] Ricalibrazione CC a 2A con monitoraggio temperatura
- [ ] Verificare soglie XHM603 definitive dopo ciclo completo
- [ ] Installazione fisica ECO-WORTHY nel robot
- [ ] Test ciclo carica/scarica completo con robot agganciato

### NotebookLM (Maggio 2026)
- [x] Notebook APSS creato — ID bc8dfeee-c3f0-412d-aa88-f8e0a4025fa5
- [x] 9 fonti caricate — sistema doppio labeling area+stato
- [x] Skill `apss-notebooklm-sync` creata in `.claude/skills/`
- [x] Firmware ESP32 docking aggiunto al repo (`docking/Esp32firmware/`)
- [x] `.gitignore` popolato

### Boot e servizi systemd (Maggio 2026)
- [x] `apss_lidar_standby.py` — script presente (CMD_STOP + CMD_MOTOR RPLIDAR)
- [~] `apss-lidar-standby.service` — file unit creato ma `disabled`, mai effettivamente eseguito al boot
- [x] Utente `hawk` aggiunto al gruppo `dialout`
- [ ] Fix RPLIDAR standby — il service non ha mai fermato il motore (topic aperto, deprioritizzato dopo fix USB)

### Fix USB enumeration non deterministica (Maggio 2026)
- [x] Diagnosi: ordine `ttyUSB0/ttyUSB1` non deterministico al boot — Yahboom (CH340) e RPLIDAR (CP2102) competono per `ttyUSB0`
- [x] Sintomo: quando RPLIDAR prende `ttyUSB0`, `rosmaster_main.py` apre il dispositivo sbagliato → `Version: -1`, beep silenziosi, motore RPLIDAR fermo (side-effect DTR su CP2102)
- [x] Regole udev `/etc/udev/rules.d/99-apss-usb.rules` — symlink stabili `/dev/yahboom` (CH340 1a86:7523) e `/dev/rplidar` (CP2102 10c4:ea60)
- [x] Patch libreria `/usr/lib/python3.10/Rosmaster_Lib/Rosmaster_Lib.py` riga 20 — apre `/dev/yahboom` invece di `/dev/ttyUSB0` hardcoded (backup `.bak-APSS`)
- [x] Launch file `apss_lidar.launch.py` — parametro `serial_port: /dev/rplidar` (backup `.bak-APSS`)
- [x] Test post-reboot verificato: enumeration "invertita" (Yahboom→ttyUSB1, RPLIDAR→ttyUSB0) e `rosmaster_main.py` parte correttamente con `Version: 3.5`
- [ ] ⚠️ Riapplicare patch libreria se `Rosmaster_Lib` viene reinstallata via apt/pip

### App Kivy Android (Maggio 2026)
- [x] VM Buildozer configurata (Ubuntu 24.04, venv-buildozer, Buildozer 1.5.0)
- [x] `buildozer.spec` configurato — API 34, NDK 25b, arm64-v8a + armeabi-v7a
- [x] APK debug 2.1 generato — `apssystem-2.1-arm64-v8a_armeabi-v7a-debug.apk`
- [ ] Test APK su Samsung S23 Ultra

---

## 🔄 IN CORSO / PROSSIMI

### Fase 0 — Integrazione nodi ROS2 base (IN CORSO)
- [ ] Fix RPLIDAR standby al boot (script delay + retry)
- [x] `oled_node.py` — subscriber `/battery` (BatteryState) per dati reali INA219 ✅
- [ ] `battery_node` + `oled_node` aggiunti ad `apss_lidar.launch.py`
- [ ] Test integrato: battery_node → /battery → oled_node → display

### Fase 1 — TOF400C VL53L1X (obstacle avoidance software)
- [x] Fix TOF destro CH4 — sensore sostituito, tutti e 3 verificati OK (0x29)
- [ ] `tof_node.py` — pubblica `sensor_msgs/Range` su `/tof/front`, `/tof/left`, `/tof/right`
- [ ] Canali reali TCA9548A: frontale→CH2, sinistro→CH3, destro→CH4
- [ ] `avoidance_node.py` — soglie 50cm (slow) / 40cm (pivot)
- [ ] `rosmaster_main.py` → subscriber `/cmd_vel` (separazione controllo/movimento)
- [ ] Test fisico obstacle avoidance su percorso chiuso

### Fase 2 — App Kivy Android
- [x] Setup Buildozer su VM dedicata Ubuntu 24.04
- [x] `buildozer.spec` configurato — API 34, NDK 25b
- [x] Build APK debug 2.1 generato
- [ ] Test APK su Samsung S23 Ultra — stream video + motori + pan/tilt + `/capture_still`

### Fase 3 — SLAM mapping
- [ ] Prima sessione di mapping con slam_toolbox
- [ ] Salvataggio mappa appartamento
- [ ] Integrazione mappa nell'app (visualizzazione PatrolScreen)
- [ ] Configurazione `nav2` su mappa salvata

### Fase 4 — Navigazione autonoma (Nav2)
- [ ] Configurazione Nav2 completa (costmap, planner, controller)
- [ ] Bridge node TOF → LaserScan per costmap fusion con RPLIDAR
- [ ] Test navigazione punto-punto senza ostacoli
- [ ] Test navigazione con ostacoli dinamici

### Fase 5 — Pattugliamento autonomo
- [ ] Definizione waypoint pattugliamento in mappa
- [ ] Nodo `patrol_node.py` — gestione ciclo waypoint
- [ ] PatrolScreen app — avvio/stop/stato pattugliamento
- [ ] Integrazione rilevamento movimento (camera)

### Fase 6 — Sorveglianza e alert
- [ ] `flame_detector` OpenCV su OV5647
- [ ] Nodo DHT-11 — topic MQTT `apss/sensors/env`
- [ ] AlertScreen app — log alert + clip video
- [ ] Notifiche push su Android

### Fase 7 — Docking autonomo
- [ ] Integrazione microswitch meccanico (NC, GPIO18) in sostituzione reed switch
- [ ] Marker ArUco sulla docking station
- [ ] Nodo `docking_node.py` — rilevamento ArUco + avvicinamento
- [ ] Test docking fisico completo
- [ ] Integrazione SoC batteria → trigger docking automatico

### Fase 8 — Sensori ambientali aggiuntivi
- [ ] Acquisto microfono USB + MQ-2/MQ-135 + ADS1115
- [ ] `audio_node.py` — MQTT `apss/sensors/audio`
- [ ] `gas_node.py` — MQTT `apss/sensors/gas`
- [ ] StatusScreen app — tutti i sensori in real-time

---

## 🔮 FUTURO (post v2.0)

- [ ] `pan_tilt_node.py` ROS2 con subscriber `/pan_tilt/cmd` (per pattugliamento autonomo)
- [ ] Architettura hardware indipendente: ESP32 + L298N/TB6612FNG + PCA9685 (sostituzione scheda Yahboom)
- [ ] Protocollo ROS2 nativo `/cmd_vel` + `/joint_states` (elimina TCP proprietario)
- [ ] Nodi fissi distribuiti nell'appartamento (ESP32 MQTT)
- [ ] Motion smoother (`MotionSmoother` class) — pausa dopo baseline tests

---

## 📝 Open items / Pending

| Item | Priorità | Note |
|------|----------|------|
| ⚠️ RPLIDAR A1M8 non comunica | Alta | Driver `rplidar_ros` 2.1.4 va in `SL_RESULT_OPERATION_TIMEOUT`. Test Python diretto: 0 bytes. Motore gira ma lidar non risponde al protocollo. Da debugare — ipotesi cavetto interno o firmware zombie |
| Reinstallare `ros-humble-slam-toolbox` su hawk | Media | Mancante post-restore SD — da reinstallare quando lidar funziona |
| Backup su USB disk via SMB | Media | \\iliadbox_Server\iliadbox — utente Rino — cifs-utils da installare su hawk |
| Microswitch docking station | Media | NC, GPIO18, stesso cablaggio reed switch |
| Bug intermittente `[ODOM] publisher's context is invalid` | Bassa | Cosmetico, sparisce su run lunghi — pre-esistente al fix USB |
| Bug Video MainScreen al primo `on_enter` | Bassa | Workaround Home→Camera→Home — pre-esistente, UX minore |
| Log rumore `Camera Init Error!` per `/dev/camera_usb` | Bassa | Handler legacy Yahboom, non funzionale — pre-esistente |
| Ripristino aggiornamenti ROS2 Humble su hawk | Bassa | Dopo hold config completa su entrambi i sistemi |

---

## 🚫 Abbandonato

| Item | Motivo |
|------|--------|
| Strafe laterale puro Mecanum | Non ottenibile anche con ruote in configurazione X — mantenuto come rotazione stretta |
| Obstacle avoidance OpenCV | Sostituito da TOF400C VL53L1X (hardware) — rimosso da codebase in v2.1 |
| Cmd TCP `0x1B` pan/tilt custom | Non necessario — pan/tilt già funzionante via cmd `0x11` nativo Yahboom |
| Profilo camera `vision` | Rimosso in v2.1 — solo profilo streaming necessario |
