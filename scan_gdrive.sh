#!/bin/bash
echo "-------------------------------------------------"
echo "🔄 Lancement du Scan Google Drive..."
echo "-------------------------------------------------"

export PYTHONPATH=backend:.
python3 backend/main.py --once
