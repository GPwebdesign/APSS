# APSS — Autonomous Patrol and Surveillance System
## Riepilogo sessione per nuova chat — Giugno 2026 #1

Contesto: Robot autonomo APSS su Yahboom Rosmaster R2 + Raspberry Pi 4 (hawk, 192.168.1.158,
Ubuntu 22.04, ROS2 Humble). VM sviluppo: gp68-vmware. Repo: rosmaster_project e ros2_py_ws
(GitHub GPwebdesign privati). Workflow: modifiche codice su VM → push GitHub → pull hawk → test.
Doc e skill solo su PC D:\_claudecodeproject\APSS\ → push APSS. Modifiche .md e .docx SEMPRE
via Claude Code (mai in chat).

---

## Completati in questa sessione 02-07/06/2026

- ✅ **Caratterizzazione scarica LiFePO4 completata**: ciclo completo 28/05-04/06/2026,
  273 campioni. Curva: plateau ~11.84V V_ina → ginocchio ~10.0V. 
- ✅ **CORREZIONE CRITICA offset INA219 hawk**: +1.5V medio vs terminali reali
  (NON +0.34V — quello è la docking station INA219 durante ricarica, sensori diversi).
- ✅ **Soglie voltage-based calibrate empiricamente**:
  LOW 11.50→11.45V, CRITICAL 11.20V invariato, EMERGENCY 10.80→10.20V.
  safety_rules.yaml aggiornato (commit 4bff64d).
- ✅ **safety_node.py v1.0 operativo**: architettura a regole dichiarative YAML,
  motore generico (ThresholdEvaluator, FrozenEvaluator, BooleanEvaluator, TopicMonitor,
  RuleEngine). 4 regole attive: battery_voltage + tof_front/left/right_frozen.
  Grace period 30s. Topic /apss/alarm JSON a 0.5Hz. Testato su hawk.
- ✅ **Fix CMakeLists.txt**: install(DIRECTORY config) senza slash — config vs config/.
- ✅ **alarm_node.py v1.0 operativo**: piper-tts v1.4.2, voce italiana/inglese
  configurabile, source labels human-readable, template dinamici, storico FIFO 20 entry.
- ✅ **Configurazione audio hawk**: utente hawk nel gruppo audio, device plughw:Headphones,
  volume persistente via alsactl store.
- ✅ **oled_node.py aggiornato**: subscriber /apss/oled_alert, scrolling riga 0
  da destra verso sinistra 8px/tick a 2Hz, prefisso "APSS | ", reset solo su cambio testo.
- ✅ **Test integrato verificato**: battery_node → safety_node → alarm_node → voce + OLED.
- ✅ **Documentazione aggiornata a v2.7**: architecture.md, apss_ros2.md, plan.md,
  CLAUDE.md, APSS_memorie.md, APSS_Documentazione_Tecnica_v2_7.docx.

## Hardware robot

- Batteria: ECO-WORTHY LiFePO4 12.8V 8Ah — ciclo scarica completato ✅
- INA219 hawk 0x40: offset +1.5V vs morsetti reali (misurato empiricamente)
- RPLIDAR A1M8: in reso, sostituto in arrivo
- TOF: tutti e 3 verificati OK (CH2/CH3/CH4 → 0x29) ✅
- OLED: funzionante via apss-oled.service al boot ✅
- Audio: jack 3.5mm RPi4, piper-tts, plughw:Headphones ✅

## Stack ROS2

| Nodo | Stato |
|------|-------|
| oled_node | ✅ funzionante + service boot + scrolling allarmi |
| battery_node | ✅ funzionante (avvio manuale) |
| safety_node | ✅ operativo v1.0 |
| alarm_node | ✅ operativo v1.0 |
| tof_node | 🔲 pianificato |
| avoidance_node | 🔲 pianificato |

## Architettura allarmi (consolidata)

- safety_node: regole YAML → /apss/alarm (JSON con ts, charging, alarms[])
- alarm_node: /apss/alarm → voce piper-tts + /apss/oled_alert + storico file
- oled_node: /apss/oled_alert → scrolling riga 0 OLED
- rosmaster_main.py: subscriber /apss/alarm → Kivy poll TCP (da implementare)
- Livelli: LOW (30s) / CRITICAL (10s) / EMERGENCY (SOS) / ERROR (60s)
- Allarmi multipli: tutti parlati in sequenza, OLED lista completa

## Soglie batteria (calibrate empiricamente — commit 4bff64d)

| Livello | V_ina | V_reale stimata | Azione |
|---------|-------|-----------------|--------|
| LOW | 11.45V | ~13.0V | Completa task, rientra al docking |
| CRITICAL | 11.20V | ~12.7V | Interrompe task, rientra immediato |
| EMERGENCY | 10.20V | ~11.7V | Stop ovunque, emergenza |

## Prossimi step (in ordine)

