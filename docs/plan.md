# APSS — Piano di Sviluppo

> Aggiornato: Aprile 2026 — v1.9  
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
- [x] Stream video MJPEG 31 FPS a 640x480
- [x] Controllo pan/tilt — movimento graduale home
- [x] Fix cmd.upper() in parse_data() — comandi case-sensitive
- [x] Calibrazione M1: `motor_calibration.json` → `m1=0.60`

### Hardware verificato
- [x] Polarità M1/M4 invertita fisicamente (fili M+/M- scambiati)
- [x] Pan home=100°, Tilt home=95° — salvati in `pan_tilt_presets.json`
- [x] Camera params: profili streaming e vision in `camera_params.json`
- [x] Package hold ROS2 — hawk e gp68-vmware a v16.0.19 (~290 pkg)

---

## 🔄 IN CORSO / PROSSIMI

### Fase 0 — Pulizia codebase (ora)
- [ ] Rimuovere obstacle avoidance OpenCV da `rosmaster_main.py`
- [ ] Semplificare `camera_params.json` — tenere solo profilo streaming
- [ ] Organizzare struttura progetto APSS (questo task)
- [ ] Verificare e correggere `cmd 0x1A` length error (`10 != 12` → usare `0x0C`)

### Fase 1 — TOF400C VL53L1X (obstacle avoidance hardware)
- [ ] Acquisto/ricezione TOF400C VL53L1X ×4 + TCA9548A I2C multiplexer
- [ ] Montaggio meccanico: frontale 0°, sinistra 30°, destra 30°, spare
- [ ] `tof_node.py` — pubblica `sensor_msgs/Range` su `/tof/front`, `/tof/left`, `/tof/right`
- [ ] Multiplexer TCA9548A: TOF1→CH0, TOF2→CH1, TOF3→CH2, TOF4→CH3
- [ ] `avoidance_node.py` — soglie 50cm (slow) / 40cm (pivot)
- [ ] `rosmaster_main.py` → subscriber `/cmd_vel` (separazione controllo/movimento)
- [ ] Test fisico obstacle avoidance su percorso chiuso

### Fase 2 — App Kivy Android
- [ ] Setup Buildozer su gp68-vmware
- [ ] `buildozer.spec` configurato per target Android
- [ ] Build APK — test su dispositivo Android reale
- [ ] Verifica stream video + controllo motori su Android

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

- [ ] Architettura hardware indipendente: ESP32 + L298N/TB6612FNG + PCA9685 (sostituzione scheda Yahboom)
- [ ] Protocollo ROS2 nativo `/cmd_vel` + `/joint_states` (elimina TCP proprietario)
- [ ] Nodi fissi distribuiti nell'appartamento (ESP32 MQTT)
- [ ] Motion smoother (`MotionSmoother` class) — pausa dopo baseline tests

---

## 📝 Open items / Bug noti

| Item | Priorità | Note |
|------|----------|------|
| `cmd 0x1A` length error `10 != 12` | Alta | Usare `0x0C` invece di `0x0A` nel campo lunghezza; verificare blocco `elif cmd == "1A"` in rosmaster_main.py |
| Camera `/capture_still` endpoint | Media | TODO: endpoint still-quality per foto singola |
| Docking station microswitch | Media | Schema finalizzazione pendente; doc tecnico a v1.2/v1.5 |
| MotionSmoother class | Bassa | Progettata ma in pausa — stop deve essere immediato, solo accel/direzione smussati |
