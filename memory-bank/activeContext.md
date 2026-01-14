# Active Context

## Current Goals

- ✅ **Frontend DDD 重構完成** - 採用領域驅動設計重構 web/frontend
- ✅ 前端自動測試套件 (Vitest + React Testing Library)
- ✅ Log 輸出可讀取 (終端機 + Agent 可追蹤)

## Current Session Focus (Jan 14, 2026)

### Frontend DDD Architecture 完成 ✅

#### 實際架構 (已建立)
```
web/frontend/src/
├── domain/              # 領域層 ✅
│   ├── entities/        # Task.ts, File.ts, Report.ts
│   ├── value-objects/   # PHIConfig.ts, PHIType.ts
│   └── index.ts
├── application/         # 應用層 ✅
│   ├── hooks/           # useTasks.ts, useFiles.ts
│   └── index.ts
├── infrastructure/      # 基礎設施層 ✅
│   ├── api/             # client.ts, tasks.ts, files.ts
│   ├── logging/         # logger.ts (window.__FRONTEND_LOGS__)
│   └── index.ts
├── presentation/        # 呈現層 ✅
│   └── components/      # 複製自 components/
├── shared/              # 共享工具 ✅
│   ├── types/
│   ├── utils/
│   └── constants/
└── lib/                 # 向後兼容 ✅
    └── utils.ts         # cn, formatBytes, formatDate
```

#### 測試結果
- **68 個測試全部通過**
- 覆蓋率: domain=100%, infrastructure=89%, lib=90%

#### Logger 使用方式 (Agent 可讀取)
```typescript
import { logger, getAllLogs } from '@/infrastructure/logging';

// 記錄日誌
logger.info('Task created', { taskId: '123' });

// Agent 讀取日誌
console.table(window.__FRONTEND_LOGS__);  // DevTools 可見
const logs = getAllLogs();
```

#### 待辦事項 (Next Steps)
- [ ] 遷移現有元件到使用新 DDD imports
- [ ] 刪除舊的 api/ 和 components/ 目錄
- [ ] 提升 Presentation 層測試覆蓋率到 70%

---

## Previous Session (Dec 30, 2025)

### Lightweight LLM Benchmark Completed ✅
完成 CPU 環境輕量 LLM 效能評測：

| 模型 | F1 Score | 速度 | 推薦 |
|------|----------|------|------|
| **granite4:1b** | 89.4% | ~16s | 🏆 最佳品質 |
| **qwen2.5:1.5b** | 66.7% | ~4s | ⭐ 最佳平衡 |
| llama3.2:1b | 55.0% | ~8s | 可用 |
| smollm2:360m | 0% | ~4s | ❌ 太小 |

### Changes Made
1. **預設模型更新為 `granite4:1b`**
   - `phi_module.py` 已更新
   - LIGHTWEIGHT_MODELS 字典包含 benchmark 數據
2. **新增 Benchmark 腳本**: `scripts/benchmark_lightweight_llms.py`
3. **新增文件**: `docs/llm-benchmark-results.md`

### Previous Issue (Resolved)
- Ollama `with_structured_output` 慢的問題
- 解決方案：使用 `granite4:1b` 替代小模型，JSON 輸出穩定

### Next Steps
1. 使用 `granite4:1b` 進行完整的 PHI 去識別化測試
2. 考慮 DSPy 優化來進一步提升 F1 Score
3. 可選：測試 GPU 環境下的效能

## Current Blockers

- None ✅