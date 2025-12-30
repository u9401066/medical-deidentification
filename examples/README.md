# Examples | 範例

這個目錄包含 Medical De-identification Toolkit 的使用範例。

## 📚 範例列表

| 範例 | 難度 | 說明 |
|------|------|------|
| [quick_start.py](quick_start.py) | ⭐ | 30 秒快速上手，最簡單的 PHI 識別 |
| [batch_example.py](batch_example.py) | ⭐⭐ | 批次處理 Excel/CSV 檔案 |
| [dspy_optimization.py](dspy_optimization.py) | ⭐⭐⭐ | DSPy 自動 prompt 優化 |

## 🚀 快速開始

```bash
# 1. 安裝依賴
pip install -e .

# 2. 啟動 Ollama
ollama serve

# 3. 下載推薦模型
ollama pull granite4:1b

# 4. 執行範例
python examples/quick_start.py
```

## 🤖 推薦模型

| 模型 | 大小 | F1 Score | 速度 | 推薦場景 |
|------|------|----------|------|----------|
| `granite4:1b` | 3.3GB | 89.4% | ~16s | 🏆 生產環境 |
| `qwen2.5:1.5b` | 986MB | 66.7% | ~4s | ⭐ 開發測試 |
| `llama3.2:1b` | 1.3GB | 55.0% | ~8s | 高召回需求 |

## 📁 舊版範例

舊版範例已移至 `_archived/` 目錄，供參考使用。

## 📖 更多文檔

- [Architecture](../docs/ARCHITECTURE.md) - 系統架構
- [Deployment](../docs/DEPLOYMENT.md) - 部署指南
- [LLM Benchmark](../docs/llm-benchmark-results.md) - 模型效能測試
