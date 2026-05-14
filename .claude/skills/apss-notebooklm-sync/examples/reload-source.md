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

Questo è il workflow corretto.

---

## Procedura passo passo

### Passo 1 — Recupera label correnti del source

Prima di qualsiasi azione di rimozione, **annota le label** che il source ha attualmente:

```python
label:list(notebook_id="bc8dfeee-c3f0-412d-aa88-f8e0a4025fa5")
```

Esempio output rilevante:
```
- overview         (📘) source_ids: [..., "197d8817-bcd3-488f-8226-8dc0a45b68e8", ...]
- stato: reference (📚) source_ids: [..., "197d8817-bcd3-488f-8226-8dc0a45b68e8", ...]
```

Annota: `architecture.md` ha label `📘 overview` + `📚 stato: reference`.

### Passo 2 — Comunica all'utente cosa deve fare

```
"Per aggiornare `architecture.md` nel notebook:
 1. Apri https://notebooklm.google.com/notebook/bc8dfeee-c3f0-412d-aa88-f8e0a4025fa5
 2. Rimuovi la fonte `architecture.md` esistente (cestino accanto al nome)
 3. Carica di nuovo il file aggiornato `D:\_claudecodeproject\APSS\docs\architecture.md`
 4. Quando hai finito, dimmi 'fatto' e io riassegno le label.

 Le label da riapplicare sono: 📘 overview + 📚 stato: reference"
```

### Passo 3 — Attendi conferma utente "fatto"

NON procedere prima della conferma. L'utente deve realmente fare le operazioni nel browser.

### Passo 4 — Recupera nuovo source_id

```python
notebook_get(notebook_id="bc8dfeee-c3f0-412d-aa88-f8e0a4025fa5")
```

Trova `title="architecture.md"` → annota il **nuovo** `id` (sarà diverso da `197d8817-...`).

Esempio nuovo ID: `c8e9d1a2-5f4b-...`

### Passo 5 — Riassegna le label

Una chiamata `label:move_source` per ogni label che il source aveva prima:

```python
# Label area: overview
label:move_source(
    action="move_source",
    notebook_id="bc8dfeee-c3f0-412d-aa88-f8e0a4025fa5",
    label_id="56502c2f-97d6-43dd-91e6-1fef9beb425c",  # overview
    source_id="c8e9d1a2-5f4b-..."  # NUOVO id
)

# Label stato: reference
label:move_source(
    action="move_source",
    notebook_id="bc8dfeee-c3f0-412d-aa88-f8e0a4025fa5",
    label_id="d385b616-8a47-42d5-9e27-109a36660fca",  # stato: reference
    source_id="c8e9d1a2-5f4b-..."  # NUOVO id
)
```

### Passo 6 — Verifica

```python
label:list(notebook_id="bc8dfeee-c3f0-412d-aa88-f8e0a4025fa5")
```

Controlla che il nuovo source_id sia sotto entrambe le label e il vecchio source_id sia sparito.

### Passo 7 — Aggiorna `references/notebook-constants.md`

Sostituisci il vecchio `source_id` con il nuovo nella tabella source.

### Passo 8 — Conferma all'utente

```
"✅ architecture.md ricaricato e riassegnato a:
   - 📘 overview
   - 📚 stato: reference
 
 Ho anche aggiornato `notebook-constants.md` con il nuovo source_id."
```

---

## Variante — Ricarica multipla

Se l'utente vuole ricaricare 3-4 fonti insieme, suggerisci batching manuale:

```
"Per evitare confusione sugli ID, ti consiglio:
 1. Rimuovi tutte le fonti che vuoi aggiornare dal notebook
 2. Ricarica tutte quelle aggiornate
 3. Dimmi 'fatte tutte' e io faccio un giro di notebook_get + label:list
    e riassegno tutte le label in batch.
 
 Ti serve la lista delle label correnti per ciascuna fonte?"
```

---

## Gotcha specifico — Stesso nome, source diversi

Se per qualche motivo nel notebook ci sono **2 fonti con lo stesso titolo** (es. dimenticando di rimuovere la vecchia prima di ricaricare):

```python
notebook_get(notebook_id="...")
# sources: [
#   {id: "197d8817-...", title: "architecture.md"},   # vecchia
#   {id: "c8e9d1a2-...", title: "architecture.md"}    # nuova
# ]
```

**NON applicare label alla nuova prima di aver chiarito con l'utente!**

```
"⚠️ Trovo 2 fonti con titolo `architecture.md` nel notebook.
 Una ha le label vecchie, l'altra è nuova. Devi rimuovere la vecchia dal browser
 prima che io applichi le label alla nuova."
```
