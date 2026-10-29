#!/bin/bash
# 00-first-boot.sh: Inicializa e aplica a personalização do Windows 11 no /config

echo "[first-boot] Verificando integridade das configurações do Windows 11..."

# 1. Se o tema do Windows 11 não estiver instalado em /config, descompactar o pacote
if [ -f /config-template/win11-theme-pack.tar.gz ]; then
    if [ ! -d /config/.themes/Windows-11-Dark-Blue ] || [ ! -d /config/.icons/Eleven-Dark ]; then
        echo "[first-boot] Descompactando temas, ícones e wallpapers do Windows 11..."
        tar -xzf /config-template/win11-theme-pack.tar.gz -C /config/ 2>/dev/null || true
    fi

    # Garante disponibilidade global no sistema
    if [ ! -d /usr/share/themes/Windows-11-Dark-Blue ]; then
        mkdir -p /usr/share/themes /usr/share/icons
        tar -xzf /config-template/win11-theme-pack.tar.gz -C /usr/share/ --strip-components=1 .themes 2>/dev/null || true
        tar -xzf /config-template/win11-theme-pack.tar.gz -C /usr/share/ --strip-components=1 .icons 2>/dev/null || true
    fi
fi

# 2. Copia arquivos de modelo para /config (incluindo diretórios ocultos como .config)
if [ -d /config-template ]; then
    echo "[first-boot] Sincronizando arquivos de configuração e atalhos..."
    # Usar . para copiar todos os arquivos e pastas ocultas
    cp -a /config-template/. /config/ 2>/dev/null || true
    rm -f /config/win11-theme-pack.tar.gz 2>/dev/null || true
fi

# 3. Forçar /defaults/xfce a usar a barra e tema do Windows 11 (evita fallback do LinuxServer)
if [ -d /config/.config/xfce4/xfconf/xfce-perchannel-xml ]; then
    mkdir -p /defaults/xfce 2>/dev/null || true
    cp -f /config/.config/xfce4/xfconf/xfce-perchannel-xml/xfce4-panel.xml /defaults/xfce/ 2>/dev/null || true
    cp -f /config/.config/xfce4/xfconf/xfce-perchannel-xml/xfwm4.xml /defaults/xfce/ 2>/dev/null || true
    cp -f /config/.config/xfce4/xfconf/xfce-perchannel-xml/xsettings.xml /defaults/xfce/ 2>/dev/null || true
fi

# 4. Ajustar permissões para o usuário abc
chown -R abc:abc /config/.themes /config/.icons /config/.config /config/Desktop /config/wallpapers /config/login_assets 2>/dev/null || true
chmod +x /config/*.sh /config/*.py /config/webtop-lock 2>/dev/null || true
chmod +x /config/Desktop/*.desktop 2>/dev/null || true

echo "[first-boot] Personalização do Windows 11 aplicada com sucesso!"
