# APSS — Autonomous Patrol and Surveillance System
## Riepilogo sessione per nuova chat — Maggio 2026 (#5)

Contesto: Robot autonomo di pattugliamento basato su Yahboom Rosmaster R2 + Raspberry Pi 4
(hawk, 192.168.1.158, Ubuntu 22.04, ROS2 Humble). VM sviluppo: gp68-vmware (192.168.1.80).
Repository: `rosmaster_project` e `ros2_py_ws` (GitHub GPwebdesign privati).

**WORKFLOW:** Modifiche codice su VM → push GitHub → pull su hawk per test. Dopo test OK →
`.\subtree-pull.bat` su PC. Modifiche da hawk → `apss-push.sh` → pull VM → `.\subtree-pull.bat`.
Doc e skills solo su PC → push APSS. MAI modificare codice sul PC.

---

## Sessione 16 Maggio 2026 — Fix USB enumeration non deterministica

### Diagnosi
All'accensione del robot `rosmaster_main.py` andava in stallo con `Version: -1` e beep silenziosi.
Il motore RPLIDAR si fermava all'avvio dello script. La causa: ordine `ttyUSB0/ttyUSB1` non
deterministico al boot — quando RPLIDAR (CP2102) prende `ttyUSB0`, la libreria Yahboom apre
il dispositivo sbagliato. Inoltre il DTR del CP2102 fermava il motore RPLIDAR come side-effect.

### Fix applicati su hawk

- ✅ Regole udev `/etc/udev/rules.d/99-apss-usb.rules` — symlink stabili:
  - `/dev/yahboom` → CH340 Yahboom (`1a86:7523`)
  - `/dev/rplidar` → CP2102 RPLIDAR (`10c4:ea60`)
- ✅ Patch libreria `/usr/lib/python3.10/Rosmaster_Lib/Rosmaster_Lib.py` riga 20 —
  apre `/dev/yahboom` invece di `/dev/ttyUSB0` hardcoded. Backup `.bak-APSS`.
- ✅ Launch file `apss_lidar.launch.py` — parametro `serial_port: '/dev/rplidar'`.
  Backup `.bak-APSS`.
- ✅ Test post-reboot verificato: enumeration invertita (Yahboom→ttyUSB1, RPLIDAR→ttyUSB0)
  e `rosmaster_main.py` parte correttamente con `Version: 3.5`.

### Memoria corretta
`apss-lidar-standby.service` è `disabled` e non ha mai effettivamente fermato il motore al boot.
La memoria precedente "installato e abilitato" era imprecisa — è un topic aperto, non un fix
funzionante. Topic deprioritizzato dopo il fix USB.

### Problemi aperti scoperti durante la sessione

| # | Problema | Severità |
|---|---|---|
| 1 | `ros-humble-rplidar-ros` reinstallato MA driver va in `SL_RESULT_OPERATION_TIMEOUT` — test Python `0xA5 0x50` GET_INFO restituisce 0 bytes. Motore gira, symlink OK, lidar non risponde al protocollo. Da debugare. | Alta |
| 2 | `ros-humble-slam-toolbox` mancante post-restore SD — da reinstallare | Media |
| 3 | `[ODOM] publisher's context is invalid` intermittente (pre-esistente, cosmetico) | Bassa |
| 4 | Video MainScreen non parte al primo `on_enter` (workaround Home→Camera→Home) | Bassa |
| 5 | Log rumore `Camera Init Error!` per `/dev/camera_usb` (handler legacy Yahboom) | Bassa |

### ⚠️ Persistenza patch libreria
Se `Rosmaster_Lib` viene reinstallata via apt/pip (dist-upgrade, reset Ubuntu, ecc.),
la patch riga 20 va riapplicata manualmente. Backup conservato in `.bak-APSS`.

---

## Sessioni precedenti (sintesi cumulativa)

### Aggiornamento pomeriggio 16 Maggio 2026 — RPLIDAR debug

Dopo il fix USB e l'installazione di `ros-humble-rplidar-ros` 2.1.4 (build 20260423):

- Lancio `apss_lidar.launch.py` → fallisce per `slam_toolbox not found` (anche slam_toolbox mancante post-restore SD)
- Lancio diretto `rplidar_a1_launch.py` con `serial_port:=/dev/rplidar` → `SL_RESULT_OPERATION_TIMEOUT` dopo `SDK Version: 2.0.0`
- Lancio diretto `ros2 run rplidar_ros rplidar_node` con tutti i parametri espliciti → stesso timeout
- Power cycle completo del robot → stesso timeout
- Test Python bare-metal (`0xA5 0x50` GET_INFO + `read(27)`) → **0 bytes ricevuti**

Conferma: il lidar fisicamente gira ma NON risponde al protocollo nativo Slamtec. Il driver ROS2 non è colpevole — il problema è hardware/firmware del lidar stesso. Sessione chiusa con problema catalogato per debug dedicato.

