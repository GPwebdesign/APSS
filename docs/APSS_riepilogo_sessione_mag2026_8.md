# APSS — Autonomous Patrol and Surveillance System
## Riepilogo sessione per nuova chat — Maggio 2026

Contesto: Robot autonomo APSS su Yahboom Rosmaster R2 + Raspberry Pi 4 (hawk, 192.168.1.158,
Ubuntu 22.04, ROS2 Humble). VM sviluppo: gp68-vmware. VM Buildozer: VMware-Ubuntu24-04-4.
Repo: `rosmaster_project` e `ros2_py_ws` (GitHub GPwebdesign privati).
Workflow: modifiche codice su VM → push GitHub → pull hawk → test.
Doc solo su PC `D:\_claudecodeproject\APSS\` → push APSS.

---

## Completati in questa sessione

- ✅ Bug video MainScreen risolto: TCP server bind `0.0.0.0` invece di IP specifico
- ✅ App Android funzionante su S23 Ultra: connessione, video, CameraScreen, cambio schermata
- ✅ `filetype` aggiunto ai requirements buildozer — crash Android risolto
- ✅ `camera_screen.py`: salvataggio foto/video in `/sdcard/DCIM/APSSystem/` visibile in galleria
- ✅ Popup conferma foto + popup Salva/Annulla/Rinomina video con notifica MediaStore
- ✅ Icona app personalizzata `icon.png` configurata in `buildozer.spec`
- ✅ `static_img/` aggiunta al repo APSS (logo black/white + sorgenti)
- ✅ `buildozer.spec` e `.gitignore` aggiornati e nel repo
- ✅ Verifica I2C post-scarica statica: tutti i sensori OK

## Hardware robot

- RPLIDAR A1M8: **in reso** (linea TX morta). Sostituto in arrivo.
- TOF400C VL53L1X: tutti e 3 verificati OK post-scarica statica (CH2/CH3/CH4 → 0x29) ✅
- INA219 0x40: operativo ✅
- OLED SSD1306: funzionante via `apss-oled.service` al boot ✅
- TCA9548A 0x70: operativo ✅

## Stack ROS2

| Nodo | Comando | Stato |
|------|---------|-------|
| `oled_node` | `ros2 run apss_ros2_pkg oled_node.py` | ✅ funzionante + service boot |
| `battery_node` | `ros2 run apss_ros2_pkg battery_node.py` | ✅ funzionante |
| `safety_node` | `ros2 run apss_ros2_pkg safety_node.py` | 🔲 pianificato |

## App Android

- APK `apssystem-2.1` — testato e funzionante su S23 Ultra ✅
- Salvataggio: `/sdcard/DCIM/APSSystem/` (foto `.jpg`, video cartella frame)
- Icona personalizzata APSS configurata
- Bug connessione risolto (TCP bind `0.0.0.0`)

## Soglie ricarica (Fase 1 — voltage based)

| Livello | Tensione | SoC stimato | Azione |
|---------|----------|-------------|--------|
| 🟡 LOW | 11.50V | ~30% | Completa task, rientra |
| 🟠 CRITICAL | 11.20V | ~15% | Interrompe task, rientra — trigger SOS beeper |
| 🔴 EMERGENCY | 10.80V | ~5% | Stop ovunque, attende recupero |

## Prossimi step (in ordine)

1. Reinstallare `ros-humble-slam-toolbox` su hawk
2. `battery_node` + `oled_node` nel launch file + test integrato (asterisco scompare)
3. Verifica pacchetti pip post-restore SD
4. Test RPLIDAR sostituto al ricevimento
5. Progettazione e implementazione `safety_node.py`
6. `tof_node.py` + `avoidance_node.py` + subscriber `/cmd_vel`
7. Fase D batteria LiFePO4 (fusibile T3A, CC 2A, soglie XHM603)

## Pending items

| Item | Priorità | Note |
|------|----------|------|
| ⚠️ RPLIDAR A1M8 in reso | Alta | Sostituto in arrivo |
| Reinstallare `ros-humble-slam-toolbox` | Alta | Pre-SLAM obbligatorio |
| Test asterisco OLED scompare con battery_node | Media | `battery_node` nel launch file |
| Verificare pacchetti pip post-restore | Media | `adafruit-circuitpython-*`, `picamera2`, ecc. |
| Fase D batteria | Media | Fusibile T3A, CC 2A, soglie XHM603 |
| Bug `[ODOM] publisher's context is invalid` | Bassa | Cosmetico, non bloccante |
| Log rumore `Camera Init Error!` | Bassa | Handler legacy Yahboom, non funzionale |
