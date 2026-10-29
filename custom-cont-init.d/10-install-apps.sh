#!/bin/bash
if ! which code >/dev/null 2>&1; then
    echo '[custom-init] Installing VS Code, Whisker Menu, Docklike, Genmon...'
    curl -sSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor -o /etc/apt/keyrings/packages.microsoft.gpg
    echo 'deb [arch=amd64,arm64,armhf signed-by=/etc/apt/keyrings/packages.microsoft.gpg] https://packages.microsoft.com/repos/code stable main' > /etc/apt/sources.list.d/vscode.list
    apt-get update
    apt-get install -y code librsvg2-common scrot xfce4-whiskermenu-plugin xfce4-docklike-plugin xfce4-genmon-plugin python3-cairo python3-gi-cairo xclip
    echo '[custom-init] Apps installed successfully.'
fi

# Ensure Microsoft Store (win-store) is installed and executable
if [ -f /config/win-store.py ]; then
    cp /config/win-store.py /usr/local/bin/win-store
    chmod +x /usr/local/bin/win-store
elif [ -f /config-template/win-store.py ]; then
    cp /config-template/win-store.py /usr/local/bin/win-store
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
Icon=/config/store-64.png
Path=/config
Terminal=false
StartupNotify=true
Categories=PackageManager;System;Settings;GTK;
StartupWMClass=win-store
EOF
chmod +x /usr/share/applications/win-store.desktop

# Ensure synaptic-pkexec redirects to win-store
cat << 'EOF' > /usr/bin/synaptic-pkexec
#!/bin/sh
exec /usr/local/bin/win-store "$@"
EOF
chmod +x /usr/bin/synaptic-pkexec

# Ensure thunar-real desktop file exists for docklike matching
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

# Ensure agy CLI auto-approve wrapper is present
rm -f /usr/local/bin/agy
cat << 'EOF' > /usr/local/bin/agy
#!/bin/bash
exec /DATA/bin/agy --dangerously-skip-permissions "$@"
EOF
chmod +x /usr/local/bin/agy

# Ensure win-taskmgr symlink and permissions
if [ -f /config/win_taskmgr.py ]; then
    chmod +x /config/win_taskmgr.py
    ln -sf /config/win_taskmgr.py /usr/local/bin/win-taskmgr
fi
