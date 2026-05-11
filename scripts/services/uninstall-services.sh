#!/bin/bash
# Medical De-identification 系統服務移除腳本
# 使用方式: sudo ./uninstall-services.sh [--purge-data]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
ENV_FILE="/etc/medical-deid/medical-deid.env"

echo "🏥 Medical De-identification 系統服務移除"
echo "========================================"
echo ""

PURGE_DATA=false
if [ "${1:-}" = "--purge-data" ]; then
    PURGE_DATA=true
fi

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

safe_rm_dir() {
    local target="$1"
    if [ -n "$target" ] && [ "$target" != "/" ]; then
        rm -rf "$target"
    fi
}

# 停止服務
echo "🛑 停止服務..."
systemctl stop medical-deid-frontend.service 2>/dev/null || true
systemctl stop medical-deid-backend.service 2>/dev/null || true

# 停用服務
echo "🔒 停用服務..."
systemctl disable medical-deid-frontend.service 2>/dev/null || true
systemctl disable medical-deid-backend.service 2>/dev/null || true

# 移除 service 檔案
echo "🗑️  移除 service 檔案..."
rm -f /etc/systemd/system/medical-deid-backend.service
rm -f /etc/systemd/system/medical-deid-frontend.service

# 重新載入 systemd
echo "🔄 重新載入 systemd..."
systemctl daemon-reload
systemctl reset-failed medical-deid-frontend.service medical-deid-backend.service 2>/dev/null || true

if [ "$PURGE_DATA" = true ]; then
    echo "🧹 清除 runtime 設定與資料..."
    DATA_DIR="$(env_value MEDICAL_DEID_DATA_DIR)"
    LOG_DIR="$(env_value MEDICAL_DEID_LOG_DIR)"
    rm -rf /etc/medical-deid
    safe_rm_dir "${DATA_DIR:-/var/lib/medical-deid}"
    safe_rm_dir "${LOG_DIR:-/var/log/medical-deid}"
    safe_rm_dir "$PROJECT_ROOT/web/backend/data"
    safe_rm_dir "$PROJECT_ROOT/web/backend/logs"
fi

echo ""
echo "========================================"
echo "✅ 移除完成！"
echo "========================================"
