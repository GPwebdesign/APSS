# alarm_node.py — Documento di Pianificazione

**Progetto:** APSS — Autonomous Patrol and Surveillance System
**Data:** 2026-06-05
**Stato:** Pianificazione

---

## 1. Ruolo e Responsabilità

`alarm_node.py` è il **dispatcher centrale delle reazioni agli allarmi** pubblicati da `safety_node`.

- **Subscriber:** `/apss/alarm` (`std_msgs/String`, payload JSON)
- **Non valuta soglie** — reagisce esclusivamente a ciò che `safety_node` pubblica
- **Tre canali di output:**
  1. Voce sintetizzata via `piper-tts` (jack 3.5mm RPi4)
  2. Display OLED via topic `/apss/oled_alert`
  3. Storico allarmi su file JSON

### Gestione stato charging

Il campo `"charging"` nel JSON di `/apss/alarm` indica se il robot è in carica.
- Se `charging: true` → le reazioni agli allarmi TOF vengono **soppresse**
- Gli allarmi batteria e altri rimangono attivi indipendentemente dallo stato charging

---

## 2. Canali di Output

### 2.1 Voce — piper-tts

- **Output:** jack audio 3.5mm su RPi4
- **Lingua:** configurabile `it | en` tramite parametro `language` in `safety_rules.yaml`
- **Testi:** generati dinamicamente da template parametrici con variabili `{source}`, `{value}`, `{message}`
- **Template:** definiti in `safety_rules.yaml` sezione `alarm_node.templates`

**Comportamento allarmi multipli simultanei:**
- Parla solo il messaggio del livello più grave attivo
- Priorità: `EMERGENCY > CRITICAL > ERROR > LOW`

**Comportamento allarme rientrato:**
- Completa il messaggio vocale corrente
- Non emette ulteriori ripetizioni

**Verifica prerequisiti da fare su hawk:**
```bash
which piper
piper --version
ls ~/piper-voices/
```

---

### 2.2 OLED — topic `/apss/oled_alert`

- **Tipo:** `std_msgs/String` con payload JSON
- **Payload formato:**
  ```json
  {"messages": ["BAT LOW 11.42V", "TOF FRONT ERR"], "scroll": true}
  ```
- **Lista vuota** → `oled_node` torna alla visualizzazione statica `"APSS"` sulla prima riga
- `alarm_node` **non scrive direttamente** sull'OLED — `oled_node` è il solo owner del display

**Comportamento prima riga OLED:**

| Stato | Prima riga |
|-------|-----------|
| Allarmi attivi | Scrolling da destra verso sinistra con tutti i messaggi in sequenza |
| Nessun allarme | `"APSS"` statico |

---

### 2.3 Storico su File

- **Path:** `~/Workspaces/rosmaster_project/logs/alarm_history.json`
- **Politica:** FIFO 20 entry — quando si raggiungono 20, si elimina la più vecchia

**Formato entry:**
```json
{
  "ts": "2026-06-02 21:37:42",
  "level": "LOW",
  "source": "battery",
  "message": "Battery voltage below LOW threshold",
  "state": "onset"
}
```

Il campo `state` assume i valori:
- `onset` — allarme entra (transizione inattivo → attivo)
- `clear` — allarme rientra (transizione attivo → inattivo)

---

## 3. Mappatura Livelli → Reazione

| Livello   | Voce                          | Ripetizione (`repeat_s`) | OLED                             |
|-----------|-------------------------------|--------------------------|----------------------------------|
| LOW       | Template LOW                  | 30s                      | Riga aggiuntiva in scrolling     |
| CRITICAL  | Template CRITICAL             | 10s                      | Sostituisce prima riga           |
| EMERGENCY | Template EMERGENCY (SOS)      | 0 (continuo)             | Display dedicato                 |
| ERROR     | Template ERROR                | 60s                      | Riga aggiuntiva in scrolling     |

**Allarmi multipli simultanei:**
- **Voce:** parla il pattern del livello più grave (`EMERGENCY > CRITICAL > ERROR > LOW`)
- **OLED:** tutti i messaggi attivi vengono inseriti in lista e scorrono in sequenza

---

## 4. Configurazione in `safety_rules.yaml`

La sezione `alarm_node` viene aggiunta al file `safety_rules.yaml` esistente:

