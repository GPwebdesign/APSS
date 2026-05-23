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
| LiDAR | RPLIDAR A1M8 | `/dev/rplidar` (symlink udev) — offset 90°, ~7.7Hz |
| Batteria | ECO-WORTHY LiFePO4 12.8V 8Ah | Installata (Maggio 2026) — sostituisce Yuasa YTZ10S AGM |
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
| TOF400C VL53L1X #3 | Destra 30° | CH4 | ✅ Verificato (0x29) — sensore originale difettoso, sostituito con scorta |
| TOF400C VL53L1X #4 | Spare | — | Non collegato |

TCA9548A: indirizzo I2C 0x70. Soglie obstacle avoidance: 50cm = rallenta, 40cm = pivot rotate.

### INA219 — Monitor alimentazione robot

Installato in serie al positivo tra il regolatore DD32AJ4B e la scheda Yahboom (Maggio 2026).

| Parametro | Valore |
|-----------|--------|
| Indirizzo I2C | 0x40 |
| Shunt | R100 (0.1Ω) |
| Libreria | adafruit-circuitpython-ina219 |
| Convenzione corrente | Positiva = DISCHARGING (robot assorbe), Negativa = CHARGING (docking) |
| Potenza | Calcolata come V × I (registro power non calibrato) |
| Assorbimento idle misurato | ~0.45–0.60 A / ~5.30–6.45 W (Maggio 2026) |
| Picco motori (memoria battery_node) | ~2.14 A / ~25.7 W |
| Caduta su shunt | 60 mV @ 0.6A → 200 mV @ 2A |

---

## Catena di alimentazione robot (Maggio 2026)

```
        ECO-WORTHY LiFePO4 12.8V 8Ah
              │  (13.09V sotto carico, batteria carica)
              ▼
        DD32AJ4B convertitore multi-uscita
          ├── Uscita trimmer regolata: setpoint 12.16V a vuoto
          │        │
          │        ▼
          │   INA219 0x40 (shunt R100)
          │        │  (11.58–11.70V sotto carico idle ~0.6A)
          │        ▼
          │   Scheda Yahboom V3.0 — motori, servo, RPi 4, RPLIDAR, ecc.
          │
          ├── Uscita 3.3V → 3x TOF400C VL53L1X + TCA9548A (alimentazione I2C)
          ├── Uscita 5V → (non collegata)
          └── Uscita 12V → (non collegata)
```

### Misure di tensione lungo la catena (Maggio 2026, batteria carica, robot acceso idle)

| Punto | A vuoto | Sotto carico (0.45–0.60 A) | Caduta |
|-------|---------|---------------------------|--------|
| Terminali batteria ECO-WORTHY | — | 13.09 V | (riferimento) |
| Uscita DD32AJ4B (tester) | 12.16 V | 11.70 V | 0.46 V (load regulation) |
| Lettura INA219 (a valle shunt) | — | 11.48–11.68 V | +0.06 V (shunt @ 0.6A) |

**Diagnosi**: la caduta di ~0.46 V dall'uscita DD32AJ4B sotto carico è dovuta alla regolazione di carico del convertitore (load regulation mediocre dei buck multi-uscita economici). Lo shunt INA219 contribuisce solo ~60 mV @ 0.6 A.

### Scelta del setpoint trimmer (Maggio 2026)

Il supporto tecnico Yahboom dichiara **input max 12V** per la Rosmaster Expansion Board V3.0. Setpoint a vuoto mantenuto a **12.16 V** (1.3% sopra spec, marginalmente tollerato) per garantire:

- Sotto carico idle (~0.6 A) → ~11.65 V — dentro range operativo
- Sotto carico motori (~2 A) → stima ~11.2 V — ancora safe

**Decisione**: il setpoint NON viene cambiato perché alzarlo (es. 12.50 V) violerebbe il limite Yahboom a vuoto, e abbassarlo (es. 11.80 V) ridurrebbe il margine durante gli spunti motore.

---

## Logica ricarica autonoma (Fase 1 — voltage based)

