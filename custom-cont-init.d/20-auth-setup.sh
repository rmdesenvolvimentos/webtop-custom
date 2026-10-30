#!/bin/bash
# 20-auth-setup.sh: Ativação segura do Nginx, servidor de autenticação e tela de bloqueio

echo "[auth-setup] Configurando Nginx e servidor de autenticação..."

# 1. Configurar Nginx (atualizar em /defaults/default.conf e em /etc/nginx)
if [ -f /config/nginx-default.conf ]; then
    cp -f /config/nginx-default.conf /defaults/default.conf 2>/dev/null || true
    cp -f /config/nginx-default.conf /etc/nginx/sites-available/default 2>/dev/null || true
    nginx -t >/dev/null 2>&1 && nginx -s reload >/dev/null 2>&1 || true
fi

# 2. Injetar lock_manager.js dinamicamente em Selkies (sem sobrescrever bundles JS nativos)
for DASH_DIR in /usr/share/selkies/web /usr/share/selkies/selkies-dashboard; do
    if [ -f "$DASH_DIR/index.html" ]; then
        if ! grep -q "lock_manager.js" "$DASH_DIR/index.html"; then
            echo "[auth-setup] Injetando lock_manager.js em $DASH_DIR/index.html..."
            sed -i 's|</body>|<script src="/lock_manager.js"></script></body>|' "$DASH_DIR/index.html"
        fi
    fi
done

# Copiar lock_manager.js para os diretórios web
if [ -f /config/lock_manager.js ]; then
    cp -f /config/lock_manager.js /usr/share/selkies/web/lock_manager.js 2>/dev/null || true
    cp -f /config/lock_manager.js /usr/share/selkies/selkies-dashboard/lock_manager.js 2>/dev/null || true
fi

# 3. Configurar e supervisionar o serviço s6 para auth_server.py
mkdir -p /run/service/svc-webtop-auth
cat << 'SRV' > /run/service/svc-webtop-auth/run
#!/usr/bin/with-contenv bash
exec python3 /config/auth_server.py
SRV
chmod +x /run/service/svc-webtop-auth/run

# Se não estiver rodando no momento, iniciar imediatamente
if ! pgrep -f "auth_server.py" >/dev/null 2>&1; then
    echo "[auth-setup] Iniciando auth_server.py em background..."
    nohup python3 /config/auth_server.py >/var/log/auth_server.log 2>&1 &
fi

# 4. Configurar GUI de preferências de usuário
if [ -f /config/account_settings_gui.py ]; then
    ln -sf /config/account_settings_gui.py /usr/local/bin/account-settings-gui
    chmod +x /config/account_settings_gui.py
fi
if [ -f "/config/Desktop/Configurações da Conta.desktop" ]; then
    cp "/config/Desktop/Configurações da Conta.desktop" /usr/share/applications/account-settings.desktop 2>/dev/null || true
elif [ -f /config/Desktop/account-settings.desktop ]; then
    cp /config/Desktop/account-settings.desktop /usr/share/applications/account-settings.desktop 2>/dev/null || true
fi

# 5. Configurar Gerenciador de Tarefas do Windows
if [ -f /config/win_taskmgr.py ]; then
    ln -sf /config/win_taskmgr.py /usr/local/bin/win-taskmgr
    ln -sf /usr/local/bin/win-taskmgr /usr/bin/xfce4-taskmanager
    chmod +x /config/win_taskmgr.py
    which dpkg >/dev/null 2>&1 && dpkg -s python3-gi-cairo >/dev/null 2>&1 || (apt-get update -qq && apt-get install -y -qq python3-cairo python3-gi-cairo >/dev/null 2>&1) || true
fi
if [ -f /usr/share/applications/win-taskmgr.desktop ]; then
    ln -sf /usr/local/bin/win-taskmgr /usr/bin/xfce4-taskmanager
    cp /usr/share/applications/win-taskmgr.desktop '/config/Desktop/Gerenciador de Tarefas.desktop' 2>/dev/null || true
    chmod +x '/config/Desktop/Gerenciador de Tarefas.desktop' 2>/dev/null || true
fi

# 6. Comandos e atalhos de bloqueio de tela
if [ -f /config/webtop-lock ]; then
    cp /config/webtop-lock /usr/local/bin/webtop-lock
    chmod +x /usr/local/bin/webtop-lock
    ln -sf /usr/local/bin/webtop-lock /usr/bin/xflock4
fi
if [ -f /config/webtop-lock.desktop ]; then
    cp /config/webtop-lock.desktop /usr/share/applications/webtop-lock.desktop
fi
if [ -f /config/webtop-logout.desktop ]; then
    cp /config/webtop-logout.desktop /usr/share/applications/webtop-logout.desktop
fi

echo "[auth-setup] Configuração de autenticação e segurança finalizada com sucesso!"
