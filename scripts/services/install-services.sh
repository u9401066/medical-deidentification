#!/bin/bash
# Medical De-identification 系統服務安裝腳本
# 使用方式: sudo ./install-services.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"

# NVM 路徑 (用於 npm/node)
NVM_NODE_PATH="/home/eric/.nvm/versions/node/v20.19.6/bin"
ENV_DIR="/etc/medical-deid"
ENV_FILE="$ENV_DIR/medical-deid.env"
APP_USER="${SUDO_USER:-eric}"
APP_GROUP="$(id -gn "$APP_USER")"

echo "🏥 Medical De-identification 系統服務安裝"
echo "========================================"
echo ""

# 檢查是否以 root 執行
if [ "$EUID" -ne 0 ]; then
    echo "❌ 請以 sudo 執行此腳本"
    echo "   sudo $0"
    exit 1
fi

env_value() {
    local key="$1"
    awk -F= -v key="$key" '$1 == key {sub(/^[^=]*=/, ""); print; exit}' "$ENV_FILE" 2>/dev/null
}

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

# 建立 production env file（首次安裝自動產生 shared token）
if [ ! -f "$ENV_FILE" ]; then
    echo "🔐 建立環境設定檔 $ENV_FILE ..."
    install -d -m 750 -o root -g root "$ENV_DIR"
    cat > "$ENV_FILE" <<EOF
# Medical De-identification runtime settings
# Default deployment is local/shared-workspace through the frontend same-origin /api proxy.
# Do not put server secrets in VITE_* browser bundles.
# Set MEDICAL_DEID_API_TOKEN only for non-browser service-to-service use.
MEDICAL_DEID_API_TOKEN=
MEDICAL_DEID_PSEUDONYM_SECRET=
VITE_API_TOKEN=
VITE_API_BASE_URL=/api
MEDICAL_DEID_LOG_LEVEL=INFO
MEDICAL_DEID_STORE_RAW_PHI=0
MEDICAL_DEID_AUTH_MODE=anonymous_session
MEDICAL_DEID_ALLOW_NO_AUTH=0
MEDICAL_DEID_ENABLE_PUBLIC_BOOTSTRAP=0
MEDICAL_DEID_SESSION_COOKIE_SECURE=0
MEDICAL_DEID_SESSION_COOKIE_SAMESITE=lax
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
MEDICAL_DEID_CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
MEDICAL_DEID_ALLOWED_LLM_HOSTS=localhost,127.0.0.1,192.168.1.2
EOF
fi

chown root:root "$ENV_DIR" "$ENV_FILE"
chmod 750 "$ENV_DIR"
chmod 600 "$ENV_FILE"

MEDICAL_DEID_API_TOKEN="${MEDICAL_DEID_API_TOKEN:-$(env_value MEDICAL_DEID_API_TOKEN)}"
VITE_API_TOKEN="${VITE_API_TOKEN:-$(env_value VITE_API_TOKEN)}"
MEDICAL_DEID_DATA_DIR="${MEDICAL_DEID_DATA_DIR:-$(env_value MEDICAL_DEID_DATA_DIR)}"
MEDICAL_DEID_LOG_DIR="${MEDICAL_DEID_LOG_DIR:-$(env_value MEDICAL_DEID_LOG_DIR)}"
MEDICAL_DEID_NODE_BIN="${MEDICAL_DEID_NODE_BIN:-$(env_value MEDICAL_DEID_NODE_BIN)}"
VITE_API_BASE_URL="${VITE_API_BASE_URL:-$(env_value VITE_API_BASE_URL)}"
if [[ "${VITE_API_BASE_URL:-}" == http://*:8000/api || "${VITE_API_BASE_URL:-}" == https://*:8000/api ]]; then
    echo "🔁 偵測到舊版 direct backend VITE_API_BASE_URL，改用同源 /api proxy"
    VITE_API_BASE_URL="/api"
    python3 - "$ENV_FILE" <<'PY'
from pathlib import Path
import sys

path = Path(sys.argv[1])
lines = path.read_text().splitlines()
found = False
out = []
for line in lines:
    if line.startswith("VITE_API_BASE_URL="):
        out.append("VITE_API_BASE_URL=/api")
        found = True
    else:
        out.append(line)
if not found:
    out.append("VITE_API_BASE_URL=/api")
path.write_text("\n".join(out) + "\n")
PY
fi

install -d -m 700 -o "$APP_USER" -g "$APP_GROUP" "${MEDICAL_DEID_DATA_DIR:-/var/lib/medical-deid}" "${MEDICAL_DEID_LOG_DIR:-/var/log/medical-deid}"

# 安裝後端依賴（root venv + web backend runtime deps）
echo "📦 檢查後端依賴..."
sudo -u "$APP_USER" bash -c "cd '$PROJECT_ROOT' && uv venv .venv && uv sync --frozen --no-dev && uv pip install --python .venv/bin/python -e web/backend && test -x .venv/bin/uvicorn"

# 建置前端
echo "🎨 建置前端..."
NODE_BIN="${MEDICAL_DEID_NODE_BIN:-$NVM_NODE_PATH}"
sudo -u "$APP_USER" bash -c "export PATH='$NODE_BIN':\$PATH; export VITE_API_BASE_URL='${VITE_API_BASE_URL:-/api}'; cd '$PROJECT_ROOT/web/frontend' && npm ci && npm run build"

# 產生 service 檔案
echo "📋 產生 systemd service 檔案..."
render_service_file "$SCRIPT_DIR/medical-deid-backend.service" /etc/systemd/system/medical-deid-backend.service
render_service_file "$SCRIPT_DIR/medical-deid-frontend.service" /etc/systemd/system/medical-deid-frontend.service

# 重新載入 systemd
echo "🔄 重新載入 systemd..."
systemctl daemon-reload

# 啟用服務
echo "✅ 啟用服務..."
systemctl enable medical-deid-backend.service
systemctl enable medical-deid-frontend.service

# 啟動服務
echo "🚀 啟動/重啟服務..."
systemctl restart medical-deid-backend.service
sleep 2
systemctl restart medical-deid-frontend.service

# 顯示狀態
echo ""
echo "========================================"
echo "✅ 安裝完成！"
echo ""
echo "📊 服務狀態:"
systemctl status medical-deid-backend.service --no-pager -l | head -10
echo ""
systemctl status medical-deid-frontend.service --no-pager -l | head -10
echo ""
echo "========================================"
echo "🌐 服務網址:"
echo "   前端介面: http://localhost:5173"
echo "   API 入口:  http://localhost:5173/api  (由前端服務代理至本機後端)"
echo "   後端本機: http://127.0.0.1:8000"
echo ""
echo "📋 管理指令:"
echo "   查看狀態: systemctl status medical-deid-backend"
echo "             systemctl status medical-deid-frontend"
echo "   查看日誌: journalctl -u medical-deid-backend -f"
echo "             journalctl -u medical-deid-frontend -f"
echo "   重啟服務: systemctl restart medical-deid-backend"
echo "             systemctl restart medical-deid-frontend"
echo "   停止服務: systemctl stop medical-deid-backend medical-deid-frontend"
echo "========================================"
