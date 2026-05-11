#!/bin/bash
# Configure the systemd deployment for authenticated LAN access.
#
# Usage:
#   sudo ./scripts/services/configure-lan-access.sh 192.168.1.201
#
# This is convenient for trusted LAN testing. Browsers should only use the
# frontend origin; /api is proxied to the local backend by frontend-server.mjs.
# For multi-user production, use configure-production-proxy.sh behind HTTPS.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
ENV_DIR="/etc/medical-deid"
ENV_FILE="$ENV_DIR/medical-deid.env"
LAN_HOST="${1:-}"
HOSTNAME_SHORT="$(hostname -s 2>/dev/null || true)"
HOSTNAME_FQDN="$(hostname -f 2>/dev/null || true)"
NVM_NODE_PATH="/home/eric/.nvm/versions/node/v20.19.6/bin"
APP_USER="${SUDO_USER:-eric}"
APP_GROUP="$(id -gn "$APP_USER")"

render_service_file() {
    local template="$1"
    local target="$2"
    python3 - "$template" "$target" "$PROJECT_ROOT" "$APP_USER" "$APP_GROUP" <<'PY'
from pathlib import Path
import sys

template, target, project_root, app_user, app_group = sys.argv[1:]
text = Path(template).read_text()
text = text.replace("__PROJECT_ROOT__", project_root)
text = text.replace("__APP_USER__", app_user)
text = text.replace("__APP_GROUP__", app_group)
Path(target).write_text(text)
PY
}

if [ "$EUID" -ne 0 ]; then
    echo "請以 sudo 執行：sudo $0 192.168.1.201"
    exit 1
fi

if [ -z "$LAN_HOST" ]; then
    LAN_HOST="$(hostname -I | tr ' ' '\n' | grep -E '^(192\.168\.|172\.(1[6-9]|2[0-9]|3[0-1])\.|10\.)' | head -n 1 || true)"
fi

if [ -z "$LAN_HOST" ]; then
    echo "找不到 LAN IP，請明確指定，例如：sudo $0 192.168.1.201"
    exit 1
fi

cors_origins="http://localhost:5173,http://127.0.0.1:5173,http://$LAN_HOST:5173"
for host in "$HOSTNAME_SHORT" "$HOSTNAME_FQDN"; do
    if [ -n "$host" ] && [ "$host" != "$LAN_HOST" ]; then
        case ",$cors_origins," in
            *",http://$host:5173,"*) ;;
            *) cors_origins="$cors_origins,http://$host:5173" ;;
        esac
    fi
done

install -d -m 750 -o root -g root "$ENV_DIR"
cat > "$ENV_FILE" <<EOF
# Medical De-identification LAN anonymous-session runtime settings
# WARNING: Trusted LAN mode. Use HTTPS reverse proxy for production.
MEDICAL_DEID_API_TOKEN=
MEDICAL_DEID_PSEUDONYM_SECRET=
VITE_API_TOKEN=
VITE_API_BASE_URL=/api
MEDICAL_DEID_AUTH_MODE=anonymous_session
MEDICAL_DEID_ALLOW_NO_AUTH=0
MEDICAL_DEID_LOG_LEVEL=INFO
# Internal QA mode keeps detected PHI values in result artifacts so the
# uploader can verify true/false positives. Raw upload files are still purged.
MEDICAL_DEID_STORE_RAW_PHI=1
MEDICAL_DEID_ALLOW_PHI_REVEAL=1
MEDICAL_DEID_SESSION_COOKIE_SECURE=0
MEDICAL_DEID_SESSION_COOKIE_SAMESITE=lax
MEDICAL_DEID_ENABLE_PUBLIC_BOOTSTRAP=0
MEDICAL_DEID_DELETE_UPLOAD_AFTER_PROCESS=1
MEDICAL_DEID_UPLOAD_TTL_HOURS=2
MEDICAL_DEID_RESULT_TTL_HOURS=24
MEDICAL_DEID_PROCESSING_WORKERS=1
MEDICAL_DEID_MIN_PASSWORD_LENGTH=8
MEDICAL_DEID_DATA_DIR=/var/lib/medical-deid
MEDICAL_DEID_LOG_DIR=/var/log/medical-deid
MEDICAL_DEID_BACKEND_HOST=127.0.0.1
MEDICAL_DEID_FRONTEND_PORT=5173
MEDICAL_DEID_NODE_BIN=$NVM_NODE_PATH
MEDICAL_DEID_CORS_ORIGINS=$cors_origins
MEDICAL_DEID_ALLOWED_LLM_HOSTS=localhost,127.0.0.1,192.168.1.2
OLLAMA_BASE_URL=http://192.168.1.2:30133
OLLAMA_MODEL=gemma3:27b
EOF
chown root:root "$ENV_FILE"
chmod 600 "$ENV_FILE"

install -d -m 700 -o "$APP_USER" -g "$APP_GROUP" /var/lib/medical-deid /var/log/medical-deid
install -d -m 700 -o "$APP_USER" -g "$APP_GROUP" /var/lib/medical-deid/llm_configs
cat > /var/lib/medical-deid/llm_configs/config.json <<EOF
{
  "provider": "ollama",
  "base_url": "http://192.168.1.2:30133",
  "model": "gemma3:27b",
  "api_key": null,
  "temperature": 0.1,
  "max_tokens": 4096,
  "timeout": 120
}
EOF
chown "$APP_USER:$APP_GROUP" /var/lib/medical-deid/llm_configs/config.json
chmod 600 /var/lib/medical-deid/llm_configs/config.json

sudo -u "$APP_USER" bash -c "cd '$PROJECT_ROOT' && uv venv .venv && uv sync --frozen --no-dev && uv pip install --python .venv/bin/python -e web/backend && test -x .venv/bin/uvicorn"

render_service_file "$SCRIPT_DIR/medical-deid-backend.service" /etc/systemd/system/medical-deid-backend.service
render_service_file "$SCRIPT_DIR/medical-deid-frontend.service" /etc/systemd/system/medical-deid-frontend.service

sudo -u "$APP_USER" bash -c "export PATH='$NVM_NODE_PATH':\$PATH; export VITE_API_BASE_URL=/api; cd '$PROJECT_ROOT/web/frontend' && npm ci && npm run build"

systemctl daemon-reload
systemctl enable medical-deid-backend.service
systemctl enable medical-deid-frontend.service
systemctl restart medical-deid-backend.service
systemctl restart medical-deid-frontend.service

echo "LAN mode configured for http://$LAN_HOST:5173"
echo "Browser API should be reachable at http://$LAN_HOST:5173/api"
echo "Backend API is intentionally bound locally at http://127.0.0.1:8000/api"
echo "CORS origins allowed: $cors_origins"
echo "Auth mode: anonymous_session (per-browser data isolation, no username/password prompt)."
echo "PHI review mode: enabled for internal QA (detected raw PHI values kept until result TTL cleanup)."
