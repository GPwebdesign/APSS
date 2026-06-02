# safety_node.py — Piano di Implementazione

**Progetto**: APSS — Autonomous Patrol and Surveillance System  
**Data**: 2026-06-02  
**Versione**: 1.0

---

## 1. Ruolo e Responsabilità

`safety_node.py` è l'aggregatore centrale di condizioni di allarme per tutti i componenti APSS.

**Responsabilità**:
- Monitora topic ROS2 configurati via YAML e valuta regole dichiarative
- Pubblica `/apss/alarm` (`std_msgs/String` JSON) a 0.5 Hz — sempre, anche a lista vuota
- Lista vuota in `alarms` = sistema OK
- **Non decide le reazioni**: rileva e pubblica. `alarm_node` decide come reagire

**Principio architetturale**: motore generico con regole dichiarative YAML. Aggiungere una nuova sorgente di allarme non richiede modifiche al codice Python — solo una voce in `safety_rules.yaml`.

---

## 2. Livelli di Allarme

| Livello | Significato |
|---------|-------------|
| `LOW` | Attenzione — nessuna azione urgente richiesta |
| `CRITICAL` | Condizione critica — azione necessaria a breve |
| `EMERGENCY` | Emergenza — azione immediata richiesta |
| `ERROR` | Errore di sistema (topic stale, frozen, mai ricevuto) |

---

## 3. Tipi di Regola

| Tipo | Trigger |
|------|---------|
| `threshold_low` | Allarme se `valore < soglia` |
| `threshold_high` | Allarme se `valore > soglia` |
| `frozen` | Allarme se il valore non cambia per N campioni consecutivi (tolleranza configurabile) |
| `boolean` | Allarme se il campo è `True` |

> **Nota**: `timeout` e `staleness` **non** sono tipi separati. Sono comportamento automatico di ogni regola tramite i parametri `watchdog_timeout_s` e `staleness_s`, con il flag `ever_received`.

---

## 4. Struttura Interna

Il nodo è composto da tre componenti principali.

### 4.1 RuleEngine

- Carica il YAML al boot
- Istanzia un valutatore per ogni regola in base al campo `type`
- I valutatori sono oggetti autonomi: stato, logica e parametri autocontenuti
- Valuta tutte le regole ad ogni tick del publisher loop
- Per le regole `threshold_low`/`threshold_high` con soglie multiple, valuta dal valore più critico al meno critico (restituisce solo il primo match)

### 4.2 TopicMonitor

- Subscribe dinamicamente ai topic unici presenti nelle regole (un subscriber per topic)
- Per ogni topic tracciato mantiene:

| Campo | Tipo | Descrizione |
|-------|------|-------------|
| `last_value` | `float \| bool \| None` | Ultimo valore ricevuto |
| `last_ts` | `float \| None` | Timestamp `time.time()` ultimo messaggio |
| `ever_received` | `bool` | True dopo il primo messaggio |
| `sample_buffer` | `deque` | Buffer campioni per valutatori `frozen` |

- Estrae il campo dal messaggio via `getattr(msg, field)`
- I buffer campioni per `frozen` vivono nel valutatore (per-regola), non in `TopicMonitor`

### 4.3 Publisher Loop

- Timer ROS2 a `publish_rate_hz` (default 0.5 Hz)
- Ad ogni tick:
  1. Legge stato charging da `/battery`
  2. `RuleEngine` valuta tutte le regole
  3. Costruisce payload JSON
  4. Pubblica su `/apss/alarm`

---

## 5. Formato Messaggio `/apss/alarm`

**Topic**: `/apss/alarm`  
**Tipo**: `std_msgs/String`  
**Payload**: JSON

```json
{
  "ts": "2026-05-29 21:37:42",
  "alarms": [
    {
      "source": "battery",
      "level": "LOW",
      "type": "threshold_low",
      "value": 11.42,
      "threshold": 11.50,
      "message": "Battery voltage below LOW threshold"
    }
  ]
}
```

| Campo | Formato / Note |
|-------|---------------|
| `ts` | `YYYY-MM-DD HH:MM:SS` |
| `alarms` | Lista vuota `[]` = sistema OK |
| `value` | `-1.0` per regole `boolean` |
| `threshold` | `-1.0` per regole `boolean` |

---

## 6. Gestione Charging

- `safety_node` rileva lo stato charging da `/battery` tramite:  
  `charging = (battery.current < -0.05A)`
- Le regole con `active_when_charging: false` (es. `battery_voltage`) vengono saltate durante la carica
- Per i sensori TOF: `safety_node` pubblica sempre. È `alarm_node` a decidere la reazione in base allo stato charging ricevuto nel messaggio

