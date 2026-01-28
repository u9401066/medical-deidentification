# PHI 去識別化 Web 應用程式規格書

> 版本: 2.1.0  
> 最後更新: 2026-01-28  
> 狀態: MVP 完善中

---

## 目錄

1. [系統概述](#系統概述)
2. [使用者故事](#使用者故事)
3. [技術架構](#技術架構)
4. [功能模組](#功能模組)
5. [API 規格](#api-規格)
6. [資料模型](#資料模型)
7. [前端元件](#前端元件)
8. [UX 設計指南](#ux-設計指南)
9. [已知問題與待改善項目](#已知問題與待改善項目)
10. [未來規劃](#未來規劃)

---

## 系統概述

### 目的
提供一個**簡單易用**的網頁介面，讓一般文書人員可以上傳包含敏感資料（PHI）的檔案，系統會自動偵測並遮罩這些敏感資訊，並產生處理報告。

### 目標使用者
- 一般文書人員（非技術人員）
- 醫療行政人員
- 資料處理人員

### 主要工作流程
```
┌─────────────────────────────────────────────────────────────────────┐
│                           Sidebar (左側)                            │
│  ┌─────────────┐                                                    │
│  │  上傳檔案   │  ← 拖放或點擊上傳多個檔案                          │
│  └─────────────┘                                                    │
│  ┌─────────────┐                                                    │
│  │  檔案列表   │  ← 點擊檔案：連動預覽/結果                         │
│  │  📄 file1   │     雙擊檔案：快速預覽                             │
│  │  📄 file2   │     勾選框：選取要處理的檔案                       │
│  │  ✓ file3   │                                                    │
│  └─────────────┘                                                    │
│  ┌─────────────┐                                                    │
│  │ [開始處理]  │  ← 處理選中的檔案                                  │
│  │ [下載結果]  │  ← 下載已完成檔案                                  │
│  └─────────────┘                                                    │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         主內容區 (右側 Tabs)                         │
│                                                                      │
│  ┌──────────┬──────────┬──────────┬──────────┬──────────┐          │
│  │ 📋 預覽  │ ⏳ 任務  │ 📊 結果  │ 📑 報告  │ ⚙️ 設定  │          │
│  └──────────┴──────────┴──────────┴──────────┴──────────┘          │
│                                                                      │
│  [根據選中的 Tab 顯示對應內容]                                       │
│  - 預覽：顯示 Sidebar 選中檔案的原始內容                             │
│  - 結果：顯示 Sidebar 選中檔案的處理結果（前後對照）                 │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 使用者故事

### US-001: 檔案上傳與預覽
**作為** 文書人員  
**我想要** 上傳多個檔案後，點擊檔案名稱就能預覽內容  
**以便** 確認上傳的檔案是否正確

**驗收條件**:
- [ ] 可拖放多個檔案同時上傳
- [ ] Sidebar 點擊檔案 → DataPreview 自動顯示該檔預覽
- [ ] 顯示上傳進度與成功/失敗提示

### US-002: 批次處理
**作為** 文書人員  
**我想要** 勾選多個檔案後一次處理  
**以便** 節省時間

**驗收條件**:
- [ ] 可勾選多個檔案
- [ ] 點擊「開始處理」後，顯示處理進度
- [ ] 處理完成後有通知提示

### US-003: 結果查看與對照
**作為** 文書人員  
**我想要** 看到處理前後的對照  
**以便** 確認去識別化的效果

**驗收條件**:
- [ ] Sidebar 點擊已處理檔案 → ResultsPanel 自動顯示該結果
- [ ] 顯示原始內容與遮罩後內容的並排對照
- [ ] 不同 PHI 類型用不同顏色標記

### US-004: 處理報告
**作為** 文書人員  
**我想要** 看到處理報告，包含費時、Token 用量、PHI 統計  
**以便** 了解處理效能和結果概況

**驗收條件**:
- [ ] 報告顯示：處理時間 (秒)
- [ ] 報告顯示：估計 Token 用量
- [ ] 報告顯示：各類型 PHI 數量與百分比圓餅圖

### US-005: 下載結果
**作為** 文書人員  
**我想要** 從 Sidebar 或結果頁面下載處理後的檔案  
**以便** 使用去識別化後的資料

**驗收條件**:
- [ ] Sidebar 提供下載按鈕（已完成檔案）
- [ ] 結果頁面提供下載按鈕
- [ ] 支援原始格式下載 (Excel/CSV/TXT)

---

## 技術架構

### 後端 (Backend)
| 項目 | 技術 |
|------|------|
| 框架 | FastAPI 2.0.0 |
| Python | 3.12+ |
| 非同步 | asyncio |
| 資料儲存 | 檔案系統 (JSON) |
| LLM 整合 | Ollama (可遠端) |

#### 目錄結構
```
web/backend/
├── main.py              # FastAPI 應用程式入口
├── config.py            # 設定檔
├── api/                 # API 路由
│   ├── files.py         # 檔案上傳/下載
│   ├── health.py        # 健康檢查
│   ├── preview.py       # 資料預覽
│   ├── processing.py    # PHI 處理
│   ├── results.py       # 處理結果
│   └── settings.py      # 設定與法規
├── models/              # Pydantic 模型
│   ├── config.py
│   ├── regulation.py
│   └── request.py
└── services/            # 業務邏輯
    ├── file_service.py
    ├── phi_config_service.py
    ├── processing_service.py
    ├── regulation_service.py
    └── task_service.py
```

### 前端 (Frontend)
| 項目 | 技術 |
|------|------|
| 框架 | React 18.3.1 |
| 語言 | TypeScript 5.6.2 |
| 建置 | Vite 5.4.6 |
| 樣式 | Tailwind CSS 3.4.11 |
| UI 元件 | Radix UI + shadcn/ui |
| 狀態管理 (Server) | TanStack React Query 5.56.2 |
| 狀態管理 (Client) | Zustand + Immer |
| 表單驗證 | React Hook Form + Zod |
| 動畫 | Framer Motion |
| 測試 | Vitest + React Testing Library + MSW |

#### 目錄結構 (DDD 架構)
```
web/frontend/src/
├── App.tsx                    # 應用程式入口
├── main.tsx                   # React 掛載點
├── application/               # 應用層 (Use Cases)
│   └── hooks/                 # 自訂 Hooks
│       ├── useFiles.ts
│       └── useTasks.ts
├── domain/                    # 領域層 (Entities, Value Objects)
│   ├── entities/
│   └── value-objects/
│       └── schemas/           # Zod 驗證
├── infrastructure/            # 基礎設施層
│   ├── api/                   # API 客戶端
│   ├── logging/               # 日誌
│   └── store/                 # Zustand Stores
└── presentation/              # 展示層 (UI)
    └── components/
        ├── ui/                # 基礎 UI 元件
        ├── Sidebar.tsx
        ├── DataPreview.tsx
        ├── TasksPanel.tsx
        ├── TaskCard.tsx
        ├── ResultsPanel.tsx
        ├── ResultsPreview.tsx
        ├── Reports.tsx
        └── Settings.tsx
```

---

## 功能模組

### 1. 檔案管理 (Sidebar)
**位置**: `Sidebar.tsx` + `api/files.py`

| 功能 | 狀態 | 說明 |
|------|------|------|
| 拖放上傳 | ✅ 完成 | 支援 Excel, CSV, JSON, TXT |
| 檔案列表 | ✅ 完成 | 顯示檔案名稱、大小、上傳時間 |
| 檔案選取 | ✅ 完成 | 多選功能 |
| 批次刪除 | ✅ 完成 | 刪除選中檔案 |
| 開始處理 | ✅ 完成 | 將選中檔案送入處理佇列 |
| 下載結果 | ✅ 完成 | 下載處理後的檔案 |
| LLM 狀態顯示 | ✅ 完成 | 顯示 Ollama 連線狀態 |

**API 端點**:
- `POST /api/upload` - 上傳檔案
- `GET /api/files` - 列出檔案
- `DELETE /api/files/{id}` - 刪除檔案
- `GET /api/download/{id}` - 下載結果

### 2. 資料預覽 (DataPreview)
**位置**: `DataPreview.tsx` + `api/preview.py`

| 功能 | 狀態 | 說明 |
|------|------|------|
| 表格預覽 | ✅ 完成 | Excel, CSV 表格顯示 |
| 文字預覽 | ✅ 完成 | TXT 純文字顯示 |
| JSON 預覽 | ✅ 完成 | JSON 格式化顯示 |
| 分頁瀏覽 | ✅ 完成 | 支援大檔案分頁 |
| 檔案選擇 | ✅ 完成 | 下拉選單切換檔案 |

**API 端點**:
- `GET /api/preview/{file_id}?page=1&page_size=50`

### 3. 處理任務 (TasksPanel)
**位置**: `TasksPanel.tsx` + `TaskCard.tsx` + `api/processing.py`

| 功能 | 狀態 | 說明 |
|------|------|------|
| 任務列表 | ✅ 完成 | 顯示所有處理任務 |
| 即時進度 | ✅ 完成 | 進度條與百分比 |
| 狀態顯示 | ✅ 完成 | pending/processing/completed/failed |
| 時間估計 | ✅ 完成 | 已用時間與預估剩餘時間 |
| 處理統計 | ✅ 完成 | 顯示處理統計資訊 |
| 自動輪詢 | ✅ 完成 | 每 2 秒更新任務狀態 |

**API 端點**:
- `POST /api/process` - 開始處理
- `GET /api/tasks` - 列出任務
- `GET /api/tasks/{task_id}` - 取得任務狀態
- `GET /api/stats/processing` - 處理統計

### 4. 處理結果 (ResultsPanel)
**位置**: `ResultsPanel.tsx` + `api/results.py`

| 功能 | 狀態 | 說明 |
|------|------|------|
| 結果列表 | ✅ 完成 | 顯示所有處理結果 |
| PHI 列表視圖 | ✅ 完成 | 表格顯示偵測到的 PHI |
| 差異比較視圖 | ✅ 完成 | 原始 vs 遮罩後對比 |
| PHI 高亮 | ✅ 完成 | 黃色標記遮罩部分 |
| 結果下載 | ✅ 完成 | 下載處理後檔案 |
| 類型顏色標記 | ✅ 完成 | 不同 PHI 類型不同顏色 |

**API 端點**:
- `GET /api/results` - 列出結果
- `GET /api/results/{task_id}` - 結果詳情

### 5. 報告 (Reports)
**位置**: `Reports.tsx` + `api/results.py`

| 功能 | 狀態 | 說明 |
|------|------|------|
| 報告列表 | ✅ 完成 | 顯示所有報告 |
| 報告概要 | ✅ 完成 | 處理檔案數、PHI 數、字數、時間 |
| PHI 類型分布 | ✅ 完成 | 聚合顯示各類型 PHI 統計 |
| PHI 詳細列表 | ✅ 完成 | 顯示每個 PHI 實體 |
| 報告資訊 | ✅ 完成 | 任務名稱、產生時間、處理速度 |
| 匯出報告 | ⚠️ 待實作 | 按鈕存在但功能未完成 |

**API 端點**:
- `GET /api/reports` - 列出報告
- `GET /api/reports/{task_id}` - 報告詳情

### 6. 設定 (Settings)
**位置**: `Settings.tsx` + `api/settings.py`

#### 6.1 PHI 設定
| 功能 | 狀態 | 說明 |
|------|------|------|
| 全域開關 | ✅ 完成 | 啟用/停用 PHI 偵測 |
| 嚴格模式 | ✅ 完成 | 使用更嚴格的規則 |
| 預設遮蔽方式 | ✅ 完成 | mask/hash/replace/delete/keep |
| PHI 類型個別設定 | ✅ 完成 | 每種類型可獨立設定 |
| 自訂替換詞 | ✅ 完成 | replace 模式時的替換文字 |
| 儲存設定 | ✅ 完成 | 儲存設定到後端 |

#### 6.2 法規管理
| 功能 | 狀態 | 說明 |
|------|------|------|
| 法規列表 | ✅ 完成 | 顯示已載入法規 |
| 上傳法規 | ✅ 完成 | 支援 md, txt, json |
| 查看內容 | ✅ 完成 | 展開查看法規內容 |
| 啟用/停用 | ⚠️ 待實作 | Switch 存在但未連接 API |

**API 端點**:
- `GET /api/settings/phi-types` - 取得 PHI 類型定義
- `GET /api/settings/config` - 取得設定
- `PUT /api/settings/config` - 更新設定
- `GET/PUT /api/settings/phi-types/{type}` - 個別類型設定
- `GET/POST /api/settings/presets` - Preset 管理
- `GET/POST /api/regulations` - 法規管理
- `GET /api/regulations/{id}/content` - 法規內容
- `PUT /api/regulations/{id}` - 更新法規狀態

### 7. 健康檢查 (Health)
**位置**: `api/health.py`

| 功能 | 狀態 | 說明 |
|------|------|------|
| 系統狀態 | ✅ 完成 | 返回 healthy 狀態 |
| LLM 狀態 | ✅ 完成 | Ollama 連線狀態 |
| 引擎狀態 | ✅ 完成 | PHI 處理引擎是否可用 |

**API 端點**:
- `GET /api/health`

---

## API 規格

### 基本資訊
- Base URL: `http://localhost:8000/api`
- Content-Type: `application/json`

### 端點總覽

| 方法 | 端點 | 說明 |
|------|------|------|
| **檔案** |||
| POST | `/upload` | 上傳檔案 |
| GET | `/files` | 列出檔案 |
| DELETE | `/files/{id}` | 刪除檔案 |
| GET | `/download/{id}` | 下載結果 |
| **預覽** |||
| GET | `/preview/{file_id}` | 預覽檔案內容 |
| **處理** |||
| POST | `/process` | 開始處理 |
| GET | `/tasks` | 列出任務 |
| GET | `/tasks/{task_id}` | 任務狀態 |
| GET | `/stats/processing` | 處理統計 |
| **結果** |||
| GET | `/results` | 列出結果 |
| GET | `/results/{task_id}` | 結果詳情 |
| GET | `/reports` | 列出報告 |
| GET | `/reports/{task_id}` | 報告詳情 |
| **設定** |||
| GET | `/settings/phi-types` | PHI 類型定義 |
| GET | `/settings/config` | 取得設定 |
| PUT | `/settings/config` | 更新設定 |
| GET/PUT | `/settings/phi-types/{type}` | 單一類型設定 |
| GET | `/settings/presets` | 列出 Preset |
| POST | `/settings/presets/{id}/apply` | 套用 Preset |
| **法規** |||
| GET | `/regulations` | 列出法規 |
| GET | `/regulations/{id}/content` | 法規內容 |
| PUT | `/regulations/{id}` | 更新法規狀態 |
| POST | `/regulations/upload` | 上傳法規 |
| **健康** |||
| GET | `/health` | 健康檢查 |

---

## 資料模型

### UploadedFile
```typescript
interface UploadedFile {
  id: string;
  filename: string;
  size: number;
  upload_time: string;
  file_type: string;
  preview_available: boolean;
  status: 'pending' | 'processing' | 'completed' | 'error';
  task_id?: string | null;
}
```

### TaskStatus
```typescript
interface TaskStatus {
  task_id: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress: number;
  message: string;
  created_at: string;
  completed_at?: string;
  started_at?: string;
  elapsed_seconds?: number;
  estimated_remaining_seconds?: number;
  processing_speed?: number;
  total_chars?: number;
  processed_chars?: number;
}
```

### PHIEntity
```typescript
interface PHIEntity {
  type: string;
  value: string;
  masked_value: string;
  field?: string | null;
  row?: number | null;
  confidence?: number;
  start_pos?: number;
  end_pos?: number;
  reason?: string;
}
```

### PHIConfig
```typescript
interface PHIConfig {
  enabled?: boolean;
  strict_mode?: boolean;
  default_masking?: MaskingType;
  phi_types?: Record<string, PHITypeConfig>;
  preserve_format?: boolean;
  custom_patterns?: Record<string, string>;
}

type MaskingType = 'mask' | 'hash' | 'replace' | 'delete' | 'keep';
```

---

## 前端元件

### 元件樹狀結構
```
App
├── Sidebar                    # 側邊欄：檔案管理 + LLM 狀態
│   └── (react-dropzone)
│
├── Tabs                       # 主要內容區塊標籤
│   ├── DataPreview           # 資料預覽
│   │   └── (Table | Pre)
│   │
│   ├── TasksPanel            # 處理任務列表
│   │   └── TaskCard          # 單一任務卡片
│   │
│   ├── ResultsPanel          # 處理結果
│   │   ├── ResultsList       # (內嵌) 結果列表
│   │   ├── PHIList           # (內嵌) PHI 列表視圖
│   │   └── DiffView          # (內嵌) 差異比較視圖
│   │
│   ├── Reports               # 報告
│   │   ├── ReportSummary     # (內嵌) 報告概要
│   │   └── PHIDetailList     # (內嵌) PHI 詳細列表
│   │
│   └── SettingsPanel         # 設定
│       ├── PHISettings       # (內嵌) PHI 設定
│       └── RegulationsSettings  # (內嵌) 法規管理
```

### 狀態管理

#### Server State (TanStack Query)
| Query Key | 資料 | 更新頻率 |
|-----------|------|----------|
| `['health']` | 系統健康狀態 | 10 秒 |
| `['files']` | 上傳檔案列表 | 手動 |
| `['preview', fileId]` | 檔案預覽資料 | 手動 |
| `['tasks']` | 處理任務列表 | 2 秒 |
| `['results']` | 處理結果列表 | 手動 |
| `['reports']` | 報告列表 | 手動 |
| `['phi-types']` | PHI 類型定義 | 手動 |
| `['config']` | 設定 | 手動 |
| `['regulations']` | 法規列表 | 手動 |

#### Client State (Zustand)
| Store | 用途 |
|-------|------|
| `uiStore` | 主題、側邊欄、通知 |
| `taskStore` | 任務選取、篩選 |
| `selectionStore` | **（新增）** 統一管理選中檔案，連動預覽/結果 |

---

## UX 設計指南

### 設計原則（針對一般文書人員）

| 原則 | 說明 | 實踐方式 |
|------|------|----------|
| **簡單直覺** | 不需要技術背景即可上手 | 拖放上傳、一鍵處理 |
| **視覺回饋** | 每個操作都有明確回饋 | Toast 通知、進度條、狀態標籤 |
| **減少選擇** | 預設值要夠好 | 預設遮罩方式、自動選取 PHI 類型 |
| **容錯設計** | 防止誤操作 | 刪除確認、撤銷功能 |

### 視覺設計規範

#### 顏色系統
| 用途 | 顏色 | Tailwind Class |
|------|------|----------------|
| 主要操作 | 藍色 | `bg-primary` |
| 成功狀態 | 綠色 | `text-green-600` |
| 警告/處理中 | 黃色 | `text-yellow-600` |
| 錯誤/危險 | 紅色 | `text-red-500` |
| 中性/次要 | 灰色 | `text-muted-foreground` |

#### PHI 類型顏色標記
| PHI 類型 | 背景色 | 用途 |
|----------|--------|------|
| NAME | 紅色系 `bg-red-100` | 人名 |
| DATE | 藍色系 `bg-blue-100` | 日期 |
| PHONE | 綠色系 `bg-green-100` | 電話 |
| EMAIL | 紫色系 `bg-purple-100` | 郵件 |
| ADDRESS | 橘色系 `bg-orange-100` | 地址 |
| ID_NUMBER | 黃色系 `bg-yellow-100` | 身分證 |
| MEDICAL_RECORD | 粉色系 `bg-pink-100` | 病歷號 |

#### 狀態標籤設計
```
待處理    →  ⚪ 灰色邊框 outline
處理中    →  🔵 藍色/黃色 secondary + spinner
已完成    →  🟢 綠色 default
錯誤      →  🔴 紅色 destructive
```

### 互動設計

#### Sidebar 檔案互動
| 操作 | 行為 | 視覺反饋 |
|------|------|----------|
| 單擊 | 選中檔案，連動預覽/結果 | 藍色邊框高亮 |
| Ctrl+單擊 | 多選（勾選用於處理） | 勾選框打勾 |
| 雙擊 | 快速切換到預覽 Tab | 自動跳轉 |
| 右鍵 | 顯示右鍵選單（預覽/處理/刪除/下載） | Context Menu |

#### 通知系統 (Toast)
| 事件 | 類型 | 訊息範例 |
|------|------|----------|
| 上傳成功 | success | ✅ 已上傳 3 個檔案 |
| 上傳失敗 | error | ❌ 上傳失敗：檔案過大 |
| 處理開始 | info | ⏳ 開始處理 2 個檔案 |
| 處理完成 | success | ✅ 處理完成，發現 15 個 PHI |
| 處理失敗 | error | ❌ 處理失敗：LLM 連線逾時 |

### 報告視覺化

#### 報告概要卡片
```
┌─────────────────────────────────────────────────────────────────┐
│                        📊 處理報告概要                          │
├────────────────┬────────────────┬────────────────┬──────────────┤
│   處理檔案數   │   發現 PHI     │   處理時間     │  Token 用量  │
│      3         │      25        │    12.5 秒     │   ~3,200     │
│     files      │     items      │                │   tokens     │
└────────────────┴────────────────┴────────────────┴──────────────┘
```

#### PHI 類型分布（圓餅圖）
- 使用簡單的水平條狀圖或圓餅圖
- 顯示各 PHI 類型的數量與百分比
- 點擊可展開查看詳細列表

---

## 已知問題與待改善項目

### � 待修復 (FIXME) - 本次迭代必修

| ID | 嚴重度 | 問題描述 | 位置 | 修正方案 |
|----|--------|----------|------|----------|
| FIX-001 | 中 | 法規 Switch 未連接 API | `Settings.tsx:309` | 接上 `updateRegulation` mutation |
| FIX-002 | 低 | Reports 匯出報告按鈕無功能 | `Reports.tsx:47` | 實作 `downloadReport` 或暫時隱藏 |
| FIX-003 | 低 | health.py 使用 subprocess+curl | `health.py:27` | 改用 httpx async |
| FIX-004 | 中 | API 模組重複定義 | `api/index.ts` + `api/tasks.ts` | 合併模組 |

### 🟡 功能差距 (GAP) - 本次迭代新增

| ID | 優先級 | 需求 | 現況 | 實作方案 |
|----|--------|------|------|----------|
| GAP-001 | 高 | Sidebar 連動預覽/結果 | 各 Tab 獨立選檔 | 建立 `selectionStore` 全域狀態 |
| GAP-002 | 中 | 報告缺少 Token 統計 | 只有 PHI 統計 | 用字數估算：`len(text) * 1.5` |
| GAP-003 | 高 | 缺少通知系統 | 錯誤無反饋 | 整合 sonner Toast |
| GAP-004 | 中 | 報告缺少 PHI 圓餅圖 | 只有數字列表 | 加入簡單圖表 (recharts) |

### ⚠️ 待改善 (IMP) - 後續迭代

| ID | 優先級 | 說明 | 建議方案 |
|----|--------|------|----------|
| IMP-001 | 中 | 大檔案處理可能 timeout | 加入 chunked upload 支援 |
| IMP-002 | 中 | 檔案狀態與任務狀態同步不完整 | 加強 websocket 或 SSE |
| IMP-003 | 低 | 報告匯出功能未完成 | 實作 PDF/Excel 匯出 |
| IMP-004 | 低 | 缺少批次任務管理 | 加入任務取消/重試功能 |

### 💡 功能缺失 (FEAT) - 未來規劃

| ID | 說明 | 優先級 |
|----|------|--------|
| FEAT-001 | 使用者認證與授權 | 低 (MVP 不需要) |
| FEAT-002 | 多使用者支援 | 低 |
| FEAT-003 | 處理歷史記錄 | 低 |
| FEAT-004 | 自訂 PHI 模式 (Regex) | 中 |
| FEAT-005 | API Rate Limiting | 低 |
| FEAT-006 | 批次下載功能 | 中 |

---

## 未來規劃

### 🎯 Phase 1: MVP 完善 (v2.1) - 當前迭代

**目標**：讓一般文書人員可以順暢使用

| 任務 | 狀態 | 說明 |
|------|------|------|
| 修復 FIX-001~004 | ⬜ 待開始 | 修復已知 bugs |
| 實作 GAP-001 | ⬜ 待開始 | Sidebar 連動預覽/結果 |
| 實作 GAP-002 | ⬜ 待開始 | Token 用量估算 |
| 實作 GAP-003 | ⬜ 待開始 | Toast 通知系統 |
| 新增 selectionStore | ⬜ 待開始 | 統一選取狀態 |
| UX 優化 | ⬜ 待開始 | 依 UX 設計指南調整 |

**預估時間**：2-3 工作天

### Phase 2: 功能增強 (v2.2)
- [ ] 實作 GAP-004: PHI 統計圖表
- [ ] 實作 IMP-003: 報告匯出
- [ ] 實作 FEAT-004: 自訂 PHI 模式
- [ ] Dark Mode 支援

### Phase 3: 企業功能 (v3.0)
- [ ] 實作 FEAT-001, FEAT-002: 使用者系統
- [ ] 實作 FEAT-005: API Rate Limiting
- [ ] 審計日誌
- [ ] 批次下載功能

---

## 附錄

### 支援的檔案格式
| 格式 | 副檔名 | 說明 |
|------|--------|------|
| Excel | .xlsx, .xls | 表格資料 |
| CSV | .csv | 逗號分隔值 |
| JSON | .json | JSON 格式 |
| 純文字 | .txt | 純文字檔案 |

### PHI 類型
| 類型 | 說明 |
|------|------|
| NAME | 個人姓名 |
| DATE | 日期 |
| PHONE | 電話號碼 |
| EMAIL | 電子郵件 |
| ADDRESS | 地址 |
| ID_NUMBER | 身分證/護照號碼 |
| MEDICAL_RECORD | 病歷號 |
| SSN | 社會安全號碼 |
| AGE_OVER_89 | 89歲以上年齡 |
| LOCATION | 地理位置 |
| FAX | 傳真號碼 |
| ACCOUNT | 帳號 |
| LICENSE | 證照號碼 |
| VEHICLE | 車輛識別碼 |
| DEVICE | 設備識別碼 |
| URL | 網址 |
| IP | IP 位址 |
| BIOMETRIC | 生物辨識 |
| PHOTO | 照片 |

### 遮蔽方式
| 方式 | 說明 | 範例 |
|------|------|------|
| mask | 星號遮蔽 | `王小明` → `***` |
| hash | 雜湊處理 | `王小明` → `[NAME_A1B2]` |
| replace | 替換文字 | `王小明` → `[已移除]` |
| delete | 刪除 | `王小明` → (空) |
| keep | 保留 | `王小明` → `王小明` |
