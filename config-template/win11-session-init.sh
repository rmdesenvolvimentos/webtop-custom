#!/bin/bash
# win11-session-init.sh: Inicialização e auto-recuperação da interface Windows 11 no login do usuário

WALLPAPER="/config/wallpapers/windows11_dark.jpg"
[ -f "$WALLPAPER" ] || WALLPAPER="/usr/share/backgrounds/windows11_dark.jpg"

# 1. Garante suporte completo a renderização de ícones SVG e cache de ícones
if [ ! -f /tmp/.win11_icons_cached ]; then
    gdk-pixbuf-query-loaders --update-cache 2>/dev/null || true
    gtk-update-icon-cache -f -t /config/.icons/Eleven-Dark 2>/dev/null || true
    gtk-update-icon-cache -f -t /config/.icons/Eleven 2>/dev/null || true
    gtk-update-icon-cache -f -t /usr/share/icons/Eleven-Dark 2>/dev/null || true
    gtk-update-icon-cache -f -t /usr/share/icons/Eleven 2>/dev/null || true
    gtk-update-icon-cache -f -t /usr/share/icons/hicolor 2>/dev/null || true
    touch /tmp/.win11_icons_cached 2>/dev/null || true
fi

# 2. Configura e garante confiança (Trusted) de todos os atalhos do Desktop (elimina erros de metadata do XFCE 4.18)
mkdir -p /config/.local/share/gvfs-metadata /config/.local/share/applications 2>/dev/null || true
[ -f /config/.local/share/gvfs-metadata/home ] || touch /config/.local/share/gvfs-metadata/home 2>/dev/null || true

# Limpa atalhos antigos com nomes problemáticos (caracteres especiais como ':')
rm -f "/config/Desktop/Disco Local (D:).desktop" "/config/Desktop/Disco%20Local%(D:).desktop" 2>/dev/null || true

for f in /config/Desktop/*.desktop; do
    [ -f "$f" ] || continue
    chmod +x "$f"
    checksum=$(sha256sum "$f" | awk '{print $1}')
    gio set -t string "$f" metadata::xfce-exe-checksum "$checksum" 2>/dev/null || true
    gio set -t string "$f" metadata::trusted true 2>/dev/null || true
    fname=$(basename "$f")
    cp -f "$f" "/usr/share/applications/$fname" 2>/dev/null || true
    cp -f "$f" "/config/.local/share/applications/$fname" 2>/dev/null || true
done

# 3. Configura Wallpaper em todos os monitores e workspaces detectados no XFCE
if [ -f "$WALLPAPER" ]; then
    # Atualiza todas as propriedades de backdrop já criadas pelo xfce4-desktop
    for prop in $(xfconf-query -c xfce4-desktop -l 2>/dev/null | grep "last-image"); do
        xfconf-query -c xfce4-desktop -p "$prop" -s "$WALLPAPER" 2>/dev/null || true
    done
    for prop in $(xfconf-query -c xfce4-desktop -l 2>/dev/null | grep "image-style"); do
        xfconf-query -c xfce4-desktop -p "$prop" -s 5 2>/dev/null || true
    done
    for prop in $(xfconf-query -c xfce4-desktop -l 2>/dev/null | grep "color-style"); do
        xfconf-query -c xfce4-desktop -p "$prop" -s 0 2>/dev/null || true
    done

    # Detecta monitores ativos via xrandr e xfconf para cobrir novas resoluções
    MONITORS=$(xrandr 2>/dev/null | grep " connected" | awk '{print $1}')
    [ -z "$MONITORS" ] && MONITORS="screen screen0 0 1 Virtual-1 Virtual1 Default HDMI-1 DP-1"
    for mon in $MONITORS; do
        for ws in workspace0 workspace1 workspace2 workspace3; do
            xfconf-query -c xfce4-desktop -p "/backdrop/screen0/monitor$mon/$ws/last-image" --create -t string -s "$WALLPAPER" 2>/dev/null || true
            xfconf-query -c xfce4-desktop -p "/backdrop/screen0/monitor$mon/$ws/image-style" --create -t int -s 5 2>/dev/null || true
            xfconf-query -c xfce4-desktop -p "/backdrop/screen0/monitor$mon/$ws/color-style" --create -t int -s 0 2>/dev/null || true
        done
    done
    xfconf-query -c xfce4-desktop -p "/backdrop/single-workspace-mode" -s true 2>/dev/null || true
    xfconf-query -c xfce4-desktop -p "/backdrop/single-workspace-number" -s 0 2>/dev/null || true
fi

# 4. Posicionamento da Barra de Tarefas na borda inferior
xfconf-query -c xfce4-panel -p /panels/panel-1/position -s "p=8;x=0;y=0" 2>/dev/null || true
xfconf-query -c xfce4-panel -p /panels/panel-1/position-locked -s true 2>/dev/null || true

# 5. Verifica integridade do menu Iniciar (Whisker Menu) e barra centralizada (Docklike)
CURRENT_P1=$(xfconf-query -c xfce4-panel -p /plugins/plugin-1 2>/dev/null || true)
if [ "$CURRENT_P1" != "whiskermenu" ]; then
    echo "[win11-session] Restaurando painel do Windows 11..."
    cp -af /config-template/.config/xfce4/xfconf/xfce-perchannel-xml/xfce4-panel.xml /config/.config/xfce4/xfconf/xfce-perchannel-xml/xfce4-panel.xml 2>/dev/null || true
    xfce4-panel -r 2>/dev/null || true
fi

# 6. Recarrega o desktop para exibir wallpaper e ícones
if [ ! -f /tmp/.win11_desktop_reloaded ]; then
    sleep 0.5
    xfdesktop --reload 2>/dev/null || true
    touch /tmp/.win11_desktop_reloaded 2>/dev/null || true
fi