---

## 7. Gestione Edge Case

### Boot / Grace Period

- `grace_period_s: 30` nei `global` del YAML
- Nei primi 30 secondi, `ever_received=False` **non** genera allarme ERROR
- Dopo il grace period: `ever_received=False` → ERROR "topic never started"

### Staleness vs Timeout (unificati)

| Condizione | Allarme generato |
|------------|-----------------|
| `ever_received=False` dopo grace period | ERROR — "topic never started" |
| `ever_received=True` e `(now - last_ts) > staleness_s` | ERROR — "topic stale" |

### Frozen

- Il buffer viene riempito progressivamente
- Buffer non ancora pieno → **nessun allarme** (non è una condizione di errore, è attesa dati)

---

## 8. Mappatura MSG_TYPE

Dizionario esplicito nel codice Python:

```python
MSG_TYPE_MAP = {
    'sensor_msgs/BatteryState': BatteryState,
    'sensor_msgs/Range': Range,
}
```

Ogni nuovo tipo di messaggio richiede:
1. Import nella sezione `import` del nodo
2. Voce nel dizionario `MSG_TYPE_MAP`

Limite accettabile e documentato: la mappa è intenzionalmente esplicita per evitare import dinamici non tracciabili.

---

## 9. File YAML delle Regole

**Path nel repo**: `ros2_py_ws/src/apss_ros2_pkg/config/safety_rules.yaml`  
**Caricamento a runtime**: `get_package_share_directory('apss_ros2_pkg')`  
**Installazione**: `ament_cmake` con `install(DIRECTORY config/)`

### Contenuto completo `safety_rules.yaml`

```yaml
global:
  publish_rate_hz: 0.5
  grace_period_s: 30
  charging_topic: /battery
  charging_field: current
  charging_threshold: -0.05

rules:
  - id: battery_voltage
    source: battery
    topic: /battery
    msg_type: sensor_msgs/BatteryState
    field: voltage
    type: threshold_low
    active_when_charging: false
    watchdog_timeout_s: 10
    staleness_s: 10
    thresholds:
      - value: 11.50
        level: LOW
        message: "Battery voltage below LOW threshold"
      - value: 11.20
        level: CRITICAL
        message: "Battery voltage below CRITICAL threshold"
      - value: 10.80
        level: EMERGENCY
        message: "Battery voltage below EMERGENCY threshold"

  - id: tof_front_frozen
    source: tof_front
    topic: /tof/front
    msg_type: sensor_msgs/Range
    field: range
    type: frozen
    frozen_samples: 5
    frozen_tolerance: 0.001
    watchdog_timeout_s: 5
    staleness_s: 5
    level: ERROR
    message: "TOF front frozen — possible I2C lockup"

  - id: tof_left_frozen
    source: tof_left
    topic: /tof/left
    msg_type: sensor_msgs/Range
    field: range
    type: frozen
    frozen_samples: 5
    frozen_tolerance: 0.001
    watchdog_timeout_s: 5
    staleness_s: 5
    level: ERROR
    message: "TOF left frozen — possible I2C lockup"

  - id: tof_right_frozen
    source: tof_right
    topic: /tof/right
    msg_type: sensor_msgs/Range
    field: range
    type: frozen
    frozen_samples: 5
    frozen_tolerance: 0.001
    watchdog_timeout_s: 5
    staleness_s: 5
    level: ERROR
    message: "TOF right frozen — possible I2C lockup"
```

---

## 10. Integrazione con Altri Componenti

| Componente | Ruolo rispetto a `/apss/alarm` |
|------------|-------------------------------|
| `alarm_node.py` | Subscriber `/apss/alarm` — dispatcher reazioni (beeper Yahboom + OLED) — mantiene storico ultime 20 condizioni su file |
| `rosmaster_main.py` | Subscriber `/apss/alarm` — mantiene ultimo stato in memoria per poll TCP da app Kivy |
| App Kivy | Poll periodico TCP ogni ~5s — mostra stato corrente in `AlertScreen` (no storico) |

---

## 11. Prossimi Step Implementativi

Ordine di esecuzione:

1. Creare `safety_rules.yaml` in `ros2_py_ws/src/apss_ros2_pkg/config/`
2. Aggiornare `CMakeLists.txt` con `install(DIRECTORY config/)`
3. Implementare `safety_node.py` in `ros2_py_ws/src/apss_ros2_pkg/scripts/`
4. Aggiungere `safety_node` al `CMakeLists.txt` (entry point)
5. `colcon build` + test con `battery_node` attivo su hawk
6. Implementare `alarm_node.py`
7. Aggiungere subscriber `/apss/alarm` in `rosmaster_main.py`
