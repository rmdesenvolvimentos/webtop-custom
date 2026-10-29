#!/bin/bash
# 1. Restore Nginx config if present
if [ -f /config/nginx-default.conf ]; then
    cp /config/nginx-default.conf /etc/nginx/sites-available/default
    nginx -t >/dev/null 2>&1 && nginx -s reload >/dev/null 2>&1 || true
fi

# 2. Restore Selkies index.html with lock_manager script
if [ -f /config/selkies-index.html ]; then
    cp /config/selkies-index.html /usr/share/selkies/web/index.html
fi

# 3. Restore s6 auth service if missing
if [ ! -d /etc/s6-overlay/s6-rc.d/svc-webtop-auth ]; then
    mkdir -p /etc/s6-overlay/s6-rc.d/svc-webtop-auth/dependencies.d
    echo "longrun" > /etc/s6-overlay/s6-rc.d/svc-webtop-auth/type
    echo "init-services" > /etc/s6-overlay/s6-rc.d/svc-webtop-auth/dependencies.d/init-services
    cat << 'SRV' > /etc/s6-overlay/s6-rc.d/svc-webtop-auth/run
#!/usr/bin/with-contenv bash
exec python3 /config/auth_server.py
SRV
    chmod +x /etc/s6-overlay/s6-rc.d/svc-webtop-auth/run
    mkdir -p /etc/s6-overlay/s6-rc.d/user/contents.d
    touch /etc/s6-overlay/s6-rc.d/user/contents.d/svc-webtop-auth
fi

# 4. Restore account settings GUI and desktop file
if [ -f /config/account_settings_gui.py ]; then
    ln -sf /config/account_settings_gui.py /usr/local/bin/account-settings-gui
    chmod +x /config/account_settings_gui.py
fi
if [ -f /config/Desktop/account-settings.desktop ]; then
    cp /config/Desktop/account-settings.desktop /usr/share/applications/account-settings.desktop
fi

# 5. Restore Windows Task Manager
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


# 6. Restore Lock & Logout Commands and Desktop Entries
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
if [ -f /config/lock_manager.js ]; then
    cp /config/lock_manager.js /usr/share/selkies/web/lock_manager.js
fi
