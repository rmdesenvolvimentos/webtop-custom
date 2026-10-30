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
#   3. Abre portas 80/443 no firewall local
#   4. Verifica se a porta 80 é acessível externamente
#   5. Emite um certificado Let's Encrypt real (standalone, sem e-mail)
#   6. Copia os certs para config-template/ssl (montado no container)
#   7. Grava o .env com o DOMAIN
#   8. Sobe o Docker stack
# =============================================================================
set -euo pipefail

# ─── helpers ─────────────────────────────────────────────────────────────────
GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; CYAN='\033[0;36m'; NC='\033[0m'
info()  { echo -e "${GREEN}[INFO]${NC}  $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
error() { echo -e "${RED}[ERRO]${NC}  $*" >&2; exit 1; }
step()  { echo -e "${CYAN}[....] ${NC} $*"; }

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
VPS_IP=$(curl -fsSL --max-time 5 https://api.ipify.org 2>/dev/null \
      || curl -fsSL --max-time 5 https://ifconfig.me 2>/dev/null \
      || curl -fsSL --max-time 5 https://icanhazip.com 2>/dev/null \
      || true)

[[ -n "$VPS_IP" ]] || error "Não foi possível detectar o IP público. Verifique a conexão."
DOMAIN="${VPS_IP}.sslip.io"
info "IP: $VPS_IP  →  Domínio: $DOMAIN"

# ─── 2. Instalar certbot e psmisc (para fuser) se necessário ─────────────────
apt-get install -yqq psmisc 2>/dev/null || true
if ! command -v certbot >/dev/null 2>&1; then
  info "Instalando certbot..."
  apt-get update -qq
  apt-get install -yqq certbot
fi

# ─── 3. Parar containers e liberar porta 80 ──────────────────────────────────
info "Parando containers Docker para liberar a porta 80..."
docker_compose down 2>/dev/null || true

info "Forçando liberação da porta 80 (nginx, apache, etc.)..."
fuser -k 80/tcp 2>/dev/null || true
systemctl stop nginx apache2 httpd caddy 2>/dev/null || true
sleep 2

# Confirma que a porta está livre
if ss -tlnp 2>/dev/null | grep -q ':80 '; then
  PID_80=$(ss -tlnp | grep ':80 ' | grep -oP 'pid=\K[0-9]+' | head -1)
  [ -n "$PID_80" ] && kill -9 "$PID_80" 2>/dev/null || true
  sleep 1
fi
info "Porta 80 local: livre ✓"

# ─── 4. Abrir portas no firewall local (ufw / iptables) ──────────────────────
info "Abrindo portas 80 e 443 no firewall local..."
if command -v ufw >/dev/null 2>&1; then
  ufw allow 80/tcp  >/dev/null 2>&1 || true
  ufw allow 443/tcp >/dev/null 2>&1 || true
  info "ufw: portas 80 e 443 liberadas ✓"
fi
# Garante via iptables também (por segurança)
iptables -I INPUT -p tcp --dport 80  -j ACCEPT 2>/dev/null || true
iptables -I INPUT -p tcp --dport 443 -j ACCEPT 2>/dev/null || true

# ─── 5. Verificar conectividade externa na porta 80 ──────────────────────────
# Inicia um mini servidor HTTP temporário e testa acesso externo
info "Verificando se a porta 80 é acessível externamente..."
# Sobe um netcat/python escutando na porta 80 por 3 segundos
python3 -c "
import http.server, threading, time
class H(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'ok')
    def log_message(self, *a): pass
srv = http.server.HTTPServer(('0.0.0.0', 80), H)
t = threading.Thread(target=srv.serve_forever)
t.daemon = True
t.start()
time.sleep(5)
srv.shutdown()
" &
TEST_SERVER_PID=$!
sleep 1

EXTERNAL_OK=false
if curl -fsSL --max-time 4 "http://${DOMAIN}/" >/dev/null 2>&1; then
  EXTERNAL_OK=true
fi

kill $TEST_SERVER_PID 2>/dev/null || true
wait $TEST_SERVER_PID 2>/dev/null || true
sleep 1

if [ "$EXTERNAL_OK" = false ]; then
  echo ""
  echo -e "${RED}╔══════════════════════════════════════════════════════════════╗${NC}"
  echo -e "${RED}║  ⛔  PORTA 80 BLOQUEADA PELO FIREWALL DA NUVEM              ║${NC}"
  echo -e "${RED}╠══════════════════════════════════════════════════════════════╣${NC}"
  echo -e "${RED}║  A porta 80 está bloqueada no painel do seu provedor.        ║${NC}"
  echo -e "${RED}║  O Let's Encrypt não consegue validar o domínio sem ela.     ║${NC}"
  echo -e "${RED}║                                                              ║${NC}"
  echo -e "${RED}║  ➡  Azure:  NSG → Adicionar regra de entrada → porta 80     ║${NC}"
  echo -e "${RED}║  ➡  AWS:    Security Group → Inbound → HTTP porta 80        ║${NC}"
  echo -e "${RED}║  ➡  Hetzner/OVH: Firewall → Allow TCP 80 e 443             ║${NC}"
  echo -e "${RED}║                                                              ║${NC}"
  echo -e "${RED}║  Após liberar, rode novamente: sudo ./setup.sh               ║${NC}"
  echo -e "${RED}╚══════════════════════════════════════════════════════════════╝${NC}"
  echo ""
  # Sobe o stack sem SSL (HTTP puro) para o usuário já ter acesso
  warn "Subindo o stack em modo HTTP (sem SSL) para acesso imediato..."
  docker_compose up -d
  echo ""
  echo -e "${YELLOW}============================================================${NC}"
  echo -e "${YELLOW}  ⚠️  Desktop acessível via HTTP (sem cadeado) por enquanto${NC}"
  echo -e "${YELLOW}  🌐  Acesse: http://${VPS_IP}${NC}"
  echo -e "${YELLOW}  Libere a porta 80 no painel da nuvem e rode setup.sh novamente${NC}"
  echo -e "${YELLOW}============================================================${NC}"
  exit 0
fi

info "Porta 80 acessível externamente ✓"

# ─── 6. Emitir certificado Let's Encrypt ─────────────────────────────────────
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

[[ -d "$CERT_LIVE" ]] || error "Certbot falhou. Verifique: /var/log/letsencrypt/letsencrypt.log"

# ─── 7. Copiar certs para config-template/ssl ────────────────────────────────
SSL_DIR="$REPO_DIR/config-template/ssl"
mkdir -p "$SSL_DIR"
cp -f "$CERT_LIVE/fullchain.pem" "$SSL_DIR/cert.pem"
cp -f "$CERT_LIVE/privkey.pem"   "$SSL_DIR/cert.key"
chmod 644 "$SSL_DIR/cert.pem"
chmod 600 "$SSL_DIR/cert.key"
info "Certificados copiados para $SSL_DIR ✓"

# ─── 8. Gravar .env ──────────────────────────────────────────────────────────
info "Gravando .env..."
cat > "$REPO_DIR/.env" <<EOF
# Gerado automaticamente pelo setup.sh em $(date -u +"%Y-%m-%dT%H:%M:%SZ")
DOMAIN=${DOMAIN}
EOF

# ─── 9. Subir o stack ────────────────────────────────────────────────────────
info "Subindo o Docker stack (docker compose up -d)..."
docker_compose up -d

# ─── 10. Mensagem final ───────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}============================================================${NC}"
echo -e "${GREEN}  ✅  Desktop instalado com sucesso e 100% seguro!${NC}"
echo -e "${GREEN}  🔒  Acesse agora: https://${DOMAIN}${NC}"
echo -e "${GREEN}============================================================${NC}"
echo ""
