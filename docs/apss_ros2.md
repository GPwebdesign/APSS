# APSS — Struttura ROS2 su hawk
> Aggiornato: Maggio 2026

---

## Ambiente

- ROS2 distro: `humble`
- Host: hawk (192.168.1.158, Ubuntu 22.04, Raspberry Pi 4)
- Shell: bash

## Workspace

| Workspace | Path assoluto | Setup.bash |
|-----------|--------------|------------|
| ROS2 base | `/opt/ros/humble` | `/opt/ros/humble/setup.bash` |
| Workspace principale | `/home/hawk/Workspaces/ros2_py_ws` | `~/Workspaces/ros2_py_ws/install/setup.bash` |
| Driver workspace | `/home/hawk/driver_ws` | `~/driver_ws/install/setup.bash` |

⚠️ Path workspace: `~/Workspaces/ros2_py_ws/` con **W maiuscola** — NON `~/ros2_py_ws/`

Tutti e tre sourced in `~/.bashrc` — disponibili in sessioni interattive ma **NON in systemd**.
Ogni service systemd deve fare source esplicito.

## Package principale

| Campo | Valore |
|-------|--------|
| Nome | `apss_ros2_pkg` |
| Tipo build | `ament_cmake` |
| Path sorgente | `/home/hawk/Workspaces/ros2_py_ws/src/apss_ros2_pkg/` |
| Path install | `/home/hawk/Workspaces/ros2_py_ws/install/apss_ros2_pkg/` |
| Build file | `CMakeLists.txt` (no `setup.py`) |

## Nodi

| Nodo | Comando esatto | File sorgente | Stato |
|------|---------------|---------------|-------|
| `oled_node` | `ros2 run apss_ros2_pkg oled_node.py` | `scripts/oled_node.py` | ✅ funzionante — subscriber `/apss/oled_alert` (scrolling messaggi allarme sulla prima riga); scrolling `/apss/oled_alert` sulla riga 0 — reset solo su cambio testo, velocità 8px/tick, prefisso APSS |
| `battery_node` | `ros2 run apss_ros2_pkg battery_node.py` | `scripts/battery_node.py` | ✅ funzionante |
| `safety_node` | `ros2 run apss_ros2_pkg safety_node.py` | `scripts/safety_node.py` | ✅ funzionante |
| `alarm_node` | `ros2 run apss_ros2_pkg alarm_node.py` | `scripts/alarm_node.py` | ✅ funzionante |
| `obstacle_detector_node` | `ros2 run apss_ros2_pkg obstacle_detector_node.py` | `scripts/obstacle_detector_node.py` | 🔲 da sviluppare |
| `navigation_controller_node` | `ros2 run apss_ros2_pkg navigation_controller_node.py` | `scripts/navigation_controller_node.py` | 🔲 da sviluppare |
| `camera_publisher` | `ros2 run apss_ros2_pkg camera_publisher.py` | `scripts/camera_publisher.py` | 🔲 da sviluppare |

⚠️ L'estensione `.py` è **obbligatoria** nel comando — il build ament_cmake installa i file con estensione.

## Messaggi custom

| Tipo | File | Usato da |
|------|------|----------|
| `apss_ros2_pkg/msg/BatteryStats` | `msg/BatteryStats.msg` | `battery_node.py` → topic `/battery/stats` |

## Topic principali

| Topic | Tipo | Produttore | Consumatore |
|-------|------|-----------|-------------|
| `/battery` | `sensor_msgs/BatteryState` | `battery_node` | `oled_node`, `safety_node` |
| `/battery/stats` | `apss_ros2_pkg/BatteryStats` | `battery_node` | — |
| `/apss/alarm` | `std_msgs/String` (JSON) | `safety_node` | `alarm_node`, `rosmaster_main.py` |
| `/apss/oled_alert` | `std_msgs/String` (JSON) | `alarm_node` | `oled_node` |
| `/scan` | `sensor_msgs/LaserScan` | `rplidar_node` | `slam_toolbox` |
| `/odom` | `nav_msgs/Odometry` | `rosmaster_main.py` (thread_odom) | `slam_toolbox` |
| `/cmd_vel` | `geometry_msgs/Twist` | `avoidance_node` (pianificato) | `rosmaster_main.py` |
| `/tof/front` `/tof/left` `/tof/right` | `sensor_msgs/Range` | `tof_node` (pianificato) | `avoidance_node` |

`/apss/oled_alert`: JSON `{messages, scroll}` — scrolling riga 0 OLED. Reset posizione solo se testo cambia.

## File di configurazione

| File | Path nel package | Caricato da |
|------|-----------------|-------------|
| `safety_rules.yaml` | `config/safety_rules.yaml` | `safety_node.py`, `alarm_node.py` |

Il file contiene due sezioni principali:
- `global` + `rules`: regole di rilevamento allarmi per safety_node
- `alarm_node`: configurazione reazioni — language (it/en), voice_enabled, alsa_device, voice_models IT/EN, source_labels IT/EN, templates per livello, beep_patterns, log_path, log_max_entries

Installato via CMakeLists.txt con `install(DIRECTORY config ...)`.
Caricato a runtime via `get_package_share_directory('apss_ros2_pkg')`.

## Servizi systemd

| Service | Comando ExecStart | Stato |
|---------|-------------------|-------|
| `apss-oled.service` | `ros2 run apss_ros2_pkg oled_node.py` | ✅ installato, enabled, funzionante al boot |
| `apss-lidar-standby.service` | — | ⛔ disabled (non funzionante) |

### Template ExecStart per service systemd
```ini
ExecStart=/bin/bash -lc 'source /opt/ros/humble/setup.bash && source /home/hawk/Workspaces/ros2_py_ws/install/setup.bash && exec ros2 run apss_ros2_pkg <nodo>.py'
```

## Launch file

| File | Path | Avvia |
|------|------|-------|
| `apss_lidar.launch.py` | `src/apss_ros2_pkg/launch/` | RPLIDAR + robot_state_publisher + slam_toolbox + RViz2 |

## Ordine avvio manuale

```bash
# 1. Prima — TCP server Yahboom
python3 ~/Workspaces/rosmaster_project/rosmaster_main.py

# 2. Poi — stack ROS2
ros2 launch apss_ros2_pkg apss_lidar.launch.py
```

## Note critiche

- `colcon build` da: `cd /home/hawk/Workspaces/ros2_py_ws && colcon build`
- Dopo build: `source install/setup.bash` obbligatorio nella sessione corrente
- `build/`, `install/`, `log/` NON sono nel repo git
- Package precedente `udemy_ros2_pkg` → rinominato `apss_ros2_pkg` (Maggio 2026)
