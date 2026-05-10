# APSS — Autonomous Patrol and Surveillance System
## Riepilogo sessione per nuova chat — Maggio 2026

Contesto: Robot autonomo di pattugliamento basato su Yahboom Rosmaster R2 + Raspberry Pi 4 (hawk, 192.168.1.158, Ubuntu 22.04, ROS2 Humble). VM sviluppo: gp68-vmware (192.168.1.80). Repository: `rosmaster_project` e `ros2_py_ws` (GitHub GPwebdesign privati).

**WORKFLOW:** Modifiche su VM → commit/push → pull su Pi. MAI modificare direttamente sul Pi. File del progetto: cercare SEMPRE su GitHub, MAI su Google Drive (Drive ha versioni vecchie).

---

## Hardware robot

Struttura proprietaria GPwebdesign con componenti Yahboom (scheda STM32, 4 motori DC Mecanum). M1/M4 polarità invertita fisicamente. Ruote Mecanum configurazione X. Calibrazione motori: m1=0.60 (motor_calibration.json sul Pi). Speed base=55. Cinematica custom Python: M1=vx-vy+vz, M2=vx+vy-vz, M3=vx+vy+vz, M4=vx-vy-vz. Strafe laterale puro ABBANDONATO — non ottenibile anche con ruote in configurazione X.

---

## App Kivy

Kivy 2.3.1 + KivyMD 1.2.0, dark, portrait. Stream MJPEG http://192.168.1.158:6500/video_feed 31FPS. Pad 3x3 con slider velocità 0.5-1.0 per forward/backward. CameraScreen con pan/tilt (home graduale), foto JPG timestamp, video sequenza JPG in rosmaster_kivy/save/. Titolo: "APSSystem" / "Autonomous Patrol and Surveillance System". Pan/tilt controllato via cmd 0x11 nativo Yahboom — cmd 0x1B NON necessario.

**APK Android:** buildozer.spec configurato — APK debug 2.1 generato per Samsung S23 Ultra (API 34, arm64-v8a + armeabi-v7a). VM Buildozer: VMware-Ubuntu24-04-4, venv ~/venv-buildozer, repo clonato in ~/Workspaces/rosmaster_project.

---

## Camera

Arducam OV5647 IR-cut motorizzato automatico (B07X1VGQSL). Fuoco fisso 0-1.5m. IR-cut automatico via LDR.

**Pipeline colore (CONSOLIDATA Maggio 2026):**
- `picamera2` restituisce frame RGB888 nativo
- `get_frame()` in `camera_rosmaster.py`: restituisce RGB direttamente — NESSUNA conversione cvtColor
- `mode_handle()` in `rosmaster_main.py`: NESSUNA conversione — RGB nativo → cv.imencode → MJPEG → Kivy `colorfmt=rgb`
- `capture_still`: frame RGB → cv.imencode JPEG qualità 95 → download diretto

**camera_params.json:** SOLO profilo streaming (profilo vision RIMOSSO). ColourGains(1.3,1.4) Sharp=2.0 Cont=1.1 Sat=0.8.

**Pan home=100°, tilt home=85°.** Pan/tilt centrato automaticamente all'avvio di rosmaster_main.py.

**Endpoint /capture_still** (porta 6500): foto JPEG qualità 95 scaricabile sul dispositivo client. Operativo e testato.

---

## Stack ROS2

URDF apss_robot.urdf.xml (base_footprint→base_link→laser z=0.33m rpy Z=90°, camera_link x=0.16m z=0.20m). Launch file apss_lidar.launch.py avvia: RPLIDAR+robot_state_publisher+tf statico map→odom+slam_toolbox+RViz2.

**Ordine avvio obbligatorio:**
1. `python3 rosmaster_main.py`
2. `ros2 launch apss_lidar.launch.py`

---

## Odometria

thread_odom in rosmaster_main.py pubblica /odom e tf dinamico odom→base_footprint. ENCODER_CPR=822 (misurato fisicamente su M2). WHEEL_RADIUS=0.0395m. sep_x=0.078m, sep_y=0.105m.

---

## RPLIDAR A1M8

/dev/ttyUSB1, offset 90°. Driver ros-humble-rplidar-ros v2.1.4 in hold. Topic /scan ~7.7Hz. slam_toolbox installato in modalità mapping. Mappe salvate in ros2_py_ws/maps/.

---

## INA219 — Monitor batteria

INA219 indirizzo 0x40, shunt R100 (0.1Ω). Installato in serie al positivo tra alimentazione e scheda Yahboom. Monitora assorbimento totale robot (esclusi display/multiplexer/TOF — assorbimento fisso e piccolo).

