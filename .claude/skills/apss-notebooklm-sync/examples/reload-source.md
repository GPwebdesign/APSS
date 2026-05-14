# Esempio — Ricarica fonte modificata

## Scenario

L'utente ha modificato `D:\_claudecodeproject\APSS\docs\architecture.md` sul PC
e vuole che il notebook abbia la versione aggiornata.

## ⚠️ Punto critico

**NotebookLM non aggiorna automaticamente** una fonte dopo modifica del file su disco.
Anche se ricarichi lo stesso file con lo stesso nome:
- Il **vecchio source viene rimosso** dal notebook
- Il **nuovo source ha un ID diverso**
- **Tutte le label assegnate al vecchio source vengono perse**
- Le label vanno **riassegnate manualmente** al nuovo source_id
- ⚠️ Il vecchio source_id può rimanere **fantasma** nelle label (vedi sezione finale)

---

## Procedura passo passo

### Passo 1 — Recupera label correnti del source

Prima di qualsiasi azione di rimozione, **annota la label** che il source ha attualmente:

```python
label:list(notebook_id="bc8dfeee-c3f0-412d-aa88-f8e0a4025fa5")
```

Esempio output rilevante (schema singolo Mag 2026):
```
- overview (📘) source_ids: [..., "330838dd-5f20-4a6c-99ec-f7c9e3d3d9a1", ...]
```

Annota: `architecture.md` ha label `📘 overview`.

### Passo 2 — Comunica all'utente cosa deve fare

```
"Per aggiornare `architecture.md` nel notebook:
 1. Apri https://notebooklm.google.com/notebook/bc8dfeee-c3f0-412d-aa88-f8e0a4025fa5
 2. Rimuovi la fonte `architecture.md` esistente (cestino accanto al nome)
 3. Carica di nuovo il file aggiornato `D:\_claudecodeproject\APSS\docs\architecture.md`
 4. Quando hai finito, dimmi 'fatto' e io riassegno la label.

 La label da riapplicare è: 📘 overview"
```

### Passo 3 — Attendi conferma utente "fatto"

NON procedere prima della conferma. L'utente deve realmente fare le operazioni nel browser.

### Passo 4 — Recupera nuovo source_id

```python
notebook_get(notebook_id="bc8dfeee-c3f0-412d-aa88-f8e0a4025fa5")
```

Trova `title="architecture.md"` → annota il **nuovo** `id` (sarà diverso dal precedente).

Esempio nuovo ID: `c8e9d1a2-5f4b-...`

### Passo 5 — Riassegna la label (1 sola, schema singolo)

```python
label:move_source(
    action="move_source",
    notebook_id="bc8dfeee-c3f0-412d-aa88-f8e0a4025fa5",
    label_id="409f12c9-72f8-4cf4-8301-f081158ce4b3",  # overview
    source_id="c8e9d1a2-5f4b-..."  # NUOVO id
)
```

### Passo 6 — Verifica + controllo fantasmi

```python
label:list(notebook_id="bc8dfeee-c3f0-412d-aa88-f8e0a4025fa5")
notebook_get(notebook_id="bc8dfeee-c3f0-412d-aa88-f8e0a4025fa5")
```

**Doppio controllo:**

1. **Il nuovo source_id è sotto la label corretta?** ✅
2. **Conteggio fantasmi:**
   ```
   somma source_ids in tutte le label  vs  source_count del notebook
   ```
   Se la somma è MAGGIORE del source_count → ci sono source fantasma (il vecchio
   source_id `330838dd-...` è rimasto nella label).
   
   In schema singolo: somma == source_count. Se è diverso, agisci.

### Passo 7 — Aggiorna `references/notebook-constants.md`

Sostituisci il vecchio `source_id` con il nuovo nella tabella source.
Aggiorna anche la data "Ultimo aggiornamento".

### Passo 8 — Conferma all'utente

