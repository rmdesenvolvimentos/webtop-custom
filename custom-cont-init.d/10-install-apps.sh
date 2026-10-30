#!/bin/bash
# 10-install-apps.sh: Aplicativos complementares e integrações da interface Windows 11

echo "[apps-init] Verificando e instalando aplicativos padrão do Windows 11..."

# 1. Google Chrome (Navegador padrão do sistema)
if ! command -v google-chrome-stable >/dev/null 2>&1 && ! command -v google-chrome >/dev/null 2>&1; then
    echo "[apps-init] Instalando Google Chrome oficial..."
    mkdir -p /etc/apt/keyrings
    curl -fsSL https://dl.google.com/linux/linux_signing_key.pub | gpg --dearmor --yes -o /etc/apt/keyrings/google-chrome.gpg 2>/dev/null || true
    echo "deb [arch=amd64 signed-by=/etc/apt/keyrings/google-chrome.gpg] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list
    export DEBIAN_FRONTEND=noninteractive
    apt-get update -qq
    apt-get install -y -qq --no-install-recommends google-chrome-stable 2>/dev/null || true
fi

# Configuração de flags do Chrome para contêiner Docker (sem sandbox travado)
mkdir -p /etc/default
cat << 'EOF' > /etc/default/google-chrome
google_chrome_flags="--no-sandbox --disable-dev-shm-usage"
EOF

# Definir Google Chrome como navegador padrão do sistema
if command -v google-chrome-stable >/dev/null 2>&1; then
    update-alternatives --set x-www-browser /usr/bin/google-chrome-stable 2>/dev/null || true
    update-alternatives --set gnome-www-browser /usr/bin/google-chrome-stable 2>/dev/null || true
    ln -sf /usr/share/applications/google-chrome.desktop /usr/share/applications/com.google.Chrome.desktop 2>/dev/null || true
    xdg-settings set default-web-browser google-chrome.desktop 2>/dev/null || true
fi

# 2. Visual Studio Code
if ! command -v code >/dev/null 2>&1; then
    echo '[apps-init] Instalando Visual Studio Code...'
    mkdir -p /etc/apt/keyrings
    curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor --yes -o /etc/apt/keyrings/packages.microsoft.gpg 2>/dev/null || true
    echo 'deb [arch=amd64,arm64,armhf signed-by=/etc/apt/keyrings/packages.microsoft.gpg] https://packages.microsoft.com/repos/code stable main' > /etc/apt/sources.list.d/vscode.list
    export DEBIAN_FRONTEND=noninteractive
    apt-get update -qq
    apt-get install -y -qq --no-install-recommends code 2>/dev/null || true
fi

# 3. OpenCode (IA Coding Assistant Desktop)
if ! command -v opencode >/dev/null 2>&1 && [ ! -d /opt/OpenCode ]; then
    (
        echo '[apps-init] Instalando OpenCode Desktop...'
        if [ -f /DATA/vps/OpenCode/opencode.deb ]; then
            dpkg -i /DATA/vps/OpenCode/opencode.deb >/dev/null 2>&1 || apt-get install -y -f >/dev/null 2>&1 || true
        else
            mkdir -p /tmp
            curl -sSL "https://github.com/anomalyco/opencode/releases/download/v2.2.3/opencode-desktop-linux-amd64.deb" -o /tmp/opencode.deb 2>/dev/null || true
            if [ -f /tmp/opencode.deb ]; then
                dpkg -i /tmp/opencode.deb >/dev/null 2>&1 || apt-get install -y -f >/dev/null 2>&1 || true
                rm -f /tmp/opencode.deb 2>/dev/null || true
            fi
        fi
        echo '[apps-init] OpenCode Desktop instalado com sucesso.'
    ) &
fi

# Wrapper opencode-desktop com flags de compatibilidade Docker
cat << 'EOF' > /usr/local/bin/opencode-desktop
#!/bin/bash
if [ -x /opt/OpenCode/ai.opencode ]; then
    exec /opt/OpenCode/ai.opencode --no-sandbox "$@"
elif [ -x /config/.local/bin/opencode ]; then
    exec /config/.local/bin/opencode "$@"
elif command -v opencode >/dev/null 2>&1; then
    exec opencode "$@"
else
    zenity --error --text="OpenCode não encontrado ou ainda está sendo instalado." 2>/dev/null || true
fi
EOF
chmod +x /usr/local/bin/opencode-desktop

