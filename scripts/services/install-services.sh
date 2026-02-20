#!/bin/bash
# Medical De-identification 系統服務安裝腳本
# 使用方式: sudo ./install-services.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"

# NVM 路徑 (用於 npm/node)
NVM_NODE_PATH="/home/eric/.nvm/versions/node/v20.19.6/bin"

echo "🏥 Medical De-identification 系統服務安裝"
echo "========================================"
echo ""

# 檢查是否以 root 執行
if [ "$EUID" -ne 0 ]; then
    echo "❌ 請以 sudo 執行此腳本"
    echo "   sudo $0"
    exit 1
fi

# 確認前端已建置
if [ ! -d "$PROJECT_ROOT/web/frontend/dist" ]; then
    echo "⚠️  前端尚未建置，正在建置..."
    sudo -u eric bash -c "export PATH=$NVM_NODE_PATH:\$PATH && cd $PROJECT_ROOT/web/frontend && npm run build"
fi

# 安裝 serve (如果沒有)
if [ ! -f "$NVM_NODE_PATH/serve" ]; then
    echo "📦 安裝 serve..."
    sudo -u eric bash -c "export PATH=$NVM_NODE_PATH:\$PATH && npm install -g serve"
fi

# 複製 service 檔案
echo "📋 複製 systemd service 檔案..."
cp "$SCRIPT_DIR/medical-deid-backend.service" /etc/systemd/system/
cp "$SCRIPT_DIR/medical-deid-frontend.service" /etc/systemd/system/

# 重新載入 systemd
echo "🔄 重新載入 systemd..."
systemctl daemon-reload

# 啟用服務
echo "✅ 啟用服務..."
systemctl enable medical-deid-backend.service
systemctl enable medical-deid-frontend.service

# 啟動服務
echo "🚀 啟動服務..."
systemctl start medical-deid-backend.service
sleep 2
systemctl start medical-deid-frontend.service

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
echo "   後端 API: http://localhost:8000"
echo "   前端介面: http://localhost:5173"
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
