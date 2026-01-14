"""
Medical De-identification Web API
FastAPI 後端服務 (模組化版本)

這是精簡後的入口檔案，所有業務邏輯已移至模組化結構：
- api/: API 路由
- models/: Pydantic 資料模型
- services/: 業務邏輯服務
- config.py: 應用配置
"""
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

# 確保 backend 目錄在 path 中
_backend_dir = Path(__file__).parent
if str(_backend_dir) not in sys.path:
    sys.path.insert(0, str(_backend_dir))

from config import CORS_ORIGINS, ensure_directories
from api import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """應用生命週期管理"""
    # 啟動時
    ensure_directories()
    logger.info("🚀 Medical De-identification API started")
    logger.info(f"📁 Data directories initialized")
    
    yield
    
    # 關閉時
    logger.info("👋 Medical De-identification API stopped")


app = FastAPI(
    title="Medical De-identification API",
    description="醫療文本去識別化 Web API",
    version="2.0.0",  # 版本升級
    lifespan=lifespan,
)

# CORS 設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 註冊 API 路由
app.include_router(api_router)


# ============================================================
# 入口點
# ============================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