**Convenzione corrente:** positiva = robot assorbe (DISCHARGING), negativa = flusso inverso (CHARGING da docking).

**battery_node.py** operativo in `ros2_py_ws/src/udemy_ros2_pkg/scripts/`:
- Pubblica `/battery` (sensor_msgs/BatteryState) ogni 2s
- Pubblica `/battery/stats` (udemy_ros2_pkg/BatteryStats custom) — min/max V/I/P + sample_count
- Tabella SoC AGM 12V: 12.70V=100% ... 11.50V=0%
- Batteria Yuasa YTZ10S 12V 8.6Ah — design_capacity=8.6Ah

**BatteryStats.msg** in `ros2_py_ws/src/udemy_ros2_pkg/msg/BatteryStats.msg`:
```
std_msgs/Header header
float32 voltage_min / voltage_max
float32 current_min / current_max
float32 power_min / power_max
uint32 sample_count
```

---

## Obstacle avoidance — TOF400C VL53L1X

Hardware fisicamente installato. TCA9548A indirizzo 0x70.

**Mappatura canali REALE:**
| Sensore | Posizione | Canale TCA9548A |
|---|---|---|
| TOF frontale | 0° | CH2 |
| TOF sinistro | 30° | CH3 |
| TOF destro | 30° | CH4 ⚠️ problema cablaggio |
| TOF scorta | — | non collegato |

⚠️ **CH4 blocca il bus I2C** — problema fisico di cablaggio sul TOF destro. Da risolvere prima di scrivere tof_node.py. CH2 e CH3 verificati OK (0x29 su entrambi i canali).

**Architettura software pianificata:**
- `tof_node.py` → pubblica `/tof/front` `/tof/left` `/tof/right` (sensor_msgs/Range)
- `avoidance_node.py` → subscribe /tof/* → pubblica /cmd_vel
- `rosmaster_main.py` → subscriber /cmd_vel (da aggiungere)
- Soglie: 50cm=rallenta, 40cm=pivot

---

## rosmaster_main.py — Stato attuale (Maggio 2026)

- Versione V2.3.3 — 1115 righe
- RIMOSSI: RosImage, g_image_pub, g_ros_node, publish_image_frame(), thread_image_publisher(), task_image
- thread_odom: odometria encoder operativa
- thread_camera: alimenta g_latest_frame con frame RGB nativo
- Endpoint /video_feed: stream MJPEG operativo, colori corretti
- Endpoint /capture_still: JPEG qualità 95, download su client
- TODO: aggiungere subscriber /cmd_vel per obstacle avoidance autonomo

---

## Docking station ESP32

Firmware v2.0 operativo. Dashboard http://192.168.1.193. INA219, reed GPIO18 NC, relay CH1 GPIO5, blackout GPIO34. Circuito ricarica: XL4016 14.82V/0.9A, XHM603 START=12.2V STOP=14.7V (compensati).

---

## Roadmap

### Completati (Maggio 2026)
1. ✅ Rimozione OpenCV obstacle avoidance + thread_image_publisher
2. ✅ Semplificazione camera_params.json — solo profilo streaming
3. ✅ Endpoint /capture_still
4. ✅ Fix pipeline colore camera RGB
5. ✅ battery_node.py — /battery + /battery/stats + BatteryStats.msg
6. ✅ APK Android debug 2.1 generato (da testare su S23 Ultra)

### Prossimi step (in ordine)
1. Fix cablaggio TOF CH4 (TOF destro)
2. `tof_node.py` — lettura CH2/CH3/CH4 via TCA9548A
3. `avoidance_node.py` — logica obstacle avoidance
4. `rosmaster_main.py` — aggiungere subscriber /cmd_vel
5. Test APK Android su Samsung S23 Ultra
6. Sessione mapping SLAM studio

### Futuri
- Nav2 navigazione autonoma
- Pattugliamento autonomo con waypoint
- Docking autonomo ArUco
- pan_tilt_node.py ROS2 con subscriber /pan_tilt/cmd

---

## Pending items

- Fix cablaggio TOF CH4 — controllare SDA/SCL/VCC/GND su connettore CH4 TCA9548A
- Test APK Android su Samsung S23 Ultra (installazione + verifica stream/motori/still)
- Backup su USB disk via SMB (cifs-utils da installare su hawk, credenziali pronte: \\iliadbox_Server\iliadbox utente Rino)
- Microswitch docking station (NC, GPIO18, stesso cablaggio reed)
- Ripristino aggiornamenti ROS2 Humble su hawk
