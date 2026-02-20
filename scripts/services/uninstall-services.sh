#!/bin/bash
# Medical De-identification 系統服務移除腳本
# 使用方式: sudo ./uninstall-services.sh

set -e

echo "🏥 Medical De-identification 系統服務移除"
echo "========================================"
echo ""

# 檢查是否以 root 執行
if [ "$EUID" -ne 0 ]; then
    echo "❌ 請以 sudo 執行此腳本"
    echo "   sudo $0"
    exit 1
fi

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

echo ""
echo "========================================"
echo "✅ 移除完成！"
echo "========================================"
