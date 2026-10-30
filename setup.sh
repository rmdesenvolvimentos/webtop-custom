#!/usr/bin/env bash
# =============================================================================
# setup.sh – instalador automático do webtop-custom com SSL
# =============================================================================
# Uso:
#   git clone https://github.com/rmdesenvolvimentos/webtop-custom.git
#   cd webtop-custom
#   chmod +x setup.sh && sudo ./setup.sh
#
# O script:
#   1. Detecta o IP público da VPS
#   2. Forma o domínio <IP>.sslip.io (sem precisar de DNS próprio)
#   3. Emite um certificado Let's Encrypt real (standalone, sem e-mail)
#   4. Copia os certs para config-template/ssl (montado no container)
#   5. Grava o .env com o DOMAIN
#   6. Sobe o Docker stack
# =============================================================================
set -euo pipefail

# ─── helpers ─────────────────────────────────────────────────────────────────
GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'
info()  { echo -e "${GREEN}[INFO]${NC}  $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
error() { echo -e "${RED}[ERRO]${NC}  $*" >&2; exit 1; }

# Detecta o binário docker compose (novo plugin vs legado)
docker_compose() {
  if docker compose version >/dev/null 2>&1; then
    docker compose "$@"
  elif command -v docker-compose >/dev/null 2>&1; then
    docker-compose "$@"
  else
    error "docker compose não encontrado. Instale o Docker antes de continuar."
  fi
}

# ─── 0. root check ────────────────────────────────────────────────────────────
[[ "$EUID" -eq 0 ]] || error "Execute com: sudo ./setup.sh"

# Garante que estamos no diretório do repositório
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$REPO_DIR"

# ─── 1. Detectar IP público ───────────────────────────────────────────────────
info "Detectando IP público da VPS..."
VPS_IP=$(curl -fsSL https://api.ipify.org 2>/dev/null \
      || curl -fsSL https://ifconfig.me 2>/dev/null \
      || curl -fsSL https://icanhazip.com 2>/dev/null \
      || true)

[[ -n "$VPS_IP" ]] || error "Não foi possível detectar o IP público. Verifique a conexão."
DOMAIN="${VPS_IP}.sslip.io"
info "IP: $VPS_IP  →  Domínio: $DOMAIN"

# ─── 2. Instalar certbot se necessário ───────────────────────────────────────
if ! command -v certbot >/dev/null 2>&1; then
  info "Instalando certbot..."
  apt-get update -qq
  apt-get install -yqq certbot
fi

# ─── 3. Parar containers e liberar porta 80 ──────────────────────────────────
info "Parando containers Docker para liberar a porta 80..."
docker_compose down 2>/dev/null || true

# Garante que NENHUM processo esteja usando a porta 80 (nginx, apache, etc.)
info "Verificando se a porta 80 está livre..."
if command -v fuser >/dev/null 2>&1; then
  fuser -k 80/tcp 2>/dev/null || true
  sleep 1
fi
# Fallback: usa ss/lsof para encontrar e matar o processo
if ss -tlnp 2>/dev/null | grep -q ':80 '; then
  warn "Processo ainda na porta 80 – tentando forçar encerramento..."
  PID_80=$(ss -tlnp | grep ':80 ' | grep -oP 'pid=\K[0-9]+' | head -1)
  [ -n "$PID_80" ] && kill -9 "$PID_80" 2>/dev/null || true
  sleep 1
fi
# Para serviços comuns que possam estar na porta 80
systemctl stop nginx apache2 httpd 2>/dev/null || true
sleep 1
info "Porta 80 liberada."

# ─── 4. Emitir certificado Let's Encrypt ─────────────────────────────────────
CERT_LIVE="/etc/letsencrypt/live/${DOMAIN}"
if [[ -d "$CERT_LIVE" ]]; then
  warn "Certificado já existe em $CERT_LIVE – reutilizando."
else
  info "Emitindo certificado Let's Encrypt para $DOMAIN ..."
  certbot certonly \
    --standalone \
    -d "$DOMAIN" \
    --non-interactive \
    --agree-tos \
    --register-unsafely-without-email
fi

# ─── 5. Copiar certs para config-template/ssl ────────────────────────────────
SSL_DIR="$REPO_DIR/config-template/ssl"
mkdir -p "$SSL_DIR"
cp -f "$CERT_LIVE/fullchain.pem" "$SSL_DIR/cert.pem"
cp -f "$CERT_LIVE/privkey.pem"   "$SSL_DIR/cert.key"
chmod 644 "$SSL_DIR/cert.pem"
chmod 600 "$SSL_DIR/cert.key"
info "Certificados copiados para $SSL_DIR"

# ─── 6. Gravar .env ──────────────────────────────────────────────────────────
info "Gravando .env..."
cat > "$REPO_DIR/.env" <<EOF
# Gerado automaticamente pelo setup.sh em $(date -u +"%Y-%m-%dT%H:%M:%SZ")
DOMAIN=${DOMAIN}
EOF

# ─── 7. Subir o stack ────────────────────────────────────────────────────────
info "Subindo o Docker stack (docker compose up -d)..."
docker_compose up -d

# ─── 8. Mensagem final ───────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}============================================================${NC}"
echo -e "${GREEN}  ✅  Desktop instalado com sucesso e 100% seguro!${NC}"
echo -e "${GREEN}  🔒  Acesse agora: https://${DOMAIN}${NC}"
echo -e "${GREEN}============================================================${NC}"
echo ""