Il robot autonomo deve decidere quando rientrare al docking. **Fase 1**: trigger basati su tensione `BatteryState.voltage` letta da `/battery`. **Fase 2 (futura)**: il robot registra autonomamente V/I/SoC durante l'uso operativo per costruire una tabella SoC LiFePO4 empirica; le soglie migreranno su `BatteryState.percentage`.

### 3 soglie di trigger (Fase 1)

| Livello | Tensione INA219 (`/battery.voltage`) | SoC stimato | Azione del robot |
|---------|--------------------------------------|-------------|------------------|
| 🟡 LOW | ~11.50 V | ~30% | Completa il task corrente, poi rientra al docking |
| 🟠 CRITICAL | ~11.20 V | ~15% | Interrompe il task, rientra immediatamente al docking |
| 🔴 EMERGENCY | ~10.80 V | ~5% | Stop ovunque, segnala emergenza, attende recupero manuale |

### Note di taratura

- I valori sopra sono **stime iniziali conservative**, non calibrati empiricamente sulla LiFePO4 ECO-WORTHY specifica
- La curva di scarica LiFePO4 è piatta tra 90% e 20% SoC e crolla rapidamente sotto il 10%
- La caduta sulla catena DD32AJ4B varia con la corrente — le soglie sono pensate per condizioni di pattugliamento (~0.6–1.0 A media)
- Il margine 11.50 → 10.80 V corrisponde a circa 90 secondi di operatività in pattugliamento, sufficiente per il rientro

### Roadmap calibrazione (Fase 2)

1. Il `battery_node.py` registra V/I/t durante uso operativo (log CSV o topic dedicato)
2. Si identificano i punti di crollo della curva LiFePO4 specifica
3. Si compila una tabella SoC voltage → percentage e si carica in `battery_node.py`
4. `BatteryState.percentage` diventa il campo affidabile per le decisioni
5. Le soglie migrano: LOW=30%, CRITICAL=15%, EMERGENCY=5%

---

## Stack ROS2 (`ros2_py_ws/`)

### File principali

| File | Funzione |
|------|---------|
| `apss_robot.urdf.xml` | Descrizione robot (URDF) |
| `apss_lidar.launch.py` | Launch: RPLIDAR + robot_state_publisher + tf + slam_toolbox + RViz2 |
| `rviz/apss.rviz` | Configurazione RViz2 |
| `oled_node.py` | Nodo OLED SSD1306 — layout: APSS / IP / V grande (asterisco se lettura diretta INA219) / A W. Subscriber `/battery` + fallback INA219 diretto con watchdog 5s |
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
| `/battery` | `sensor_msgs/BatteryState` | battery_node | oled_node ✅, safety_node (pianificato) |
| `/battery/stats` | `apss_ros2_pkg/BatteryStats` | battery_node | — |
| `/apss/alarm` | `std_msgs/String` | safety_node (pianificato) | (consumer futuri) |
| `/apss/mode` | `std_msgs/String` | (futuro) | oled_node |
| `/apss/sensors/env` | `std_msgs/String` JSON | (futuro) | oled_node |
| `/cmd_vel` | `geometry_msgs/Twist` | (pianificato: avoidance_node / nav2) | rosmaster_main.py |
| `/tof/front` `/tof/left` `/tof/right` | `sensor_msgs/Range` | tof_node (pianificato) | avoidance_node |

---

## Servizi systemd (hawk)

| Service | File | Stato | Funzione |
|---------|------|-------|----------|
| `apss-lidar-standby.service` | `rosmaster_project/apss_lidar_standby.py` | ⛔ Disabled (topic aperto) | Stop motore RPLIDAR al boot — non ha mai effettivamente fermato il motore |
| `apss-oled.service` | `ros2_py_ws` — `ros2 run apss_ros2_pkg oled_node.py` | ✅ Installato, enabled, funzionante al boot (Mag 2026) | Avvio OLED al boot, indipendente da launch file — `After=network-online.target`, `Restart=on-failure` |

---

## USB device naming (Maggio 2026)

