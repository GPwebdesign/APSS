---
name: apss-notebooklm-sync
description: >
  Attiva quando l'utente parla di: aggiornare/sincronizzare/verificare fonti
  NotebookLM APSS, allineamento notebook ↔ disco, ricaricare documenti nel
  notebook, modificare label del notebook, aggiungere nuova fonte, rimuovere
  fonte, "il notebook è aggiornato?", "verifica notebook APSS",
  "aggiorna le fonti", "ricarica nel notebook". Workflow ricorrente di
  manutenzione del notebook NotebookLM APSS.
version: 1.0
references:
  - references/notebook-constants.md   # ID notebook, label, source (da verificare al primo uso)
  - references/label-schema.md         # regole assegnazione area+stato + nuova fonte
examples:
  - examples/verify-alignment.md       # verifica allineamento disco ↔ notebook
  - examples/add-source.md             # aggiunta nuova fonte
  - examples/reload-source.md          # ricarica fonte modificata (relabel obbligatorio)
---

# apss-notebooklm-sync

Skill di manutenzione del notebook NotebookLM **APSS — Autonomous Patrol and
Surveillance System**. Automatizza verifica allineamento, aggiunta, ricarica
e rimozione di fonti, mantenendo coerente lo schema di label.

---

## Contesto

- **Notebook ID:** `bc8dfeee-c3f0-412d-aa88-f8e0a4025fa5`
- **URL:** https://notebooklm.google.com/notebook/bc8dfeee-c3f0-412d-aa88-f8e0a4025fa5
- **Cartelle sorgente sul PC:**
  - Root APSS: `D:\_claudecodeproject\APSS\` (CLAUDE.md, APSS_memorie.md)
  - Docs: `D:\_claudecodeproject\APSS\docs\` (tutti gli altri .md/.docx/.pdf)
- **MAI caricare nel notebook:** `CLAUDE.local.md` (contiene credenziali)
- **Tool MCP richiesti:** `notebooklm`, `Filesystem` (entrambi disponibili)

> Le costanti specifiche (ID label, ID source) sono in
> `@references/notebook-constants.md` e vanno **verificate al primo uso** di
> ogni sessione con `notebook_get` + `label list`.

---

## Step 1 — Riconoscere l'operazione richiesta

| L'utente vuole… | Esempio frase | Procedura |
|---|---|---|
| Verificare se tutto è allineato | "il notebook è aggiornato?" | → Step 2 (verify-alignment) |
| Aggiungere una fonte nuova | "aggiungi X al notebook" | → Step 3 (add-source) |
| Aggiornare una fonte esistente | "ho modificato architecture.md" | → Step 4 (reload-source) |
| Rimuovere una fonte obsoleta | "rimuovi riepilogo_2 dal notebook" | → Step 5 (remove-source) |
| Creare/modificare label | "aggiungi label Y" | → Step 6 (label-management) |

Se non è chiaro, **chiedi** prima di muoverti.

---

## Step 2 — Verifica allineamento disco ↔ notebook

1. `Filesystem:list_directory_with_sizes` sulle due cartelle sorgente
2. `notebook_get(notebook_id)` per la lista fonti correnti
3. **Confronto:** segnala fonti su disco non nel notebook, fonti nel notebook non più su disco, e differenze di dimensione/timestamp
4. **Non confrontare contenuti automaticamente** (costoso): se l'utente ha modificato un file, lo dice lui. In caso di dubbio si può usare `source_get_content(source_id)` per leggere il testo indicizzato e confrontare a campione
5. Presenta un report tabellare con le azioni proposte (ricarica/aggiungi/rimuovi) e attendi conferma utente

Dettaglio: `@examples/verify-alignment.md`

---

## Step 3 — Aggiungere una nuova fonte

1. **Verifica che il file esista** su disco con `Filesystem:get_file_info`
2. **Verifica che non sia escluso** (`CLAUDE.local.md`, file con credenziali, file `*local*`)
3. **Dì all'utente di caricarlo manualmente** dal browser nel notebook (l'API NotebookLM non supporta upload da percorsi locali)
4. **Attendi conferma "caricato"**, poi `notebook_get` per ottenere il nuovo `source_id`
5. **Proponi label** in base allo schema area+stato (vedi `@references/label-schema.md`) e attendi OK utente
6. **Applica label** con `label:move_source` (una chiamata per ogni label)
7. **Aggiorna la nota di onboarding** se cambia la struttura (nuova area, nuova categoria di stato)
8. **Aggiorna la memoria Claude** se cambiano costanti rilevanti

Dettaglio: `@examples/add-source.md`

---

## Step 4 — Ricaricare una fonte modificata

> ⚠️ **CRITICO:** quando una fonte viene rimossa e ricaricata, **il `source_id` cambia** e
> tutte le label assegnate vengono perse. La ri-assegnazione delle label è
> obbligatoria.

1. **Recupera label correnti** del source prima della rimozione con `label:list`
   e salvale (annota le label per quel source_id)
2. **L'utente rimuove e ricarica** manualmente la fonte dal browser
3. **`notebook_get`** per ottenere il NUOVO `source_id`
4. **Riassegna tutte le label** che il source aveva prima
5. Verifica finale con `label:list`

Dettaglio: `@examples/reload-source.md`

---

## Step 5 — Rimuovere una fonte obsoleta

1. **Conferma esplicita** dall'utente ("rimuovere `nome.md` dal notebook è irreversibile, confermi?")
2. **L'utente rimuove manualmente** dal browser (NotebookLM non espone delete sicuro via API a oggi nel server MCP)
3. **Verifica con `notebook_get`** che il source_count sia sceso
4. **Aggiorna la nota di onboarding** rimuovendo il riferimento

---

## Step 6 — Gestione label

- **Schema corrente:** doppio labeling area + stato (vedi `@references/label-schema.md`)
- **Nuova label:** `label:create` + `label:set_emoji` + `label:move_source` per ogni fonte
- **Coerenza emoji:** rispettare lo schema esistente (📘 overview, 🤖 onboarding-ai, 🗺️ roadmap, 📝 session-log, 🔄 workflow-git, 🔌 hardware-docking, 📚 stato:reference, ⚙️ stato:in-corso)
- **Aggiorna `notebook-constants.md`** quando crei una nuova label (per future sessioni)

---

## Regole critiche

- **MAI caricare `CLAUDE.local.md`** o file con credenziali nel notebook
- **MAI assumere che le costanti siano valide:** verificare `notebook_get` + `label:list` al primo uso di sessione
- **MAI eseguire azioni di scrittura senza conferma utente** (creazione label, assegnazioni multiple, ecc.)
- **Mostra sempre il piano** prima di eseguire più chiamate API consecutive (es. "creerò la label X poi assegnerò 3 fonti, OK?")
- **Aggiorna la nota di onboarding** ogni volta che cambia la struttura (nuova fonte, nuova label, fonte rimossa)
- **Dopo modifiche significative**, suggerisci all'utente: "vuoi committare la skill aggiornata su GitHub?"

---

## ⚠️ Gotchas (errori noti da evitare)

- **`source_id` cambia ad ogni ricaricamento** — le label vanno riassegnate (vedi Step 4)
- **`memory_user_edits` ha limite 500 caratteri per edit** — se aggiorni costanti in memoria, sii conciso
- **`label:auto` richiede 5+ fonti** — sotto soglia fallisce silenziosamente
- **NotebookLM indicizza tutto il testo, inclusi commenti** — `CLAUDE.local.md` ha credenziali commentate con `#` ma sono comunque indicizzabili → NON caricarlo
- **L'API non fa upload file:** caricamento sempre manuale via browser
- **L'API non espone delete source affidabile:** rimozione sempre manuale via browser
- **Separatore label `: `** (con spazio dopo i due punti): `stato: reference`, non `stato:reference`
- **Nota di onboarding** ha un solo `note_id` fisso — usare sempre `note:update`, mai `note:create` per rifare l'onboarding (causerebbe duplicati)
- **`notebook_get` vs `label:list`:** il primo dà i source, il secondo dà l'associazione source↔label. Per un report completo servono entrambi
- **Aggiornamento contenuto fonte da disco non automatico:** NotebookLM indicizza al caricamento; modificare il file su disco NON aggiorna il notebook. Vedi Step 4
