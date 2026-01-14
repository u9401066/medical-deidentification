"""
API Package - FastAPI 路由
"""
import sys
from pathlib import Path

# 處理相對 import
_backend_dir = Path(__file__).parent.parent
if str(_backend_dir) not in sys.path:
    sys.path.insert(0, str(_backend_dir))

from fastapi import APIRouter

from api.files import router as files_router
from api.preview import router as preview_router
from api.processing import router as processing_router
from api.results import router as results_router
from api.settings import router as settings_router
from api.health import router as health_router

# 建立主路由
api_router = APIRouter(prefix="/api")

# 註冊子路由
api_router.include_router(files_router, tags=["Files"])
api_router.include_router(preview_router, tags=["Preview"])
api_router.include_router(processing_router, tags=["Processing"])
api_router.include_router(results_router, tags=["Results"])
api_router.include_router(settings_router, tags=["Settings"])
api_router.include_router(health_router, tags=["Health"])

__all__ = ["api_router"]