### Completati nelle sessioni #3 e #4
- ✅ Rimozione OpenCV obstacle avoidance + `thread_image_publisher` da `rosmaster_main.py`
- ✅ Pipeline colore camera consolidata (RGB nativo picamera2, no cvtColor intermediate)
- ✅ Semplificazione `camera_params.json` (solo profilo streaming)
- ✅ Endpoint `/capture_still` (JPEG qualità 95)
- ✅ INA219 0x40 in serie al positivo + `battery_node.py` con `/battery` + `/battery/stats`
- ✅ `BatteryStats.msg` custom — min/max V/I/P + sample_count
- ✅ `oled_node.py` subscriber `/battery` (BatteryState)
- ✅ 3x TOF400C VL53L1X installati e verificati OK (CH2 frontale, CH3 sx, CH4 dx)
- ✅ Libreria `adafruit-circuitpython-vl53l1x` v1.2.9 su hawk
- ✅ APK Android debug 2.1 generato (Buildozer 1.5.0, Ubuntu 24.04 VM)
- ✅ `APSS_Documentazione_Tecnica_v2_3.docx`
- ✅ Skill `allinea-apss` e `apss-notebooklm-sync` create
- ✅ Batteria LiFePO4 ECO-WORTHY 12V 8Ah acquistata, XL4016 ricalibrato 14.40V/0.9A,
  XHM603 soglie conservative STOP=14.2V/START=13.1V, prima ricarica parziale OK

---

## Hardware robot

Struttura proprietaria GPwebdesign. M1/M4 polarità invertita fisicamente.
Cinematica custom: M1=vx-vy+vz, M2=vx+vy-vz, M3=vx+vy+vz, M4=vx-vy-vz. Speed base=55.
INA219 0x40 in serie al positivo — corrente positiva=DISCHARGING, negativa=CHARGING.
3x TOF400C VL53L1X installati (frontale CH2, sx CH3, dx CH4 — tutti OK).
USB: Yahboom CH340 → `/dev/yahboom`, RPLIDAR CP2102 → `/dev/rplidar` (symlink udev stabili).

---

## Stack ROS2

- `battery_node.py`: pubblica `/battery` (BatteryState) e `/battery/stats` (BatteryStats) ogni 2s
- `oled_node.py`: subscriber `/battery` (BatteryState)
- `apss-lidar-standby.service`: disabled, mai funzionato (topic aperto, deprioritizzato)
- Libreria TOF: `adafruit-circuitpython-vl53l1x` v1.2.9 installata su hawk

---

## Roadmap — Prossimi step (in ordine)

1. ⚠️ **Debug RPLIDAR non comunicante** — verificare cavetto interno testa↔PCB, provare reset firmware se possibile, test su altro Pi/PC come ulteriore isolamento
2. **Reinstallare `ros-humble-slam-toolbox`** — quando lidar torna a comunicare
3. `battery_node` + `oled_node` aggiunti ad `apss_lidar.launch.py`
4. Test integrato: battery_node → `/battery` → oled_node → display
5. `tof_node.py` — legge CH2/CH3/CH4 via TCA9548A, pubblica `/tof/front|left|right`
6. `avoidance_node.py` — soglie 50cm (slow) / 40cm (pivot)
7. `rosmaster_main.py` subscriber `/cmd_vel`
8. Test APK Android su Samsung S23 Ultra
9. Batteria LiFePO4 Fase D — fusibile T3A, CC 2A, tabella SoC LiFePO4, soglie ESP32 definitive

## Pending items

| Item | Priorità | Note |
|------|----------|------|
| Debug RPLIDAR non comunicante | Alta | Driver OK, lidar non risponde — ipotesi cavetto interno o firmware zombie |
| Reinstallare `ros-humble-slam-toolbox` | Alta | Mancante post-restore SD — dipendenza per SLAM |
| Batteria LiFePO4 Fase D | Alta | Fusibile T3A + CC 2A + soglie XHM603 definitive |
| Test APK Android | Media | Samsung S23 Ultra — APK debug 2.1 già generato |
| Backup su USB disk via SMB | Media | `\\iliadbox_Server\iliadbox` — cifs-utils da installare |
| Microswitch docking station | Media | NC, GPIO18, stesso cablaggio reed switch |
| Cleanup fantasmi NotebookLM | Bassa | 3 source_id orfani in label |
| Bug `[ODOM] context invalid` | Bassa | Cosmetico intermittente |
| Bug Video MainScreen primo `on_enter` | Bassa | Workaround Home→Camera→Home |
| Log `Camera Init Error!` `/dev/camera_usb` | Bassa | Handler legacy Yahboom |
| Ripristino aggiornamenti ROS2 Humble | Bassa | Dopo hold config completa |
