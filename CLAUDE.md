# APSS — Autonomous Patrol and Surveillance System

## Cosa è questo progetto
Robot autonomo di pattugliamento e sorveglianza per interni (appartamento).
Piattaforma custom con componenti Yahboom Rosmaster R2, Raspberry Pi 4, ROS2 Humble.

## Architettura in una riga
`RPi4 (hawk)` → ROS2 Humble + rosmaster_main.py (TCP server) → Kivy App (Android/Linux) via WiFi

## Repository e path critici

| Sistema | Path | Ruolo |
|---------|------|-------|
| RPi4 `hawk` (192.168.1.158) | `~/rosmaster_project/` | Server TCP, camera, pan/tilt, odometria |
| RPi4 `hawk` | `~/Workspaces/ros2_py_ws/` | Stack ROS2: URDF, launch, SLAM, RViz2 |
| VM `gp68-vmware` (192.168.1.80) | `/home/gp68/rosmaster_project/` | Mirror sviluppo (stesso codice) |
| VM `gp68-vmware` | `/home/gp68/ros2_py_ws/` | Mirror sviluppo ROS2 |
| Docking station ESP32 | `http://192.168.1.193` | Dashboard MicroPython, INA219, relay |

## Regole essenziali per Claude Code

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
- Home: Pan=100°, Tilt=95° (non 90/90)
- Calibrazione: `pan_tilt_presets.json`

### Package hold — NON aggiornare ROS2
Entrambi i sistemi hanno ~290 package ROS2 in hold a v16.0.19.
Per sbloccare solo se necessario:
```bash
dpkg -l | grep "^ii  ros-humble-" | awk '{print $2}' | xargs sudo apt-mark unhold
```

### File di test
Tutti i nuovi script di test vanno in `rosmaster_project/test_files/`

## Documentazione estesa
- `@docs/architecture.md` — architettura completa hardware e software
- `@docs/plan.md` — roadmap con stato avanzamento
- Documentazione tecnica completa: `APSS_Documentazione_Tecnica_v1_9.docx`
