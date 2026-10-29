#!/bin/bash
set -e

# 1. Aplicar GTK e Gerenciador de Janelas Dark
xfconf-query -c xsettings -p /Net/ThemeName -s "Windows-11-Dark-Blue" 2>/dev/null || true
xfconf-query -c xfwm4 -p /general/theme -s "Windows-11-Dark-Blue" 2>/dev/null || true

# 2. Aplicar Ícones Windows 11 Dark
xfconf-query -c xsettings -p /Net/IconThemeName -s "Win11-dark" 2>/dev/null || true

# 3. Aplicar Wallpaper Dark no Desktop e Login
WALLPAPER="/config/wallpapers/windows11_dark.jpg"
if [ -f "$WALLPAPER" ]; then
    xfconf-query -c xfce4-desktop -p /backdrop/screen0/monitorscreen/workspace0/last-image -s "$WALLPAPER" 2>/dev/null || true
    cp -f "$WALLPAPER" /config/login_assets/wallpaper.jpg 2>/dev/null || true
fi

# 4. Estilo Dark para Barra de Tarefas
cat << 'EOF' > /config/.config/gtk-3.0/theme-mode.css
/* Modo Escuro - Barra de Tarefas */
.xfce4-panel {
    background-color: #101010;
    color: #ffffff;
}
.xfce4-panel button {
    color: #ffffff;
}
.xfce4-panel button:hover {
    background-color: rgba(255, 255, 255, 0.08);
}
EOF

# 5. Recarregar painel
xfce4-panel -r 2>/dev/null &

# 6. Notificacao
notify-send "Modo Escuro Ativado" "Tema Windows 11 Dark e ícones aplicados com sucesso." -i weather-clear-night 2>/dev/null || true
echo "WinDark ativado com sucesso!"
