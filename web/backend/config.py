"""
Web Backend Configuration
後端配置模組
"""

import os
from pathlib import Path

# LLM 配置 (支援遠端 Ollama API)
# 預設使用外部 Ollama 服務
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://192.168.1.2:30133")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma3:27b")

# 資料目錄
DATA_DIR = Path(os.getenv("MEDICAL_DEID_DATA_DIR", Path(__file__).parent / "data")).resolve()
UPLOAD_DIR = DATA_DIR / "uploads"
RESULTS_DIR = DATA_DIR / "results"
REPORTS_DIR = DATA_DIR / "reports"
REGULATIONS_DIR = DATA_DIR / "regulations"
TASKS_DB_FILE = DATA_DIR / "tasks_db.json"
LOG_DIR = Path(os.getenv("MEDICAL_DEID_LOG_DIR", Path(__file__).parent / "logs")).resolve()

# 檔案限制
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
MAX_CONFIG_UPLOAD_SIZE = 1 * 1024 * 1024  # 1MB
MAX_REGULATION_UPLOAD_SIZE = 5 * 1024 * 1024  # 5MB

# 隱私/安全設定
BACKEND_HOST = os.getenv("MEDICAL_DEID_BACKEND_HOST", "127.0.0.1")
STORE_RAW_PHI = os.getenv("MEDICAL_DEID_STORE_RAW_PHI", "0").lower() in {"1", "true", "yes"}
AUTH_MODE = os.getenv("MEDICAL_DEID_AUTH_MODE", "password").strip().lower()
if AUTH_MODE not in {"password", "anonymous_session"}:
    raise RuntimeError("MEDICAL_DEID_AUTH_MODE must be 'password' or 'anonymous_session'")
API_TOKEN = os.getenv("MEDICAL_DEID_API_TOKEN", "")
ALLOW_NO_AUTH = os.getenv("MEDICAL_DEID_ALLOW_NO_AUTH", "0").lower() in {"1", "true", "yes"}
BOOTSTRAP_TOKEN = os.getenv("MEDICAL_DEID_BOOTSTRAP_TOKEN", "")
ENABLE_PUBLIC_BOOTSTRAP = os.getenv("MEDICAL_DEID_ENABLE_PUBLIC_BOOTSTRAP", "0").lower() in {
    "1",
    "true",
    "yes",
}
SESSION_COOKIE_NAME = os.getenv("MEDICAL_DEID_SESSION_COOKIE", "medical_deid_session")
SESSION_COOKIE_SECURE = os.getenv("MEDICAL_DEID_SESSION_COOKIE_SECURE", "1").lower() in {
    "1",
    "true",
    "yes",
}
SESSION_COOKIE_SAMESITE = os.getenv("MEDICAL_DEID_SESSION_COOKIE_SAMESITE", "lax")
DELETE_UPLOAD_AFTER_PROCESS = os.getenv("MEDICAL_DEID_DELETE_UPLOAD_AFTER_PROCESS", "1").lower() in {
    "1",
    "true",
    "yes",
}
UPLOAD_TTL_HOURS = float(os.getenv("MEDICAL_DEID_UPLOAD_TTL_HOURS", "2"))
RESULT_TTL_HOURS = float(os.getenv("MEDICAL_DEID_RESULT_TTL_HOURS", "24"))
PROCESSING_WORKERS = max(1, int(os.getenv("MEDICAL_DEID_PROCESSING_WORKERS", "1")))
MIN_PASSWORD_LENGTH = max(1, int(os.getenv("MEDICAL_DEID_MIN_PASSWORD_LENGTH", "8")))
PROGRESS_ESTIMATE_SECONDS = max(10, int(os.getenv("MEDICAL_DEID_PROGRESS_ESTIMATE_SECONDS", "75")))

# CORS 設定
_cors_origins = os.getenv("MEDICAL_DEID_CORS_ORIGINS", "")
CORS_ORIGINS = (
    [origin.strip() for origin in _cors_origins.split(",") if origin.strip()]
    if _cors_origins
    else [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
    ]
)


# 確保目錄存在
def ensure_directories():
    """確保所有資料目錄存在"""
    for d in [UPLOAD_DIR, RESULTS_DIR, REPORTS_DIR, REGULATIONS_DIR, LOG_DIR]:
        d.mkdir(parents=True, exist_ok=True)


__all__ = [
    "API_TOKEN",
    "ALLOW_NO_AUTH",
    "AUTH_MODE",
    "BACKEND_HOST",
    "BOOTSTRAP_TOKEN",
    "CORS_ORIGINS",
    "DATA_DIR",
    "DELETE_UPLOAD_AFTER_PROCESS",
    "ENABLE_PUBLIC_BOOTSTRAP",
    "LOG_DIR",
    "MAX_CONFIG_UPLOAD_SIZE",
    "MAX_FILE_SIZE",
    "MAX_REGULATION_UPLOAD_SIZE",
    "MIN_PASSWORD_LENGTH",
    "OLLAMA_BASE_URL",
    "OLLAMA_MODEL",
    "PROCESSING_WORKERS",
    "PROGRESS_ESTIMATE_SECONDS",
    "REGULATIONS_DIR",
    "REPORTS_DIR",
    "RESULT_TTL_HOURS",
    "RESULTS_DIR",
    "SESSION_COOKIE_NAME",
    "SESSION_COOKIE_SAMESITE",
    "SESSION_COOKIE_SECURE",
    "STORE_RAW_PHI",
    "TASKS_DB_FILE",
    "UPLOAD_TTL_HOURS",
    "UPLOAD_DIR",
    "ensure_directories",
]
