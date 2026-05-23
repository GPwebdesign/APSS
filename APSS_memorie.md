# APSS — Memorie di sessione
> Revisione v1.2 — Maggio 2026

---

## Sessione 23 Maggio 2026
- Bug video MainScreen risolto: TCP server bind su `0.0.0.0` invece di IP specifico — connessione con IP default senza passare da Settings
- APK Android v2.1: `ModuleNotFoundError: No module named 'filetype'` risolto aggiungendo `filetype` ai requirements buildozer
- App Android funzionante su S23 Ultra: connessione, video MainScreen, CameraScreen, cambio schermata
- `camera_screen.py`: salvataggio foto/video in `/sdcard/DCIM/APSSystem/` (visibile in galleria), popup conferma foto, popup Salva/Annulla video con rinomina, notifica MediaStore
- Icona app personalizzata `APSS_logo_black.png` → `icon.png` in `rosmaster_kivy/`, configurata in `buildozer.spec`
- `buildozer.spec` aggiunto al repo `rosmaster_project` con `.gitignore` aggiornato per includere `icon.png`
- `static_img/` aggiunta al repo APSS (APSS_logo_black.png, APSS_logo_white.png + sorgenti .ai/.psd)
- Verifica I2C post-scarica statica: OLED 0x3c ✅, INA219 0x40 ✅, TCA9548A 0x70 ✅, tutti e 3 TOF 0x29 ✅
- VM Buildozer: git configurato (rinopcode@gmail.com / GPwebdesign), token aggiornato
- Regola memoria: riepilogo sessione è solo append in cima, sessioni precedenti intatte
- `apss_ros2.md` creato in `docs/` — memoria permanente struttura ROS2 su hawk

---

## Sessione 22 Maggio 2026
- Package ROS2 rinominato `udemy_ros2_pkg` → `apss_ros2_pkg` — build pulita, 7 packages finished
- Script Udemy eliminati: `publisher.py`, `subscriber.py`, `rpm_pub.py`, `rpm_sub.py`, `speed_calc.py`, `speed_calc_no_ param.py`, `service_client.py`, `service_server.py`, `turn_camera_client.py`, `turn_camera_server.py`
- Srv Udemy eliminate: `OddEvenCheck.srv`, `TurnCamera.srv` — `BatteryStats.msg` mantenuta
- `CMakeLists.txt` ripulito — solo script APSS reali nell'`install()`
- Path workspace corretto confermato: `~/Workspaces/ros2_py_ws/` (W maiuscola, NON `~/ros2_py_ws/`)
- `apss-oled.service` installato e funzionante al boot — `Main PID: 1027`, `active (running)` post-reboot
- Eseguibile richiede estensione: `ros2 run apss_ros2_pkg oled_node.py` (non `oled_node`)
- File memoria ROS2 `apss_ros2.md` da creare (rimandato)
- Repo allineati: `ros2_py_ws` commit `dd2cefd`, APSS commit `9322a60`

---

## Sessione 18 Maggio 2026
- RPLIDAR A1M8 hardware guasto — reso autorizzato, sostituto in arrivo. Diagnosi: linea TX lidar morta (cavetto interno testa↔PCB o chip CP2102 TX). Test Python bare-metal con DTR=False: STOP+GET_INFO+GET_HEALTH → 0 bytes risposta
- `ros-humble-slam-toolbox` da reinstallare su hawk (perso nel restore SD Aprile) — priorità Alta prima della sessione SLAM
- `oled_node.py` riadattato: fallback INA219 diretto + watchdog 5s su `/battery`, layout SSD1306 128x64 con asterisco se lettura diretta INA219, rimosso `/apss/battery` JSON legacy — testato e funzionante su hawk
- `luma.oled` 3.15.0 reinstallato post-restore SD
- Catena alimentazione misurata: ECO-WORTHY 13.09V → DD32AJ4B setpoint 12.16V (a vuoto) / 11.70V (sotto carico, 0.46V load regulation) → INA219 → Yahboom 11.58V. Setpoint confermato — non modificare
- 3 soglie ricarica voltage-based definite: LOW 11.50V (~30% SoC) / CRITICAL 11.20V (~15% SoC) / EMERGENCY 10.80V (~5% SoC) — da implementare in `patrol_node.py`
- `apss-lidar-standby.service`: installato ma motore RPLIDAR non si ferma — deprioritizzato
- Pacchetti pip post-restore da verificare proattivamente (`adafruit-circuitpython-*`, `picamera2`, ecc.)
- Architettura `safety_node` concordata: nodo dedicato per tutti gli allarmi (beeper, soglie batteria, sensori futuri)
- Soglia SOS batteria: 11.20V (CRITICAL) — allarme acustico contestuale al rientro forzato
- `apss-oled.service`: service systemd indipendente (opzione A) con `After=network-online.target` — sfrutta fallback INA219 + watchdog già in `oled_node.py`
- Beeper fisico: su scheda Yahboom (confermato, non GPIO Raspberry)
- `oled_node.py`: nessuna modifica codice oggi — prima il service, poi `safety_node`

