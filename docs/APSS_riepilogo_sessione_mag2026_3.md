# APSS — Autonomous Patrol and Surveillance System
## Riepilogo sessione per nuova chat — Maggio 2026 (#3)

Contesto: Robot autonomo di pattugliamento basato su Yahboom Rosmaster R2 + Raspberry Pi 4
(hawk, 192.168.1.158, Ubuntu 22.04, ROS2 Humble). VM sviluppo: gp68-vmware (192.168.1.80).
Repository: `rosmaster_project` e `ros2_py_ws` (GitHub GPwebdesign privati).

**WORKFLOW:** Modifiche codice su VM → push GitHub → pull su hawk per test. Dopo test OK →
`.\subtree-pull.bat` su PC. Modifiche da hawk → `apss-push.sh` → pull VM → `.\subtree-pull.bat`.
Doc e skills solo su PC → push APSS. MAI modificare codice sul PC.

---

## Completati in questa sessione (10 Maggio 2026)

- ✅ `apss-lidar-standby.service` installato e abilitato su hawk
- ✅ `apss_lidar_standby.py` — script CMD_STOP + CMD_MOTOR RPLIDAR al boot
- ✅ Utente `hawk` aggiunto al gruppo `dialout`
- ✅ `oled_node.py` — subscriber `/battery` (BatteryState) da battery_node — topic allineato
- ✅ `plan.md` aggiornato a v2.3, `architecture.md` aggiornato
- ✅ Skill `allinea-apss` creata in `.claude/skills/allinea-apss/SKILL.md`
- ✅ Tutti e tre i repo allineati: rosmaster_project `7945ca8`, ros2_py_ws `ee6fa7d`

## Problema aperto

⚠️ **RPLIDAR standby**: il motore riparte dopo il boot nonostante il service giri con successo.
Script con `sleep(3.0)` + loop 3x pronto ma non ancora testato dopo reboot.
Da testare come prima cosa nella prossima sessione.

---

## Hardware robot

Struttura proprietaria GPwebdesign. M1/M4 polarità invertita fisicamente.
Cinematica custom: M1=vx-vy+vz, M2=vx+vy-vz, M3=vx+vy+vz, M4=vx-vy-vz. Speed base=55.
INA219 0x40 in serie al positivo — corrente positiva=DISCHARGING, negativa=CHARGING.
3x TOF400C VL53L1X installati (frontale CH2, sx CH3, dx CH4 ⚠️ cablaggio).

---

## Stack ROS2

- `battery_node.py`: pubblica `/battery` (BatteryState) + `/battery/stats` ogni 2s
- `oled_node.py`: subscriber `/battery` (BatteryState) ✅ + `/apss/battery` (JSON legacy)
- `apss-lidar-standby.service`: stop RPLIDAR al boot — ⚠️ motore riparte, fix in sospeso
- Build hawk post-modifica: `colcon build --symlink-install` completata OK

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

### Prossimi step (in ordine)
1. Fix RPLIDAR standby al boot (test script delay 3s + retry — da fare dopo reboot)
2. `battery_node` + `oled_node` aggiunti ad `apss_lidar.launch.py`
3. Test integrato: battery_node → /battery → oled_node → display
4. Fix cablaggio TOF CH4
5. `tof_node.py` + `avoidance_node.py`
6. `rosmaster_main.py` subscriber `/cmd_vel`
7. Test APK Android su Samsung S23 Ultra

## Pending items

| Item | Priorità | Note |
|------|----------|------|
| Fix RPLIDAR standby boot | Alta | Script pronto (sleep 3s + loop 3x) — da testare dopo reboot |
| Fix cablaggio TOF CH4 | Alta | Blocca bus I2C — controllare SDA/SCL/VCC/GND |
| Test APK Android | Media | Samsung S23 Ultra — APK debug 2.1 già generato |
| Backup su USB disk via SMB | Media | cifs-utils da installare su hawk |
| Microswitch docking station | Media | NC, GPIO18, stesso cablaggio reed |