```
"✅ architecture.md ricaricato e riassegnato a 📘 overview.
 Ho aggiornato anche `notebook-constants.md` con il nuovo source_id.
 Conteggio post-operazione: N source, M source_ids in label (✅ allineati)"
```

---

## Variante — Ricarica multipla (3+ fonti)

Se l'utente vuole ricaricare più fonti insieme (es. dopo un `git commit` con
modifiche a `architecture.md` + `plan.md` + `APSS_memorie.md`):

```
"Per evitare confusione sugli ID, ti consiglio:
 1. Rimuovi TUTTE le fonti che vuoi aggiornare dal notebook (in un colpo)
 2. Ricarica TUTTE quelle aggiornate (in un colpo)
 3. Dimmi 'fatte tutte' e io faccio un giro di notebook_get + label:list
    e riassegno tutte le label in batch.
 
 Le label correnti per ciascuna fonte sono:
  - architecture.md  → 📘 overview
  - plan.md          → 🗺️ roadmap
  - APSS_memorie.md  → 📝 session-log"
```

⚠️ **Dopo ricarica multipla, controllo fantasmi obbligatorio** (vedi sotto). Quanti più
file ricarichi insieme, più probabile l'accumulo di fantasmi.

---

## ⚠️ Source fantasma — sezione dedicata

### Cosa sono

Quando una fonte viene rimossa dal browser, NotebookLM **rimuove il source** ma **non
pulisce automaticamente i riferimenti nelle label**. Il vecchio `source_id` resta come
"fantasma" in `label:list` ma non compare più in `notebook_get`.

### Come rilevarli

```python
nb = notebook_get(notebook_id="...")  # source_count = N
ll = label:list(notebook_id="...")    # somma source_ids = M

# Schema singolo: ogni source ha 1 label, quindi M dovrebbe essere == N
# Se M > N → ci sono (M - N) source fantasma
```

Anche identificabile per esclusione: confrontare i `source_id` in `label:list` con
quelli in `notebook_get` — quelli che compaiono solo in `label:list` sono fantasmi.

### Come pulirli

⚠️ **Non esiste un'API "unassign source from label"**. Le opzioni:

| Approccio | Pro | Contro |
|---|---|---|
| Lasciarli stare | Innocui, nascosti nell'UI browser | Sporcano i conteggi API |
| `move_source` su source fantasma | Tentativo no-op | Non funziona (success ma fantasma resta) |
| `reorganize unlabeled_only=true` | Sicuro | Non tocca fantasmi |
| **`reorganize unlabeled_only=false confirm=true`** | Pulisce davvero | **Distruttivo: cancella tutte le label** |

**Se i fantasmi danno fastidio:** usa la procedura completa in `@examples/cleanup-ghosts.md`
(reorganize distruttivo + ricostruzione manuale delle label).

### Quando pulire e quando no

| Situazione | Decisione |
|---|---|
| 1-2 fantasmi dopo reload singolo | Lascia stare, innocui |
| 3+ fantasmi accumulati | Considera cleanup |
| Conteggi API rotti / confusione utente | Cleanup |
| Refactoring schema label | Cleanup (occasione perfetta) |

---

## Gotcha specifico — Stesso nome, source diversi

Se per qualche motivo nel notebook ci sono **2 fonti con lo stesso titolo** (es. dimenticando di rimuovere la vecchia prima di ricaricare):

```python
notebook_get(notebook_id="...")
# sources: [
#   {id: "330838dd-...", title: "architecture.md"},   # vecchia
#   {id: "c8e9d1a2-...", title: "architecture.md"}    # nuova
# ]
```

**NON applicare label alla nuova prima di aver chiarito con l'utente!**

```
"⚠️ Trovo 2 fonti con titolo `architecture.md` nel notebook.
 Una ha la label vecchia, l'altra è nuova. Devi rimuovere la vecchia dal browser
 prima che io applichi la label alla nuova."
```
