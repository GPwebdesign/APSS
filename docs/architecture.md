# APSS — Architettura di Sistema

> Documento di riferimento esteso. Caricarlo on-demand con `@docs/architecture.md`

## Stack tecnologico

| Layer | Tecnologia |
|-------|-----------|
| OS Robot | Ubuntu 22.04.5 LTS aarch64 (hawk) |
| Middleware | ROS2 Humble Hawksbill |
| Server robot | Python 3.10 — `rosmaster_main.py` |
| App controllo | Kivy 2.3.1 + KivyMD 1.2.0 |
| Firmware docking | MicroPython su ESP32 WROOM-32D |
| Comunicazione | TCP porta 6000 (controllo) + HTTP porta 6500 (MJPEG + `/capture_still`) |

---

## Hardware robot

### Componenti principali

| Componente | Modello | Note |
|-----------|---------|------|
| Elaboratore | Raspberry Pi 4 | Ubuntu 22.04, hostname `hawk` |
| Scheda espansione | Yahboom Rosmaster V3.0 | STM32F103RCT6 + IMU MPU9250 |
| Ruote | 4x motori DC encoder Mecanum | M1=ant.sx, M2=ant.dx, M3=post.sx, M4=post.dx |
| Camera | Arducam OV5647 CSI IR-cut | Focus fisso 0–1.5m, IR-cut via LDR |
| Pan/Tilt | 2x servo PWM | S1=Tilt, S2=Pan (swap fisico) — home: Pan=100°, Tilt=85° |
| LiDAR | RPLIDAR A1M8 | `/dev/ttyUSB1`, offset 90°, ~7.7Hz |
| Batteria | Yuasa YTZ10S 12V 8.6Ah AGM | Unica fonte energia robot |
| Monitor alimentazione | INA219 0x40 | In serie al positivo — shunt R100 — libreria adafruit |
| OLED | SSD1306 0x3C | Operativo via `oled_node.py` |

### Cinematica Mecanum — VALORI FISICI VERIFICATI

```
ENCODER_CPR   = 822       (misurato fisicamente)
WHEEL_RADIUS  = 0.0395 m
sep_x         = 0.078 m   (semidistanza ant/post)
sep_y         = 0.105 m   (semidistanza sx/dx)
Footprint     = 35 × 28 cm
```

Formula motori (vx=avanti, vy=laterale, vz=rotazione):
```
M1 = vx - vy + vz   (polarità invertita: fili M+/M- scambiati fisicamente)
M2 = vx + vy - vz
M3 = vx + vy + vz
M4 = vx - vy - vz   (polarità invertita: fili M+/M- scambiati fisicamente)
```

Calibrazione velocità: `motor_calibration.json` → `m1 = 0.60`

### Sensori TOF (INSTALLATI — Maggio 2026)

| Sensore | Posizione | Canale reale TCA9548A | Stato |
|---------|-----------|----------------------|-------|
| TOF400C VL53L1X #1 | Frontale 0° | CH2 | ✅ Verificato (0x29) |
| TOF400C VL53L1X #2 | Sinistra 30° | CH3 | ✅ Verificato (0x29) |
| TOF400C VL53L1X #3 | Destra 30° | CH4 | ⚠️ Problema cablaggio |
| TOF400C VL53L1X #4 | Spare | — | Non collegato |

TCA9548A: indirizzo I2C 0x70. Soglie obstacle avoidance: 50cm = rallenta, 40cm = pivot rotate.

### INA219 — Monitor alimentazione robot

Installato in serie al positivo tra alimentazione e scheda Yahboom (Maggio 2026).

| Parametro | Valore |
|-----------|--------|
| Indirizzo I2C | 0x40 |
| Shunt | R100 (0.1Ω) |
| Libreria | adafruit-circuitpython-ina219 |
| Convenzione corrente | Positiva = DISCHARGING (robot assorbe), Negativa = CHARGING (docking) |
| Potenza | Calcolata come V × I (registro power non calibrato) |

---

## Stack ROS2 (`ros2_py_ws/`)

### File principali

| File | Funzione |
|------|---------|
| `apss_robot.urdf.xml` | Descrizione robot (URDF) |
| `apss_lidar.launch.py` | Launch: RPLIDAR + robot_state_publisher + tf + slam_toolbox + RViz2 |
| `rviz/apss.rviz` | Configurazione RViz2 |
| `oled_node.py` | Nodo OLED SSD1306 |
| `battery_node.py` | Monitor INA219 — pubblica `/battery` + `/battery/stats` ogni 2s |
| `tof_node.py` | (pianificato) Legge TCA9548A CH2/CH3/CH4 — pubblica `/tof/*` |
| `avoidance_node.py` | (pianificato) Obstacle avoidance — subscribe `/tof/*` → pubblica `/cmd_vel` |

### TF tree
```
map → odom (statico, da launch)
odom → base_footprint (dinamico, da thread_odom in rosmaster_main.py)
base_footprint → base_link → [laser_frame, camera_frame, ...]
```

### Topic principali