1. Subscriber /apss/alarm in rosmaster_main.py per Kivy poll TCP
2. tof_node.py + avoidance_node.py + /cmd_vel subscriber
3. Reinstallare ros-humble-slam-toolbox su hawk (pre-SLAM obbligatorio)
4. Prima sessione SLAM mapping

## Pending items

| Item | Priorità | Note |
|------|----------|------|
| Subscriber /apss/alarm in rosmaster_main.py | Media | Per Kivy poll TCP — AlertScreen |
| tof_node.py | Alta | Prerequisito avoidance_node |
| avoidance_node.py | Alta | Dopo tof_node |
| ros-humble-slam-toolbox | Alta | Da reinstallare su hawk prima della sessione SLAM |
| RPLIDAR A1M8 sostituto | Alta | Reso autorizzato, sostituto in arrivo |
| status_node | Media | Pianificato dopo safety/alarm — stato sensori on demand per Kivy |
| battery_node nel launch file | Media | Aggiungere ad apss_lidar.launch.py |
| Firmware ESP32 v2.2 | Media | relay_chiudi/apri loggano V/A/W; microswitch montaggio fisico |

---

## Completati in sessione 07/06/2026 — chat #2

- ✅ **Server APSS TCP porta 6010 in rosmaster_main.py**:
  - Thread daemon task_apss_server su porta 6010 (canale JSON APSS generico, estensibile)
  - Subscriber ROS2 /apss/alarm con push immediato al client connesso
  - Cache ultimo stato (g_apss_alarm_cache), fallback ros2_unavailable se ROS2 non attivo
  - GET_HISTORY: il client può richiedere lo storico corrente
  - rclpy.spin_once(node, timeout_sec=0) aggiunto nel loop thread_odom per processare callback
  - Porta cambiata da 6001 a 6010 (conflitto NoMachine nxnode.bin)
  - Fix NumPy: downgrade numpy<2 (piper-tts aveva aggiornato a 2.2.6, incompatibile con OpenCV)
- ✅ **AlarmClient — rosmaster_kivy/network/alarm_client.py**:
  - Stesso pattern threading di TCPClient (connect/recv worker, lock)
  - Protocollo JSON newline-delimited, porta 6010
  - Callback on_alarm, on_history, on_connected, on_disconnected
  - request_history() per GET_HISTORY, update_host() propagato da save_settings()
- ✅ **AlertScreen funzionale — rosmaster_kivy/screens/alert_screen.py**:
  - UI completamente in Python (rimossa regola <AlertScreen> dal .kv — conflitto doppia UI)
  - MDTopAppBar "Alert Sicurezza" + pulsante back, lista scrollabile storico allarmi
  - Pulsante "Aggiorna" → request_history()
  - update_alarms(data): popola lista con ts, charging, allarmi per livello/source/message
- ✅ **Popup allarmi in main.py**:
  - Popup MDDialog "⚠ Allarme APSS" su qualsiasi schermata
  - Dedup via firma frozenset(source, level): popup si apre solo se lista allarmi cambia
  - Popup si chiude automaticamente se lista allarmi si svuota
  - Reset firma solo su svuotamento lista, NON al dismiss manuale (OK)
- ✅ **start_robot_APSS.sh**: script avvio robot — rosmaster_main.py +
  battery_node e safety_node in terminali terminator separati
- ✅ **Icona app desktop**: Window.set_icon('icon.png') in build()

## Architettura canale APSS TCP porta 6010 (aggiornata)

- Canale JSON bidirezionale generico — estensibile per future comunicazioni app↔robot
- Server: thread daemon in rosmaster_main.py, una connessione alla volta
- Push immediato al cambio /apss/alarm, fallback ros2_unavailable
- Client: AlarmClient con pattern connect/recv worker identico a TCPClient
- Protocollo: JSON newline-delimited, tipo "alarm"/"history"/"status"

## Prossimi step aggiornati

1. tof_node.py + avoidance_node.py + /cmd_vel subscriber
2. Reinstallare ros-humble-slam-toolbox su hawk (pre-SLAM obbligatorio)
3. Prima sessione SLAM mapping

## Pending items aggiornati

| Item | Priorità | Note |
|------|----------|------|
| tof_node.py | Alta | Prerequisito avoidance_node |
| avoidance_node.py | Alta | Dopo tof_node |
| ros-humble-slam-toolbox | Alta | Da reinstallare su hawk prima della sessione SLAM |
| RPLIDAR A1M8 sostituto | Alta | Reso autorizzato, sostituto in arrivo |
| APK Android v2.2 | Media | Rebuild con AlertScreen e AlarmClient dopo test completo su Linux |
| status_node | Media | Pianificato dopo safety/alarm — stato sensori on demand per Kivy |
| battery_node nel launch file | Media | Aggiungere ad apss_lidar.launch.py |
| Firmware ESP32 v2.2 | Media | relay_chiudi/apri loggano V/A/W; microswitch montaggio fisico; ricarica completata → relay OFF; valutare relay CH2 per isolare INA da barra rame a fine ricarica |
