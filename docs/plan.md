# APSS — Piano di Sviluppo

> Aggiornato: Maggio 2026 — v2.2  
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
- [ ] Fix cablaggio TOF destro CH4 — blocca bus I2C

### Monitor batteria ROS2 (Maggio 2026)
- [x] `battery_node.py` — legge INA219, pubblica `/battery` (BatteryState) ogni 2s
- [x] `BatteryStats.msg` custom — min/max V/I/P + sample_count
- [x] `/battery/stats` topic operativo — accumula statistiche da avvio nodo
- [x] Logica status corretta: corrente positiva=DISCHARGING, negativa=CHARGING
- [x] Tabella SoC AGM 12V integrata (12.70V=100% ... 11.50V=0%)

### App Kivy Android (Maggio 2026)
- [x] VM Buildozer configurata (Ubuntu 24.04, venv-buildozer, Buildozer 1.5.0)
- [x] `buildozer.spec` configurato — API 34, NDK 25b, arm64-v8a + armeabi-v7a
- [x] APK debug 2.1 generato — `apssystem-2.1-arm64-v8a_armeabi-v7a-debug.apk`
- [ ] Test APK su Samsung S23 Ultra

---

## 🔄 IN CORSO / PROSSIMI

### Fase 1 — TOF400C VL53L1X (obstacle avoidance software)
- [ ] Fix cablaggio TOF destro CH4 (blocca bus I2C)
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
| Backup su USB disk via SMB | Media | \\iliadbox_Server\iliadbox — utente Rino — cifs-utils da installare su hawk |
| Microswitch docking station | Media | NC, GPIO18, stesso cablaggio reed switch |
| Ripristino aggiornamenti ROS2 Humble su hawk | Bassa | Dopo hold config completa su entrambi i sistemi |

---

## 🚫 Abbandonato

| Item | Motivo |
|------|--------|
| Strafe laterale puro Mecanum | Non ottenibile anche con ruote in configurazione X — mantenuto come rotazione stretta |
| Obstacle avoidance OpenCV | Sostituito da TOF400C VL53L1X (hardware) — rimosso da codebase in v2.1 |
| Cmd TCP `0x1B` pan/tilt custom | Non necessario — pan/tilt già funzionante via cmd `0x11` nativo Yahboom |
| Profilo camera `vision` | Rimosso in v2.1 — solo profilo streaming necessario |
