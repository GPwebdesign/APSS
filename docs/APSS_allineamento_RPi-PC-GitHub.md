# APSS — Guida Allineamento Repository

> Riferimento rapido per mantenere sincronizzati i tre repository del progetto.

---

## Struttura dei repository

```
github.com/GPwebdesign/APSS              ← repo principale (documentazione + subtree)
github.com/GPwebdesign/rosmaster_project ← codice robot (server TCP, camera, kivy)
github.com/GPwebdesign/ros2_py_ws        ← stack ROS2 (URDF, launch, SLAM, nodi)
```

`rosmaster_project` e `ros2_py_ws` vivono dentro APSS come **subtree** — copie del codice
incorporate direttamente nel repo, non come submodule.

---

## Flusso standard (uso quotidiano)

### 1. Modifiche al codice su hawk → PC

```
hawk$ ./apss-push.sh          (in rosmaster_project/ o ros2_py_ws/)
PC>   subtree-pull.bat         (opzione 1, 2 o 3 — fa pull + push APSS automatico)
```

### 2. Modifiche ai file .md → GitHub

Il batch `subtree-pull.bat` controlla i file `.md` all'avvio e chiede se committare.
In alternativa, dal terminale in `APSS/`:

```bash
git add CLAUDE.md docs/plan.md docs/architecture.md docs/allineamento_repo.md
git commit -m "docs: aggiorna documentazione"
git push
```

---

## Comandi manuali — riferimento completo

### rosmaster_project

**Da hawk — push su GitHub:**
```bash
cd ~/Workspaces/rosmaster_project
./apss-push.sh
```

**Dal PC — aggiorna APSS da GitHub:**
```bash
git subtree pull --prefix=rosmaster_project https://github.com/GPwebdesign/rosmaster_project.git main --squash
git push origin master
```

---

### ros2_py_ws

**Da hawk — push su GitHub:**
```bash
cd ~/Workspaces/ros2_py_ws
./apss-push.sh
```

**Dal PC — aggiorna APSS da GitHub:**
```bash
git subtree pull --prefix=ros2_py_ws https://github.com/GPwebdesign/ros2_py_ws.git main --squash
git push origin master
```

---

### APSS — file documentazione (.md)

**Dal PC — commit e push:**
```bash
cd D:\_claudecodeproject\APSS
git add *.md docs/*.md .claude/skills/*.md
git commit -m "docs: aggiorna documentazione"
git push origin master
```

**Verifica stato:**
```bash
git status --short -- "*.md" "docs/*.md"
```

---

### APSS — clone su nuovo PC

```bash
git clone https://github.com/GPwebdesign/APSS.git
cd APSS
```
Il clone include già tutto: documentazione + codice rosmaster_project + ros2_py_ws.

---

## Verifica allineamento

**Stato locale vs GitHub:**
```bash
git log --oneline -5
git status
```

**Verifica che origin sia allineato:**
```bash
git fetch origin
git log --oneline origin/master -3
```

Se `origin/master` e `HEAD -> master` puntano allo stesso commit, tutto è allineato.

---

## Casi particolari

### Subtree pull fallisce — "working tree has modifications"
Il working tree di APSS ha modifiche non committate. Committale prima:
```bash
git add -A
git commit -m "wip: salvataggio prima di subtree pull"
git subtree pull --prefix=rosmaster_project ... --squash
```

### Subtree pull fallisce — "Updates were rejected"
GitHub è avanti rispetto al locale. Fai prima un pull di APSS:
```bash
git pull origin master
git subtree pull --prefix=rosmaster_project ... --squash
```

### Verificare l'ultimo commit di un subtree
```bash
git log --oneline -- rosmaster_project/ | head -5
git log --oneline -- ros2_py_ws/ | head -5
```

---

## Sbloccare aggiornamenti ROS2 (solo se necessario)

Entrambi i sistemi hanno ~290 package ROS2 in hold a v16.0.19.

```bash
# Su hawk o gp68-vmware
dpkg -l | grep "^ii  ros-humble-" | awk '{print $2}' | xargs sudo apt-mark unhold
```

> ⚠️ Non eseguire senza necessità — il hold garantisce stabilità del sistema.
