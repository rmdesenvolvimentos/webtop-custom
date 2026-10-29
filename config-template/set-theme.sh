#!/bin/bash
set -e

THEME_CHOICE="$1"

if [ -z "$THEME_CHOICE" ]; then
    if which zenity >/dev/null 2>&1; then
        THEME_CHOICE=$(zenity --list --radiolist \
            --title="Personalização do Windows 10 & 11" \
            --text="Escolha a variação visual desejada:" \
            --column="Ativo" --column="Código" --column="Descrição" \
            TRUE "dark-blue" "Windows 11 Dark - Borda Azul (Ícones Win11 Dark)" \
            FALSE "dark-graphite" "Windows 11 Dark - Borda Grafite (Ícones Win11 Dark)" \
            FALSE "light-blue" "Windows 11 Light - Borda Azul (Ícones Win11)" \
            FALSE "light-classic" "Windows 10 Light - Borda Clássica (Ícones Win10)" \
            --hide-column=2 --width=480 --height=280 2>/dev/null || true)
    fi
fi

if [ -z "$THEME_CHOICE" ]; then
    echo "Nenhum tema selecionado."
    exit 0
fi

case "$THEME_CHOICE" in
    "dark-blue")
        echo "Aplicando Windows 11 Dark (Blue Accent)..."
        xfconf-query -c xsettings -p /Net/ThemeName -s "Windows-11-Dark-Blue" 2>/dev/null || true
        xfconf-query -c xfwm4 -p /general/theme -s "Windows-11-Dark-Blue" 2>/dev/null || true
        xfconf-query -c xsettings -p /Net/IconThemeName -s "Eleven-Dark" 2>/dev/null || true
        WALLPAPER="/config/wallpapers/windows11_dark.jpg"
        BORDER_COLOR="#0078D4"
        PANEL_BG="#101010"
        PANEL_FG="#ffffff"
        ;;
    "dark-graphite")
        echo "Aplicando Windows 11 Dark (Graphite)..."
        xfconf-query -c xsettings -p /Net/ThemeName -s "Windows-11-Dark-Graphite" 2>/dev/null || true
        xfconf-query -c xfwm4 -p /general/theme -s "Windows-11-Dark-Graphite" 2>/dev/null || true
        xfconf-query -c xsettings -p /Net/IconThemeName -s "Eleven-Dark" 2>/dev/null || true
        WALLPAPER="/config/wallpapers/windows11_dark.jpg"
        BORDER_COLOR="#555555"
        PANEL_BG="#101010"
        PANEL_FG="#ffffff"
        ;;
    "light-blue")
        echo "Aplicando Windows 11 Light (Blue Accent)..."
        xfconf-query -c xsettings -p /Net/ThemeName -s "Windows-11-Light-Blue" 2>/dev/null || true
        xfconf-query -c xfwm4 -p /general/theme -s "Windows-11-Light-Blue" 2>/dev/null || true
        xfconf-query -c xsettings -p /Net/IconThemeName -s "Eleven" 2>/dev/null || true
        WALLPAPER="/config/wallpapers/windows11_light.jpg"
        BORDER_COLOR="#0078D4"
        PANEL_BG="#f0f0f0"
        PANEL_FG="#111111"
        ;;
    "light-classic")
        echo "Aplicando Windows 10 Light (Classic)..."
        xfconf-query -c xsettings -p /Net/ThemeName -s "Windows-11-Light-Classic" 2>/dev/null || true
        xfconf-query -c xfwm4 -p /general/theme -s "Windows-11-Light-Classic" 2>/dev/null || true
        xfconf-query -c xsettings -p /Net/IconThemeName -s "Windows-10" 2>/dev/null || true
        WALLPAPER="/config/wallpapers/windows11_light.jpg"
        BORDER_COLOR="#0078D4"
        PANEL_BG="#f0f0f0"
        PANEL_FG="#111111"
        ;;
    *)
        echo "Opção inválida: $THEME_CHOICE"
        exit 1
        ;;
esac

# Atualizar contorno de janela dinamico no CSS
cat << EOF > /config/.config/gtk-3.0/theme-mode.css
/* Modo / Cores de Contorno de Janela */
@define-color window_border_color ${BORDER_COLOR};
@define-color window_border_inactive #3d3d3d;

/* Barra de Tarefas */
.xfce4-panel {
    background-color: ${PANEL_BG};
    color: ${PANEL_FG};
}
.xfce4-panel button {
    color: ${PANEL_FG};
}
.xfce4-panel button:hover {
    background-color: rgba(255, 255, 255, 0.08);
}
EOF

# Atualizar Wallpaper no Desktop se existir
if [ -f "$WALLPAPER" ]; then
    xfconf-query -c xfce4-desktop -p /backdrop/screen0/monitorscreen/workspace0/last-image -s "$WALLPAPER" 2>/dev/null || true
    # Também atualiza a tela de login
    cp -f "$WALLPAPER" /config/login_assets/wallpaper.jpg 2>/dev/null || true
fi

# Reiniciar painel para recarregar estilos e icones
xfce4-panel -r 2>/dev/null &

echo "Tema $THEME_CHOICE aplicado com sucesso!"
