# Esempio — Cleanup source fantasma

## Scenario

`label:list` mostra source_id che non esistono più in `notebook_get`. Sono "fantasmi"
residui da operazioni di ricarica/rimozione di fonti. Innocui ma sporcano i conteggi.

**Soglia consigliata per agire:** 3+ fantasmi accumulati, oppure refactoring schema label.

## ⚠️ Avvertenze critiche

Questa procedura è **distruttiva e non interrompibile a metà**:
- Cancella **tutte** le label esistenti
- Le label vanno **ricostruite manualmente** subito dopo
- Durante la ricostruzione, NON chiamare `label:list` o `label:auto`
  (riattiverebbero l'AI auto-labeling)

Tempo stimato: 5-10 minuti, ~20 chiamate API.

---

## Procedura passo passo

### Passo 0 — Inventario dei fantasmi

```python
nb = notebook_get(notebook_id="bc8dfeee-c3f0-412d-aa88-f8e0a4025fa5")
ll = label:list(notebook_id="bc8dfeee-c3f0-412d-aa88-f8e0a4025fa5")

source_validi = {s["id"] for s in nb["sources"]}
source_in_label = set()
for label in ll["labels"]:
    source_in_label.update(label["source_ids"])

fantasmi = source_in_label - source_validi
print(f"Source validi: {len(source_validi)}, in label: {len(source_in_label)}")
print(f"Fantasmi: {len(fantasmi)}")
```

Se `fantasmi` è vuoto → niente da pulire, esci.

### Passo 1 — Conferma utente

```
"Per pulire i N source fantasma serve un reset distruttivo delle label.
 Tutte le 6 label area verranno cancellate e ricreate da zero.
 Le 9 fonti restano intatte, ma le assegnazioni vanno rifatte.
 
 Tempo stimato: 5 minuti. Procediamo?"
```

**Attendi conferma esplicita ("sì", "procedi") prima di muoverti.**

### Passo 2 — Salva snapshot delle assegnazioni correnti

Dal `label:list` già recuperato, costruisci una mappa:

```python
snapshot = {}  # source_id (valido) -> [label_name, ...]
for label in ll["labels"]:
    for sid in label["source_ids"]:
        if sid in source_validi:  # ignora i fantasmi
            snapshot.setdefault(sid, []).append(label["name"])
```

Questa mappa servirà al Passo 7 per riassegnare i source nelle nuove label.

### Passo 3 — Reorganize distruttivo

```python
label:reorganize(
    action="reorganize",
    notebook_id="bc8dfeee-c3f0-412d-aa88-f8e0a4025fa5",
    unlabeled_only=False,
    confirm=True
)
```

⚠️ Dopo questo:
- Tutte le label vecchie sono cancellate (insieme ai fantasmi)
- NotebookLM AI ha creato N label nuove in inglese (es. "Project Management", "Hardware Design")
- I source sono assegnati a queste label AI

### Passo 4 — Cancella le label AI

```python
# Dall'output di reorganize, estrai gli ID delle label AI
ai_label_ids = [l["id"] for l in reorganize_output["labels"]]

label:delete(
    action="delete",
    notebook_id="bc8dfeee-c3f0-412d-aa88-f8e0a4025fa5",
    label_ids=ai_label_ids,
    confirm=True
)
```

⚠️ **NON chiamare `label:list` qui!** Triggererebbe auto-labeling di nuovo. Vai diretto al Passo 5.

### Passo 5 — Crea le 6 label area APSS

```python
label_specs = [
    ("overview", "📘"),
    ("onboarding-ai", "🤖"),
    ("roadmap", "🗺️"),
    ("session-log", "📝"),
    ("workflow-git", "🔄"),
    ("hardware-docking", "🔌"),
]

new_label_ids = {}
for name, emoji in label_specs:
    r = label:create(action="create", notebook_id="...", name=name)
    new_label_ids[name] = r["label_id"]
    label:set_emoji(
        action="set_emoji",
        notebook_id="...",
        label_id=r["label_id"],
        emoji=emoji
    )
```

### Passo 6 — Riassegna i source

Per ogni source valido, applica la sua label area (dal snapshot del Passo 2 oppure
da tabella canonica `@references/notebook-constants.md`):

```python
# Mappa source → label area
source_to_label = {
    "e2068f37-...": "overview",       # APSS_Documentazione_Tecnica_v2_2.docx
    "330838dd-...": "overview",       # architecture.md
    "5ddedb66-...": "onboarding-ai",  # CLAUDE.md
    "38293aac-...": "roadmap",        # plan.md
    "326f0e30-...": "session-log",    # APSS_riepilogo_sessione_mag2026_3.md
    "28d05d12-...": "session-log",    # APSS_memorie.md
    "2c9b15b2-...": "workflow-git",   # APSS_allineamento_ RPi-PC-GitHub.md
    "d0da390f-...": "workflow-git",   # APSS_allineamento_RPi-VMware-GitHub.md
    "3141e7b2-...": "hardware-docking", # Schema Circuitale
}

for source_id, label_name in source_to_label.items():
    label:move_source(
        action="move_source",
        notebook_id="...",
        label_id=new_label_ids[label_name],
        source_id=source_id
    )
```

### Passo 7 — Verifica finale

```python
ll_new = label:list(notebook_id="...")
nb_new = notebook_get(notebook_id="...")

source_in_label_new = set()
for label in ll_new["labels"]:
    source_in_label_new.update(label["source_ids"])

assert len(source_in_label_new) == nb_new["notebook"]["source_count"]
assert len(ll_new["labels"]) == 6  # 6 label area attese
```

Se gli assert passano → pulizia riuscita, zero fantasmi.

### Passo 8 — Aggiorna `notebook-constants.md`

I `label_id` sono cambiati (nuove label create). Aggiorna la tabella label nel file
delle costanti:

```python
Filesystem:write_file(
    path="D:\\_claudecodeproject\\APSS\\.claude\\skills\\apss-notebooklm-sync\\references\\notebook-constants.md",
    content=...  # con nuovi label_id e data aggiornata
)
```

### Passo 9 — Aggiorna nota di onboarding (se schema cambiato)

Se la pulizia è stata anche occasione di refactoring schema (es. doppio→singolo
labeling), aggiorna la mappa nella nota:

```python
note:update(
    action="update",
    notebook_id="...",
    note_id="56fcad43-...",
    title="📍 Onboarding — Come navigare questo notebook",
    content=...
)
```

### Passo 10 — Suggerisci commit

```
"✅ Cleanup completato. N fantasmi rimossi, 6 label ricostruite, 9 source assegnati.
 Ho aggiornato notebook-constants.md con i nuovi label_id.
 Vuoi committare la skill aggiornata su GitHub?"
```

---

## Storico — Sessione 14 Mag 2026

Primo cleanup ghost eseguito su APSS NotebookLM:

| Dato | Valore |
|---|---|
| Fantasmi rimossi | 4 (vecchi `APSS_memorie`, `architecture`, `plan`, `Doc_v2_1`) |
| Label vecchie cancellate | 8 (era schema doppio: area + stato) |
| Label nuove create | 6 (schema singolo: solo area) |
| Tempo totale | ~5 minuti |
| Esito | ✅ Conteggi puliti (9 source = 9 source_ids in label) |
| Lezione | Auto-labeling AI scatta anche su `label:list` post-delete totale |

---

## Variante — Cleanup senza refactoring schema

Se vuoi solo pulire i fantasmi mantenendo lo schema esistente:
- Passo 5 → ricrea le label **identiche** a prima (stessi nomi + emoji)
- Passo 6 → riassegna **dallo snapshot** (Passo 2), non da tabella canonica
- Passo 8 → solo aggiornare i `label_id` nel file delle costanti

Tutto il resto identico. Tempo: invariato (~20 chiamate API).
