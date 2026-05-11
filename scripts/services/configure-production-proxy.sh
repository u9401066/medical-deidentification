#!/bin/bash
# Configure application services for HTTPS reverse-proxy production mode.
#
# Usage:
#   sudo ./scripts/services/configure-production-proxy.sh deid.example.org admin [ollama-base-url]
#
# The reverse proxy should forward all HTTP traffic to http://127.0.0.1:5173.
# The frontend service serves static assets and proxies /api to the local backend.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
ENV_DIR="/etc/medical-deid"
ENV_FILE="$ENV_DIR/medical-deid.env"
DOMAIN="${1:-}"
ADMIN_USER="${2:-}"
OLLAMA_BASE_URL_VALUE="${3:-${OLLAMA_BASE_URL:-http://192.168.1.2:30133}}"
ADMIN_PASSWORD="${MEDICAL_DEID_BOOTSTRAP_ADMIN_PASSWORD:-}"
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
    echo "請以 sudo 執行：sudo $0 deid.example.org admin [ollama-base-url]"
    exit 1
fi

if [ -z "$DOMAIN" ] || [ -z "$ADMIN_USER" ]; then
    echo "Usage: sudo $0 <domain> <bootstrap-admin-user> [ollama-base-url]"
    exit 1
fi

if ! [[ "$DOMAIN" =~ ^[A-Za-z0-9.-]+$ ]]; then
    echo "domain 僅能包含英數字、點與連字號"
    exit 1
fi

if [ -z "$ADMIN_PASSWORD" ]; then
    if [ -t 0 ]; then
        read -r -s -p "Bootstrap admin password: " ADMIN_PASSWORD
        echo
    else
        echo "請互動式執行，或用 MEDICAL_DEID_BOOTSTRAP_ADMIN_PASSWORD 提供一次性 bootstrap 密碼"
        exit 1
    fi
fi

if [[ "$ADMIN_USER" == *$'\n'* || "$ADMIN_PASSWORD" == *$'\n'* ]]; then
    echo "admin user/password 不可包含換行字元"
    exit 1
fi

OLLAMA_HOST="$(python3 -c 'from urllib.parse import urlparse; import sys; print(urlparse(sys.argv[1]).hostname or "")' "$OLLAMA_BASE_URL_VALUE")"
if [ -z "$OLLAMA_HOST" ]; then
    echo "Ollama URL 無效：$OLLAMA_BASE_URL_VALUE"
    exit 1
fi

env_quote() {
    python3 -c 'import shlex, sys; print(shlex.quote(sys.argv[1]))' "$1"
}

ADMIN_USER_ENV="$(env_quote "$ADMIN_USER")"
ADMIN_PASSWORD_ENV="$(env_quote "$ADMIN_PASSWORD")"
OLLAMA_BASE_URL_ENV="$(env_quote "$OLLAMA_BASE_URL_VALUE")"
PSEUDONYM_SECRET="$(python3 -c 'import secrets; print(secrets.token_urlsafe(48))')"

install -d -m 750 -o root -g root "$ENV_DIR"
cat > "$ENV_FILE" <<EOF
# Medical De-identification production settings
MEDICAL_DEID_API_TOKEN=
MEDICAL_DEID_PSEUDONYM_SECRET=$PSEUDONYM_SECRET
VITE_API_TOKEN=
VITE_API_BASE_URL=/api
MEDICAL_DEID_AUTH_MODE=password
MEDICAL_DEID_ALLOW_NO_AUTH=0
MEDICAL_DEID_ENABLE_PUBLIC_BOOTSTRAP=0
MEDICAL_DEID_LOG_LEVEL=INFO
MEDICAL_DEID_STORE_RAW_PHI=0
MEDICAL_DEID_SESSION_COOKIE_SECURE=1
MEDICAL_DEID_SESSION_COOKIE_SAMESITE=lax
MEDICAL_DEID_DELETE_UPLOAD_AFTER_PROCESS=1
MEDICAL_DEID_UPLOAD_TTL_HOURS=2
MEDICAL_DEID_RESULT_TTL_HOURS=24
MEDICAL_DEID_PROCESSING_WORKERS=1
MEDICAL_DEID_MIN_PASSWORD_LENGTH=8
MEDICAL_DEID_BOOTSTRAP_ADMIN_USER=$ADMIN_USER_ENV
MEDICAL_DEID_BOOTSTRAP_ADMIN_PASSWORD=$ADMIN_PASSWORD_ENV
MEDICAL_DEID_DATA_DIR=/var/lib/medical-deid
MEDICAL_DEID_LOG_DIR=/var/log/medical-deid
MEDICAL_DEID_BACKEND_HOST=127.0.0.1
MEDICAL_DEID_FRONTEND_PORT=5173
MEDICAL_DEID_NODE_BIN=$NVM_NODE_PATH
MEDICAL_DEID_CORS_ORIGINS=https://$DOMAIN
MEDICAL_DEID_ALLOWED_LLM_HOSTS=localhost,127.0.0.1,$OLLAMA_HOST
OLLAMA_BASE_URL=$OLLAMA_BASE_URL_ENV
OLLAMA_MODEL=gemma3:27b
EOF
chown root:root "$ENV_FILE"
chmod 600 "$ENV_FILE"

