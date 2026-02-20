# 後端模組化重構計畫

## 📋 目標

將 `main.py` (1258 行) 拆分成模組化結構，符合 DDD 原則。

## 🏗️ 新目錄結構

```
web/backend/
├── main.py                 # 精簡的入口 (約 50 行)
├── config.py               # 應用配置
├── api/                    # API 路由 (Interface Layer)
│   ├── __init__.py
│   ├── dependencies.py     # 共用依賴
│   ├── files.py           # 檔案上傳/下載
│   ├── preview.py         # 資料預覽
│   ├── processing.py      # PHI 處理任務
│   ├── results.py         # 結果與報告
│   ├── settings.py        # 設定與法規
│   └── health.py          # 健康檢查
├── models/                 # 資料模型 (Domain Layer)
│   ├── __init__.py
│   ├── config.py          # PHIConfig, PHITypeConfig
│   ├── task.py            # TaskStatus, ProcessRequest
│   ├── file.py            # UploadedFile
│   └── regulation.py      # RegulationRule
├── services/               # 業務邏輯 (Application Layer)
│   ├── __init__.py
│   ├── file_service.py    # 檔案操作
│   ├── task_service.py    # 任務管理
│   ├── processing_service.py  # PHI 處理
│   └── regulation_service.py  # 法規管理
└── data/                   # 資料目錄 (Infrastructure)
    ├── uploads/
    ├── results/
    ├── reports/
    └── regulations/
```

## 📦 模組職責

### 1. `config.py` - 應用配置
- OLLAMA_BASE_URL
- DATA_DIR, UPLOAD_DIR, RESULTS_DIR...
- MAX_FILE_SIZE
- CORS 設定

### 2. `models/` - Pydantic 模型
- `config.py`: PHITypeConfig, PHIConfig
- `task.py`: TaskStatus, ProcessRequest
- `file.py`: UploadedFile
- `regulation.py`: RegulationRule, RegulationContent

### 3. `services/` - 業務服務
- `file_service.py`: upload, list, delete, download
- `task_service.py`: tasks_db 管理, 狀態查詢
- `processing_service.py`: PHI 處理邏輯, 引擎調用
- `regulation_service.py`: 法規 CRUD

### 4. `api/` - FastAPI 路由
- `dependencies.py`: 共用的 Depends
- 每個 router 使用 `APIRouter(prefix="/api/xxx")`

## 🔄 遷移順序

1. ✅ 建立目錄結構
2. ✅ 抽取 models (config.py, task.py, file.py, regulation.py)
3. ✅ 抽取 services (task_service, file_service, processing_service, regulation_service)
4. ✅ 抽取 api routers (files, preview, processing, results, settings, health)
5. ✅ 精簡 main.py (1258 行 → 60 行)
6. ✅ 測試驗證 (21 個 API 端點全部通過)

## ✅ 完成時間

- **完成日期**: 2025-01-14
- **原始程式碼**: `main_legacy.py` (46KB, 1258 行)
- **新架構**: 模組化結構 (main.py 僅 60 行)
- **測試結果**: 所有 9 個主要端點通過測試

## 📌 注意事項

- 保持向後相容 (API 路徑不變)
- `tasks_db` 需考慮線程安全
- 日誌保持現有格式
- 遵循專案 DDD 架構風格
