#!/bin/bash
# Web Application Startup Script
# 啟動 PHI 去識別化 Web 應用程式

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
WEB_DIR="$PROJECT_ROOT/web"

echo "🚀 啟動 PHI 去識別化 Web 應用程式"
echo "=================================="

# 檢查是否有必要的套件
echo ""
echo "📦 檢查依賴..."

# 使用專案根目錄的虛擬環境
VENV_PYTHON="$PROJECT_ROOT/.venv/bin/python"
if [ ! -f "$VENV_PYTHON" ]; then
    echo "⚠️  專案虛擬環境不存在，正在建立..."
    cd "$PROJECT_ROOT"
    uv venv
    uv pip install -e .
fi

# 確保 Web 依賴已安裝 (在根目錄的 venv 中)
echo "📦 檢查 Web 後端依賴..."
cd "$PROJECT_ROOT"
uv pip install fastapi uvicorn python-multipart

# 檢查前端依賴
if [ ! -d "$WEB_DIR/frontend/node_modules" ]; then
    echo "⚠️  前端 node_modules 不存在，正在安裝..."
    cd "$WEB_DIR/frontend"
    npm install
fi

# 建立所需目錄
mkdir -p "$WEB_DIR/backend/uploads"
mkdir -p "$WEB_DIR/backend/results"
mkdir -p "$WEB_DIR/backend/reports"

# 啟動後端 (使用根目錄的 venv 和 uvicorn)
echo ""
echo "🔧 啟動後端 (FastAPI on port 8000)..."
cd "$WEB_DIR/backend"
"$VENV_PYTHON" -m uvicorn main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
echo "   Backend PID: $BACKEND_PID"

# 等待後端啟動
sleep 2

# 啟動前端
echo ""
echo "🎨 啟動前端 (Vite on port 5173)..."
cd "$WEB_DIR/frontend"
npm run dev &
FRONTEND_PID=$!
echo "   Frontend PID: $FRONTEND_PID"

# 等待前端啟動
sleep 3

echo ""
echo "=================================="
echo "✅ 應用程式已啟動！"
echo ""
echo "📌 存取網址:"
echo "   Frontend: http://localhost:5173"
echo "   Backend:  http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"
echo ""
echo "按 Ctrl+C 停止所有服務"
echo "=================================="

# 等待中斷信號
trap "echo ''; echo '🛑 正在停止服務...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit 0" INT TERM

wait
