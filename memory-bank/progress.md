# Progress (Updated: 2025-12-30)

## Done

- Python 3.12 升級完成 (uv python install 3.12)
- pyproject.toml 更新 requires-python>=3.12
- LangChain with_structured_output 使用 method="json_schema" (修復卡住問題)
- 建立 async_processors.py - Python 3.12 異步處理模組 (TaskGroup)
- 建立 python312-optimization.md 優化文檔
- 修復 id_validator_tool.py SyntaxWarning (raw string)
- 更新 LLMConfig 新增 keep_alive 和 num_ctx 參數
- PHI 識別測試成功 (~35s 單文檔)
- README.md 更新 - Python 3.12+ badge, uv 安裝方式

## Doing

- 準備 Git commit 和 push

## Next

- 測試 async_processors 在生產環境
- GPU 加速 Ollama 部署
- 測試更大模型 (8B+)
- 優化 Prompt 長度
