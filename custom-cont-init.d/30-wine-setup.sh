#!/bin/bash
# 30-wine-setup.sh: Persistencia do wine, ptrace, launcher e otimizacoes de desempenho

echo 0 > /proc/sys/kernel/yama/ptrace_scope 2>/dev/null || true

# Configura ALSA dummy para evitar que softwares travem tentando abrir placas inexistentes
cat << 'ASOUND' > /etc/asound.conf
pcm.!default {
    type null
}
ctl.!default {
    type null
}
ASOUND
cp -f /etc/asound.conf /config/.asoundrc 2>/dev/null || true

# 1. Launcher silencioso e otimizado
cat << "LAUNCHER" > /usr/local/bin/win-launcher
#!/usr/bin/env bash
export WINEPREFIX="${WINEPREFIX:-/config/.wine}"
export WINEDEBUG="-all"
export WINEESYNC=1
export WINEFSYNC=1
export DISPLAY="${DISPLAY:-:1}"

ulimit -n 524288 2>/dev/null || true
export LP_NUM_THREADS=4
export MESA_GL_VERSION_OVERRIDE=4.5
export MESA_GLSL_VERSION_OVERRIDE=450
export WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS="--disable-gpu --disable-software-rasterizer --disable-dev-shm-usage --no-sandbox"

unset LD_PRELOAD
export LD_PRELOAD=""

TARGET="$1"
[ -z "$TARGET" ] && exit 0
[ ! -f "$TARGET" ] && [ -f "$(pwd)/$TARGET" ] && TARGET="$(pwd)/$TARGET"
[ ! -f "$TARGET" ] && exit 1

TARGET_DIR="$(dirname "$TARGET")"
TARGET_FILE="$(basename "$TARGET")"
EXT="${TARGET_FILE##*.}"
EXT_LOWER="$(echo "$EXT" | tr "[:upper:]" "[:lower:]")"
shift
chmod +r "$TARGET" 2>/dev/null || true
cd "$TARGET_DIR" || exit 1

LOG_FILE="/config/.wine/last_run.log"
echo "[$(date)] Executando: $TARGET" >> "$LOG_FILE" 2>/dev/null || true

EXTRA_FLAGS=()
case "${TARGET_FILE,,}" in
    terminal*.exe)
        EXTRA_FLAGS=("/portable")
        ;;
esac

case "$EXT_LOWER" in
    msi) nohup wine msiexec /i "$TARGET" "$@" "${EXTRA_FLAGS[@]}" >> "$LOG_FILE" 2>&1 & ;;
    bat|cmd) nohup wine cmd /c "$TARGET" "$@" "${EXTRA_FLAGS[@]}" >> "$LOG_FILE" 2>&1 & ;;
    reg) nohup wine regedit "$TARGET" >> "$LOG_FILE" 2>&1 & ;;
    *) nohup wine "$TARGET" "$@" "${EXTRA_FLAGS[@]}" >> "$LOG_FILE" 2>&1 & ;;
esac
disown 2>/dev/null || true
exit 0
LAUNCHER
chmod +x /usr/local/bin/win-launcher

# 2. Desktop file
cat << "DESK" > /usr/share/applications/win-launcher.desktop
[Desktop Entry]
Version=1.0
Type=Application
Name=Aplicativo Windows
GenericName=Executável do Windows
Comment=Executar programas do Windows (.exe, .msi)
Exec=/usr/local/bin/win-launcher %f
Icon=application-x-ms-dos-executable
MimeType=application/vnd.microsoft.portable-executable;application/x-ms-dos-executable;application/x-msdownload;application/x-dosexec;application/x-msi;application/x-bat;application/x-mswinurl;application/x-ms-shortcut;
Terminal=false
StartupNotify=true
NoDisplay=true
Categories=System;Utility;
DESK

# 3. Mapeamento D: para /DATA
if [ -d /config/.wine/dosdevices ] && [ ! -L /config/.wine/dosdevices/d: ]; then
    ln -sf /DATA /config/.wine/dosdevices/d:
fi

update-desktop-database /usr/share/applications 2>/dev/null || true
