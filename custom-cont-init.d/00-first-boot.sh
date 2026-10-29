#!/bin/bash
# 00-first-boot.sh: Copia arquivos de modelo para /config se for o primeiro boot

if [ -d /config-template ] && [ ! -f /config/auth_server.py ]; then
    echo "[first-boot] Detectado primeiro boot do container! Inicializando /config..."
    cp -rn /config-template/* /config/ 2>/dev/null || true
    echo "[first-boot] Arquivos de modelo copiados com sucesso."
fi
