# APSS — Autonomous Patrol and Surveillance System
## Riepilogo sessione per nuova chat — Maggio 2026 (#4)

Contesto: Robot autonomo di pattugliamento basato su Yahboom Rosmaster R2 + Raspberry Pi 4
(hawk, 192.168.1.158, Ubuntu 22.04, ROS2 Humble). VM sviluppo: gp68-vmware (192.168.1.80).
Repository: `rosmaster_project` e `ros2_py_ws` (GitHub GPwebdesign privati).

**WORKFLOW:** Modifiche codice su VM → push GitHub → pull su hawk per test. Dopo test OK →
`.\subtree-pull.bat` su PC. Modifiche da hawk → `apss-push.sh` → pull VM → `.\subtree-pull.bat`.
Doc e skills solo su PC → push APSS. MAI modificare codice sul PC.

---

## Completati in questa sessione (15 Maggio 2026)

- ✅ TOF CH4 risolto — sensore originale difettoso sostituito con scorta — tutti e 3 OK (0x29)
- ✅ Libreria `adafruit-circuitpython-vl53l1x` v1.2.9 installata su hawk
- ✅ Approccio I2C smbus2+busio.I2C verificato su CH2, CH3, CH4
- ✅ `APSS_Documentazione_Tecnica_v2_3.docx` — struttura v1.9 ripristinata, sezione 11.1 Sviluppo Futuro inclusa
- ✅ Allineamento completo tutti i repo: APSS `b1a1f19`

## Problema aperto

⚠️ **RPLIDAR standby al boot**: `apss-lidar-standby.service` installato ma motore riparte.
Script aggiornato (delay 3s + retry) presente in `rosmaster_project/apss_lidar_standby.py` — da testare dopo reboot.

---

## Hardware robot

Struttura proprietaria GPwebdesign. M1/M4 polarità invertita fisicamente.
Cinematica custom: M1=vx-vy+vz, M2=vx+vy-vz, M3=vx+vy+vz, M4=vx-vy-vz. Speed base=55.
INA219 0x40 in serie al positivo — corrente positiva=DISCHARGING, negativa=CHARGING.
3x TOF400C VL53L1X installati (frontale CH2, sx CH3, dx CH4 ✅ tutti OK).

---

## Stack ROS2

- `battery_node.py`: pubblica `/battery` (BatteryState) e `/battery/stats` (BatteryStats) ogni 2s
- `oled_node.py`: subscriber `/battery` (BatteryState) ✅
- `apss-lidar-standby.service`: stop RPLIDAR al boot — ⚠️ motore riparte, fix in sospeso
- Libreria TOF: `adafruit-circuitpython-vl53l1x` v1.2.9 installata su hawk

---

## Roadmap

### Completati
1. ✅ Rimozione OpenCV obstacle avoidance + thread_image_publisher
2. ✅ Semplificazione camera_params.json
3. ✅ Endpoint /capture_still
4. ✅ battery_node.py con /battery e /battery/stats
5. ✅ BatteryStats.msg custom
6. ✅ oled_node.py subscriber /battery (BatteryState)
7. ✅ apss-lidar-standby.service installato
8. ✅ Skill allinea-apss
9. ✅ TOF CH4 fix (sensore scorta) — tutti e 3 verificati OK
10. ✅ APK Android debug 2.1 generato
11. ✅ Documentazione_Tecnica v2.3

### Prossimi step (in ordine)
1. Fix RPLIDAR standby al boot (test script delay 3s + retry — da fare dopo reboot)
2. `battery_node` + `oled_node` aggiunti ad `apss_lidar.launch.py`
3. Test integrato: battery_node → /battery → oled_node → display
4. `tof_node.py` — legge CH2/CH3/CH4 via TCA9548A, pubblica /tof/front|left|right
5. `avoidance_node.py` — soglie 50cm/40cm
6. `rosmaster_main.py` subscriber /cmd_vel
7. Test APK Android su Samsung S23 Ultra

## Pending items

| Item | Priorità | Note |
|------|----------|------|
| Fix RPLIDAR standby boot | Alta | Script pronto (sleep 3s + loop 3x) — da testare dopo reboot |
| Fix cablaggio TOF CH4 | ✅ Risolto | Sensore sostituito con scorta |
| Test APK Android | Media | Samsung S23 Ultra — APK debug 2.1 già generato |
| Backup su USB disk via SMB | Media | cifs-utils da installare su hawk |
| Microswitch docking station | Media | NC, GPIO18, stesso cablaggio reed |
| Batteria LiFePO4 Fase D | Alta | Fusibile T3A + CC 2A + soglie XHM603 definitive |
