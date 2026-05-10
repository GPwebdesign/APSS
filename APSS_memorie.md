# APSS — Memorie di sessione
> Revisione v1.1 — Maggio 2026

---

## #1 — Username sistemi
Username su hawk è `hawk` (non gp68). Home: `/home/hawk/`.
Username su VM gp68-vmware è `gp68`.

---

## #2 — Firmware ESP32 v2.0
Firmware ESP32 "fw test da banco" v2.0 **CONSOLIDATO** (Apr 2026).
File: `boot.py`, `config.json`, `ina219.py`, `main.py`.
Features: webserver dashboard `http://192.168.1.193`, NTP pool.ntp.org, INA219 ogni 2s, IRQ reed GPIO18, blackout GPIO34, relay CH1 GPIO5.
Corrente positiva = ricarica, negativa = flusso inverso normale.
Dashboard: data/ora reale, V/I/W, badge NTP/INA/relay/reed/grid, log timestamp.
Programmazione via USB Thonny con cavo lungo fisso sulla breakout.

---

## #3 — Pan/Tilt
Pan/tilt **CONSOLIDATO** (Apr 2026). S1=Tilt, S2=Pan (swap fisico).
Fili: marrone=GND, rosso=VCC, arancione=PWM.
`calibrate_pan_tilt.py`: frecce tty, INVIO=home 90/90, 1-5 preset, salva JSON.
`control_pan_tilt.py`: legge JSON, frecce ±5°, INVIO=home lento (5°/0.1s), 1=tour PAN, 2=tour TILT, 3=combinato, sweep 3°/0.05s, slow_move 5°/0.1s.

---

## #4 — App Kivy
App Kivy **CONSOLIDATA** (Apr 2026). Kivy 2.3.1 + KivyMD 1.2.0, dark, portrait.
TCP 0x1A set_motor, cinematica Mecanum Python, speed base=55.
Slider velocità 0.5-1.0 forward/backward. Rotate factor=0.8, strafe factor=0.9.
CameraScreen: pan/tilt home graduale, foto JPG timestamp, video sequenza JPG.
Fix: `cmd.upper()` in `parse_data`.
Pan/tilt controllato via cmd `0x11` nativo Yahboom — cmd `0x1B` NON necessario.
Strafe laterale puro **ABBANDONATO** — non ottenibile anche con ruote in configurazione X.

---

## #5 — Nome progetto
APSS = **Autonomous Patrol and Surveillance System**.
Il progetto usa hardware Yahboom Rosmaster R2 ma il sistema si chiama APSS.
Tutta la documentazione, app e comunicazioni usano APSS.
L'app Kivy mostra "APSSystem" nella toolbar e "Autonomous Patrol and Surveillance System" come titolo finestra.

---

## #6 — Sorgenti Yahboom
Sorgenti Yahboom sulla VM (gp68-vmware): `/home/gp68/ROS-robot-expansion-board`
→ contiene `rosmaster_main.py`, `Rosmaster_Lib.py`, `wifi_rosmaster.py` e tutta la libreria Yahboom originale.
Sul robot (hawk): `~/Workspaces/rosmaster_project/`.

---

## #7 — Struttura rosmaster_project
Struttura `rosmaster_project` (Apr 2026):

**Root:** `rosmaster_main.py`, `camera_rosmaster.py`, `calibrate_pan_tilt.py`, `control_pan_tilt.py`, `CHANGELOG.md`, `pan_tilt_presets.json`, `camera_params.json`, `motor_calibration.json`, `requirements.txt`.

**Cartelle:** `rosmaster_kivy/` (main.py, rosmaster.kv, network/tcp_client.py, screens/, tools/frames_to_mp4.py, save/), `test_files/`, `static/`, `templates/`, `pre_modifica/`.

> Tutti i nuovi test in `test_files/`.

---

## #8 — RPLIDAR A1M8
RPLIDAR A1M8 **CONSOLIDATO** (Apr 2026): `/dev/ttyUSB1`, offset fisico 90°.
Driver ROS2 `ros-humble-rplidar-ros` v2.1.4 in hold. Topic `/scan` ~7.7Hz.
URDF + tf tree completati. Launch file `apss_lidar.launch.py` operativo. `slam_toolbox` installato.
Odometria encoder integrata in `rosmaster_main.py` (`thread_odom`).
`ENCODER_CPR=822` misurato fisicamente. `WHEEL_RADIUS=0.0395m`. `sep_x=0.078m`, `sep_y=0.105m`.

---

## #9 — Stack ROS2
Stack ROS2 APSS **CONSOLIDATO** (Apr 2026):
URDF `apss_robot.urdf.xml`. Launch file `apss_lidar.launch.py` avvia: RPLIDAR + robot_state_publisher + tf statico map→odom + slam_toolbox + RViz2.
tf `odom→base_footprint` dinamico da `thread_odom` in `rosmaster_main.py`.
Config RViz2: `rviz/apss.rviz`. Display OLED SSD1306 0x3C operativo con `oled_node.py`.

**Ordine avvio:**
1. `python3 rosmaster_main.py`
2. `ros2 launch apss_lidar.launch.py`

---

## #10 — Hardware installato (TOF + INA219)
HW **INSTALLATO** (Mag 2026): 3x TOF400C VL53L1X + TCA9548A.

| Sensore | Posizione | Canale TCA9548A |
|---|---|---|
| TOF frontale | 0° | CH2 |
| TOF sinistro | 30° | CH3 |
| TOF destro | 30° | CH4 ⚠️ problema cablaggio |

