# NotebookLM APSS — Costanti

> ⚠️ Verificare al primo uso di ogni sessione con:
> - `notebook_get(notebook_id="bc8dfeee-c3f0-412d-aa88-f8e0a4025fa5")`
> - `label:list(notebook_id="bc8dfeee-c3f0-412d-aa88-f8e0a4025fa5")`
>
> Se gli ID seguenti non corrispondono ai valori restituiti, **aggiornare questo file**
> prima di procedere con altre operazioni.

> Ultimo aggiornamento: 14 Maggio 2026

---

## Notebook

| Campo | Valore |
|---|---|
| ID | `bc8dfeee-c3f0-412d-aa88-f8e0a4025fa5` |
| Titolo | `APSS — Autonomous Patrol and Surveillance System` |
| URL | https://notebooklm.google.com/notebook/bc8dfeee-c3f0-412d-aa88-f8e0a4025fa5 |
| Source count atteso | 9 |
| Label count atteso | 8 |

---

## Nota di onboarding

| Campo | Valore |
|---|---|
| Note ID | `56fcad43-9a61-4307-9184-c96034c95502` |
| Titolo | `📍 Onboarding — Come navigare questo notebook` |

> ⚠️ Esiste **una sola** nota nel notebook. Per modificarla usare `note:update`,
> mai `note:create` (causerebbe duplicati).

---

## Label

### Per AREA (5 label)

| Label | Emoji | ID | Source assegnati |
|---|---|---|---|
| `overview` | 📘 | `56502c2f-97d6-43dd-91e6-1fef9beb425c` | Documentazione_Tecnica + architecture |
| `onboarding-ai` | 🤖 | `a87bd8a4-b5f8-4452-b7f1-f58ec3ae0b03` | CLAUDE.md |
| `roadmap` | 🗺️ | `875027a5-c712-4fa2-bae4-11bb40f70586` | plan |
| `session-log` | 📝 | `4b2d9dc5-a8d6-4f71-b18a-05cef7c81b2f` | riepilogo_3 + APSS_memorie |
| `workflow-git` | 🔄 | `2e1c0f37-de94-41fd-a37b-257734d650f0` | allineamento RPi-PC + allineamento RPi-VMware |
| `hardware-docking` | 🔌 | `7355efd2-379f-4795-af37-0d15abe86c99` | Schema Circuitale Docking |

### Per STATO (2 label)

| Label | Emoji | ID | Source assegnati |
|---|---|---|---|
| `stato: reference` | 📚 | `d385b616-8a47-42d5-9e27-109a36660fca` | 7 fonti (tutte tranne plan + riepilogo_3) |
| `stato: in-corso` | ⚙️ | `4ff44f72-f20d-415c-9934-20fab2492433` | plan + riepilogo_3 |

---

## Source (9 fonti)

> ⚠️ Gli `id` cambiano ad ogni ricaricamento. Se le label di una fonte si "perdono",
> probabilmente il source è stato ricaricato → recupera nuovo ID e ri-assegna label.

| File su disco | Source ID atteso | Area | Stato |
|---|---|---|---|
| `APSS_Documentazione_Tecnica_v2_1.docx` | `a4f7604a-283d-4b82-92c4-0070b687f6b3` | 📘 overview | 📚 reference |
| `architecture.md` | `197d8817-bcd3-488f-8226-8dc0a45b68e8` | 📘 overview | 📚 reference |
| `CLAUDE.md` | `5ddedb66-1ee5-4aad-8fef-a341d06068a5` | 🤖 onboarding-ai | 📚 reference |
| `plan.md` | `53a08de2-1601-422b-a429-8ebb22093e60` | 🗺️ roadmap | ⚙️ in-corso |
| `APSS_riepilogo_sessione_mag2026_3.md` | `326f0e30-6ccf-44bb-b025-f442f07c8a32` | 📝 session-log | ⚙️ in-corso |
| `APSS_memorie.md` | `5fdb8f73-1ffd-4551-b2fe-5c3e7430de17` | 📝 session-log | 📚 reference |
| `APSS_allineamento_ RPi-PC-GitHub.md` | `2c9b15b2-a320-4e1a-815a-e36b4f780690` | 🔄 workflow-git | 📚 reference |
| `APSS_allineamento_RPi-VMware-GitHub.md` | `d0da390f-cf22-42b1-8976-9316badb00ad` | 🔄 workflow-git | 📚 reference |
| `Schema Circuitale Docking Station — Rosmaster R2.pdf` | `3141e7b2-1e6f-4b27-93dc-5141d8797739` | 🔌 hardware-docking | 📚 reference |

---

## Path sorgente sul PC

```
D:\_claudecodeproject\APSS\
├── CLAUDE.md                              ✅ nel notebook
├── CLAUDE.local.md                        ❌ NON nel notebook (credenziali)
├── APSS_memorie.md                        ✅ nel notebook
└── docs\
    ├── APSS_Documentazione_Tecnica_v2_1.docx
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
