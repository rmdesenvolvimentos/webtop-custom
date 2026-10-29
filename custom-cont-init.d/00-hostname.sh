#!/bin/bash
# 00-hostname.sh: Garante que o hostname amigavel persista no boot do container

TARGET_HOST="cloud-vps"
if [ -f /config/.custom_prompt_env ]; then
    CUSTOM_VAL=$(grep "CUSTOM_HOST=" /config/.custom_prompt_env | cut -d "=" -f2 | tr -d "\"'" | tr -d " ")
    if [ -n "$CUSTOM_VAL" ]; then
        TARGET_HOST="$CUSTOM_VAL"
    fi
fi

# Define o hostname no sistema
hostname "$TARGET_HOST" 2>/dev/null || true
echo "$TARGET_HOST" > /etc/hostname 2>/dev/null || true

# Mapeia no /etc/hosts para o sudo resolver sem lentidao
if ! grep -qw "$TARGET_HOST" /etc/hosts; then
    echo "127.0.0.1 $TARGET_HOST" >> /etc/hosts 2>/dev/null || true
fi
