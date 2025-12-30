# Active Context

## Current Goals

- ## 當前工作焦點 (2025-12-30)
- ### Python 3.12 升級完成
- - 使用 `uv python install 3.12` 安裝 Python 3.12.12
- - 重建虛擬環境 `uv venv --python 3.12`
- - 所有依賴已通過 `uv sync` 安裝
- ### 核心技術棧
- - **Python**: 3.12.12
- - **Package Manager**: uv 0.9.17 (唯一)
- - **LLM**: granite4:1b (131K context, 1.6B params)
- - **LangChain**: with_structured_output(method="json_schema")
- - **Ollama**: systemd 服務, keep_alive=30m
- ### 關鍵發現
- 1. `with_structured_output` 使用 `function_calling` 方法會卡住
- 2. 改用 `method="json_schema"` 解決，使用 Ollama 原生 structured output API
- 3. LLM 推理是瓶頸，Python 版本對效能影響有限
- 4. 單文檔 PHI 識別 ~35s，並行處理可用但受 Ollama 單實例限制
- ### 新增檔案
- - `async_processors.py`: Python 3.12 異步 PHI 識別 (TaskGroup)
- - `docs/python312-optimization.md`: 優化指南
- ### 下一步
- - 部署 GPU 加速 Ollama
- - 測試更大模型 (8B+)
- - 優化 Prompt 長度

## Current Session Focus (Dec 30, 2025)

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