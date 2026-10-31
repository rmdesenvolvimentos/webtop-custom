#!/bin/bash
# 00-first-boot.sh: Inicializa e aplica a personalização do Windows 11 no /config

echo "[first-boot] Verificando integridade das configurações do Windows 11..."

# 1. Garante que os pacotes de idioma, plugins e dependências essenciais de UI estejam instalados
if [ ! -f /etc/.locales_configured ]; then
    echo "[first-boot] Instalando pacotes de idiomas oficiais (IT, ES, DE, FR, PT, EN)..."
    export DEBIAN_FRONTEND=noninteractive
    apt-get update -qq
    apt-get install -y -qq --no-install-recommends \
        locales \
        language-pack-it \
        language-pack-gnome-it \
        language-pack-es \
        language-pack-gnome-es \
        language-pack-de \
        language-pack-gnome-de \
        language-pack-fr \
        language-pack-gnome-fr \
        language-pack-pt \
        language-pack-gnome-pt \
        language-pack-en \
        language-pack-gnome-en \
        xfce4-whiskermenu-plugin \
        xfce4-docklike-plugin \
        xfce4-genmon-plugin \
        librsvg2-common \
        librsvg2-bin \
        scrot \
        python3-cairo \
        python3-gi-cairo \
        xclip \
        zenity \
        hicolor-icon-theme 2>/dev/null || true
    locale-gen pt_BR.UTF-8 en_US.UTF-8 es_ES.UTF-8 de_DE.UTF-8 fr_FR.UTF-8 it_IT.UTF-8 2>/dev/null || true
    update-locale 2>/dev/null || true
    gdk-pixbuf-query-loaders --update-cache 2>/dev/null || true
    touch /etc/.locales_configured 2>/dev/null || true
fi

