# Schema Label NotebookLM APSS

## Principio (schema singolo — Mag 2026)

**Singolo labeling per AREA:** ogni fonte ha **esattamente 1 label** che descrive il dominio di contenuto.

Lo **stato** (stabile vs in evoluzione) si capisce dal nome del file stesso:
- File con `_v2_X` nel nome → revisione, indica documento "reference"
- File con `_sessione_mag2026_N` → log temporale, indica "in-corso"
- File `plan.md` → roadmap, sempre in evoluzione
- Altri (`architecture.md`, `CLAUDE.md`, schemi `.pdf`) → reference per default

### Perché schema singolo invece di doppio

Lo schema originale era doppio (area + stato), ma è stato semplificato a singolo dopo
test reali (vedi `@examples/cleanup-ghosts.md`):
- **Manutenzione 2x più costosa** (2 assegnazioni per source invece di 1)
- **Superficie doppia per i bug fantasma** (8 label invece di 6)
- **Valore informativo dello stato basso** — si deduce comunque dal filename
- **Auto-labeling AI di NotebookLM** non rispetta lo schema doppio dopo `reorganize` distruttivo

---

## Label per AREA

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
- `hardware-robot` 🔧 → schemi/foto del robot stesso (oggi tutto sta in overview/Documentazione Tecnica)
- `code-snippets` 💻 → snippet di codice riusabili
- `troubleshooting` 🩺 → soluzioni a problemi ricorrenti

---

## Tabella di mapping operativo

Quando una nuova fonte viene aggiunta, applicare questo flowchart:

```
È un .docx/.pdf di documentazione master?           → 📘 overview
È istruzioni operative per AI (CLAUDE.md-like)?     → 🤖 onboarding-ai
È un plan/roadmap con task tracking?                → 🗺️ roadmap
È un log di sessione/memorie storiche?              → 📝 session-log
È un file su Git workflow/repo alignment?           → 🔄 workflow-git
È uno schema elettrico della docking station?       → 🔌 hardware-docking
Altro?                                              → CHIEDI all'utente prima di creare nuove label
```

---

## Convenzioni nomi

- **Nome label:** una parola lowercase, eventualmente kebab-case (es. `workflow-git`, `onboarding-ai`)
- **Emoji:** sempre 1 emoji, scelta perché evoca la categoria senza ambiguità
- **Niente label con prefisso `stato: `** — questo era lo schema vecchio, non riproporlo

---

## Verifica coerenza

Dopo modifiche alle label, eseguire:

```python
label:list(notebook_id="bc8dfeee-c3f0-412d-aa88-f8e0a4025fa5")
notebook_get(notebook_id="bc8dfeee-c3f0-412d-aa88-f8e0a4025fa5")
```

Controlli (schema singolo):
1. **Ogni fonte ha esattamente 1 label?**
   La somma dei source_ids in tutte le label deve essere uguale a `source_count`.
   Se è maggiore → ci sono fantasmi o doppie assegnazioni.
2. **Nessuna fonte ha 2 aree contemporaneamente?**
   Una fonte = 1 area, sempre. Se cambi area, prima rimuovi da quella vecchia
   (ma attenzione: l'API non ha `unassign` — l'unico modo è `reorganize` distruttivo).
3. **Tutti i 6 label hanno almeno 1 source assegnato?**
   Label vuote sono OK ma segnalano possibili refactoring (forse area inutile).

---

## Comportamento auto-labeling AI di NotebookLM

⚠️ **Attenzione:** NotebookLM ha un'AI di auto-labeling che si attiva in alcune condizioni:

| Trigger | Effetto |
|---|---|
| `label:auto` esplicito | Genera label inglesi generiche (es. "Project Synchronization") |
| `label:reorganize unlabeled_only=false confirm=true` | Cancella tutte le label e ricrea da AI |
| `label:list` quando nessuna label esiste | **Trigger nascosto:** ricrea label AI |
| Cancellazione di TUTTE le label | Al successivo `list`, AI le rigenera |

**Implicazione pratica:** se devi fare un reset distruttivo, **non chiamare `list` tra `delete` e `create`** — l'AI ti rigenerebbe le label inglesi che dovresti poi cancellare di nuovo. Vai diretto a `create` con le tue label.
