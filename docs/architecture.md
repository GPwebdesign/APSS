# APSS — Architettura di Sistema

> Documento di riferimento esteso. Caricarlo on-demand con `@docs/architecture.md`

## Stack tecnologico

| Layer | Tecnologia |
|-------|-----------|
| OS Robot | Ubuntu 22.04.5 LTS aarch64 (hawk) |
| Middleware | ROS2 Humble Hawksbill |
| Server robot | Python 3.10 — `rosmaster_main.py` |
| App controllo | Kivy 2.3.1 + KivyMD 1.2.0 |
| Firmware docking | MicroPython su ESP32 WROOM-32D v2.1 |
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

> ⚠️ **Nota architetturale critica:** l'INA219 hawk è posizionato **dopo** il convertitore DD32AJ4B. Misura quindi la tensione **regolata** (~12.10V stabili) e non la tensione reale della batteria ECO-WORTHY. La stima SoC da tensione INA219 è inutilizzabile — il `battery_node.py` usa **coulomb counting** (integrazione corrente nel tempo) come metodo primario di stima SoC.

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
| `battery_node.py` | Monitor INA219 v2.0 — pubblica `/battery` (BatteryState, LiFePO4, coulomb counting) + `/battery/stats` ogni 2s |
| `tof_node.py` | (pianificato) Legge TCA9548A CH2/CH3/CH4 — pubblica `/tof/*` |
| `avoidance_node.py` | (pianificato) Obstacle avoidance — subscribe `/tof/*` → pubblica `/cmd_vel` |

### battery_node.py — v2.0 (Maggio 2026)

Aggiornato per batteria ECO-WORTHY LiFePO4 12.8V 8Ah (ECO-LFPYZ1208).

| Parametro | Valore |
|-----------|--------|
| Batteria | ECO-WORTHY LiFePO4 12.8V 8Ah — `design_capacity=8.0`, `serial_number='ECO-LFPYZ1208'` |
| Tecnologia | `POWER_SUPPLY_TECHNOLOGY_LIPO` (enum ROS2 più vicino a LiFePO4) |
| Metodo SoC | **Coulomb counting** — integrazione corrente nel tempo |
| SoC iniziale | 85% (SOC_INITIAL) — assunto al boot, si aggiorna durante l'uso |
| Capacità nominale | 8.0 Ah = 28800 C (BATTERY_CAPACITY_C) |
| Reset SoC | 100% quando corrente scende sotto 0.05A durante ricarica (fine carica CV) |
| Tabella tensione LiFePO4 | VOLTAGE_TABLE_LIFEPO4 mantenuta come riferimento futuro — NON usata per SoC (INA219 misura tensione regolata DD32AJ4B ~12.10V stabili) |
| Log | `[BATTERY] V=...V I=...A P=...W SoC=...% status=... [coulomb]` |

> ⚠️ La stima SoC da tensione INA219 hawk è inutilizzabile perché misura la tensione regolata dal DD32AJ4B (~12.10V costanti), non la tensione reale della batteria. Il coulomb counting è il metodo corretto in questa architettura.

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
| `/battery` | `sensor_msgs/BatteryState` | battery_node v2.0 | oled_node ✅, safety_node (pianificato) |
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

### Circuito ricarica (aggiornato Maggio 2026 — LiFePO4)

```
220VAC → [PSU 20V/3.25A] → [Relay CH1 ESP32 GPIO5] → [XL4016 CC/CV 14.40V/1.5A]
       → [Fusibile T3.15A slow-blow] → [XHM603 v1.0] → [INA219 HW-831B]
       → [Pogo pin] → [Pad rame robot] → [ECO-WORTHY LiFePO4 12.8V 8Ah]
```

#### Parametri XL4016 (calibrati Maggio 2026)

| Parametro | Valore | Note |
|-----------|--------|------|
| Tensione uscita (CV) | **14.40V** | Calibrato con trimmer — LiFePO4 max 14.6V |
| Corrente massima (CC) | **1.5A** | Calibrato con trimmer — tasso di carica 0.19C su 8Ah |
| Fusibile | T3.15A 250V slow-blow | Sostituisce T1.5A precedente |

> ⚠️ Corrente di 2A genera spike alla chiusura relay che fanno scattare erroneamente XHM603. 1.5A è il valore di compromesso ottimale verificato sperimentalmente.

#### Parametri XHM603 v1.0 (calibrati Maggio 2026 — LiFePO4)

| Parametro | Valore display | Tensione reale stimata | Note |
|-----------|---------------|----------------------|------|
| Soglia STOP | **14.4V** | ~13.70–13.80V ai terminali | Scatta al **superamento** → effettivo a 14.5V display |
| Soglia START | **13.1V** | ~12.40V ai terminali | Avvia ricarica a ~20% SoC |

