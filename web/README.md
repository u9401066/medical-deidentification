# Medical De-identification Web Interface

現代化的 PHI (Protected Health Information) 去識別化 Web 介面。

## 功能特色

- 📤 **檔案上傳**: 支援拖放上傳 Excel, CSV, JSON, TXT 檔案
- 👀 **資料預覽**: 即時預覽上傳的資料內容
- 🔒 **PHI 處理**: 使用 LLM 進行智慧 PHI 偵測與遮蔽
- 📊 **報告生成**: 詳細的處理報告與統計分析
- ⚙️ **彈性設定**: 可配置 PHI 類型和遮蔽方式
- 📜 **法規管理**: 上傳並管理 HIPAA、台灣個資法等法規
- 🔄 **任務持久化**: 重新整理頁面後任務不會消失
- 🛠️ **系統維護**: 清除資料、重置設定功能

## 新功能 (2026-01-28)

### Hard Rules (LLM 後處理)
- **AGE_OVER_89**: 自動過濾年齡 < 89 的 LLM 誤判

### 任務持久化
- 任務狀態保存到 `data/tasks_db.json`
- 重新整理頁面後任務不會消失

### 系統維護
- 清除上傳檔案 / 結果檔案 / 報告檔案
- 儲存空間統計
- PHI 設定重置為預設值

## 快速開始

### 前置需求

- Python 3.12+
- Node.js 18+
- [uv](https://github.com/astral-sh/uv) (Python 套件管理)
- npm (Node.js 套件管理)

### 安裝

```bash
# 安裝後端依賴
cd web/backend
uv pip install fastapi uvicorn python-multipart pandas openpyxl loguru pydantic pydantic-settings

# 安裝前端依賴
cd ../frontend
npm install
```

### 啟動

**方法一: 使用啟動腳本**

```bash
./scripts/start-web.sh
```

**方法二: 分別啟動**

```bash
# 終端機 1: 啟動後端
cd web/backend
uv run uvicorn main:app --reload --port 8000

# 終端機 2: 啟動前端
cd web/frontend
npm run dev
```

### 存取網址

- 前端介面: http://localhost:5173
- 後端 API: http://localhost:8000
- API 文件: http://localhost:8000/docs

## 專案結構

```
web/
├── backend/                 # FastAPI 後端
│   ├── main.py             # API 端點定義
│   ├── pyproject.toml      # uv 依賴配置
│   └── README.md
│
└── frontend/               # React + TypeScript 前端 (DDD 架構)
    ├── src/
    │   ├── domain/           # 領域層 - 純業務邏輯
    │   │   ├── entities/     # 實體 (Task, File, Report)
    │   │   └── value-objects/# 值物件 (PHIConfig, PHIType)
    │   ├── application/      # 應用層 - Use Cases
    │   │   └── hooks/        # React Query hooks
    │   ├── infrastructure/   # 基礎設施層
    │   │   ├── api/          # API 客戶端
    │   │   └── logging/      # 日誌系統 (可供 Agent 讀取)
    │   ├── presentation/     # 呈現層 - UI
    │   │   └── components/   # React 元件
    │   │       ├── ui/       # 通用 UI 元件
    │   │       ├── Sidebar.tsx
    │   │       ├── TasksPanel.tsx
    │   │       ├── ResultsPanel.tsx
    │   │       ├── Reports.tsx
    │   │       └── Settings.tsx
    │   ├── shared/           # 共享工具
    │   │   ├── types/        # TypeScript 類型
    │   │   └── utils/        # 工具函數
    │   ├── lib/              # 向後兼容工具
    │   ├── App.tsx           # 主應用程式
    │   └── main.tsx          # 進入點
    ├── package.json          # npm 依賴配置
    └── vite.config.ts        # Vite 配置
```

## 使用流程

1. **上傳資料**: 在側邊欄拖放或點擊上傳檔案
2. **預覽資料**: 在「資料預覽」分頁確認內容
3. **開始處理**: 選擇檔案後點擊「開始處理」
4. **查看結果**: 在「處理結果」分頁監控進度
5. **檢視報告**: 在「報告」分頁查看詳細統計
6. **下載結果**: 點擊「下載結果」取得去識別化後的檔案

## 設定

### PHI 類型配置

在「設定」分頁的「PHI 設定」中可以：
- 啟用/停用特定 PHI 類型的偵測
- 選擇各類型的遮蔽方式 (遮蔽、雜湊、替換、刪除、保留)
- 開啟嚴格模式進行更嚴格的偵測

### 法規管理

在「設定」分頁的「法規管理」中可以：
- 上傳新的法規文件 (Markdown, TXT, PDF)
- 檢視已載入的法規規則
- 啟用/停用特定法規

## 技術堆疊

### 後端
- FastAPI 0.115+
- Uvicorn
- Pandas
- Pydantic

### 前端
- React 18
- TypeScript 5
- Vite 5
- TailwindCSS 3
- Radix UI
- TanStack Query