# 2. Descompacta temas, ícones e wallpapers
if [ -f /config-template/win11-theme-pack.tar.gz ]; then
    if [ ! -d /config/.themes/Windows-11-Dark-Blue ] || [ ! -d /config/.icons/Eleven-Dark ]; then
        echo "[first-boot] Descompactando temas, ícones e wallpapers do Windows 11 em /config..."
        tar -xzf /config-template/win11-theme-pack.tar.gz -C /config/ 2>/dev/null || true
    fi

    # Garante disponibilidade global no sistema (/usr/share/themes e /usr/share/icons)
    if [ ! -d /usr/share/themes/Windows-11-Dark-Blue ]; then
        echo "[first-boot] Instalando temas globais em /usr/share/themes..."
        mkdir -p /usr/share/themes /usr/share/icons /usr/share/backgrounds
        tar -xzf /config-template/win11-theme-pack.tar.gz -C /usr/share/themes/ --strip-components=1 .themes 2>/dev/null || true
    fi
    if [ ! -d /usr/share/icons/Eleven-Dark ]; then
        echo "[first-boot] Instalando ícones globais em /usr/share/icons..."
        mkdir -p /usr/share/icons
        tar -xzf /config-template/win11-theme-pack.tar.gz -C /usr/share/icons/ --strip-components=1 .icons 2>/dev/null || true
    fi
    if [ -d /config/wallpapers ]; then
        mkdir -p /usr/share/backgrounds
        cp -af /config/wallpapers/* /usr/share/backgrounds/ 2>/dev/null || true
    fi
fi

# 3. Ícones da loja e caches de temas
mkdir -p /usr/share/icons/hicolor/64x64/apps /usr/share/icons/hicolor/48x48/apps 2>/dev/null || true
if [ -f /config-template/store-64.png ]; then
    cp -f /config-template/store-64.png /usr/share/icons/hicolor/64x64/apps/win-store.png 2>/dev/null || true
    cp -f /config-template/store-48.png /usr/share/icons/hicolor/48x48/apps/win-store.png 2>/dev/null || true
    [ -d /config/.icons/Eleven/48/apps ] && cp -f /config-template/store-48.png /config/.icons/Eleven/48/apps/win-store.png 2>/dev/null || true
    [ -d /config/.icons/Eleven/64/apps ] && cp -f /config-template/store-64.png /config/.icons/Eleven/64/apps/win-store.png 2>/dev/null || true
fi

gtk-update-icon-cache -f -t /config/.icons/Eleven-Dark 2>/dev/null || true
gtk-update-icon-cache -f -t /config/.icons/Eleven 2>/dev/null || true
gtk-update-icon-cache -f -t /usr/share/icons/Eleven-Dark 2>/dev/null || true
gtk-update-icon-cache -f -t /usr/share/icons/Eleven 2>/dev/null || true
gtk-update-icon-cache -f -t /usr/share/icons/hicolor 2>/dev/null || true

# 4. Copia arquivos de modelo para /config
if [ -d /config-template ]; then
    echo "[first-boot] Sincronizando arquivos de configuração e atalhos..."
    cp -a /config-template/. /config/ 2>/dev/null || true
    rm -f /config/win11-theme-pack.tar.gz 2>/dev/null || true

    mkdir -p /config/.config/xfce4/xfconf/xfce-perchannel-xml
    cp -af /config-template/.config/xfce4/xfconf/xfce-perchannel-xml/* /config/.config/xfce4/xfconf/xfce-perchannel-xml/ 2>/dev/null || true
fi

# 5. Forçar /defaults a usar os padrões Windows 11 (evita fallback do LinuxServer)
mkdir -p /defaults/xfce 2>/dev/null || true
if [ -d /config-template/.config/xfce4/xfconf/xfce-perchannel-xml ]; then
    cp -af /config-template/.config/xfce4/xfconf/xfce-perchannel-xml/* /defaults/xfce/ 2>/dev/null || true
fi
if [ -f /config/nginx-default.conf ]; then
    cp -f /config/nginx-default.conf /defaults/default.conf 2>/dev/null || true
fi

# 6. Autostart global de inicialização da sessão do Windows 11
mkdir -p /etc/xdg/autostart 2>/dev/null || true
if [ -f /config-template/.config/autostart/win11-session-init.desktop ]; then
    cp -f /config-template/.config/autostart/win11-session-init.desktop /etc/xdg/autostart/ 2>/dev/null || true
fi
if [ -f /config-template/win11-session-init.sh ]; then
    cp -f /config-template/win11-session-init.sh /usr/local/bin/win11-session-init
    chmod +x /usr/local/bin/win11-session-init
fi

# 7. Garantir diretório /DATA (Disco D:) e permissões
mkdir -p /DATA 2>/dev/null || true
chown -R abc:abc /DATA 2>/dev/null || true
chmod 775 /DATA 2>/dev/null || true
if [ ! -f /DATA/LEIA-ME.txt ] && [ -f /config-template/Desktop/LEIA-ME.txt ]; then
    cp -f /config-template/Desktop/LEIA-ME.txt /DATA/LEIA-ME.txt 2>/dev/null || true
    chown abc:abc /DATA/LEIA-ME.txt 2>/dev/null || true
fi

# 8. Garantir GVFS metadata e confiar em todos os atalhos do Desktop
mkdir -p /config/.local/share/gvfs-metadata /config/.local/share/applications /usr/share/applications 2>/dev/null || true
[ -f /config/.local/share/gvfs-metadata/home ] || touch /config/.local/share/gvfs-metadata/home 2>/dev/null || true

# Limpa atalhos antigos com nomes problemáticos
rm -f "/config/Desktop/Disco Local (D:).desktop" "/config/Desktop/Disco%20Local%(D:).desktop" 2>/dev/null || true

# Executa atribuição de confiança via D-Bus session para garantir que o GVfs registre o checksum SHA-256
dbus-run-session bash -c '
for f in /config/Desktop/*.desktop; do
    [ -f "$f" ] || continue
    chmod +x "$f"
    checksum=$(sha256sum "$f" | awk "{print \$1}")
    gio set -t string "$f" metadata::xfce-exe-checksum "$checksum" 2>/dev/null || true
    gio set -t string "$f" metadata::trusted true 2>/dev/null || true
    fname=$(basename "$f")
    cp -f "$f" "/usr/share/applications/$fname" 2>/dev/null || true
    cp -f "$f" "/config/.local/share/applications/$fname" 2>/dev/null || true
done
' 2>/dev/null || true

# 9. Garantir permissões do .htpasswd e autenticação para o usuário abc
mkdir -p /etc/nginx 2>/dev/null || true
touch /etc/nginx/.htpasswd 2>/dev/null || true
chown abc:abc /etc/nginx/.htpasswd 2>/dev/null || true
chmod 664 /etc/nginx/.htpasswd 2>/dev/null || true

# Limpa duplicação do ícone do Google Chrome no docklike
if [ -f /config/.config/xfce4/panel/docklike-2.rc ]; then
    sed -i 's/com\.google\.Chrome;//g' /config/.config/xfce4/panel/docklike-2.rc 2>/dev/null || true
fi

# 10. Ajustar permissões gerais
chown abc:abc /config 2>/dev/null || true
chown -R abc:abc /config/.themes /config/.icons /config/.config /config/.local /config/Desktop /config/wallpapers /config/login_assets 2>/dev/null || true
chmod +x /config/*.sh /config/*.py /config/webtop-lock 2>/dev/null || true
chmod +x /config/Desktop/*.desktop 2>/dev/null || true
chmod 644 /config/Desktop/*.txt 2>/dev/null || true
chmod 600 /config/.auth_secret 2>/dev/null || true

# 10b. Configura assistente de idioma e utilitários
for py_util in language_wizard.py win_language.py; do
    if [ -f "/config-template/$py_util" ]; then
        cp -f "/config-template/$py_util" "/config/$py_util"
        chmod +x "/config/$py_util"
    fi
done
mkdir -p /config/.config/autostart 2>/dev/null || true
if [ -f /config-template/.config/autostart/language-wizard.desktop ]; then
    cp -f /config-template/.config/autostart/language-wizard.desktop \
          /config/.config/autostart/language-wizard.desktop
fi

# Aplica idioma salvo em /etc/environment e s6 container_environment
LANG_PREF_FILE="/config/.language_preference"
if [ -f "$LANG_PREF_FILE" ]; then
    PREF_CODE=$(cat "$LANG_PREF_FILE" | tr -d '[:space:]')
    if [ -n "$PREF_CODE" ]; then
        LOCALE_STR="${PREF_CODE}.UTF-8"
        LANG_SHORT="${PREF_CODE%%_*}"
        printf 'LANG=%s\nLANGUAGE=%s:%s\nLC_ALL=%s\n' \
            "$LOCALE_STR" "$PREF_CODE" "$LANG_SHORT" "$LOCALE_STR" \
            > /etc/environment 2>/dev/null || true
        for s6_dir in /var/run/s6/container_environment /run/s6/container_environment; do
            if [ -d "$s6_dir" ]; then
                echo -n "$LOCALE_STR" > "$s6_dir/LANG" 2>/dev/null || true
                echo -n "$LOCALE_STR" > "$s6_dir/LC_ALL" 2>/dev/null || true
                echo -n "$PREF_CODE:$LANG_SHORT" > "$s6_dir/LANGUAGE" 2>/dev/null || true
            fi
        done
        echo "[first-boot] Idioma aplicado no ambiente: $PREF_CODE"
    fi
fi

# Injeta interceptor de locale no /defaults/startwm.sh para carregar o idioma antes de abrir a sessão XFCE
if [ -f /defaults/startwm.sh ] && ! grep -q "LANGUAGE_INTERCEPTOR" /defaults/startwm.sh; then
    sed -i '2i # LANGUAGE_INTERCEPTOR\nif [ -f /config/.language_preference ]; then\n  _P=$(cat /config/.language_preference | tr -d "[:space:]")\n  if [ -n "$_P" ]; then\n    export LANG="${_P}.UTF-8"\n    export LC_ALL="${_P}.UTF-8"\n    export LANGUAGE="${_P}:${_P%%_*}"\n  fi\nfi\n' /defaults/startwm.sh 2>/dev/null || true
fi

# 11. SSL automático via sslip.io + Let's Encrypt (Opção Zero-Touch)
# Só executa se /config/ssl/cert.pem ainda não existir (ou estiver vazio).
# Se o usuário rodou setup.sh no host, os certs já estarão presentes e este bloco é pulado.
if [ ! -s /config/ssl/cert.pem ]; then
    echo "[first-boot] Certificado SSL não encontrado – iniciando emissão automática via Let's Encrypt..."
    export DEBIAN_FRONTEND=noninteractive
    if ! command -v certbot >/dev/null 2>&1; then
        apt-get update -qq
        apt-get install -y -qq --no-install-recommends certbot
    fi

    VPS_IP=$(curl -fsSL https://api.ipify.org 2>/dev/null \
          || curl -fsSL https://ifconfig.me 2>/dev/null \
          || curl -fsSL https://icanhazip.com 2>/dev/null \
          || true)

    if [ -n "$VPS_IP" ]; then
        DOMAIN="${VPS_IP}.sslip.io"
        echo "[first-boot] IP detectado: $VPS_IP  →  Domínio: $DOMAIN"

        CERT_LIVE="/etc/letsencrypt/live/${DOMAIN}"
        if [ ! -d "$CERT_LIVE" ]; then
            # Para o nginx momentaneamente para liberar a porta 80
            nginx -s stop 2>/dev/null || true
            sleep 1

            certbot certonly \
                --standalone \
                -d "$DOMAIN" \
                --non-interactive \
                --agree-tos \
                --register-unsafely-without-email 2>&1 | tee -a /config/ssl-setup.log || true

            # Reinicia o nginx (o supervisor vai fazê-lo de qualquer jeito)
            nginx 2>/dev/null || true
        fi

        if [ -d "$CERT_LIVE" ]; then
            mkdir -p /config/ssl
            cp -f "$CERT_LIVE/fullchain.pem" /config/ssl/cert.pem
            cp -f "$CERT_LIVE/privkey.pem"   /config/ssl/cert.key
            chmod 644 /config/ssl/cert.pem
            chmod 600 /config/ssl/cert.key
            echo "[first-boot] ✅ Certificado SSL aplicado para https://${DOMAIN}"
            echo "DOMAIN=${DOMAIN}" > /config/ssl/.domain
        else
            echo "[first-boot] ⚠️  Certbot não emitiu o certificado. Verifique /config/ssl-setup.log"
        fi
    else
        echo "[first-boot] ⚠️  Não foi possível detectar o IP público – SSL não configurado automaticamente."
    fi
fi

echo "[first-boot] Personalização do Windows 11 aplicada com sucesso!"
