#!/bin/bash

# APSS — Push rosmaster_project su GitHub
# Eseguire dalla root di ~/Workspaces/rosmaster_project/

set -e  # interrompi su qualsiasi errore

cd "$(dirname "$0")"

# Verifica che siamo nel repo giusto
if [ ! -f "rosmaster_main.py" ]; then
    echo "ERRORE: non sei nella root di rosmaster_project"
    exit 1
fi

echo "============================================"
echo "  APSS — Push rosmaster_project → GitHub"
echo "============================================"
echo ""

# Mostra modifiche in sospeso
echo "[ git status ]"
git status --short
echo ""

# Chiede messaggio commit
read -p "Messaggio commit (invio = 'update: modifiche in corso'): " msg
if [ -z "$msg" ]; then
    msg="update: modifiche in corso"
fi

# Add tutto, commit e push
git add -A
git commit -m "$msg"
git push origin main

echo ""
echo "OK — rosmaster_project pushato su GitHub."
echo "Ora esegui subtree-pull.bat sul PC per aggiornare APSS."
