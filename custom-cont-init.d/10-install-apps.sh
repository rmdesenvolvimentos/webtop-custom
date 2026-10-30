#!/bin/bash
# 10-install-apps.sh: Aplicativos complementares e integrações da interface Windows 11

# Instalação do VS Code em segundo plano (não trava a inicialização do desktop)
if ! command -v code >/dev/null 2>&1; then
    (
        echo '[custom-init] Baixando VS Code em segundo plano...'
        mkdir -p /etc/apt/keyrings
        curl -sSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor -o /etc/apt/keyrings/packages.microsoft.gpg 2>/dev/null || true
        echo 'deb [arch=amd64,arm64,armhf signed-by=/etc/apt/keyrings/packages.microsoft.gpg] https://packages.microsoft.com/repos/code stable main' > /etc/apt/sources.list.d/vscode.list
        export DEBIAN_FRONTEND=noninteractive
        apt-get update -qq && apt-get install -y -qq --no-install-recommends code 2>/dev/null || true
        echo '[custom-init] VS Code instalado com sucesso.'
    ) &
fi

# Instalação da Microsoft Store (win-store)
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
