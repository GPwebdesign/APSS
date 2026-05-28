# APSS — Autonomous Patrol and Surveillance System
## Riepilogo sessione per nuova chat — Maggio 2026

Contesto: Robot autonomo APSS su Yahboom Rosmaster R2 + Raspberry Pi 4 (hawk, 192.168.1.158,
Ubuntu 22.04, ROS2 Humble). VM sviluppo: gp68-vmware. Repo: rosmaster_project e ros2_py_ws
(GitHub GPwebdesign privati). Workflow: modifiche codice su VM → push GitHub → pull hawk → test.
Doc e skill solo su PC D:\_claudecodeproject\APSS\ → push APSS. Modifiche .md e .docx SEMPRE
via Claude Code (mai in chat).

---

## Completati in questa sessione 28/05/2026

- ✅ **Batteria LiFePO4 installata nel robot** (confermato in sessione)
- ✅ **CORREZIONE INA219 hawk**: i ~12.10V "stabili" in documentazione erano uscita DD32AJ4B
  SOLO con PSU 20V al posto batteria. Con batteria LiFePO4 reale INA219 legge <12.0V e segue
  la tensione reale → BatteryState.voltage è segnale utile, soglie voltage-based valide.
  architecture.md, doc_firmware.md e docx aggiornati.
- ✅ **Fix commento battery_node.py**: msg.current commentato correttamente
  (positivo=discharge, negativo=charge). Confermato da logica coulomb counting.
- ✅ **discharge_logger.py + morsetti_logger.py**: creati in rosmaster_project/test_files/.
  Logger di caratterizzazione scarica LiFePO4 attivo su hawk (discharge_20260528_2137.csv).
  Bande campionamento adattivo: >11.5V=300s, 11.2-11.5V=60s, <11.2V=10s.
  Potenza calcolata V*|I| (sensor.power non usare: riporta mW non W con shunt R100).
- ✅ **Documentazione aggiornata a v2.5**: architecture.md (4 fix INA219/microswitch),
  doc_firmware.md (roadmap microswitch posizione precisa + nota webapp reed→microswitch),
  APSS_Documentazione_Tecnica_v2_5.docx generata, v2_4 e v2_4_2 rimossi.
- ✅ **skill allinea-apss v1.1**: .md e .docx SEMPRE via Claude Code, mai in chat.
- ✅ **plan.md aggiornato a v2.9**: batteria installata spuntata, discharge_logger aggiunto,
  alarm_node.py aggiunto in roadmap safety node.

## Hardware robot

- Batteria: ECO-WORTHY LiFePO4 12.8V 8Ah installata ✅
- INA219 0x40: V_ina ~11.84V idle con batteria reale (NON 12.10V — quello era con PSU)
- Corrente idle misurata: ~0.48-0.55A (positiva = discharging confermato)
- RPLIDAR A1M8: in reso, sostituto in arrivo
- TOF: tutti e 3 verificati OK (CH2/CH3/CH4 → 0x29) ✅
- OLED: funzionante via apss-oled.service al boot ✅

## Stack ROS2

| Nodo | Stato |
|------|-------|
| oled_node | ✅ funzionante + service boot |
| battery_node | ✅ funzionante (avvio manuale) |
| safety_node | 🔲 in attesa dati scarica empirici |
| alarm_node | 🔲 dopo safety_node |
| tof_node | 🔲 pianificato |
| avoidance_node | 🔲 pianificato |

## Caratterizzazione scarica LiFePO4 (IN CORSO)

- File attivo: discharge_20260528_2137.csv su hawk in test_files/
- note_morsetti.csv: 2 righe (13.35V avvio + 13.19V riavvio)
- V_ina plateau: ~11.84V stabile, corrente ~0.48-0.55A idle
- Campionamento: 300s sul plateau, 60s in discesa, 10s al ginocchio
- Regola operativa: NON caricare tra sessioni dello stesso ciclo di scarica

## Architettura safety_node/alarm_node (confermata)

- safety_node: valuta soglie su /battery, pubblica /apss/alarm (JSON: livello+valore+source+ts)
- alarm_node: subscriber /apss/alarm, reagisce con beeper Yahboom + messaggio OLED
- Soglie voltage-based Fase 1: LOW 11.50V / CRITICAL 11.20V / EMERGENCY 10.80V
- Comportamento allarme: ad ogni ciclo, no stato (no latching)
- Soglie da tarare empiricamente dopo ciclo scarica completo

## Prossimi step (in ordine)

1. Attendere completamento ciclo scarica — analisi discharge_*.csv + note_morsetti.csv
2. Tarare soglie voltage-based empiriche su dati reali
3. safety_node.py — orchestratore soglie
4. alarm_node.py — dispatcher allarmi
5. tof_node.py + avoidance_node.py + /cmd_vel subscriber
6. Reinstallare ros-humble-slam-toolbox su hawk (pre-SLAM obbligatorio)

## Pending items

| Item | Priorità | Note |
|------|----------|------|
| Ciclo scarica LiFePO4 in corso | Alta | discharge_logger.py attivo su hawk — non caricare fino al completamento |
| safety_node.py | Alta | In attesa dati scarica empirici |
| RPLIDAR A1M8 sostituto | Alta | Reso autorizzato, sostituto in arrivo |
| ros-humble-slam-toolbox | Alta | Da reinstallare su hawk prima della sessione SLAM |
| alarm_node.py | Media | Dopo safety_node |
| battery_node nel launch file | Media | Aggiungere ad apss_lidar.launch.py |
| Test asterisco OLED scompare con battery_node | Media | Dopo battery_node nel launch file |
| Firmware ESP32 v2.2 | Media | relay_chiudi/apri loggano V/A/W; microswitch su fronte docking; webapp reed→microswitch |
| Fase D batteria — pendenti | Media | Fusibile T3A, CC 2A, soglie XHM603 post-ciclo completo |
| Bug [ODOM] publisher context invalid | Bassa | Cosmetico, non bloccante |
