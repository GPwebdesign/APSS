---
name: apss-notebooklm-sync
description: >
  Attiva quando l'utente parla di: aggiornare/sincronizzare/verificare fonti
  NotebookLM APSS, allineamento notebook ↔ disco, ricaricare documenti nel
  notebook, modificare label del notebook, aggiungere nuova fonte, rimuovere
  fonte, "il notebook è aggiornato?", "verifica notebook APSS",
  "aggiorna le fonti", "ricarica nel notebook", pulire source fantasma.
  Workflow ricorrente di manutenzione del notebook NotebookLM APSS.
version: 1.1
references:
  - references/notebook-constants.md   # ID notebook, label, source (da verificare al primo uso)
  - references/label-schema.md         # schema singolo area + nuova fonte
examples:
  - examples/verify-alignment.md       # verifica allineamento disco ↔ notebook (+ check fantasmi)
  - examples/add-source.md             # aggiunta nuova fonte
  - examples/reload-source.md          # ricarica fonte modificata (con gotcha fantasmi)
  - examples/cleanup-ghosts.md         # pulizia source fantasma via reorganize distruttivo
---

# apss-notebooklm-sync

Skill di manutenzione del notebook NotebookLM **APSS — Autonomous Patrol and
Surveillance System**. Automatizza verifica allineamento, aggiunta, ricarica
e rimozione di fonti, mantenendo coerente lo schema di label.

> **Versione 1.1 (Mag 2026)** — schema label semplificato a singolo livello (solo area).
> Aggiunto workflow `cleanup-ghosts` dopo scoperta del bug source fantasma.

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

## Step 0 — Verifica autenticazione (NUOVO in v1.1)

Prima di qualsiasi operazione, verifica che l'autenticazione NotebookLM sia valida:

```python
notebook_get(notebook_id="bc8dfeee-c3f0-412d-aa88-f8e0a4025fa5")
```

Se la chiamata fallisce con `"Authentication expired"`:

1. **Prima prova:** `refresh_auth()` per ricaricare i token da disco
2. **Se ancora fallisce:** i token su disco sono comunque scaduti
3. **Chiedi all'utente** di eseguire `nlm login` da terminale sul PC
4. **Dopo conferma utente:** richiama `refresh_auth()` e ritenta `notebook_get`

⚠️ Non procedere con altre operazioni finché l'auth non funziona.

---

## Step 1 — Riconoscere l'operazione richiesta

| L'utente vuole… | Esempio frase | Procedura |
|---|---|---|
| Verificare se tutto è allineato | "il notebook è aggiornato?" | → Step 2 (verify-alignment) |
| Aggiungere una fonte nuova | "aggiungi X al notebook" | → Step 3 (add-source) |
| Aggiornare una fonte esistente | "ho modificato architecture.md" | → Step 4 (reload-source) |
| Rimuovere una fonte obsoleta | "rimuovi riepilogo_2 dal notebook" | → Step 5 (remove-source) |
| Creare/modificare label | "aggiungi label Y" | → Step 6 (label-management) |
| Pulire source fantasma | "ci sono fantasmi nelle label" / "pulisci notebook" | → Step 7 (cleanup-ghosts) |

Se non è chiaro, **chiedi** prima di muoverti.

---

## Step 2 — Verifica allineamento disco ↔ notebook

1. `Filesystem:list_directory_with_sizes` sulle due cartelle sorgente
2. `notebook_get(notebook_id)` per la lista fonti correnti
3. `label:list(notebook_id)` per integrità label
4. **Confronto:** segnala fonti su disco non nel notebook, fonti nel notebook non più su disco, e differenze di dimensione/timestamp
5. **Controllo fantasmi:** somma `source_ids` in tutte le label vs `source_count` del notebook (schema singolo: deve essere ==). Se > → fantasmi presenti
6. Presenta un report tabellare con le azioni proposte e attendi conferma utente

Dettaglio: `@examples/verify-alignment.md`

---

## Step 3 — Aggiungere una nuova fonte

1. **Verifica che il file esista** su disco con `Filesystem:get_file_info`
2. **Verifica che non sia escluso** (`CLAUDE.local.md`, file con credenziali, file `*local*`)
3. **Dì all'utente di caricarlo manualmente** dal browser nel notebook (l'API NotebookLM non supporta upload da percorsi locali)
4. **Attendi conferma "caricato"**, poi `notebook_get` per ottenere il nuovo `source_id`
5. **Proponi label area** in base allo schema (vedi `@references/label-schema.md`) e attendi OK utente
6. **Applica label** con `label:move_source` (1 sola chiamata, schema singolo)
7. **Aggiorna la nota di onboarding** se cambia la struttura (nuova area)
8. **Aggiorna `notebook-constants.md`** con il nuovo source_id

Dettaglio: `@examples/add-source.md`

---

## Step 4 — Ricaricare una fonte modificata

> ⚠️ **CRITICO:** quando una fonte viene rimossa e ricaricata, **il `source_id` cambia** e
> tutte le label assegnate vengono perse. Inoltre, il **vecchio source_id resta come
> fantasma nelle label** (NotebookLM non lo pulisce automaticamente).

1. **Recupera label correnti** del source prima della rimozione con `label:list`
   e annota la label per quel source_id
2. **L'utente rimuove e ricarica** manualmente la fonte dal browser
3. **`notebook_get`** per ottenere il NUOVO `source_id`
4. **Riassegna la label** che il source aveva prima
5. **Verifica integrità:** somma `source_ids` in label vs `source_count` notebook
6. Se i fantasmi diventano molesti (3+ accumulati): → Step 7 (cleanup-ghosts)

