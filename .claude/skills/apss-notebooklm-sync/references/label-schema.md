# Schema Label NotebookLM APSS

## Principio

**Doppio labeling:** ogni fonte ha **esattamente 2 label**:
- 1 label di **AREA** (cosa tratta il documento)
- 1 label di **STATO** (come evolve nel tempo)

Le label sono **non gerarchiche** in NotebookLM — un source può essere in più label. La regola "2 label per source" è una convenzione del progetto APSS, non un vincolo tecnico.

---

## Label per AREA

Le label di area descrivono **il dominio del contenuto**. Ogni fonte appartiene a esattamente 1 area.

| Label | Emoji | Quando usarla |
|---|---|---|
| `overview` | 📘 | Visione d'insieme tecnica del progetto (documentazione master, architettura) |
| `onboarding-ai` | 🤖 | Istruzioni operative per assistenti AI (regole, vincoli, gotcha prescrittivi) |
| `roadmap` | 🗺️ | Pianificazione fasi, milestone, task tracking |
| `session-log` | 📝 | Log di sessioni, memorie storiche, snapshot temporali |
| `workflow-git` | 🔄 | Sincronizzazione repository, workflow di sviluppo |
| `hardware-docking` | 🔌 | Schemi elettrici, componenti hardware specifici della docking station |

### Quando creare una nuova label di AREA

Crea una nuova area solo se:
1. Le label esistenti **non sono appropriate** (forzare un fit causa confusione)
2. Ci sono **almeno 2 fonti** che la useranno (sotto soglia è prematura)
3. L'utente ha **esplicitamente confermato** la creazione

Areas potenziali future (non ancora create):
- `hardware-robot` 🤖 → schemi/foto del robot stesso (oggi tutto sta in overview/Documentazione Tecnica)
- `code-snippets` 💻 → snippet di codice riusabili
- `troubleshooting` 🩺 → soluzioni a problemi ricorrenti

> ⚠️ NB: l'emoji 🤖 è già usato per `onboarding-ai`. Se creo `hardware-robot` userò un'altra emoji.

---

## Label per STATO

Le label di stato descrivono **come evolve la fonte nel tempo**. Ogni fonte appartiene a esattamente 1 stato.

| Label | Emoji | Quando usarla |
|---|---|---|
| `stato: reference` | 📚 | Documentazione stabile, cambia raramente (architettura consolidata, schemi elettrici, regole) |
| `stato: in-corso` | ⚙️ | Documenti che cambiano ad ogni sessione (plan, riepiloghi sessione attiva) |

### Regola di classificazione stato

| Domanda da farsi | Risposta SI → label |
|---|---|
| Questo file lo modificherò nelle prossime 2-3 sessioni? | ⚙️ in-corso |
| Questo file è stato modificato nelle ultime 2-3 sessioni? | ⚙️ in-corso |
| Questo file resta stabile per mesi? | 📚 reference |
| Schema elettrico/protocollo consolidato? | 📚 reference |

### Possibile evoluzione futura

Quando una fase si chiude, una label `stato: completato` ✅ avrà senso per archiviare fonti che descrivono fasi finite ma ancora utili come reference storica. Per ora i due stati bastano.

---

## Tabella di mapping operativo

Quando una nuova fonte viene aggiunta, applicare questo flowchart:

```
È un .docx/.pdf di documentazione master?           → overview + reference
È istruzioni operative per AI (CLAUDE.md-like)?     → onboarding-ai + reference
È un plan/roadmap con task tracking?                → roadmap + (in-corso se attivo, altrimenti reference)
È un log di sessione/memorie storiche?              → session-log + (in-corso se ultima sessione, altrimenti reference)
È un file su Git workflow/repo alignment?           → workflow-git + reference
È uno schema elettrico della docking station?       → hardware-docking + reference
Altro?                                              → CHIEDI all'utente prima di creare nuove label
```

---

## Convenzioni nomi e separatori

- **Nome label area:** una parola lowercase, eventualmente kebab-case (es. `workflow-git`, `onboarding-ai`)
- **Nome label stato:** `stato: <valore>` con **separatore `: `** (due punti + spazio)
  - ✅ `stato: reference`
  - ❌ `stato:reference` (senza spazio)
  - ❌ `Stato: Reference` (maiuscole)
- **Emoji:** sempre 1 emoji, scelta perché evoca la categoria senza ambiguità

---

## Verifica coerenza

Dopo modifiche alle label, eseguire:

```python
label:list(notebook_id="bc8dfeee-c3f0-412d-aa88-f8e0a4025fa5")
```

Controlli:
1. **Tutte le fonti hanno almeno 1 area + 1 stato?**
   Calcola: per ogni source_id nelle aree, verifica che compaia anche in uno stato
2. **Nessuna fonte ha 2 aree contemporaneamente?**
   (Se sì, è un errore di assegnazione: una fonte = 1 area, salvo eccezione esplicita)
3. **Nessuna fonte ha 2 stati contemporaneamente?**
   (in-corso E reference insieme è un errore)
