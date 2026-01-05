# Python 3.12 優化指南

## 已完成的升級

### 1. Python 版本升級
```bash
# 使用 uv 安裝 Python 3.12
uv python install 3.12

# 建立新虛擬環境
uv venv --python 3.12

# 安裝依賴
uv sync
```

### 2. pyproject.toml 更新
- `requires-python = ">=3.12"`
- `target-version = "py312"` (ruff)
- `python_version = "3.12"` (mypy)

## Python 3.12 效能改進

### 自動生效的優化
1. **CPython 解釋器更快** (~5% 整體提升)
2. **PEP 709 內聯 Comprehension** - 列表推導式自動優化
3. **更快的 f-string** - 格式化字串效能提升
4. **更好的錯誤訊息** - 調試更容易

### 新增的異步處理模組
`core/infrastructure/rag/chains/async_processors.py`

```python
# 使用方式
import asyncio
from langchain_ollama import ChatOllama
from core.infrastructure.rag.chains.async_processors import (
    identify_phi_async,
    identify_phi_sync
)

llm = ChatOllama(model='granite4:1b', keep_alive='30m')

# 異步版本
result = asyncio.run(identify_phi_async(llm, text, language='zh-tw'))

# 同步版本
result = identify_phi_sync(llm, text, language='zh-tw')
```

### Python 3.11+ 功能
- **TaskGroup** - 結構化並發，更好的錯誤處理
- **slots=True in dataclass** - 記憶體效率更高
- **asyncio 改進** - 更快的事件循環

## 效能瓶頸分析

### 目前瓶頸
| 瓶頸 | 原因 | 解決方案 |
|------|------|----------|
| LLM 推理速度 | granite4:1b 是小模型 | 換用 GPU 或更大模型 |
| 單一 Ollama 實例 | 並行請求仍需排隊 | 部署多個 Ollama 實例 |
| Prompt 長度 | 每次都發送完整 prompt | 使用更短的 prompt |

### 可能的進一步優化

1. **批次處理 API** (Ollama 支援)
```python
# 未來可以使用 Ollama 的 batch API
results = llm.batch([doc1, doc2, doc3])
```

2. **使用 GPU**
```bash
# 如果有 NVIDIA GPU
ollama run granite4:1b --gpu
```

3. **模型量化**
```bash
# 使用更小的量化版本
ollama pull granite4:1b:q4_0
```

4. **更大的模型 (如果有足夠資源)**
```bash
ollama pull granite4:8b
```

## uv 常用命令

```bash
# 安裝 Python 版本
uv python install 3.12

# 建立虛擬環境
uv venv --python 3.12

# 安裝依賴
uv sync

# 安裝開發依賴
uv sync --all-groups

# 新增依賴
uv add langchain-ollama

# 移除依賴
uv remove package-name

# 查看已安裝套件
uv pip list
```

## 測試結果

| 測試 | Python 3.10 | Python 3.12 | 改善 |
|------|-------------|-------------|------|
| 單文檔 PHI 識別 | ~35s | ~35s | ~0% (LLM 限制) |
| 3 文檔順序處理 | ~163s | ~163s | ~0% (LLM 限制) |
| 2 文檔並行處理 | N/A | ~109s | 可用 |

**結論**: Python 3.12 的效能改進主要在 CPU 密集型任務。對於 LLM 推理任務，瓶頸在模型本身，Python 版本影響有限。

## 建議的下一步

1. ✅ 已升級到 Python 3.12
2. ✅ 已建立異步處理模組
3. ⬜ 部署 GPU 加速 Ollama
4. ⬜ 測試更大的模型 (8B+)
5. ⬜ 優化 Prompt 長度
