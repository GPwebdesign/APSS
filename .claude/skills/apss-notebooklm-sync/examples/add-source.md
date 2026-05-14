# Esempio — Aggiunta nuova fonte

## Scenario

L'utente ha creato un nuovo file `D:\_claudecodeproject\APSS\docs\nuovo_doc.md`
e vuole aggiungerlo al notebook.

## Procedura passo passo

### Passo 1 — Verifica esistenza e contenuto

```python
Filesystem:get_file_info(path="D:\\_claudecodeproject\\APSS\\docs\\nuovo_doc.md")
Filesystem:read_text_file(path="D:\\_claudecodeproject\\APSS\\docs\\nuovo_doc.md", head=50)
```

Leggi le prime righe per capire:
- **Tipo di contenuto** (è documentazione? log? schema?)
- **Sensibilità** (contiene credenziali? IP privati? token?)
- **Area di pertinenza** (vedi `@references/label-schema.md`)

### Passo 2 — Verifica esclusioni

Controlla che NON sia uno dei file da escludere:
- `CLAUDE.local.md` o varianti `*local*`
- File con stringhe come `password`, `token`, `secret`, `ssh_key`, `api_key`
- File temporanei (`.bak`, `.tmp`)

Se sospetti credenziali → **NON aggiungerlo e segnala all'utente**.

### Passo 3 — Proponi label

In base al contenuto, proponi label area + stato:

```
"Ho letto `nuovo_doc.md` — sembra un log di una sessione di test motori.
Proporrei queste label:
  - Area:  📝 session-log
  - Stato: ⚙️ stato: in-corso  (perché documenta una fase attiva)

Va bene o preferisci diversamente?"
```

**Attendi conferma utente.**

### Passo 4 — Carica manualmente (utente)

```
"Caricalo manualmente dal browser nel notebook APSS:
 https://notebooklm.google.com/notebook/bc8dfeee-c3f0-412d-aa88-f8e0a4025fa5
 
 Quando hai finito, dimmi 'caricato' e io applico le label."
```

### Passo 5 — Recupera nuovo source_id

Dopo conferma "caricato":

```python
notebook_get(notebook_id="bc8dfeee-c3f0-412d-aa88-f8e0a4025fa5")
```

Trova il nuovo entry con `title="nuovo_doc.md"` e annota `id` (es. `f1a2b3c4-...`).

### Passo 6 — Applica label

```python
# Label area (es. session-log)
label:move_source(
    action="move_source",
    notebook_id="bc8dfeee-c3f0-412d-aa88-f8e0a4025fa5",
    label_id="4b2d9dc5-a8d6-4f71-b18a-05cef7c81b2f",  # session-log
    source_id="f1a2b3c4-..."  # nuovo source_id
)

# Label stato (es. in-corso)
label:move_source(
    action="move_source",
    notebook_id="bc8dfeee-c3f0-412d-aa88-f8e0a4025fa5",
    label_id="4ff44f72-f20d-415c-9934-20fab2492433",  # stato: in-corso
    source_id="f1a2b3c4-..."
)
```

### Passo 7 — Verifica

```python
label:list(notebook_id="bc8dfeee-c3f0-412d-aa88-f8e0a4025fa5")
```

Verifica che il nuovo source_id compaia sotto le 2 label scelte.

### Passo 8 — Aggiorna nota di onboarding

Se la nuova fonte è significativa (non un duplicato concettuale), aggiungerla
alla mappa nella nota di onboarding:

```python
note:update(
    action="update",
    notebook_id="bc8dfeee-c3f0-412d-aa88-f8e0a4025fa5",
    note_id="56fcad43-9a61-4307-9184-c96034c95502",
    title="📍 Onboarding — Come navigare questo notebook",
    content="<contenuto aggiornato con il nuovo file>"
)
```

### Passo 9 — Aggiorna `references/notebook-constants.md`

Aggiungi la nuova fonte alla tabella source nel file
`D:\_claudecodeproject\APSS\.claude\skills\apss-notebooklm-sync\references\notebook-constants.md`.

Aggiorna anche `source_count atteso` e la data di "Ultimo aggiornamento".

### Passo 10 — Suggerisci commit

```
"Tutto fatto. Ho aggiornato anche `notebook-constants.md`.
 Vuoi committare le modifiche alla skill su GitHub?"
```

---

## Caso speciale — Crea nuova label

Se la fonte non si adatta a nessuna label esistente, prima di aggiungerla:

1. **Discuti con l'utente:**
   ```
   "Questa fonte tratta di [argomento X] e non rientra bene in nessuna label
    esistente. Proporrei una nuova label `nome-label` con emoji 🎯.
    Procediamo o preferisci forzarla in una label esistente?"
   ```

2. **Se OK, crea label:**
   ```python
   label:create(notebook_id="...", name="nome-label")
   label:set_emoji(notebook_id="...", label_id="...", emoji="🎯")
   ```

3. **Aggiorna `references/label-schema.md`** con la nuova area
4. **Aggiorna `references/notebook-constants.md`** con il nuovo label_id
5. **Procedi con assegnazione** (Passo 6)