---

## Sessione 15 Maggio 2026
- TOF CH4 risolto: sensore originale difettoso sostituito con scorta — tutti e 3 i TOF verificati OK (0x29)
- Libreria `adafruit-circuitpython-vl53l1x` v1.2.9 installata su hawk — approccio smbus2+busio.I2C verificato su tutti i canali
- `APSS_Documentazione_Tecnica_v2_3.docx` generata — struttura v1.9 ripristinata, sezione 11.1 Sviluppo Futuro inclusa
- Cartella `Siti Web Rino` rimossa erroneamente da `D:\_claudecodeproject\APSS\` — rimossa manualmente
- Repo allineati: APSS commit `b1a1f19`, rosmaster_project e ros2_py_ws aggiornati
- Prossimo step: `tof_node.py`

---

## Sessione 10 Maggio 2026
- `apss-lidar-standby.service` installato e abilitato su hawk — utente `hawk` aggiunto a gruppo `dialout`
- `apss_lidar_standby.py`: script stop motore RPLIDAR al boot (CMD_STOP + CMD_MOTOR) — ⚠️ motore riparte ancora, delay 3s + retry in test
- `oled_node.py`: aggiunto subscriber `/battery` (BatteryState) per ricevere dati reali da `battery_node.py` — topic `/apss/battery` (JSON) mantenuto per compatibilità
- `plan.md` aggiornato a v2.3, `architecture.md` aggiornato con tabella topic e sezione systemd
- Workflow APSS consolidato: VM→hawk→PC→push. MAI modificare codice sul PC.
- Skill `allinea-apss` creata in `.claude/skills/allinea-apss/SKILL.md`
- Test assorbimento INA219: 89 campioni — idle 0.63A/7.7W, picco 2.14A/25.7W
- Tutti e tre i repo allineati su: rosmaster_project `7945ca8`, ros2_py_ws `ee6fa7d`, APSS `bb5ddd2`

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

| Sensore | Posizione | Canale TCA9548A | Stato |
|---|---|---|---|
| TOF frontale | 0° | CH2 | ✅ OK (0x29) |
| TOF sinistro | 30° | CH3 | ✅ OK (0x29) |
| TOF destro | 30° | CH4 | ✅ OK (0x29) — sensore originale difettoso, sostituito con scorta |

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

## #19 — Fase D (batteria LiFePO4 — IN CORSO)
Fase D batteria LiFePO4 — **parzialmente completata**:

1. ✅ **XL4016 ricalibrato** da 14,82V a 14,40V
2. ✅ **Soglie XHM603 conservative:** STOP=14,2V / START=13,1V display
3. ✅ **Prima ricarica parziale completata** — OCV post-carica 13,27V (~85-90% SoC)
4. ⚠️ **Fusibile** T1,5A → T3A slow-blow (da sostituire prima di alzare CC a 2A)
5. ⚠️ **Ricalibrazione CC** da 0,9A a 2A
6. ⚠️ **Soglie XHM603 definitive** da verificare dopo ciclo completo
7. ⚠️ **Installazione fisica** ECO-WORTHY nel robot
8. ⚠️ **Software:** `battery_node.py` tabella SoC LiFePO4 + ESP32 `config.json`

Offset catena misurato: display XHM603 vs terminali = +0,70V, INA219 vs terminali = +0,34V.

---

## #20 — NotebookLM APSS
Notebook **CREATO** (14 Mag 2026):
- ID: `bc8dfeee-c3f0-412d-aa88-f8e0a4025fa5`
- URL: https://notebooklm.google.com/notebook/bc8dfeee-c3f0-412d-aa88-f8e0a4025fa5
- 9 fonti da `D:\_claudecodeproject\APSS\` (radice + docs/)
- Escluso: `CLAUDE.local.md` (credenziali)
- Doppio labeling: area (📘🤖🗺️📝🔄🔌) + stato (📚⚙️)
- Skill manutenzione: `.claude/skills/apss-notebooklm-sync/`
- Firmware ESP32 docking nel repo: `docking/Esp32firmware/`
- `.gitignore` popolato (era vuoto)
- Gotcha critico: ricaricare fonte su NotebookLM cambia source_id e perde le label → riassegnazione obbligatoria

---

*Aggiornato il 14 Maggio 2026 — APSS GPwebdesign*