# Ícone e atalho no menu para OpenCode
mkdir -p /usr/share/icons/hicolor/64x64/apps 2>/dev/null || true
if [ -f /config-template/opencode-64.png ]; then
    cp -f /config-template/opencode-64.png /usr/share/icons/hicolor/64x64/apps/ai.opencode.png 2>/dev/null || true
    gtk-update-icon-cache -f -t /usr/share/icons/hicolor 2>/dev/null || true
fi

cat << 'EOF' > /usr/share/applications/ai.opencode.desktop.desktop
[Desktop Entry]
Name=OpenCode
GenericName=AI Coding Assistant
Comment=Open source AI coding agent and editor
Exec=/usr/local/bin/opencode-desktop %U
Terminal=false
Type=Application
Icon=ai.opencode
StartupWMClass=ai.opencode.desktop
MimeType=x-scheme-handler/opencode;
Categories=Development;IDE;
EOF
chmod +x /usr/share/applications/ai.opencode.desktop.desktop
ln -sf /usr/share/applications/ai.opencode.desktop.desktop /usr/share/applications/opencode.desktop 2>/dev/null || true

# 4. Instalação da Microsoft Store (win-store)
if [ -f /config/win-store.py ]; then
    cp -f /config/win-store.py /usr/local/bin/win-store
    chmod +x /usr/local/bin/win-store
elif [ -f /config-template/win-store.py ]; then
    cp -f /config-template/win-store.py /usr/local/bin/win-store
    chmod +x /usr/local/bin/win-store
fi

cat << 'EOF' > /usr/share/applications/win-store.desktop
[Desktop Entry]
Version=1.0
Type=Application
Name=Microsoft Store
GenericName=Loja de Aplicativos
Comment=Instalar e Desinstalar Aplicativos e Pacotes
Exec=/usr/local/bin/win-store
Icon=win-store
Path=/config
Terminal=false
StartupNotify=true
Categories=PackageManager;System;Settings;GTK;
StartupWMClass=win-store
EOF
chmod +x /usr/share/applications/win-store.desktop

# Redirecionamento synaptic-pkexec para win-store
cat << 'EOF' > /usr/bin/synaptic-pkexec
#!/bin/sh
exec /usr/local/bin/win-store "$@"
EOF
chmod +x /usr/bin/synaptic-pkexec

# Compatibilidade thunar-real para o Docklike
cat << 'EOF' > /usr/share/applications/thunar-real.desktop
[Desktop Entry]
Name=Arquivos
Comment=Gerenciador de Arquivos
GenericName=Gerenciador de Arquivos
Exec=thunar %U
Icon=org.xfce.thunar
Terminal=false
StartupNotify=true
Type=Application
Categories=System;FileManager;
StartupWMClass=thunar-real
EOF
chmod +x /usr/share/applications/thunar-real.desktop

# Gerenciador de Tarefas do Windows
if [ -f /config/win_taskmgr.py ]; then
    chmod +x /config/win_taskmgr.py
    ln -sf /config/win_taskmgr.py /usr/local/bin/win-taskmgr
    ln -sf /usr/local/bin/win-taskmgr /usr/bin/xfce4-taskmanager
fi

# Wrapper agy (se presente no host)
if [ -f /DATA/bin/agy ]; then
    cat << 'EOF' > /usr/local/bin/agy
#!/bin/bash
exec /DATA/bin/agy --dangerously-skip-permissions "$@"
EOF
    chmod +x /usr/local/bin/agy
fi

# Sincronização de atalhos da área de trabalho e remoção de resíduos do Chromium
if [ -d /config/Desktop ]; then
    rm -f /config/Desktop/chromium*.desktop /config/Desktop/*chromium*.desktop 2>/dev/null || true
    if [ -f /usr/share/applications/google-chrome.desktop ] && [ ! -f "/config/Desktop/Google Chrome.desktop" ]; then
        cp -f /usr/share/applications/google-chrome.desktop "/config/Desktop/Google Chrome.desktop" 2>/dev/null || true
        chmod +x "/config/Desktop/Google Chrome.desktop" 2>/dev/null || true
        chown abc:abc "/config/Desktop/Google Chrome.desktop" 2>/dev/null || true
    fi
    if [ -f /config-template/Desktop/OpenCode.desktop ] && [ ! -f "/config/Desktop/OpenCode.desktop" ]; then
        cp -f /config-template/Desktop/OpenCode.desktop "/config/Desktop/OpenCode.desktop" 2>/dev/null || true
        chmod +x "/config/Desktop/OpenCode.desktop" 2>/dev/null || true
        chown abc:abc "/config/Desktop/OpenCode.desktop" 2>/dev/null || true
    fi
fi
