#!/usr/bin/env bash
# =============================================================================
# setup.sh – instalador automático do webtop-custom com SSL
# =============================================================================
# Uso:
#   git clone https://github.com/rmdesenvolvimentos/webtop-custom.git
#   cd webtop-custom
#   chmod +x setup.sh && sudo ./setup.sh
# =============================================================================
set -euo pipefail

# ─── Cores ───────────────────────────────────────────────────────────────────
GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'

# ─── Multilanguage: detecta idioma do sistema (fallback: inglês) ──────────────
_SYS_LANG="${LANG:-${LC_ALL:-en}}"
case "$_SYS_LANG" in
  pt*) LANG_CODE="pt" ;;
  es*) LANG_CODE="es" ;;
  *)   LANG_CODE="en" ;;
esac

_t() {
  # _t <pt> <en> [es]
  case "$LANG_CODE" in
    pt) echo "$1" ;;
    es) echo "${3:-$2}" ;;
    *)  echo "$2" ;;
  esac
}

info()  { echo -e "${GREEN}[INFO]${NC}  $(_t "$1" "${2:-$1}" "${3:-}")"; }
warn()  { echo -e "${YELLOW}[AVISO]${NC} $(_t "$1" "${2:-$1}" "${3:-}")"; }
error() { echo -e "${RED}[ERRO]${NC}  $(_t "$1" "${2:-$1}" "${3:-}")" >&2; exit 1; }

# ─── Docker compose helper ───────────────────────────────────────────────────
docker_compose() {
  if docker compose version >/dev/null 2>&1; then
    docker compose "$@"
  elif command -v docker-compose >/dev/null 2>&1; then
    docker-compose "$@"
  else
    error "docker compose não encontrado. Instale o Docker antes de continuar." \
          "docker compose not found. Please install Docker first."
  fi
}

# ─── 0. Verificação de root ───────────────────────────────────────────────────
[[ "$EUID" -eq 0 ]] || error \
  "Execute com: sudo ./setup.sh" \
  "Run as root: sudo ./setup.sh"

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$REPO_DIR"

echo ""
echo -e "${GREEN}========================================================${NC}"
echo -e "${GREEN}  🚀  Webtop Custom – Setup automático com SSL          ${NC}"
echo -e "${GREEN}========================================================${NC}"
echo ""

# ─── 1. Detectar IP público ───────────────────────────────────────────────────
info "Detectando IP público da VPS..." "Detecting public IP of the VPS..."
VPS_IP=$(  curl -fsSL --max-time 5 https://api.ipify.org 2>/dev/null \
        || curl -fsSL --max-time 5 https://ifconfig.me  2>/dev/null \
        || curl -fsSL --max-time 5 https://icanhazip.com 2>/dev/null \
        || true)
[[ -n "$VPS_IP" ]] || error \
  "Não foi possível detectar o IP público. Verifique a conexão." \
  "Could not detect the public IP. Check your internet connection."

DOMAIN="${VPS_IP}.sslip.io"
info "IP detectado: $VPS_IP  →  Domínio: $DOMAIN" \
     "Detected IP: $VPS_IP  →  Domain: $DOMAIN"

# ─── 2. Instalar dependências ─────────────────────────────────────────────────
if ! command -v certbot >/dev/null 2>&1; then
  info "Instalando certbot..." "Installing certbot..."
  apt-get update -qq
  apt-get install -yqq certbot
fi
apt-get install -yqq psmisc 2>/dev/null || true   # para fuser

# ─── 3. Parar containers e liberar porta 80 (certbot standalone precisa dela) ─
info "Parando containers e liberando porta 80..." \
     "Stopping containers and freeing port 80..."

docker_compose down --remove-orphans 2>/dev/null || true
fuser -k 80/tcp 2>/dev/null || true
systemctl stop nginx apache2 httpd caddy 2>/dev/null || true
sleep 2

# Força kill de qualquer remanescente
if ss -tlnp 2>/dev/null | grep -q ':80 '; then
  PID_80=$(ss -tlnp | grep ':80 ' | grep -oP 'pid=\K[0-9]+' | head -1 || true)
  [[ -n "$PID_80" ]] && kill -9 "$PID_80" 2>/dev/null || true
  sleep 1
fi
info "Porta 80 local liberada ✓" "Port 80 is free ✓"