#### Offset catena di potenza docking (misurati fisicamente — Maggio 2026)

| Coppia | Offset | Condizione |
|--------|--------|------------|
| Display XHM603 vs terminali batteria | **+0.70V** | Relay aperto (a vuoto) |
| INA219 docking vs terminali batteria | **+0.34V** | In ricarica attiva |
| Display XHM603 vs INA219 docking | **+0.40V** | In ricarica attiva |

#### Note operative XHM603

- La soglia scatta al **superamento** del valore impostato: STOP=14.4V → scatta a 14.5V display
- Misurare tensione con tester sui terminali batteria **durante la ricarica** può far scattare il relay per perturbazione del circuito — riarmare manualmente da webapp ESP32
- Con OCV finale misurato a 13.40V (30 min post-carica) → SoC ~95% → soglia STOP corretta, non modificare

#### Dati ciclo di ricarica completo (verificato Maggio 2026)

| Parametro | Valore |
|-----------|--------|
| OCV inizio ciclo | 13.23V (~60-70% SoC) |
| Durata ricarica completa | ~3h (da ~60% a ~95% SoC) |
| Corrente fase CC | ~1.35A media |
| Corrente fine carica (fase CV) | ~0.99A al momento scatto |
| Display al momento scatto | 14.5V (soglia 14.4V + superamento) |
| OCV post-scatto immediato | 13.60V |
| OCV stabile (30 min) | **13.40V (~95% SoC)** |

### INA219 HW-831B — Monitor ricarica docking

| Parametro | Valore |
|-----------|--------|
| Indirizzo I2C | 0x40 |
| Bus I2C | ESP32 (SDA=GPIO21, SCL=GPIO22) |
| Shunt | R100 (0.1Ω) onboard |
| Posizione nella catena | Dopo XHM603, prima dei pogo pin |
| Convenzione corrente | Positiva = ricarica attiva, Negativa = flusso inverso (batteria alimenta XHM603 a relay aperto) |
| Lettura corrente ricarica tipica | ~1.35A fase CC, ~0.99A fine CV |
| Lettura corrente a relay aperto | ~-0.02A (flusso inverso minimo) |

### ESP32 firmware v2.1 (Maggio 2026)

| File | Funzione |
|------|---------|
| `boot.py` | Relay GPIO5=HIGH (aperto) come prima istruzione — sicurezza fault software. CPU 240MHz. WebREPL start. |
| `config.json` | WiFi, pin GPIO, soglie INA219, parametri ricarica (START/STOP reference), debounce reed |
| `ina219.py` | Driver I2C INA219 — lettura V/A/W con convenzione corrente verificata fisicamente |
| `main.py` | Webserver HTTP dashboard, loop sensori 2s, IRQ microswitch con debounce 2000ms, relay automatico, watchdog CAL INA219, sync NTP |

GPIO mapping:
- GPIO5: Relay CH1 (LOW=chiuso=ricarica abilitata, HIGH=aperto=ricarica bloccata)
- GPIO18: Microswitch NC (sostituisce reed switch — comportamento erratico verificato). Attualmente fissato in posizione aperta → GPIO18 pull-up = 1 costante → relay si chiude automaticamente al boot con rete presente
- GPIO34: Blackout detection via partitore R1=47kΩ/R2=10kΩ — V_misura=3.51V con rete presente

#### Fix applicati in v2.1 rispetto a v2.0

| Fix | Problema risolto |
|-----|-----------------|
| Debounce IRQ 2000ms su GPIO18 | Spike dalla chiusura relay XHM603 interpretati come sgancio → relay ESP32 aperto → ricarica interrotta |
| Relay automatico nel loop 2s | Relay sempre aperto al boot richiedeva intervento manuale da webapp ad ogni avvio |
| Watchdog CAL INA219 | Reset a caldo ESP32 azzerava registro CAL → corrente legge 0A con tensione corretta |
| config.json aggiornato LiFePO4 | max_expected_amps 3.0→2.0, soglie tensione aggiornate, sezione ricarica aggiunta |

Dashboard: `http://192.168.1.193` — V/I/W in tempo reale, log eventi, controllo relay, scan I2C.
Comandi REPL: `r1()` relay ON, `r0()` relay OFF, `stato_txt()` stato seriale.
Documentazione completa firmware: `docs/doc_firmware.md`.

#### Roadmap firmware v2.2

- `relay_chiudi()` e `relay_apri()` devono loggare automaticamente V/A/W INA219 al momento esatto di avvio e stop ricarica
- Installazione microswitch meccanico sul paraurti robot (attualmente fissato con scotch)

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
