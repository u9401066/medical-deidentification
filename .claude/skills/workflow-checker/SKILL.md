# Workflow Checker Skill

## 用途

自動排查 PHI 去識別化工具的完整使用流程是否正常。
對應使用說明頁面 (Guide.tsx) 的 8 個步驟，逐一驗證。

## 觸發詞

- `workflow`, `流程`, `排查`, `check`, `驗證`, `健康檢查`, `功能測試`
- `使用流程`, `流程排查`, `整合測試`

## 工具

主要腳本: `scripts/check_workflow.py`

## 使用方式

### 快速驗證（跳過 LLM 處理）

```bash
# 只驗證 API 可用性，不執行去識別化（速度快，約 5 秒）
.venv/bin/python scripts/check_workflow.py --skip-process

# 指定後端 URL
.venv/bin/python scripts/check_workflow.py --url http://localhost:8001 --skip-process
```

### 完整驗證（含 LLM 去識別化）

```bash
# 執行完整流程（含 LLM，需要 1-3 分鐘）
.venv/bin/python scripts/check_workflow.py --url http://localhost:8001

# 詳細模式（顯示 API 回應內容）
.venv/bin/python scripts/check_workflow.py --url http://localhost:8001 --verbose
```

### 保留測試資料（除錯用）

```bash
# 跳過清理，保留上傳的測試檔案
.venv/bin/python scripts/check_workflow.py --skip-cleanup --verbose
```

## 步驟對應

| 腳本步驟 | 說明 | API |
|---------|------|-----|
| 0 | Server 可連線 | GET /docs |
| 1 | LLM 連線 + PHI 引擎 | GET /api/health |
| 2 | 上傳測試 CSV | POST /api/upload |
| 3 | 預覽上傳資料 | GET /api/preview/{file_id} |
| 4 | PHI 設定讀取 | GET /api/settings/phi-types + /config |
| 5 | 執行去識別化 | POST /api/process + 輪詢 GET /api/tasks/{id} |
| 6 | 查看結果 | GET /api/results + /results/{task_id} |
| 7 | 查看報告 | GET /api/reports + /reports/{task_id} |
| 8 | 下載去識別化資料 | GET /api/download/{task_id} |

## 常見問題排查

### 後端無法啟動？

```bash
# 確認 config.py 有 TASKS_DB_FILE
grep TASKS_DB_FILE web/backend/config.py

# 手動測試啟動
cd web/backend && .venv/bin/uvicorn main:app --port 8001

# 使用啟動腳本
./scripts/start-web.sh
```

### LLM 離線？

```bash
# 確認 Ollama URL
cat web/backend/config.py | grep OLLAMA

# 直接測試 Ollama
curl http://192.168.1.2:30133/api/tags

# 使用環境變數覆蓋
OLLAMA_BASE_URL=http://localhost:11434 .venv/bin/python scripts/check_workflow.py --url http://localhost:8001
```

### 上傳失敗 (405)？

確認使用 `POST /api/upload`（舊路徑 `/api/files/upload` 已廢除）。

### 去識別化 timeout？

LLM 呼叫需要 30-60 秒。腳本預設等待 120 秒，若仍超時可用 `--skip-process` 先跳過，
然後在 UI 手動驗證去識別化功能。

## 自動化排查流程（Agent 執行步驟）

當使用者說「排查流程」或「check workflow」時，執行以下步驟：

1. **確認後端是否運行**
   ```bash
   curl -s http://localhost:8001/api/health 2>/dev/null || echo "backend not running"
   ```

2. **若後端未啟動，在背景啟動**
   ```bash
   cd web/backend && .venv/bin/uvicorn main:app --port 8001 --log-level error &
   sleep 3
   ```

3. **執行快速驗證腳本**
   ```bash
   .venv/bin/python scripts/check_workflow.py --url http://localhost:8001 --skip-process --verbose
   ```

4. **分析結果**
   - ✓ 全部通過：API 功能正常，提示用戶可以到 http://localhost:5173 使用 UI
   - ✗ 上傳失敗：檢查 POST /api/upload 端點
   - ✗ 設定 404：確認 /api/settings/phi-types 端點存在
   - ✗ LLM 離線：提示用戶連線 Ollama

5. **若需要完整驗證（含 LLM）**
   ```bash
   .venv/bin/python scripts/check_workflow.py --url http://localhost:8001 --verbose
   ```

## 前端 E2E 測試

UI 流程測試使用 Playwright（需要前端運行中）：

```bash
cd web/frontend
npx playwright test e2e/app.spec.ts  # 頁面佈局測試
npx playwright test e2e/           # 全部 E2E 測試
```

## 整合 Git Pre-commit

可在 `.git/hooks/pre-commit` 中加入快速排查（`--skip-process` 版本不影響速度）：

```bash
# 在 pre-commit hook 的 Python 檢查後加入
if git diff --cached --name-only | grep -q "^web/backend"; then
    echo "🔍 排查後端 API..."
    if command -v curl &>/dev/null; then
        if curl -s http://localhost:8001/api/health | grep -q '"status":"healthy"'; then
            .venv/bin/python scripts/check_workflow.py --url http://localhost:8001 --skip-process 2>&1 | tail -5
        fi
    fi
fi
```
