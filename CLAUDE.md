# APSS — Autonomous Patrol and Surveillance System

## Cosa è questo progetto
Robot autonomo di pattugliamento e sorveglianza per interni (appartamento).
Piattaforma custom con componenti Yahboom Rosmaster R2, Raspberry Pi 4, ROS2 Humble.

## Architettura in una riga
`RPi4 (hawk)` → ROS2 Humble + rosmaster_main.py (TCP server) → Kivy App (Android/Linux) via WiFi

## Repository e path critici

| Sistema | Path | Ruolo |
|---------|------|-------|
| RPi4 `hawk` (192.168.1.158) | `~/Workspaces/rosmaster_project/` | Server TCP, camera, pan/tilt, odometria |
| RPi4 `hawk` | `~/Workspaces/ros2_py_ws/` | Stack ROS2: URDF, launch, SLAM, RViz2 |
| VM `gp68-vmware` (192.168.1.80) | `~/Workspaces/rosmaster_project/` | Sviluppo principale — commit/push da qui |
| VM `gp68-vmware` | `~/Workspaces/ros2_py_ws/` | Sviluppo ROS2 — commit/push da qui |
| PC Windows | `D:\_claudecodeproject\APSS\` | Repo principale APSS (subtree) — Filesystem MCP attivo |
| Docking station ESP32 | `http://192.168.1.193` | Dashboard MicroPython, INA219, relay |

## Regole essenziali per Claude Code

### Workflow sviluppo — CRITICO
- **Modifiche codice sempre sulla VM** (gp68-vmware, VSCode/ClaudeCode) → commit/push GitHub → pull su hawk per test
- **Dopo test OK su hawk** → aggiornare subtree PC con `.\subtree-pull.bat`
- **Modifiche da hawk** → `apss-push.sh` → pull su VM → `.\subtree-pull.bat` su PC
- **Modifiche doc** (.md, skills) solo su PC in `D:\_claudecodeproject\APSS\` → push APSS
- **MAI modificare codice direttamente sul PC** senza passare da VM o hawk
- File di progetto: cercare su **GitHub** (mai Google Drive — versioni vecchie)
- Filesystem MCP attivo su PC (`D:\_claudecodeproject`) — Claude può leggere/modificare file direttamente

### Motori — CRITICO
- **NON usare mai** `set_car_motion()` dalla libreria Rosmaster_Lib → produce movimenti errati
- **Usare sempre** `set_motor()` diretto via TCP `cmd 0x1A`
- Formula Mecanum custom verificata fisicamente:
  ```
  M1 (ant.sx) = vx - vy + vz    ← polarità fisica invertita (fili scambiati)
  M2 (ant.dx) = vx + vy - vz
  M3 (post.sx) = vx + vy + vz
  M4 (post.dx) = vx - vy - vz   ← polarità fisica invertita (fili scambiati)
  ```

### Protocollo TCP
- Formato: `$[payload_hex][checksum_hex]#`
- Lunghezza nel payload: `data_size − 8` (non la lunghezza totale)
- `cmd 0x10` = 7 byte totali con byte lunghezza fisso `0x08`
- Fix critico in `parse_data()`: `cmd = data[3:5].upper()` (case-sensitive)

### ROS2 — ordine di avvio su hawk
```bash
# 1. Prima
python3 ~/rosmaster_project/rosmaster_main.py
# 2. Poi
ros2 launch ~/ros2_py_ws/apss_lidar.launch.py
```

### Servo pan/tilt
- S1 = Tilt, S2 = Pan (swap fisico rispetto alla denominazione Yahboom)
- Home: Pan=100°, Tilt=85°
- Calibrazione: `pan_tilt_presets.json`
- Cmd `0x11` nativo Yahboom — cmd `0x1B` NON necessario

### Camera — pipeline colore (CONSOLIDATA v2.1)
- `picamera2` restituisce RGB888 nativo — NESSUNA conversione in `get_frame()`
- `mode_handle()`: NESSUNA conversione — RGB → `cv.imencode` → MJPEG → Kivy `colorfmt=rgb`
- `/capture_still` (porta 6500): frame RGB → JPEG qualità 95 → download client
- `camera_params.json`: SOLO profilo streaming (vision rimosso)
- **NON aggiungere** conversioni `cvtColor` intermediate — invertono R e B

### INA219 — monitor batteria
- Indirizzo 0x40, shunt R100 (0.1Ω) — in serie al positivo tra alimentazione e scheda Yahboom
- Corrente positiva = DISCHARGING, negativa = CHARGING
- `battery_node.py`: pubblica `/battery` (BatteryState) + `/battery/stats` (BatteryStats custom) ogni 2s
- Potenza calcolata come V×I (registro power INA219 non calibrato)

### TOF400C VL53L1X — obstacle avoidance
- TCA9548A multiplexer: indirizzo 0x70
- Canali REALI: frontale→CH2, sinistro→CH3, destro→CH4 (NON CH0/CH1/CH2)
- CH4 ha problema cablaggio — da risolvere
- Architettura: `tof_node.py` → `/tof/front|left|right` → `avoidance_node.py` → `/cmd_vel`
- Soglie: 50cm=rallenta, 40cm=pivot

### Package hold — NON aggiornare ROS2
Entrambi i sistemi hanno ~290 package ROS2 in hold a v16.0.19.
Per sbloccare solo se necessario:
```bash
dpkg -l | grep "^ii  ros-humble-" | awk '{print $2}' | xargs sudo apt-mark unhold
```

### Servizi systemd su hawk
- `apss-oled.service` — service indipendente, `After=network-online.target`, utente `hawk`
  - Avvia: `ros2 run <pkg> oled_node`
  - `Restart=on-failure`, `RestartSec=5`
  - Indipendente da `apss_lidar.launch.py` — sfrutta watchdog/fallback già in `oled_node.py`
- `apss-lidar-standby.service` — `disabled`, mai effettivamente eseguito al boot (deprioritizzato)

### File di test
Tutti i nuovi script di test vanno in `rosmaster_project/test_files/`

## Documentazione estesa
- `@docs/architecture.md` — architettura completa hardware e software
- `@docs/plan.md` — roadmap con stato avanzamento (v2.3)
- `APSS_memorie.md` — memorie di sessione (v1.2)
- Documentazione tecnica completa: `APSS_Documentazione_Tecnica_v2_1.docx`
