# APSS — Autonomous Patrol and Surveillance System
## Riepilogo sessione per nuova chat — Maggio 2026

Contesto: Robot autonomo APSS su Yahboom Rosmaster R2 + Raspberry Pi 4 (hawk, 192.168.1.158,
Ubuntu 22.04, ROS2 Humble). VM sviluppo: gp68-vmware. Repo: `rosmaster_project` e `ros2_py_ws`
(GitHub GPwebdesign privati). Workflow: modifiche codice su VM → push GitHub → pull hawk → test.
Doc solo su PC `D:\_claudecodeproject\APSS\` → push APSS.

---

## Completati in questa sessione

- ✅ Allineamento APSS: `APSS_memorie.md`, `CLAUDE.md`, `plan.md` (v2.7), `architecture.md`
- ✅ Architettura `safety_node` concordata — nodo dedicato per tutti gli allarmi futuri

## In corso

- 🚧 `apss-oled.service` — service systemd indipendente per avvio OLED al boot. Architettura
  decisa (opzione A: `After=network-online.target`, `Restart=on-failure`, utente hawk), in attesa
  di dati da hawk (nome package ROS2, path workspace) per completare il file unit.

## Hardware robot

- RPLIDAR A1M8: **in reso** (linea TX morta, diagnosi confermata). Sostituto in arrivo.
  Quando arriva: test Python bare-metal protocollo + driver ROS2.
- TOF400C VL53L1X: tutti e 3 verificati OK (CH2/CH3/CH4). Pronti per `tof_node.py`.
- INA219 0x40: operativo. `oled_node.py` usa fallback INA219 diretto con watchdog 5s su `/battery`.
- OLED SSD1306: `oled_node.py` funzionante manualmente, asterisco visibile quando `battery_node`
  non gira.
- Batteria ECO-WORTHY LiFePO4: installata. Catena misurata:
  ECO-WORTHY 13.09V → DD32AJ4B (12.16V vuoto / 11.70V carico) → INA219 → Yahboom 11.58V.

## Stack ROS2

- `oled_node.py`: autonomo, fallback INA219 + watchdog `/battery` 5s — funzionante
- `battery_node.py`: pubblica `/battery` + `/battery/stats` — funzionante
- `apss-oled.service`: 🚧 in corso
- `slam_toolbox`: ⚠️ da reinstallare su hawk (perso post-restore SD) — priorità Alta
- `safety_node.py`: pianificato — orchestratore allarmi, subscriber `/battery`, publisher `/apss/alarm`

## Soglie ricarica (Fase 1 — voltage based)

| Livello | Tensione | SoC stimato | Azione |
|---------|----------|-------------|--------|
| 🟡 LOW | 11.50V | ~30% | Completa task, rientra |
| 🟠 CRITICAL | 11.20V | ~15% | Interrompe task, rientra subito — trigger SOS beeper |
| 🔴 EMERGENCY | 10.80V | ~5% | Stop ovunque, attende recupero |

SOS beeper: morse ···---··· via scheda Yahboom, 3 ripetizioni a 3s di distanza — da implementare
in `safety_node.py`.

## Roadmap

### Completati
1. ✅ Fix USB enumeration non deterministica (udev symlink `/dev/yahboom` + `/dev/rplidar`)
2. ✅ `oled_node.py` riadattato (fallback INA219 + watchdog + layout nuovo)
3. ✅ `battery_node.py` con `/battery` e `/battery/stats`
4. ✅ TOF CH4 riparato — tutti e 3 i sensori OK
5. ✅ Catena alimentazione misurata + 3 soglie ricarica definite
6. ✅ APK Android debug 2.1 generato (da testare su S23 Ultra)

### Prossimi step (in ordine)
1. Fornire a Claude dati hawk (`ros2 pkg` + path workspace) → completare `apss-oled.service`
2. Reinstallare `ros-humble-slam-toolbox` su hawk
3. `battery_node` + `oled_node` nel launch file + test integrato OLED (asterisco scompare)
4. Verifica pacchetti pip post-restore SD (`adafruit-circuitpython-*`, `picamera2`, ecc.)
5. Test RPLIDAR sostituto al ricevimento
6. Progettazione e implementazione `safety_node.py`
7. `tof_node.py` + `avoidance_node.py` + subscriber `/cmd_vel` in `rosmaster_main.py`
8. Test APK Android Samsung S23 Ultra
9. Fase D batteria LiFePO4 (fusibile T3A, CC 2A, soglie XHM603 definitive)

## Pending items

| Item | Priorità | Note |
|------|----------|------|
| ⚠️ RPLIDAR A1M8 in reso | Alta | Sostituto in arrivo |
| Reinstallare `ros-humble-slam-toolbox` | Alta | Pre-SLAM obbligatorio |
| Completare `apss-oled.service` | Media | Serve nome pkg ROS2 + path workspace da hawk |
| Verificare pacchetti pip post-restore | Media | `adafruit-circuitpython-*`, `picamera2`, ecc. |
| `battery_node` nel launch file | Media | Test integrato OLED |
| Test APK S23 Ultra | Media | APK 2.1 pronto |
| Fase D batteria | Media | Fusibile T3A, CC 2A, soglie XHM603 |
| Bug `[ODOM] publisher's context is invalid` | Bassa | Cosmetico, non bloccante |
| Bug Video MainScreen primo `on_enter` | Bassa | Workaround Home→Camera→Home |
