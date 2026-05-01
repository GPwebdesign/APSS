# APSS — Procedura Allineamento Git tra Raspberry Pi e VM

**Contesto:** Due repository Git separati su GitHub (GPwebdesign, privati).
Sviluppo sulla VM (gp68-vmware), deploy sul Pi (hawk). Workflow: VM → push → pull Pi.

---

## Repository

| Repository | Contenuto |
|---|---|
| `rosmaster_project` | Codice Python: app Kivy, rosmaster_main.py, camera, pan/tilt, test_files/ |
| `ros2_py_ws` | Workspace ROS2: nodi, URDF, launch file, mappe |

---

## Workflow Standard VM → Pi

```bash
# VM — dopo modifiche
cd ~/Workspaces/rosmaster_project   # o ros2_py_ws
git add -A
git commit -m "descrizione"
git push

# Pi — ricezione modifiche
cd ~/Workspaces/rosmaster_project   # o ros2_py_ws
git pull
```

---

## Build obbligatoria dopo modifiche ros2_py_ws

```bash
cd ~/Workspaces/ros2_py_ws
git pull
colcon build --symlink-install
source ~/.bashrc
```

---

## Verifica allineamento prima di iniziare una sessione

```bash
# Su entrambe le macchine — confronta l'hash del commit
git log --oneline -3
# I primi 7 caratteri dell'hash devono coincidere
```

---

## Branch divergenti — problema frequente

Si verifica quando si modificano file direttamente sul Pi senza sincronizzare.

```bash
# Soluzione standard — merge
git config pull.rebase false
git pull

# Se ci sono conflitti — risolverli manualmente poi:
git add -A
git commit -m "merge"
git push   # se sei sul Pi e vuoi portare le modifiche sulla VM
```

---

## File modificati solo sul Pi da portare su VM

```bash
# Pi
git add <file>
git commit -m "modifica da hawk"
git push

# VM
git pull
```

---

## Regole su file speciali

- **`motor_calibration.json`** — si modifica direttamente sul Pi dopo calibrazione. Fare sempre push dal Pi e pull sulla VM.
- **`rosmaster_kivy/save/`** — foto e video, cartella locale, NON nel repository.
- **File `.pyc` e `__pycache__/`** — già in .gitignore, non tracciati.
- **Mappe `ros2_py_ws/maps/*.pgm` e `*.yaml`** — vanno nel repo con commit esplicito dopo ogni sessione di mappatura.

---

## Commit mappa dopo sessione SLAM

```bash
# Pi — dopo salvataggio mappa con slam_toolbox
cd ~/Workspaces/ros2_py_ws
git add maps/
git commit -m "map: sessione N - descrizione stanza"
git push

# VM
git pull
```

---

## Verifica stato completo — da eseguire all'inizio di ogni sessione

```bash
# VM
cd ~/Workspaces/rosmaster_project && git status && git log --oneline -3
cd ~/Workspaces/ros2_py_ws && git status && git log --oneline -3

# Pi
cd ~/Workspaces/rosmaster_project && git status && git log --oneline -3
cd ~/Workspaces/ros2_py_ws && git status && git log --oneline -3
```

---

## Regola generale

> Modificare sempre prima sulla VM → push → pull sul Pi.
> Evitare di modificare lo stesso file su Pi e VM senza sincronizzare.

---

*APSS — GPwebdesign — Aprile 2026*
