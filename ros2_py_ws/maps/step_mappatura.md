# APSS — Guida alla Mappatura con slam_toolbox

## Prerequisiti
- Robot a terra in posizione di partenza
- RPLIDAR A1M8 collegato su /dev/ttyUSB1
- ROS2 Humble attivo su hawk (192.168.1.158)
- Cartella mappe: ~/Workspaces/ros2_py_ws/maps/

---

## 1. Avvio stack di mappatura

**Terminale 1 — Pi (hawk):**
```bash
source ~/.bashrc
ros2 launch udemy_ros2_pkg apss_lidar.launch.py
```

Attendi che tutti i nodi siano avviati:
- `[rplidar_composition]` — RPLidar health status: OK
- `[robot_state_publisher]` — got segment base_link
- `[async_slam_toolbox_node]` — Registering sensor: Custom Described Lidar
- RViz2 si apre automaticamente sulla VM con Map + LaserScan

**Terminale 2 — VM:**
```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard
```

---

## 2. Tasti di teleoperazione

| Tasto | Azione |
|---|---|
| `i` | Avanti |
| `,` | Indietro |
| `j` | Ruota sinistra |
| `l` | Ruota destra |
| `k` | Stop immediato |
| `q` | Aumenta velocità lineare |
| `z` | Diminuisce velocità lineare |

**Velocità consigliata per SLAM: 0.15-0.20 m/s**

---

## 3. Tecnica di mappatura corretta

- Muovi il robot **lentamente e in modo fluido**
- Evita rotazioni brusche — ruota lentamente sul posto
- Percorri il perimetro di ogni stanza prima di mappare il centro
- Nelle zone di giunzione tra stanze: **sovrapponi il percorso** passando due volte
- Il LiDAR deve sempre vedere almeno 3 punti fissi per mantenere la localizzazione
- Se il robot si perde (la mappa si distorce): fermati, ruota lentamente su se stesso

---

## 4. Salvataggio mappa — OBBLIGATORIO prima di interrompere

**Terminale 3 — Pi:**
```bash
ros2 service call /slam_toolbox/save_map \
  slam_toolbox/srv/SaveMap \
  "{name: {data: '/home/hawk/Workspaces/ros2_py_ws/maps/apss_map_v1'}}"
```

Attendi la conferma:
response: slam_toolbox.srv.SaveMap_Response(result=0)

**Solo dopo la conferma** premi Ctrl+C nel Terminale 1.

I file salvati sono:
- `maps/apss_map_v1.pgm` — immagine della mappa (apribile con qualsiasi visualizzatore)
- `maps/apss_map_v1.yaml` — metadati (risoluzione, origine, soglie)

**NON premere Ctrl+C prima della conferma — la mappa verrebbe persa.**

---

## 5. Versionamento mappa su Git

```bash
cd ~/Workspaces/ros2_py_ws
git add maps/
git commit -m "map: aggiornamento mappa apss_map_v1"
git push
```

---

## 6. Riprendere la mappatura da dove si era interrotto

**Avvia il launch file normalmente:**
```bash
ros2 launch udemy_ros2_pkg apss_lidar.launch.py
```

**Carica la mappa esistente — Terminale 2 — Pi:**
```bash
ros2 service call /slam_toolbox/deserialize_map \
  slam_toolbox/srv/DeserializePoseGraph \
  "{filename: {data: '/home/hawk/Workspaces/ros2_py_ws/maps/apss_map_v1'}}"
```

Attendi la conferma poi riprendi la teleoperazione.
Salva sempre con un nuovo nome versione: apss_map_v2, apss_map_v3, ecc.

---

## 7. Aggiornamento launch file per caricare mappa al boot

Quando la mappa è completa e verificata, aggiungere al nodo slam_toolbox
in apss_lidar.launch.py:

```python
'map_file_name': '/home/hawk/Workspaces/ros2_py_ws/maps/apss_map_finale',
'map_start_at_dock': True,
```

Questo passa slam_toolbox dalla modalità **mapping** alla modalità **localization**.

---

## 8. Checklist pre-mappatura

- [ ] Robot a terra, posizione di partenza definita
- [ ] RPLIDAR alimentato e che gira
- [ ] ttyUSB1 assegnato a RPLIDAR (verificare con ls /dev/ttyUSB*)
- [ ] rosmaster_main.py NON in esecuzione (conflitto porta seriale)
- [ ] Batteria robot carica (>12V)
- [ ] Spazio libero sul pavimento — rimuovi ostacoli temporanei

---

## 9. Naming convention mappe

| Nome file | Descrizione |
|---|---|
| apss_map_v1 | Prima sessione mappatura |
| apss_map_v2 | Seconda sessione — aggiunta stanza X |
| apss_map_finale | Mappa completa approvata per navigazione |

---

## 10. Waypoint di pattugliamento APSS — Definitivi

Ordine di pattugliamento pianificato basato sulla planimetria reale:

| # | Stanza | Priorità | Note |
|---|---|---|---|
| 1 | Studio | HOME | Punto di partenza e docking station |
| 2 | Ingresso | Alta | Nodo centrale — controllo accessi |
| 3 | Salotto | Alta | Zona sorveglianza principale |
| 4 | Cucina | ⚠️ Critica | Rischio allagamento + gas |
| 5 | Corridoio | Media | Punto di passaggio zona notte |
| 6 | Lavanderia | ⚠️ Critica | Rischio allagamento |
| 7 | Bagno1 | ⚠️ Critica | Rischio allagamento |
| 8 | Letto1 | Media | Zona notte principale |
| 9 | Letto2 | Media | Zona notte secondaria |
| 10 | Bagno2 | ⚠️ Critica | Rischio allagamento |

### Zone critiche — comportamento robot
Nelle zone ⚠️ il robot durante il pattugliamento:
- Rileva umidità anomala via DHT-11 (segnale allagamento)
- Rileva gas via MQ-2/MQ-135 (perdita gas in cucina)
- Pubblica alert su /apss/sensors/env e /apss/sensors/gas
- Invia notifica immediata via MQTT all'app Kivy

### Note geometriche
- Larghezza robot: 29cm — compatibile con tutte le porte
- Bagni e Lavanderia: spazi stretti ma percorribili
- Partenza sempre da Studio (docking station) per odometria coerente

---

*Documento generato — APSS v0.14.0 — Aprile 2026*
