# APSS — Workflow allineamento RPi ↔ PC ↔ GitHub

## Strumenti
- `~/Workspaces/apss-push.sh` — su hawk (RPi), gestisce push di entrambi i repo
- `subtree-pull.bat` — su PC Windows, nella root di `D:\_claudecodeproject\APSS\`

---

## Caso 1 — Ho modificato codice su hawk, voglio aggiornare il PC

**Su hawk:**
```bash
~/Workspaces/apss-push.sh
```
- Seleziona `1` (rosmaster_project), `2` (ros2_py_ws) o `3` (entrambi)
- Lo script mostra `git status --short`, chiede messaggio commit, fa `git add -A + commit + push origin main`
- I due repo (`rosmaster_project` e `ros2_py_ws`) sono repo git indipendenti su GitHub

**Sul PC:**
- Lancia `subtree-pull.bat`
- Il batch all'avvio controlla se ci sono file `.md` non committati in APSS → chiede se committare e pushare
- Seleziona `1`, `2` o `3` per fare il pull del subtree corrispondente
- Dopo ogni pull riuscito il batch fa automaticamente `git push origin master` per allineare `github.com/GPwebdesign/APSS`

---

## Caso 2 — Ho modificato file .md o skill in APSS sul PC

**Sul PC:**
- Lancia `subtree-pull.bat`
- Il batch all'avvio vede i file `.md` modificati/non tracciati, li elenca e chiede `[s/n]`
- Rispondi `s`, inserisci messaggio commit → il batch fa `git add + commit + push` automaticamente
- Poi procedi normalmente con il menu subtree se necessario

> I file `.md` (CLAUDE.md, docs/, .claude/skills/) vivono **solo in APSS sul PC** —
> non fanno parte di nessun subtree e non passano per hawk.

---

## Caso 3 — Clone su nuovo PC

```bash
git clone https://github.com/GPwebdesign/APSS.git
```
Include già tutto: documentazione + codice rosmaster_project + ros2_py_ws.

---

## Decisioni chiave da ricordare

- `rosmaster_project` e `ros2_py_ws` sono **subtree** dentro APSS — copie del codice, non submodule
- `apss-push.sh` usa **SSH** (`git@github.com`) — `subtree-pull.bat` usa **HTTPS** — compatibili
- `apss-push.sh` risiede in `~/Workspaces/` e **non è tracciato** da nessun repo git (script locale su hawk)
- Il batch controlla **solo i `.md`** nella root e in `docs/` e `.claude/skills/` — non il codice nei subtree
- `--squash` sempre attivo nel subtree pull — la storia dei repo di codice non inquina APSS
- Stop su hawk sempre con `./apss-push.sh` dalla dir `~/Workspaces/` — mai dai singoli repo