INA219 `0x40` in serie al positivo.
Corrente positiva = DISCHARGING, negativa = CHARGING.
`battery_node.py`: pubblica `/battery` (BatteryState) e `/battery/stats` (BatteryStats — min/max V/I/P + sample_count).
Soglie TOF: 50cm = rallenta, 40cm = pivot.

---

## #11 — Camera
Camera **CONSOLIDATA** (Mag 2026): OV5647 IR-cut auto.
`camera_params.json`: SOLO profilo streaming (vision rimosso).
`camera_rosmaster.py`: picamera2 restituisce RGB nativo, nessuna conversione in `get_frame()`.
`mode_handle()`: nessuna conversione — RGB → imencode → MJPEG → Kivy `colorfmt=rgb`.
`/capture_still` su porta 6500: JPEG qualità 95.
Pan home=100°, tilt home=85°.

---

## #12 — Roadmap aggiornata
Roadmap aggiornata (Mag 2026):

**Completati:**
1. ✅ Rimozione OpenCV + thread_image_publisher
2. ✅ Semplificazione camera_params.json
3. ✅ Endpoint /capture_still
4. ✅ battery_node.py con /battery e /battery/stats
5. ✅ BatteryStats.msg custom

**Prossimi:** Fix cablaggio TOF CH4 → `tof_node.py` → `avoidance_node.py` → `rosmaster_main.py` subscriber `/cmd_vel`. Poi: Build Kivy Android, Mapping SLAM.

---

## #13 — Architettura software TOF
Architettura software TOF **CONFERMATA** (Mag 2026):
`tof_node` pubblica misure, `avoidance_node` decide azione, `rosmaster_main.py` subscriber `/cmd_vel`.
Topic: `sensor_msgs/Range` — `/tof/front`, `/tof/left`, `/tof/right`.
Canali REALI TCA9548A: frontale→CH2, sx→CH3, dx→CH4 (**NON** CH0/CH1/CH2 come pianificato inizialmente).
Bridge TOF→LaserScan per nav2 costmap: futuro.

---

## #14 — Fonte file di progetto
⚠️ **IMPORTANTE**: Per cercare file del progetto APSS usare **SEMPRE GitHub** (repo `GPwebdesign/rosmaster_project` e `GPwebdesign/ros2_py_ws`) — **MAI Google Drive**. I file su Drive sono spesso versioni vecchie non aggiornate.

---

## #15 — Struttura repo PC
Progetto APSS — struttura repo PC (Mag 2026):
Repo principale `github.com/GPwebdesign/APSS` (privato, branch master) in `D:\_claudecodeproject\APSS\`.
Contiene: `CLAUDE.md`, `CLAUDE.local.md`, `.gitignore`, `subtree-pull.bat`, `docs/`, `.claude/skills/apss_tcp_protocol/`.
`rosmaster_project` e `ros2_py_ws` sono subtree.
Filesystem MCP attivo (allowed: `D:\_claudecodeproject`). Claude può leggere e modificare file direttamente sul PC.

---

## #16 — Workflow allineamento
Workflow allineamento APSS (Mag 2026):
- **hawk**: usa `~/Workspaces/apss-push.sh` (menu 1=rosmaster_project, 2=ros2_py_ws, 3=entrambi; SSH; non tracciato da git)
- **PC**: usa `subtree-pull.bat` (menu pull subtree + push APSS automatico + check `docs/` e `.claude/skills/` non committati all'avvio)

File `.md` e skill vivono solo in APSS sul PC. `subtree-pull.bat` controlla `docs/` intera (non solo .md) e `.claude/skills/`.

---

## #17 — Bug NoMachine
🐛 **BUG NoMachine su hawk**: quando un monitor fisico è collegato via HDMI al Pi, NoMachine rallenta drasticamente il mouse.
**Soluzione**: scollegare il monitor HDMI — il mouse si normalizza immediatamente.

---

## #18 — Sostituzione batteria (ACQUISTATA)
Sostituzione batteria APSS (Mag 2026):
**YTZ10S piombo 8.6Ah → ECO-WORTHY 12V 8Ah LiFePO4 (B0CCJ8JJV3) ACQUISTATA a 50€ Amazon.it.**

| Parametro | Valore |
|---|---|
| Dimensioni reali | 152 × 65 × 96 mm |
| Compatibilità vano APSS | ✅ OK (vano libero su tutti i lati) |
| Peso | 1,05 kg (-2,15 kg vs YTZ10S) |
| Autonomia attesa | ~7-8h mista |
| Corrente idle (INA219) | 0,65 A / 7,7 W |
| Picco movimento (INA219 0.5Hz) | 2,14 A / 25,7 W |
| Picchi reali stimati | 3-4 A (sub-secondo, non catturati a 0.5Hz) |

Stato: **in attesa consegna** per Fase D implementazione.

---

## #19 — Fase D (da eseguire all'arrivo batteria)
Fase D batteria LiFePO4 — **da eseguire quando la batteria arriva**:

1. **Ricalibrare XL4016** da 14,82V a 14,4-14,5V (max LiFePO4 = 14,6V)
2. **Aggiornare `battery_node.py`** con tabella SoC LiFePO4 (curva piatta, plateau ~13,1-13,2V) — valutare coulomb counting
3. **Nuove soglie START/STOP** in ESP32 `config.json`
4. **Aggiornare documentazione**: `architecture.md` Sez.3, `Documentazione_Tecnica v2.2`, `CHANGELOG.md`

**Verifiche pre-collegamento:**
- Tensione a vuoto attesa: 13,0-13,4V
- Verificare polarità terminali con tester
- Verificare tipo terminali (F1/F2)
- Foto etichetta per archivio
- ⚠️ NON collegare al XL4016 prima della ricalibrazione

---

*Esportato il 10 Maggio 2026 — APSS GPwebdesign*
