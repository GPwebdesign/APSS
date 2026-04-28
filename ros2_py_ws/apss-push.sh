#!/bin/bash

# APSS — Push ros2_py_ws su GitHub
# Eseguire dalla root di ~/Workspaces/ros2_py_ws/

set -e

cd "$(dirname "$0")"

# Verifica che siamo nel repo giusto
if [ ! -d "src" ]; then
    echo "ERRORE: non sei nella root di ros2_py_ws"
    exit 1
fi

echo "============================================"
echo "  APSS > Push ros2_py_ws > GitHub"
echo "============================================"
echo ""

echo "[ git status ]"
git status --short
echo ""

read -p "Messaggio commit (invio = 'update: modifiche in corso'): " msg
if [ -z "$msg" ]; then
    msg="update: modifiche in corso"
fi

git add -A
git commit -m "$msg"
git push origin main

echo ""
echo "OK > ros2_py_ws pushato su GitHub."
echo "Ora esegui subtree-pull.bat sul PC per aggiornare APSS."
