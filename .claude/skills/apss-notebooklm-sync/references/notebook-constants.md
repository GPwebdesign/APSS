# NotebookLM APSS — Costanti

> ⚠️ Verificare al primo uso di ogni sessione con:
> - `notebook_get(notebook_id="bc8dfeee-c3f0-412d-aa88-f8e0a4025fa5")`
> - `label:list(notebook_id="bc8dfeee-c3f0-412d-aa88-f8e0a4025fa5")`
>
> Se gli ID seguenti non corrispondono ai valori restituiti, **aggiornare questo file**
> prima di procedere con altre operazioni.

> Ultimo aggiornamento: 14 Maggio 2026 (post-cleanup fantasmi, schema singolo)

---

## Notebook

| Campo | Valore |
|---|---|
| ID | `bc8dfeee-c3f0-412d-aa88-f8e0a4025fa5` |
| Titolo | `APSS — Autonomous Patrol and Surveillance System` |
| URL | https://notebooklm.google.com/notebook/bc8dfeee-c3f0-412d-aa88-f8e0a4025fa5 |
| Source count atteso | 9 |
| Label count atteso | 6 |

---

## Nota di onboarding

| Campo | Valore |
|---|---|
| Note ID | `56fcad43-9a61-4307-9184-c96034c95502` |
| Titolo | `📍 Onboarding — Come navigare questo notebook` |

> ⚠️ Esiste **una sola** nota nel notebook. Per modificarla usare `note:update`,
> mai `note:create` (causerebbe duplicati).

---

## Label (schema singolo per area — semplificato Mag 2026)

> **Storia:** il notebook è nato con schema doppio (area + stato). Dopo l'incidente
> dei "source fantasma" del 14 Mag, lo schema è stato semplificato a singolo livello
> (solo area). Vedi `@examples/cleanup-ghosts.md` per il contesto.

| Label | Emoji | ID | Source assegnati |
|---|---|---|---|
| `overview` | 📘 | `409f12c9-72f8-4cf4-8301-f081158ce4b3` | Documentazione_v2_2 + architecture |
| `onboarding-ai` | 🤖 | `a0678d6c-b5e3-456b-8ed3-b537ae048337` | CLAUDE.md |
| `roadmap` | 🗺️ | `31dd4031-a057-441d-a11e-cb0652373d18` | plan |
| `session-log` | 📝 | `257a0d0e-1f2b-4a83-ae18-7ea329b4b85e` | riepilogo_3 + APSS_memorie |
| `workflow-git` | 🔄 | `489aaabd-d071-4c90-824f-d716fd54f68c` | allineamento RPi-PC + RPi-VMware |
| `hardware-docking` | 🔌 | `4c95cb0d-a9cb-494b-9419-b09c89949c11` | Schema Circuitale Docking |

---

## Source (9 fonti)

> ⚠️ Gli `id` cambiano ad ogni ricaricamento. Se le label di una fonte si "perdono",
> probabilmente il source è stato ricaricato → recupera nuovo ID e ri-assegna label.

| File su disco | Source ID atteso | Label area |
|---|---|---|
| `APSS_Documentazione_Tecnica_v2_2.docx` | `e2068f37-a0bb-4025-91f2-34214747f2d1` | 📘 overview |
| `architecture.md` | `330838dd-5f20-4a6c-99ec-f7c9e3d3d9a1` | 📘 overview |
| `CLAUDE.md` | `5ddedb66-1ee5-4aad-8fef-a341d06068a5` | 🤖 onboarding-ai |
| `plan.md` | `38293aac-4f1c-49af-8570-7fbdeddf2426` | 🗺️ roadmap |
| `APSS_riepilogo_sessione_mag2026_3.md` | `326f0e30-6ccf-44bb-b025-f442f07c8a32` | 📝 session-log |
| `APSS_memorie.md` | `28d05d12-8ed9-4451-99dc-454a35dd1ee5` | 📝 session-log |
| `APSS_allineamento_ RPi-PC-GitHub.md` | `2c9b15b2-a320-4e1a-815a-e36b4f780690` | 🔄 workflow-git |
| `APSS_allineamento_RPi-VMware-GitHub.md` | `d0da390f-cf22-42b1-8976-9316badb00ad` | 🔄 workflow-git |
| `Schema Circuitale Docking Station — Rosmaster R2.pdf` | `3141e7b2-1e6f-4b27-93dc-5141d8797739` | 🔌 hardware-docking |

---

## Path sorgente sul PC

```
D:\_claudecodeproject\APSS\
├── CLAUDE.md                              ✅ nel notebook
├── CLAUDE.local.md                        ❌ NON nel notebook (credenziali)
├── APSS_memorie.md                        ✅ nel notebook
└── docs\
    ├── APSS_Documentazione_Tecnica_v2_2.docx
    ├── APSS_allineamento_ RPi-PC-GitHub.md
    ├── APSS_allineamento_RPi-VMware-GitHub.md
    ├── APSS_riepilogo_sessione_mag2026_3.md
    ├── architecture.md
    ├── plan.md
    └── Schema Circuitale Docking Station — Rosmaster R2.pdf
```

---

## File esclusi dal notebook (mai caricare)

| File | Motivo |
|---|---|
| `CLAUDE.local.md` | Contiene credenziali SSH/SMB anche se commentate con `#` — NotebookLM le indicizzerebbe comunque |
| `APSS_riepilogo_sessione_mag2026_2.md` | Obsoleto, sostituito da `_3.md`. Cancellato dal disco |
| `APSS_Documentazione_Tecnica_v2_1.docx` | Sostituita da v2.2 in maggio 2026 |
| `.git/`, `.claude/skills/` | Repository e skill stessa, non sono knowledge da indicizzare |
| `subtree-pull.bat`, `.gitignore` | File operativi non documentali |

---

## Procedura di re-sync delle costanti

Quando si nota disallineamento, eseguire:

```python
# 1. Recupera tutto il notebook
notebook_get(notebook_id="bc8dfeee-c3f0-412d-aa88-f8e0a4025fa5")

# 2. Recupera tutte le label con i loro source assegnati
label:list(notebook_id="bc8dfeee-c3f0-412d-aa88-f8e0a4025fa5")

# 3. Aggiorna le tabelle qui sopra
# 4. Aggiorna la riga "Ultimo aggiornamento" in cima al file
```

---

## ⚠️ Source fantasma — segnali di allarme

Se `label:list` mostra **più source_id di quelli che dovrebbero esserci**, è probabile
ci siano source fantasma (vecchi ID rimasti dopo un ricaricamento). Controlla:

```
source_count nel notebook_get  vs  somma source_ids unici in label:list
```

Se non corrispondono → ci sono fantasmi. Vedi `@examples/cleanup-ghosts.md` per la procedura.

Nello stato attuale (Mag 2026): 9 source totali, ogni source ha esattamente 1 label
→ somma source_ids in tutte le label = 9.