| Topic | Tipo | Produttore | Consumatore |
|-------|------|-----------|-------------|
| `/scan` | `sensor_msgs/LaserScan` | rplidar_node | slam_toolbox |
| `/odom` | `nav_msgs/Odometry` | thread_odom (rosmaster_main.py) | slam_toolbox |
| `/battery` | `sensor_msgs/BatteryState` | battery_node | oled_node (⚠️ subscriber mancante) |
| `/battery/stats` | `udemy_ros2_pkg/BatteryStats` | battery_node | — |
| `/apss/battery` | `std_msgs/String` JSON | — | oled_node (topic attuale — da allineare) |
| `/apss/mode` | `std_msgs/String` | — | oled_node |
| `/cmd_vel` | `geometry_msgs/Twist` | (pianificato: avoidance_node / nav2) | rosmaster_main.py |
| `/tof/front` `/tof/left` `/tof/right` | `sensor_msgs/Range` | tof_node (pianificato) | avoidance_node |

> ⚠️ **Disallineamento topic batteria:** `battery_node` pubblica su `/battery` (BatteryState), `oled_node` subscribes `/apss/battery` (String JSON). Fix in corso: aggiungere subscriber `/battery` in `oled_node.py`.

---

## Servizi systemd (hawk)

| Service | File | Stato | Funzione |
|---------|------|-------|----------|
| `apss-lidar-standby.service` | `rosmaster_project/apss_lidar_standby.py` | ✅ Installato/abilitato | Stop motore RPLIDAR al boot — ⚠️ delay init firmware da risolvere |

---

## Hardware docking station

### Circuito ricarica

```
220VAC → [PSU 20V/3.25A] → [XL4016 CC/CV 14.82V/0.9A] → [Fusibile T1.6A]
       → [XHM603 IN+] → [Relay] → [Batteria YTZ10S]
```

Soglie XHM603 (compensate offset display +0.23/0.25V):
- START: 12.2V (display) → ~11.95V reale
- STOP: 14.7V (display) → ~14.47V reale

### ESP32 firmware v2.0

| File | Funzione |
|------|---------|
| `boot.py` | Init WiFi |
| `config.json` | Soglie, intervalli, SSID |
| `ina219.py` | Driver I2C INA219 |
| `main.py` | Webserver + loop principale |

GPIO mapping:
- GPIO5: Relay CH1 (ricarica)
- GPIO18: Reed switch NC (conferma docking)
- GPIO34: Blackout detection (assenza 230V)

Convenzione INA219: corrente positiva = ricarica attiva, negativa = flusso inverso normale

---

## App Kivy (`rosmaster_project/rosmaster_kivy/`)

### Schermate

| Schermata | Stato | Funzione |
|-----------|-------|---------|
| MainScreen | Operativa | Stream video + pad motori 3x3 |
| CameraScreen | Operativa | Stream + pan/tilt |
| SettingsScreen | Operativa | IP robot, porte TCP/HTTP |
| PatrolScreen | Placeholder | Pattugliamento autonomo (Fase 5) |
| AlertScreen | Placeholder | Log alert + clip video (Fase 6) |
| StatusScreen | Placeholder | Stato sistema, batteria (Fase 7) |

**APK Android:** `apssystem-2.1-arm64-v8a_armeabi-v7a-debug.apk` generato con Buildozer 1.5.0 — target API 34, NDK 25b, Samsung S23 Ultra. Da testare.

### Parametri movimento

```python
speed_base   = 55
slider_range = 0.5 – 1.0   (avanti/indietro)
rotate_factor = 0.8
strafe_factor = 0.9
```

### Protocollo TCP — comandi implementati

| Cmd | Formato | Funzione |
|-----|---------|---------|
| Init | `$020f040116#` | car_type=2, g_mode=Standard — obbligatorio post-connessione |
| 0x1A | `$02 1A 0C [m1][m2][m3][m4] 00 [cs]#` | set_motor diretto |
| 0x11 | `$02 11 06 [id][angle][cs]#` | Servo: id 1=Tilt, 2=Pan |
| Stop | `$021a0c000000000028#` | Tutti motori a zero |

### Pipeline camera (v2.1 — consolidata)

| Componente | Comportamento |
|-----------|---------------|
| `picamera2` / `get_frame()` | Restituisce frame RGB888 nativo — NESSUNA conversione cvtColor |
| `thread_camera` / `g_latest_frame` | Contiene frame RGB nativo |
| `mode_handle()` / stream MJPEG | NESSUNA conversione — RGB → `cv.imencode` → MJPEG → Kivy `colorfmt=rgb` |
| `/capture_still` endpoint | Frame RGB → `cv.imencode` JPEG qualità 95 → download su client |
| `camera_params.json` | SOLO profilo streaming (profilo vision rimosso in v2.1) |
| Profilo streaming | `ColourGains(1.3,1.4)` Sharpness=2.0 Contrast=1.1 Brightness=0.0 Saturation=0.8 |

> ⚠️ NON aggiungere conversioni `cvtColor` intermediate — il frame è RGB in tutto il pipeline.

### Endpoint HTTP (porta 6500)

| Endpoint | Metodo | Risposta |
|----------|--------|----------|
| `/video_feed` | GET | Stream MJPEG 31 FPS 640x480 |
| `/capture_still` | GET | File JPEG qualità 95 — nome: `still_YYYYMMDD_HHMMSS.jpg` |

---

## Sensori ambientali (pianificati)

| Sensore | Hardware | Topic MQTT | Stato |
|---------|---------|-----------|-------|
| Temperatura/Umidità | DHT-11 GPIO | `apss/sensors/env` | Hardware disponibile |
| Fiamma/Fumo | OpenCV OV5647 | `apss/sensors/flame` | Da implementare |
| Microfono | USB mic | `apss/sensors/audio` | Da acquistare |
| Gas | MQ-2/MQ-135 + ADS1115 | `apss/sensors/gas` | Da acquistare |