install -d -m 700 -o "$APP_USER" -g "$APP_GROUP" /var/lib/medical-deid /var/log/medical-deid
install -d -m 700 -o "$APP_USER" -g "$APP_GROUP" /var/lib/medical-deid/llm_configs
python3 - "$OLLAMA_BASE_URL_VALUE" "${OLLAMA_MODEL:-gemma3:27b}" <<'PY'
from pathlib import Path
import json
import sys

config = {
    "provider": "ollama",
    "base_url": sys.argv[1],
    "model": sys.argv[2],
    "api_key": None,
    "temperature": 0.1,
    "max_tokens": 4096,
    "timeout": 120,
}
Path("/var/lib/medical-deid/llm_configs/config.json").write_text(
    json.dumps(config, ensure_ascii=False, indent=2) + "\n"
)
PY
chown "$APP_USER:$APP_GROUP" /var/lib/medical-deid/llm_configs/config.json
chmod 600 /var/lib/medical-deid/llm_configs/config.json

render_service_file "$SCRIPT_DIR/medical-deid-backend.service" /etc/systemd/system/medical-deid-backend.service
render_service_file "$SCRIPT_DIR/medical-deid-frontend.service" /etc/systemd/system/medical-deid-frontend.service

sudo -u "$APP_USER" bash -c "cd '$PROJECT_ROOT' && uv venv .venv && uv sync --frozen --no-dev && uv pip install --python .venv/bin/python -e web/backend"
sudo -u "$APP_USER" bash -c "export PATH='$NVM_NODE_PATH':\$PATH; export VITE_API_BASE_URL=/api; cd '$PROJECT_ROOT/web/frontend' && npm ci && npm run build"

systemctl daemon-reload
systemctl enable medical-deid-backend.service medical-deid-frontend.service
systemctl restart medical-deid-backend.service medical-deid-frontend.service

BOOTSTRAPPED=0
for _ in $(seq 1 30); do
    if curl -fsS http://127.0.0.1:8000/api/auth/setup-required | grep -q '"setup_required":false'; then
        BOOTSTRAPPED=1
        break
    fi
    sleep 1
done

if [ "$BOOTSTRAPPED" = "1" ]; then
    python3 - "$ENV_FILE" <<'PY'
from pathlib import Path
import sys

path = Path(sys.argv[1])
lines = path.read_text().splitlines()
secret_keys = {
    "MEDICAL_DEID_BOOTSTRAP_ADMIN_USER",
    "MEDICAL_DEID_BOOTSTRAP_ADMIN_PASSWORD",
}
out = []
for line in lines:
    key = line.split("=", 1)[0] if "=" in line and not line.startswith("#") else ""
    out.append(f"{key}=" if key in secret_keys else line)
path.write_text("\n".join(out) + "\n")
PY
    chown root:root "$ENV_FILE"
    chmod 600 "$ENV_FILE"
    systemctl restart medical-deid-backend.service
else
    echo "⚠️ 無法確認 bootstrap admin 已建立；已保留 bootstrap env，請檢查 backend log 後手動清除。"
fi

echo "Application services configured for https://$DOMAIN"
echo "Install a reverse proxy using deploy/reverse-proxy/Caddyfile.example or nginx-medical-deid.conf.example"
