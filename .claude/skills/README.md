# .claude/skills — APSS Custom Skills

Questa cartella contiene le skill specifiche per il progetto APSS,
utilizzabili con Claude Code.

## Struttura di una skill
.claude/skills/
└── nome-skill/
├── SKILL.md          ← Frontmatter YAML + istruzioni (max ~50 righe)
│                        Sezione finale: "## ⚠️ Gotchas"
├── references/
│   └── *.md          ← Riferimenti tecnici dettagliati
├── scripts/
│   └── *.py          ← Script di supporto/validazione
└── examples/
├── basic-usage.md
└── advanced.md

## Skill pianificate per APSS

| Skill | Stato | Contenuto |
|-------|-------|----------|
| `tcp-protocol/` | Da creare | Protocollo TCP Yahboom, formati comandi, checksum |
| `mecanum-kinematics/` | Da creare | Formula motori, calibrazione, test cinematica |
| `ros2-apss/` | Da creare | TF tree, topic, ordine avvio, package hold |
| `esp32-firmware/` | Da creare | MicroPython patterns, INA219, webserver chunked |

## Come creare una skill

1. Crea la cartella: `.claude/skills/nome-skill/`
2. Crea `SKILL.md` con frontmatter YAML:
```yaml
   ---
   name: nome-skill
   description: "Quando usare questa skill — trigger precisi"
   version: 1.0
   ---
```
3. Aggiungi istruzioni core (max 50 righe nel SKILL.md)
4. Sposta i dettagli in `references/` e `examples/`
5. Chiudi sempre con `## ⚠️ Gotchas (errori noti da evitare)`