# ─── 4. Abrir portas no firewall local ───────────────────────────────────────
if command -v ufw >/dev/null 2>&1; then
  ufw allow 80/tcp  >/dev/null 2>&1 || true
  ufw allow 443/tcp >/dev/null 2>&1 || true
fi
iptables -I INPUT -p tcp --dport 80  -j ACCEPT 2>/dev/null || true
iptables -I INPUT -p tcp --dport 443 -j ACCEPT 2>/dev/null || true

# ─── 5. Verificar conectividade externa (sem background process) ──────────────
info "Verificando se a porta 80 é acessível externamente..." \
     "Checking if port 80 is reachable from the internet..."

# Sobe servidor de teste síncrono por 6 segundos em subshell foreground
# (o timeout garante que não fica preso)
EXTERNAL_OK=false
( python3 - "$DOMAIN" <<'PYEOF'
import sys, http.server, threading, time, socket
domain = sys.argv[1]
class H(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'ok')
    def log_message(self, *a): pass
try:
    srv = http.server.HTTPServer(('0.0.0.0', 80), H)
    t = threading.Thread(target=srv.serve_forever)
    t.daemon = True
    t.start()
    time.sleep(6)
    srv.shutdown()
except OSError as e:
    sys.exit(1)
PYEOF
) &
PY_PID=$!
sleep 2   # aguarda servidor subir

if curl -fsSL --max-time 4 "http://${DOMAIN}/" >/dev/null 2>&1; then
  EXTERNAL_OK=true
fi

# Para o servidor de teste antes de qualquer outra saída
kill "$PY_PID" 2>/dev/null || true
wait "$PY_PID" 2>/dev/null || true
sleep 1

# ─── 6. Emitir certificado Let's Encrypt ─────────────────────────────────────
CERT_LIVE="/etc/letsencrypt/live/${DOMAIN}"

if [ "$EXTERNAL_OK" = false ]; then
  echo ""
  echo -e "${RED}╔══════════════════════════════════════════════════════════════╗${NC}"
  echo -e "${RED}║  ⛔  PORTA 80 BLOQUEADA PELO FIREWALL DA NUVEM              ║${NC}"
  echo -e "${RED}╠══════════════════════════════════════════════════════════════╣${NC}"
  echo -e "${RED}║  ➡  Azure:  NSG → Regras de entrada → porta 80 TCP         ║${NC}"
  echo -e "${RED}║  ➡  AWS:    Security Group → Inbound → HTTP porta 80       ║${NC}"
  echo -e "${RED}║  ➡  Hetzner/OVH: Firewall → Allow TCP 80 e 443            ║${NC}"
  echo -e "${RED}║                                                              ║${NC}"
  echo -e "${RED}║  Após liberar, rode novamente: sudo ./setup.sh               ║${NC}"
  echo -e "${RED}╚══════════════════════════════════════════════════════════════╝${NC}"
  echo ""
  warn "Subindo o stack em modo HTTP (sem SSL) para acesso imediato..." \
       "Starting stack in HTTP mode (no SSL) for immediate access..."
  docker_compose up -d
  echo ""
  echo -e "${YELLOW}============================================================${NC}"
  echo -e "${YELLOW}  ⚠️  Desktop disponível via HTTP (sem cadeado)${NC}"
  echo -e "${YELLOW}  🌐  Acesse: http://${VPS_IP}${NC}"
  echo -e "${YELLOW}  Libere a porta 80 na nuvem e rode: sudo ./setup.sh${NC}"
  echo -e "${YELLOW}============================================================${NC}"
  exit 0
fi

info "Porta 80 acessível externamente ✓" "Port 80 is reachable externally ✓"

if [[ -d "$CERT_LIVE" ]]; then
  warn "Certificado já existe em $CERT_LIVE – reutilizando." \
       "Certificate already exists at $CERT_LIVE – reusing."
else
  info "Emitindo certificado Let's Encrypt para $DOMAIN ..." \
       "Issuing Let's Encrypt certificate for $DOMAIN ..."
  certbot certonly \
    --standalone \
    -d "$DOMAIN" \
    --non-interactive \
    --agree-tos \
    --register-unsafely-without-email
fi

[[ -d "$CERT_LIVE" ]] || error \
  "Certbot falhou. Verifique: /var/log/letsencrypt/letsencrypt.log" \
  "Certbot failed. Check: /var/log/letsencrypt/letsencrypt.log"