Dettaglio: `@examples/reload-source.md`

---

## Step 5 — Rimuovere una fonte obsoleta

1. **Conferma esplicita** dall'utente ("rimuovere `nome.md` dal notebook è irreversibile, confermi?")
2. **L'utente rimuove manualmente** dal browser (NotebookLM non espone delete sicuro via API a oggi nel server MCP)
3. **Verifica con `notebook_get`** che il source_count sia sceso
4. **Aggiorna la nota di onboarding** rimuovendo il riferimento
5. **Aggiorna `notebook-constants.md`** rimuovendo il source

⚠️ Anche qui può rimanere un fantasma nelle label → check integrità post-operazione.

---

## Step 6 — Gestione label

- **Schema corrente (v1.1):** singolo labeling per AREA (vedi `@references/label-schema.md`)
- **Nuova label:** `label:create` + `label:set_emoji` + `label:move_source` per ogni fonte
- **Coerenza emoji:** rispettare lo schema esistente (📘 overview, 🤖 onboarding-ai, 🗺️ roadmap, 📝 session-log, 🔄 workflow-git, 🔌 hardware-docking)
- **Aggiorna `notebook-constants.md`** quando crei una nuova label (per future sessioni)

---

## Step 7 — Cleanup source fantasma (NUOVO in v1.1)

Procedura distruttiva per ripulire fantasmi accumulati:

1. **Inventario fantasmi:** `notebook_get` + `label:list` → diff
2. **Conferma utente** esplicita (operazione distruttiva)
3. **Salva snapshot** assegnazioni correnti
4. **`reorganize` distruttivo** con `confirm=True`
5. **Cancella label AI** generate da NotebookLM
6. ⚠️ **NON chiamare `label:list` tra delete e create** (riattiva auto-labeling)
7. **Crea le 6 label area** APSS + emoji
8. **Riassegna i source** dalla mappa snapshot o canonica
9. **Verifica:** somma `source_ids` == `source_count`
10. **Aggiorna `notebook-constants.md`** con nuovi label_id

Dettaglio: `@examples/cleanup-ghosts.md`

---

## Regole critiche

- **MAI caricare `CLAUDE.local.md`** o file con credenziali nel notebook
- **MAI assumere che le costanti siano valide:** verificare `notebook_get` + `label:list` al primo uso di sessione
- **MAI eseguire azioni di scrittura senza conferma utente** (creazione label, assegnazioni multiple, ecc.)
- **MAI chiamare `label:list` o `label:auto` durante un cleanup** (riattiva auto-labeling AI)
- **Mostra sempre il piano** prima di eseguire più chiamate API consecutive (es. "creerò la label X poi assegnerò 3 fonti, OK?")
- **Aggiorna la nota di onboarding** ogni volta che cambia la struttura (nuova fonte, nuova label, fonte rimossa)
- **Dopo modifiche significative**, suggerisci all'utente: "vuoi committare la skill aggiornata su GitHub?"

---

## ⚠️ Gotchas (errori noti da evitare)

- **Auth scade silenziosamente:** `notebook_get` può fallire con "Authentication expired" anche se la sessione precedente funzionava. Step 0 obbligatorio
- **`refresh_auth` da solo non basta:** se i token su disco sono scaduti serve `nlm login` da terminale utente
- **`source_id` cambia ad ogni ricaricamento** — le label vanno riassegnate (vedi Step 4)
- **Source fantasma dopo rimozione:** il vecchio source_id resta nelle label come riferimento orfano. Non c'è API per `unassign` — l'unico modo per pulire è `reorganize` distruttivo (Step 7)
- **`move_source` su source_id inesistente** ritorna success ma è no-op silenzioso (il fantasma non si crea né si pulisce con questa chiamata)
- **`label:list` dopo cancellazione totale label** triggera auto-labeling AI di NotebookLM (rigenera label inglesi generiche)
- **`reorganize unlabeled_only=true`** NON pulisce i fantasmi (no-op se tutti i source validi sono già labelati)
- **`label:reorganize unlabeled_only=false confirm=true`** è l'unico modo per pulire fantasmi MA è distruttivo: cancella tutte le label e l'AI ne crea di nuove (in inglese) — vanno cancellate e ricostruite manualmente
- **`memory_user_edits` ha limite 500 caratteri per edit** — se aggiorni costanti in memoria, sii conciso
- **`label:auto` richiede 5+ fonti** — sotto soglia fallisce silenziosamente
- **NotebookLM indicizza tutto il testo, inclusi commenti** — `CLAUDE.local.md` ha credenziali commentate con `#` ma sono comunque indicizzabili → NON caricarlo
- **L'API non fa upload file:** caricamento sempre manuale via browser
- **L'API non espone delete source affidabile:** rimozione sempre manuale via browser
- **Nota di onboarding** ha un solo `note_id` fisso — usare sempre `note:update`, mai `note:create` per rifare l'onboarding (causerebbe duplicati)
- **`notebook_get` vs `label:list`:** il primo dà i source validi, il secondo dà l'associazione source↔label (inclusi fantasmi). Per un report completo + check integrità servono entrambi
- **Aggiornamento contenuto fonte da disco non automatico:** NotebookLM indicizza al caricamento; modificare il file su disco NON aggiorna il notebook. Vedi Step 4
- **Schema label semplificato in v1.1:** prima era doppio (area + stato), ora singolo (solo area). Lo stato si deduce dal nome del file
