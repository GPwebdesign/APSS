# APSS — Autonomous Patrol and Surveillance System
## Riepilogo sessione per nuova chat — Maggio 2026

Contesto: Robot autonomo APSS su Yahboom Rosmaster R2 + Raspberry Pi 4 (hawk, 192.168.1.158,
Ubuntu 22.04, ROS2 Humble). VM sviluppo: gp68-vmware. Repo: `rosmaster_project` e `ros2_py_ws`
(GitHub GPwebdesign privati). Workflow: modifiche codice su VM → push GitHub → pull hawk → test.
Doc solo su PC `D:\_claudecodeproject\APSS\` → push APSS.

---

## Completati in questa sessione

- ✅ Package ROS2 rinominato `udemy_ros2_pkg` → `apss_ros2_pkg` — build pulita, 7 packages
- ✅ Script e srv Udemy eliminati — codebase pulita
- ✅ `CMakeLists.txt` ripulito — solo nodi APSS reali
- ✅ `apss-oled.service` installato, enabled, funzionante al boot (Main PID 1027 post-reboot)
- ✅ Allineamento APSS: `APSS_memorie.md`, `CLAUDE.md`, `plan.md` (v2.7), `architecture.md`
- ✅ `apss_ros2.md` creato — memoria permanente struttura ROS2
- ✅ Repo allineati: `ros2_py_ws` commit `dd2cefd`, APSS commit `9322a60`

## Note critiche emerse oggi

- Path workspace hawk: `~/Workspaces/ros2_py_ws/` (**W maiuscola**) — NON `~/ros2_py_ws/`
- Eseguibile richiede estensione: `ros2 run apss_ros2_pkg oled_node.py` (non `oled_node`)
- Package è `ament_cmake` (non `ament_python`) — nessun `setup.py`, build via `CMakeLists.txt`

## Hardware robot

- RPLIDAR A1M8: **in reso** (linea TX morta). Sostituto in arrivo.
- TOF400C VL53L1X: tutti e 3 OK (CH2/CH3/CH4). Pronti per `tof_node.py`.
- INA219 0x40: operativo. Fallback in `oled_node.py` con watchdog 5s su `/battery`.
- OLED SSD1306: funzionante via service systemd al boot. Asterisco visibile senza `battery_node`.
- Batteria ECO-WORTHY LiFePO4: catena misurata:
  ECO-WORTHY 13.09V → DD32AJ4B (12.16V vuoto / 11.70V carico) → INA219 → Yahboom 11.58V.

## Stack ROS2

| Nodo | Comando | Stato |
|------|---------|-------|
| `oled_node` | `ros2 run apss_ros2_pkg oled_node.py` | ✅ funzionante + service boot |
| `battery_node` | `ros2 run apss_ros2_pkg battery_node.py` | ✅ funzionante |
| `safety_node` | `ros2 run apss_ros2_pkg safety_node.py` | 🔲 pianificato |
| `slam_toolbox` | — | ⚠️ da reinstallare su hawk |

## Servizi systemd su hawk

| Service | Stato |
|---------|-------|
| `apss-oled.service` | ✅ enabled, active (running), boot verificato |
| `apss-lidar-standby.service` | ⛔ disabled |

## Soglie ricarica (Fase 1 — voltage based)

| Livello | Tensione | SoC stimato | Azione |
|---------|----------|-------------|--------|
| 🟡 LOW | 11.50V | ~30% | Completa task, rientra |
| 🟠 CRITICAL | 11.20V | ~15% | Interrompe task, rientra — trigger SOS beeper |
| 🔴 EMERGENCY | 10.80V | ~5% | Stop ovunque, attende recupero |

SOS beeper: morse ···---··· via scheda Yahboom, 3 ripetizioni a 3s — da implementare in `safety_node.py`.

## Prossimi step (in ordine)

1. Reinstallare `ros-humble-slam-toolbox` su hawk
2. `battery_node` + `oled_node` nel launch file + test integrato OLED (asterisco scompare)
3. Verifica pacchetti pip post-restore SD (`adafruit-circuitpython-*`, `picamera2`, ecc.)
4. Test RPLIDAR sostituto al ricevimento
5. Progettazione e implementazione `safety_node.py`
6. `tof_node.py` + `avoidance_node.py` + subscriber `/cmd_vel` in `rosmaster_main.py`
7. Test APK Android Samsung S23 Ultra
8. Fase D batteria LiFePO4 (fusibile T3A, CC 2A, soglie XHM603 definitive)

## Pending items

| Item | Priorità | Note |
|------|----------|------|
| ⚠️ RPLIDAR A1M8 in reso | Alta | Sostituto in arrivo |
| Reinstallare `ros-humble-slam-toolbox` | Alta | Pre-SLAM obbligatorio |
| Test asterisco OLED scompare con battery_node | Media | `battery_node` nel launch file |
| Verificare pacchetti pip post-restore | Media | `adafruit-circuitpython-*`, `picamera2`, ecc. |
| Test APK S23 Ultra | Media | APK 2.1 pronto |
| Fase D batteria | Media | Fusibile T3A, CC 2A, soglie XHM603 |
| Bug `[ODOM] publisher's context is invalid` | Bassa | Cosmetico, non bloccante |
| Bug Video MainScreen primo `on_enter` | Bassa | Workaround Home→Camera→Home |
