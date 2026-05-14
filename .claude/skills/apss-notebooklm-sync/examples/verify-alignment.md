# Esempio — Verifica allineamento disco ↔ notebook

## Scenario

L'utente chiede: *"verifica se il notebook è allineato con i file su disco"*

## Procedura passo passo

### Passo 0 — Verifica autenticazione

```python
notebook_get(notebook_id="bc8dfeee-c3f0-412d-aa88-f8e0a4025fa5")
```

Se ritorna `"Authentication expired"`:
1. Prova `refresh_auth()` — se restituisce success ma il `notebook_get` fallisce ancora, i token su disco sono comunque scaduti
2. Chiedi all'utente di eseguire `nlm login` da terminale sul PC
3. Dopo conferma utente, richiama `refresh_auth()` e ritenta

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

### Passo 2 — Lista fonti nel notebook + check integrità

```python
notebook_get(notebook_id="bc8dfeee-c3f0-412d-aa88-f8e0a4025fa5")
label:list(notebook_id="bc8dfeee-c3f0-412d-aa88-f8e0a4025fa5")
```

**Doppio controllo:**

1. **Allineamento disco↔notebook:** confronto file su disco vs `sources[].title`
2. **Integrità label (no fantasmi):**
   - somma `source_ids` in tutte le label
   - confronta con `source_count` del notebook
   - schema singolo: deve essere **==** (ogni source ha 1 label)
   - se > source_count → fantasmi (vedi `@examples/cleanup-ghosts.md`)
   - se < source_count → ci sono source senza label

### Passo 3 — Confronto

Costruisci una tabella di allineamento. Esempio output:

```
| File | Su disco | Nel notebook | Azione |
|---|---|---|---|
| architecture.md           | ✅ 8.45 KB | ✅ | OK |
| plan.md                   | ✅ 8.47 KB | ✅ | OK |
| APSS_riepilogo_..._3.md   | ✅ 3.38 KB | ✅ | OK |
| nuovo_doc.md              | ✅ 2.10 KB | ❌ | → AGGIUNGERE |
| APSS_Documentazione_v2_1  | ❌ removed | ✅ | → RIMUOVERE |
| CLAUDE.local.md           | ✅ 1.06 KB | — | escluso (credenziali) |

Integrità label: 9 source totali, 9 source_ids in label ✅ (no fantasmi)
```

### Passo 4 — Segnalazione confronto contenuti (opzionale)

Per i file presenti su entrambi i lati, il confronto **byte-a-byte non è possibile**
(il notebook ha contenuto indicizzato, non file binari). Strategie:

1. **Confronto leggero (default):** se la dimensione su disco è cambiata vs ultima sync nota → suggerisci ricarica
2. **Confronto via filesystem:** se nelle costanti hai annotato la dimensione precedente, confronta con `Filesystem:get_file_info` per individuare modifiche silenti
3. **Confronto profondo (su richiesta):** leggere il contenuto indicizzato con
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
**Integrità label:** ✅ nessun fantasma / ⚠️ K source fantasma rilevati

### Azioni proposte
- [ ] Aggiungere: `nuovo_doc.md` (suggerisco label: `📝 session-log`)
- [ ] Rimuovere: `vecchio_doc.md` (obsoleto su disco)
- [ ] Ricaricare: `architecture.md` (modificato su disco — verifica manuale richiesta)
- [ ] [se fantasmi presenti] Cleanup fantasmi: vedi `cleanup-ghosts.md`

Vuoi che proceda con queste azioni?
```

**Attendi conferma** prima di muoverti.

---

## Esempio reale — Sessione 14 Maggio 2026

```
Utente: "ho aggiornato plan.md, architecture.md, APSS_memorie.md e bumpato la
         Documentazione Tecnica a v2.2. Il notebook è in pari?"

Claude:
1. notebook_get(...) → 9 fonti, Documentazione v2.1 ancora presente
2. Filesystem:list_directory_with_sizes("D:\\..\\docs") → vedo Documentazione_v2_2.docx (nuovo)
   e niente più v2_1
3. Risposta tabellare:
   - architecture.md       modified  → ricaricare
   - plan.md               modified  → ricaricare
   - APSS_memorie.md       modified  → ricaricare
   - Documentazione v2_1   deleted   → rimuovere
   - Documentazione v2_2   new       → aggiungere
   
   "Servono 5 operazioni manuali nel browser. Procediamo?"

→ Utente: "fatte"

→ Claude (dopo ricarica multipla):
   - label:list → conteggio: 13 source_ids in label vs source_count 9
   - DIAGNOSI: 4 source fantasma (i vecchi 4 source rimossi)
   - Propone cleanup completo via reorganize distruttivo
```

---

## Quando saltare la procedura completa

Se l'utente specifica un'azione singola (es. "aggiungi `nuovo_doc.md`"), non serve
fare l'intero allineamento — vai direttamente al workflow `add-source` o `reload-source`.

La procedura di allineamento completa è utile quando:
- L'utente ha appena fatto un commit Git con più modifiche
- È passato del tempo dall'ultima sync (incertezza sullo stato)
- L'utente sta chiudendo una sessione di sviluppo (usare insieme alla skill `allinea-apss`)
