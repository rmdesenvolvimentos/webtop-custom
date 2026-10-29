#!/bin/bash
set -e

# 1. Aplicar GTK e Gerenciador de Janelas Light
xfconf-query -c xsettings -p /Net/ThemeName -s "Windows-11-Light-Blue" 2>/dev/null || true
xfconf-query -c xfwm4 -p /general/theme -s "Windows-11-Light-Blue" 2>/dev/null || true

# 2. Aplicar Ícones Windows 11 Light
xfconf-query -c xsettings -p /Net/IconThemeName -s "Win11" 2>/dev/null || true

# 3. Aplicar Wallpaper Light no Desktop e Login
WALLPAPER="/config/wallpapers/windows11_light.jpg"
if [ -f "$WALLPAPER" ]; then
    xfconf-query -c xfce4-desktop -p /backdrop/screen0/monitorscreen/workspace0/last-image -s "$WALLPAPER" 2>/dev/null || true
    cp -f "$WALLPAPER" /config/login_assets/wallpaper.jpg 2>/dev/null || true
fi

# 4. Estilo Light para Barra de Tarefas
cat << 'EOF' > /config/.config/gtk-3.0/theme-mode.css
/* Modo Claro - Barra de Tarefas */
.xfce4-panel {
    background-color: #f3f3f3;
    color: #1a1a1a;
}
.xfce4-panel button {
    color: #1a1a1a;
}
.xfce4-panel button:hover {
    background-color: rgba(0, 0, 0, 0.08);
}
EOF

# 5. Recarregar painel
xfce4-panel -r 2>/dev/null &

# 6. Notificacao
notify-send "Modo Claro Ativado" "Tema Windows 11 Light e ícones aplicados com sucesso." -i weather-clear 2>/dev/null || true
echo "WinLight ativado com sucesso!"
