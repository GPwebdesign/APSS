# APSS — Autonomous Patrol and Surveillance System
## Riepilogo sessione per nuova chat — 02 Maggio 2026

Contesto: Robot autonomo di pattugliamento basato su Yahboom Rosmaster R2 + Raspberry Pi 4 (hawk, 192.168.1.158, Ubuntu 22.04, ROS2 Humble). VM sviluppo: gp68-vmware (192.168.1.80). Repository: `rosmaster_project` e `ros2_py_ws` (GitHub GPwebdesign privati).

**WORKFLOW:** Modifiche su VM → commit/push → pull su Pi. MAI modificare direttamente sul Pi. File del progetto: cercare SEMPRE su GitHub, MAI su Google Drive (Drive ha versioni vecchie).

---

## Hardware robot

Struttura proprietaria GPwebdesign con componenti Yahboom (scheda STM32, 4 motori DC Mecanum). M1/M4 polarità invertita fisicamente. Ruote Mecanum configurazione X. Calibrazione motori: m1=0.60 (motor_calibration.json sul Pi). Speed base=55. Cinematica custom Python: M1=vx-vy+vz, M2=vx+vy-vz, M3=vx+vy+vz, M4=vx-vy-vz. Strafe laterale puro non ottenibile — mantenuto come rotazione stretta.

---

## App Kivy

Kivy 2.3.1 + KivyMD 1.2.0, dark, portrait. Stream MJPEG http://192.168.1.158:6500/video_feed 31FPS. Pad 3x3 con slider velocità 0.5-1.0 per forward/backward. CameraScreen con pan/tilt (home graduale), foto JPG timestamp, video sequenza JPG in rosmaster_kivy/save/. Titolo: "APSSystem" / "Autonomous Patrol and Surveillance System".

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

thread_odom in rosmaster_main.py pubblica /odom e tf dinamico odom→base_footprint. ENCODER_CPR=822 (misurato fisicamente su M2). WHEEL_RADIUS=0.0395m. sep_x=0.078m, sep_y=0.105m. Avviare con `python3` di sistema (non sudo venv) per avere rclpy disponibile.

---

## RPLIDAR A1M8

/dev/ttyUSB1, offset 90°. Driver ros-humble-rplidar-ros v2.1.4 in hold. Topic /scan ~7.7Hz. slam_toolbox installato in modalità mapping. Mappe salvate in ros2_py_ws/maps/.

---

## Obstacle avoidance — DECISIONE DEFINITIVA

OpenCV abbandonato. Sistema primario: 3x TOF400C VL53L1X (frontale 0°, sx 30°, dx 30°) + 1 scorta. Multiplexer TCA9548A (TOF1→CH0, TOF2→CH1, TOF3→CH2, TOF4→CH3). Architettura: tof_node pubblica /tof/front /tof/left /tof/right → avoidance_node decide → /cmd_vel → rosmaster_main.py subscriber. Soglie: 50cm=rallenta, 40cm=ruota pivot.

---

## rosmaster_main.py — Stato attuale (Maggio 2026)

- Versione V2.3.3 — 1115 righe
- RIMOSSI (Maggio 2026): RosImage import, g_image_pub, g_ros_node globals, publish_image_frame(), thread_image_publisher(), task_image in main
- thread_odom: odometria encoder operativa, image_pub rimosso
- thread_camera: alimenta g_latest_frame con frame RGB nativo
- Endpoint /video_feed: stream MJPEG operativo, colori corretti
- Endpoint /capture_still: JPEG qualità 95, download su client
- cmd 0x1A: controllo motori Mecanum via TCP (da testare/verificare)

---

## Docking station ESP32

Firmware v2.0 operativo. Dashboard http://192.168.1.193. INA219, reed GPIO18 NC, relay CH1 GPIO5, blackout GPIO34. Circuito ricarica: XL4016 14.82V/0.9A, XHM603 START=12.2V STOP=14.7V (compensati).

---

## Roadmap

### Completati (Maggio 2026)
1. ✅ Rimozione codice OpenCV obstacle avoidance + thread_image_publisher da rosmaster_main.py
2. ✅ Semplificazione camera_params.json — solo profilo streaming
3. ✅ Endpoint /capture_still per foto qualità still
4. ✅ Fix pipeline colore camera: RGB nativo picamera2, nessuna conversione intermedia

### Prossimi step
4. Build app Kivy per Android (Buildozer)
5. Sessione mapping SLAM studio con app Android
6. Integrazione TOF400C VL53L1X via TCA9548A

### Futuri
- Nav2 navigazione autonoma
- Pattugliamento autonomo con waypoint
- Docking autonomo ArUco
- pan_tilt_node.py ROS2 + cmd TCP 0x1B per pan/tilt dall'app
- Verifica strafe dopo rimontaggio ruote Mecanum in X

---

## Pending items

- TCP cmd `0x1B` per pan/tilt da Kivy (payload: pan+tilt 2 byte 0-180)
- `pan_tilt_node.py` ROS2 con subscriber `/pan_tilt/cmd`
- Verifica strafe laterale puro dopo rimontaggio ruote Mecanum
- Backup su USB disk via SMB (path e credenziali pendenti)
- Microswitch docking station (NC, GPIO18, stesso cablaggio reed)
- Ripristino aggiornamenti ROS2 Humble su hawk dopo hold config completa