# ─── 7. Copiar certificados para config-template/ssl ─────────────────────────
SSL_DIR="$REPO_DIR/config-template/ssl"
mkdir -p "$SSL_DIR"
cp -f "$CERT_LIVE/fullchain.pem" "$SSL_DIR/cert.pem"
cp -f "$CERT_LIVE/privkey.pem"   "$SSL_DIR/cert.key"
chmod 644 "$SSL_DIR/cert.pem"
chmod 600 "$SSL_DIR/cert.key"
info "Certificados copiados para $SSL_DIR ✓" "Certificates copied to $SSL_DIR ✓"

# ─── 8. Configurar .env (preserva variáveis existentes) ──────────────────────
if [ ! -f "$REPO_DIR/.env" ]; then
  cp "$REPO_DIR/.env.example" "$REPO_DIR/.env"
  info ".env criado a partir de .env.example" ".env created from .env.example"
fi
if grep -q "^DOMAIN=" "$REPO_DIR/.env"; then
  sed -i "s|^DOMAIN=.*|DOMAIN=${DOMAIN}|" "$REPO_DIR/.env"
else
  echo "DOMAIN=${DOMAIN}" >> "$REPO_DIR/.env"
fi
info "DOMAIN=${DOMAIN} gravado em .env ✓" "DOMAIN=${DOMAIN} saved to .env ✓"

# ─── 9. Subir o Docker stack ─────────────────────────────────────────────────
# Pré-criar pastas de dados com permissão para o usuário interno (UID/GID 1000)
info "Preparando diretórios de dados e permissões..." "Preparing data directories and permissions..."
mkdir -p "$REPO_DIR/data/config" "$REPO_DIR/data/storage"
chown -R 1000:1000 "$REPO_DIR/data" 2>/dev/null || true

info "Subindo o Docker stack..." "Starting Docker stack..."
docker_compose up -d

# ─── 10. Health-check: aguarda o sistema estar 100% pronto ───────────────────
info "Aguardando o sistema concluir a instalação (pode levar 2-5 min na 1ª vez)..." \
     "Waiting for the system to finish setup (may take 2-5 min first time)..."

# Remove qualquer flag antiga de execuções prévias
rm -f "$REPO_DIR/data/config/.ready_flag" 2>/dev/null || true

MAX_WAIT=480   # 8 minutos para download de pacotes e setup
ELAPSED=0
INTERVAL=3
READY=false

while [ $ELAPSED -lt $MAX_WAIT ]; do
  # Progresso visual dinâmico com porcentagem e tempo decorrido
  PERCENT=$(( (ELAPSED * 100) / MAX_WAIT ))
  BAR_LEN=$(( PERCENT / 4 ))
  EMPTY_LEN=$(( 25 - BAR_LEN ))
  BAR=$(printf "%${BAR_LEN}s" "" | tr ' ' '█')
  EMPTY=$(printf "%${EMPTY_LEN}s" "" | tr ' ' '-')
  printf "\r    [${CYAN}%s%s${NC}] %3d%% (%ds/%ds)" "$BAR" "$EMPTY" "$PERCENT" "$ELAPSED" "$MAX_WAIT"

  # Verifica se o último script do container concluiu com sucesso
  if [ -f "$REPO_DIR/data/config/.ready_flag" ]; then
    READY=true
    break
  fi

  sleep $INTERVAL
  ELAPSED=$((ELAPSED + INTERVAL))
done

if [ "$READY" = true ]; then
  printf "\r    [${CYAN}%s${NC}] 100%% (%ds) - Sistema 100%% pronto!            \n" "$(printf '%25s' '' | tr ' ' '█')" "$ELAPSED"
else
  printf "\n"
  warn "Tempo limite atingido (%ds). O contêiner ainda pode estar concluindo as tarefas." "$MAX_WAIT" \
       "Timeout reached (%ds). The container might still be finishing tasks." "$MAX_WAIT"
fi

if [ "$READY" = false ]; then
  warn "Timeout aguardando resposta (${MAX_WAIT}s). Sistema pode ainda estar instalando." \
       "Timeout waiting for response (${MAX_WAIT}s). System may still be installing."
  warn "Tente em alguns minutos: https://${DOMAIN}" \
       "Try in a few minutes: https://${DOMAIN}"
fi

# ─── 10. Mensagem final (SEMPRE por último) ───────────────────────────────────
echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  ✅  Desktop instalado com sucesso e 100% seguro!            ║${NC}"
echo -e "${GREEN}║  🔒  Acesse agora: https://${DOMAIN}${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""
