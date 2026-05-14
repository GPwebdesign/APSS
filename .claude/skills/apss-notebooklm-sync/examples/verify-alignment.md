# Esempio — Verifica allineamento disco ↔ notebook

## Scenario

L'utente chiede: *"verifica se il notebook è allineato con i file su disco"*

## Procedura passo passo

### Passo 1 — Lista file su disco

```python
Filesystem:list_directory_with_sizes(
    path="D:\\_claudecodeproject\\APSS",
    sortBy="name"
)
Filesystem:list_directory_with_sizes(
    path="D:\\_claudecodeproject\\APSS\\docs",
    sortBy="name"
)
```

Filtra dai risultati i file **da includere** nel notebook (vedi `@references/notebook-constants.md` per la lista canonica) e escludi `CLAUDE.local.md`, `.git/`, ecc.

### Passo 2 — Lista fonti nel notebook

```python
notebook_get(notebook_id="bc8dfeee-c3f0-412d-aa88-f8e0a4025fa5")
```

Estrai `sources[].title` per avere la lista delle fonti correnti.

### Passo 3 — Confronto

Costruisci una tabella di allineamento. Esempio output:

```
| File | Su disco | Nel notebook | Azione |
|---|---|---|---|
| architecture.md           | ✅ 8.16 KB | ✅ | OK |
| plan.md                   | ✅ 7.40 KB | ✅ | OK |
| APSS_riepilogo_..._3.md   | ✅ 3.38 KB | ✅ | OK |
| nuovo_doc.md              | ✅ 2.10 KB | ❌ | → AGGIUNGERE |
| APSS_riepilogo_..._2.md   | ❌ removed | ✅ | → RIMUOVERE |
| CLAUDE.local.md           | ✅ 1.06 KB | — | escluso (credenziali) |
```

### Passo 4 — Segnalazione confronto contenuti (opzionale)

Per i file presenti su entrambi i lati, il confronto **byte-a-byte non è possibile**
(il notebook ha contenuto indicizzato, non file binari). Strategie:

1. **Confronto leggero (default):** se la dimensione su disco è cambiata vs ultima sync nota → suggerisci ricarica
2. **Confronto profondo (su richiesta):** leggere il contenuto indicizzato con
   `source_get_content(source_id)` e confrontare a campione con `Filesystem:read_text_file`
   - Costoso: usalo solo se l'utente esprime dubbi specifici su un file
   - Esempio: "ho riscritto architecture.md, verifica che il notebook abbia la versione nuova"

### Passo 5 — Report finale all'utente

Sempre con un riepilogo strutturato:

```markdown
## 📊 Report allineamento — DD Mese YYYY

**Stato:** ✅ Allineato / ⚠️ Da aggiornare / ❌ Disallineato

**Fonti su disco:** N file
**Fonti nel notebook:** M file

### Azioni proposte
- [ ] Aggiungere: `nuovo_doc.md` (suggerisco label: `📝 session-log` + `⚙️ stato: in-corso`)
- [ ] Rimuovere: `vecchio_doc.md` (obsoleto su disco)
- [ ] Ricaricare: `architecture.md` (modificato su disco — verifica manuale richiesta)

Vuoi che proceda con queste azioni?
```

**Attendi conferma** prima di muoverti.

---

## Esempio reale (Maggio 2026)

```
Utente: "ho aggiornato plan.md e architecture.md, il notebook è in pari?"

Claude:
1. Filesystem:list_directory_with_sizes("D:\\_claudecodeproject\\APSS\\docs")
   → plan.md 7.40 KB, architecture.md 8.16 KB
2. notebook_get(...)
   → 9 fonti, plan.md e architecture.md presenti
3. Filesystem:get_file_info(plan.md) → modified: 14 Mag 2026
4. Risposta:
   "Entrambi i file sono presenti nel notebook ma `plan.md` risulta modificato
    oggi su disco. Il notebook ha la versione precedente (caricata il 13 Mag).
    Per allineare, dovresti rimuoverlo e ricaricarlo manualmente dal browser
    (poi io riassegno le label).
    Procediamo?"
```