La scheda Yahboom (chip CH340 `1a86:7523`) e il RPLIDAR A1M8 (chip CP2102 `10c4:ea60`) sono entrambi collegati via USB. L'ordine `ttyUSB0` / `ttyUSB1` assegnato al boot dal kernel non è deterministico, quindi sono necessari nomi stabili.

### Regole udev

File: `/etc/udev/rules.d/99-apss-usb.rules`

```
SUBSYSTEM=="tty", ATTRS{idVendor}=="1a86", ATTRS{idProduct}=="7523", SYMLINK+="yahboom", GROUP="dialout", MODE="0660"
SUBSYSTEM=="tty", ATTRS{idVendor}=="10c4", ATTRS{idProduct}=="ea60", SYMLINK+="rplidar", GROUP="dialout", MODE="0660"
```

Dopo l'installazione/modifica del file:

```bash
sudo udevadm control --reload-rules
sudo udevadm trigger --action=add --subsystem-match=tty
```

### Symlink risultanti (stabili)

| Symlink | Punta a | Usato da |
|---------|---------|---------|
| `/dev/yahboom` | CH340 Yahboom — `ttyUSB0` o `ttyUSB1` a seconda del boot | `Rosmaster_Lib` (patchato) |
| `/dev/rplidar` | CP2102 RPLIDAR — `ttyUSB0` o `ttyUSB1` a seconda del boot | `rplidar_ros` (via launch file) |

### Patch libreria Yahboom

La libreria `Rosmaster_Lib` ha un bug noto: il parametro `com` del costruttore è ignorato e la porta `/dev/ttyUSB0` è hardcoded a riga 20. Patch applicata in:

`/usr/lib/python3.10/Rosmaster_Lib/Rosmaster_Lib.py`

```python
# Riga 20 — prima:
self.ser = serial.Serial('/dev/ttyUSB0', 115200)
# Riga 20 — dopo (apre il symlink stabile):
self.ser = serial.Serial('/dev/yahboom', 115200)
```

Backup originale conservato in `Rosmaster_Lib.py.bak-APSS`.

> ⚠️ **Persistenza**: la patch va riapplicata manualmente se la libreria `Rosmaster_Lib` viene reinstallata via apt/pip (es. dopo dist-upgrade o reset Ubuntu).

### Launch file ROS2

`ros2_py_ws/src/udemy_ros2_pkg/launch/apss_lidar.launch.py` configurato con `serial_port: '/dev/rplidar'` (originale `/dev/ttyUSB1`). Backup originale in `.bak-APSS`. Modifica persistente nel repo Git.

---

## Hardware docking station

### Circuito ricarica

```
220VAC → [PSU 20V/3.25A] → [XL4016 CC/CV 14.40V/0.9A] → [Fusibile T1.5A slow-blow]
       → [XHM603 IN+] → [Relay] → [Batteria LiFePO4 ECO-WORTHY]
```

Soglie XHM603 aggiornate per LiFePO4 (conservative):
- START: 13.1V (display)
- STOP: 14.2V (display)
- Offset catena: display XHM603 vs terminali = +0.70V, INA219 vs terminali = +0.34V

> ⚠️ **Fase D in corso:** fusibile T1.5A → T3A slow-blow, ricalibrazione CC a 2A, soglie XHM603 definitive da confermare dopo ciclo completo.

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
| MainScreen | Operativa — ✅ bug video primo `on_enter` risolto (TCP bind 0.0.0.0) | Stream video + pad motori 3x3 |
| CameraScreen | Operativa | Stream + pan/tilt |
| SettingsScreen | Operativa | IP robot, porte TCP/HTTP |
| PatrolScreen | Placeholder | Pattugliamento autonomo (Fase 5) |
| AlertScreen | Placeholder | Log alert + clip video (Fase 6) |
| StatusScreen | Placeholder | Stato sistema, batteria (Fase 7) |

**APK Android:** `apssystem-2.1-arm64-v8a_armeabi-v7a-debug.apk` generato con Buildozer 1.5.0 — target API 34, NDK 25b, Samsung S23 Ultra. ✅ Testato e funzionante. Salvataggio media in `/sdcard/DCIM/APSSystem/` con notifica MediaStore. Icona personalizzata configurata.

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
