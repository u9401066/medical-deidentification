"""
Web Backend Configuration
後端配置模組
"""

import os
from pathlib import Path

# LLM 配置 (支援遠端 Ollama API)
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma3:27b")

# 資料目錄
DATA_DIR = Path(__file__).parent / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
RESULTS_DIR = DATA_DIR / "results"
REPORTS_DIR = DATA_DIR / "reports"
REGULATIONS_DIR = DATA_DIR / "regulations"

# 檔案限制
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

# CORS 設定
CORS_ORIGINS = [
    "http://localhost:5173",
    "http://localhost:3000",
    "http://127.0.0.1:5173",
]


# 確保目錄存在
def ensure_directories():
    """確保所有資料目錄存在"""
    for d in [UPLOAD_DIR, RESULTS_DIR, REPORTS_DIR, REGULATIONS_DIR]:
        d.mkdir(parents=True, exist_ok=True)


__all__ = [
    "CORS_ORIGINS",
    "DATA_DIR",
    "MAX_FILE_SIZE",
    "OLLAMA_BASE_URL",
    "OLLAMA_MODEL",
    "REGULATIONS_DIR",
    "REPORTS_DIR",
    "RESULTS_DIR",
    "UPLOAD_DIR",
    "ensure_directories",
]
