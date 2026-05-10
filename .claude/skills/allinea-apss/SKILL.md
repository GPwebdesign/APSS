---
name: allinea-apss
description: >
  Attiva SEMPRE quando l'utente scrive "allinea APSS" o varianti come
  "aggiorna APSS", "sincronizza APSS", "aggiorna i file APSS", "chiudi sessione APSS",
  "riepilogo sessione APSS". Automatizza l'aggiornamento completo dei file di
  progetto APSS: memorie, CLAUDE.md, CLAUDE.local.md, plan.md, architecture.md,
  riepilogo sessione, documentazione tecnica (.docx), pulizia file obsoleti e
  verifica allineamento repo Git. Accede direttamente al filesystem
  D:\_claudecodeproject\APSS\ tramite il Filesystem MCP.
version: 1.0
---

# allinea-apss

Skill di chiusura/allineamento sessione APSS. Esegui i passi in ordine,
mostrando all'utente l'esito di ogni step prima di procedere al successivo.

---

## Contesto progetto

- **Root APSS:** `D:\_claudecodeproject\APSS\`
- **Docs:** `D:\_claudecodeproject\APSS\docs\`
- **Subtree codice:** `ros2_py_ws\` e `rosmaster_project\` (solo doc, MAI modificare codice qui)
- **Repo GitHub:** `GPwebdesign/APSS` (branch `master`)
- **Filesystem MCP:** attivo su `D:\_claudecodeproject`

---

## Step 1 — Aggiorna file root APSS

Leggi la conversazione corrente ed estrai le informazioni rilevanti.
Poi aggiorna in sequenza:

### 1a. `APSS_memorie.md`
- Leggi: `D:\_claudecodeproject\APSS\APSS_memorie.md`
- Aggiungi in cima una sezione datata con le informazioni chiave della sessione
- Formato sezione:
  ```
  ## Sessione DD Mese YYYY
  - [fatto rilevante 1]
  - [fatto rilevante 2]
  ```
- Mantieni le sezioni precedenti intatte

### 1b. `CLAUDE.md`
- Leggi: `D:\_claudecodeproject\APSS\CLAUDE.md`
- Aggiorna solo se ci sono nuove regole, pattern o vincoli emersi nella sessione
- Se non ci sono modifiche, segnalalo e passa oltre

### 1c. `CLAUDE.local.md`
- Leggi: `D:\_claudecodeproject\APSS\CLAUDE.local.md`
- Aggiorna solo se ci sono nuove configurazioni locali o path emersi nella sessione
- Se non ci sono modifiche, segnalalo e passa oltre

---

## Step 2 — Aggiorna docs/

### 2a. `plan.md`
- Leggi: `D:\_claudecodeproject\APSS\docs\plan.md`
- Spunta i task completati nella sessione `[x]`
- Aggiungi nuovi task emersi
- Aggiorna la versione nel frontmatter (es. v2.3 → v2.4)
- Mostra all'utente un diff delle modifiche prima di salvare

### 2b. `architecture.md`
- Leggi: `D:\_claudecodeproject\APSS\docs\architecture.md`
- Aggiorna tabelle hardware, topic ROS2, servizi systemd se ci sono novità
- Aggiorna note ⚠️ se problemi sono stati risolti o ne sono emersi di nuovi
- Mostra all'utente un diff delle modifiche prima di salvare

### 2c. Riepilogo sessione
- Cerca file `APSS_riepilogo_sessione_*.md` in `D:\_claudecodeproject\APSS\docs\`
- Determina il numero progressivo corretto (ultimo + 1)
- Crea nuovo file: `APSS_riepilogo_sessione_[mese][anno]_[N].md`
- Contenuto del riepilogo:
  ```markdown
  # APSS — Autonomous Patrol and Surveillance System
  ## Riepilogo sessione per nuova chat — [Mese YYYY]

  Contesto: [una riga di contesto generale aggiornato]

  ## Completati in questa sessione
  - ✅ [item 1]
  - ✅ [item 2]

  ## Hardware robot
  [stato aggiornato HW]

  ## Stack ROS2
  [stato aggiornato]

  ## Roadmap
  ### Completati
  [lista aggiornata]

  ### Prossimi step (in ordine)
  [lista aggiornata]

  ## Pending items
  [lista aggiornata]
  ```
- Mostra il contenuto all'utente per approvazione prima di salvare

---

## Step 3 — Documentazione tecnica .docx

> ⚠️ **STOP OBBLIGATORIO** — Prima di procedere, chiedi sempre:
> "Vuoi aggiornare anche `APSS_Documentazione_Tecnica_vX_X.docx`?
> (richiede più tempo — genera un nuovo file Word)"
>
> **Attendi la risposta prima di qualsiasi altra azione.**
> Non procedere allo Step 4 senza aver ricevuto una risposta esplicita (sì/no).

- **Se sì:** leggi lo skill `docx` (`/mnt/skills/public/docx/SKILL.md`),
  poi genera il nuovo .docx aggiornando versione e data nel registro revisioni.
  Salva in `D:\_claudecodeproject\APSS\docs\` con il nuovo numero di versione.
  Chiedi se eliminare la versione precedente.
- **Se no:** passa allo step 4.

---

## Step 4 — Pulizia file obsoleti

- Elenca i file in `D:\_claudecodeproject\APSS\` e `D:\_claudecodeproject\APSS\docs\`
- Identifica file potenzialmente obsoleti:
  - Riepilogo sessioni vecchie (mantenere solo gli ultimi 2)
  - File `.md` duplicati o superati
  - File temporanei o di test
- Mostra la lista all'utente e chiedi:
  > "Vuoi eliminare questi file obsoleti? [lista file]"
- **Attendi conferma esplicita** prima di qualsiasi eliminazione
- ⚠️ MAI eliminare senza conferma dell'utente

---

## Step 5 — Allineamento repo Git

### 5a. Verifica stato
Chiedi all'utente di eseguire su PC:
```powershell
cd D:\_claudecodeproject\APSS
git status
git log --oneline -3
```

### 5b. Commit e push se necessario
Se ci sono file modificati non committati:
```powershell
git add docs/plan.md docs/architecture.md docs/APSS_riepilogo_sessione_*.md
git add APSS_memorie.md CLAUDE.md CLAUDE.local.md
git add .claude/skills/allinea-apss/SKILL.md
git commit -m "docs: allineamento sessione [data]"
git push origin master
```

### 5c. Verifica allineamento subtree
Chiedi all'utente lo stato di VM e hawk:
```bash
# Su gp68-vmware e hawk
cd ~/Workspaces/rosmaster_project && git log --oneline -1
cd ~/Workspaces/ros2_py_ws && git log --oneline -1
```
Se disallineati, guida l'utente nel workflow corretto:
- Modifiche da hawk → `apss-push.sh` → pull VM → `.\subtree-pull.bat` PC
- Modifiche da VM → push GitHub → pull hawk → `.\subtree-pull.bat` PC

---

## Riepilogo finale

Al termine mostra un riepilogo:
```
✅ APSS_memorie.md aggiornato
✅/⏭️ CLAUDE.md [aggiornato / nessuna modifica]
✅/⏭️ CLAUDE.local.md [aggiornato / nessuna modifica]
✅ plan.md aggiornato (vX.Y)
✅ architecture.md aggiornato
✅ Riepilogo sessione creato: APSS_riepilogo_sessione_XXX.md
✅/⏭️ Documentazione tecnica [aggiornata / saltata]
✅/⏭️ File obsoleti [rimossi / nessuno]
✅ Repo Git allineato
```

---

## Regole critiche

- **MAI modificare file in `rosmaster_project\` o `ros2_py_ws\`** — sono subtree di sola lettura sul PC. Il codice si modifica su gp68-vmware.
- **Mostra sempre un diff o anteprima** prima di salvare modifiche a file esistenti
- **Attendi conferma esplicita** per eliminazioni e per il .docx
- **Un step alla volta** — non procedere al successivo senza segnalare l'esito del precedente
- Se un file non esiste ancora, crealo
- Se la conversazione non contiene informazioni sufficienti per aggiornare un file, segnalalo e chiedi all'utente