```yaml
alarm_node:
  language: it          # it | en
  voice_enabled: true
  log_path: ~/Workspaces/rosmaster_project/logs/alarm_history.json
  log_max_entries: 20

  templates:
    it:
      LOW:       "Attenzione, {source}. {message}. Valore attuale {value}."
      CRITICAL:  "Attenzione critica, {source}. {message}."
      EMERGENCY: "Emergenza {source}. {message}."
      ERROR:     "Errore rilevato: {source}. {message}."
    en:
      LOW:       "Warning, {source}. {message}. Current value {value}."
      CRITICAL:  "Critical alert, {source}. {message}."
      EMERGENCY: "Emergency {source}. {message}."
      ERROR:     "Sensor error: {source}. {message}."

  beep_patterns:
    LOW:       {repeat_s: 30}
    CRITICAL:  {repeat_s: 10}
    EMERGENCY: {repeat_s: 0}
    ERROR:     {repeat_s: 60}
```

---

## 5. Struttura Interna `alarm_node`

### `AlarmNode(rclpy.node.Node)`

**`__init__`:**
- Carica sezione `alarm_node` da `safety_rules.yaml` via `get_package_share_directory`
- Istanzia `VoiceManager`, `OledAlertPublisher`, `AlarmHistory`
- Crea subscriber `/apss/alarm`

---

### `VoiceManager`

- Carica template dalla configurazione YAML
- **`speak(alarm_dict)`** — espande template con `{source}`, `{value}`, `{message}`, chiama `piper-tts` via `subprocess`
- Gestisce timing di ripetizione per livello (`repeat_s`)
- **Voce bloccante:** completa il messaggio corrente prima di accettare un nuovo allarme dello stesso livello
- Parla solo il livello più grave tra gli allarmi attivi correnti

---

### `OledAlertPublisher`

- Publisher su `/apss/oled_alert` (`std_msgs/String`)
- **`update(alarms_list)`** — costruisce payload JSON e pubblica
- Lista vuota → pubblica `{"messages": [], "scroll": false}`

---

### `AlarmHistory`

- Carica/salva `~/Workspaces/rosmaster_project/logs/alarm_history.json`
- **`record(alarm_dict, state)`** — aggiunge entry, mantiene FIFO 20 entry
- Rileva `onset` / `clear` confrontando stato corrente con stato precedente memorizzato

---

### Callback `/apss/alarm`

Flusso di esecuzione:

```
1. Parsa JSON payload
2. Legge campo "charging"
3. Filtra allarmi TOF se charging=true
4. AlarmHistory.record() per onset/clear
5. OledAlertPublisher.update() con lista allarmi attivi
6. VoiceManager.speak() per il livello più grave
```

---

## 6. Modifiche ad Altri Nodi

### `oled_node.py`

- Aggiungere subscriber `/apss/oled_alert` (`std_msgs/String` JSON)
- **Se `messages` non vuota:** prima riga in scrolling con i messaggi in sequenza
- **Se `messages` vuota:** prima riga torna a `"APSS"` statico
- **Scrolling:** testo scorre da destra verso sinistra a velocità costante

### `safety_rules.yaml`

- Aggiungere sezione `alarm_node` con:
  - `templates` (it/en)
  - `beep_patterns`
  - `language`
  - `voice_enabled`
  - `log_path`
  - `log_max_entries`

---

## 7. Prerequisiti da Verificare su Hawk

```bash
# piper-tts installato
which piper && piper --version

# Voce italiana disponibile
ls ~/piper-voices/

# Directory log esistente
mkdir -p ~/Workspaces/rosmaster_project/logs/

# Uscita audio jack attiva
aplay -l
```

---

## 8. Prossimi Step Implementativi

In ordine di esecuzione:

1. **Verificare prerequisiti** `piper-tts` su hawk (sezione 7)
2. **Aggiornare `safety_rules.yaml`** con la sezione `alarm_node` (sezione 4)
3. **Implementare `alarm_node.py`** in `ros2_py_ws/src/apss_ros2_pkg/scripts/`
4. **Aggiungere `alarm_node.py` al `CMakeLists.txt`**
5. **Modificare `oled_node.py`** per subscriber `/apss/oled_alert` e scrolling (sezione 6)
6. **Colcon build + test integrato:**
   ```
   battery_node → safety_node → alarm_node → voce + OLED
   ```
7. **Integrare subscriber `/apss/alarm` in `rosmaster_main.py`** per Kivy poll
