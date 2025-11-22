# Package Versions - Working State (2025-11-22)

## 測試狀態
✅ 多語言測試可以啟動並執行
✅ LLM factory 可以處理 dict 和 LLMConfig
✅ PHI Identification Chain 可以初始化

## 核心 LLM 套件

### LangChain 生態系統
- **langchain**: 1.0.8 (從 0.1.0 升級)
- **langchain-core**: 1.1.0 (從 0.1.23 升級)
- **langchain-community**: 0.4.1 (從 0.0.10 升級)
- **langchain-anthropic**: 1.1.0 (新增)
- **langchain-openai**: 1.0.3 (新增)
- **langchain-ollama**: 1.0.0 (新增)
- **langchain-huggingface**: 1.0.1 (新增)
- **langchain-text-splitters**: 1.0.0
- **langchain-classic**: 1.0.0

### LLM 提供商
- **anthropic**: 0.74.1 (從 0.18.1 升級)
- **openai**: 1.109.1
- **ollama**: 0.6.1

## RAG & Embeddings

### 向量存儲
- **chromadb**: 0.4.24
- **faiss-cpu**: 1.13.0

### Embeddings & Transformers
- **sentence-transformers**: 2.7.0
- **transformers**: 4.57.1
- **tokenizers**: 0.22.1
- **huggingface-hub**: 0.36.0

### 深度學習框架 (重要!)
- **torch**: 2.2.0+cpu (降級自 2.9.1，因 Windows DLL 問題)
  - 來源: https://download.pytorch.org/whl/cpu
  - 原因: torch 2.9.1 在 Windows 上有 c10.dll 載入失敗問題
- **numpy**: 1.26.4 (降級自 2.2.6，因 torch 2.2.0 相容性)
  - 原因: torch 2.2.0 需要 numpy < 2.0

## 資料處理

### 核心資料套件
- **pydantic**: 2.12.4
- **pydantic-core**: 2.41.5
- **pydantic-settings**: 2.12.0
- **pandas**: 2.3.3
- **numpy**: 1.26.4 (見上方說明)

### NLP
- **spacy**: 3.8.11
- **spacy-legacy**: 3.0.12
- **spacy-loggers**: 1.0.5

## 工具套件

### 日誌與監控
- **loguru**: 0.7.3
- **rich**: 13.9.4
- **tqdm**: 4.67.1

### 重試與可靠性
- **tenacity**: 8.5.0
- **backoff**: 2.2.1

### CLI
- **typer**: 0.9.4
- **click**: 8.3.1

## 檔案處理
- **openpyxl**: 3.1.5 (Excel)
- **python-docx**: 1.2.0 (Word)
- **PyPDF2**: 3.0.1 (PDF)
- **pdfplumber**: 0.11.8 (PDF)
- **xlrd**: 2.0.2 (舊版 Excel)

## HTTP & 網路
- **httpx**: 0.28.1
- **httpcore**: 1.0.9
- **requests**: 2.32.5
- **aiohttp**: 3.13.2

## 配置 & 環境
- **python-dotenv**: 1.2.1
- **PyYAML**: 6.0.3

## 重要依賴決策

### 1. PyTorch 版本降級 (2.9.1 → 2.2.0+cpu)
**問題**: torch 2.9.1 在 Windows 上有 DLL 載入失敗
```
OSError: [WinError 1114] Error loading "torch\lib\c10.dll"
```

**解決方案**:
```bash
pip uninstall torch -y
pip install torch==2.2.0 --index-url https://download.pytorch.org/whl/cpu
```

### 2. NumPy 版本降級 (2.2.6 → 1.26.4)
**問題**: torch 2.2.0 與 numpy 2.x 不相容
```
RuntimeWarning: A module that was compiled using NumPy 1.x cannot be run in NumPy 2.2.6
```

**解決方案**:
```bash
pip install "numpy<2"
```

### 3. LangChain 生態系統大升級 (0.1.x → 1.0.x)
**問題**: langchain 0.1.0 與 langchain-core 1.1.0 不相容
```
ImportError: cannot import name 'InvalidToolCall' from 'langchain_core.messages'
```

**解決方案**: 升級整個 langchain 生態系統到 1.0+
- langchain: ^0.3.0
- langchain-core: ^0.3.0
- langchain-community: ^0.3.0
- 新增: langchain-anthropic, langchain-openai, langchain-ollama, langchain-huggingface

### 4. Anthropic SDK 升級 (0.18.1 → 0.74.1)
**原因**: 配合新版 langchain-anthropic 需求

## 已知問題與限制

### 1. Invalid Distribution Warning
```
WARNING: Ignoring invalid distribution -orch
```
這是 torch 卸載後的殘留，不影響運作。

清理方式:
```bash
rm -r .venv/lib/site-packages/~orch*
```

### 2. Ollama Native Structured Output 效能
在 `phi_identification_chain.py:454` 使用 ollama native client 的 structured output 可能較慢。
考慮切換到 LangChain wrapper 或優化 chunk 大小。

## pyproject.toml 需要更新的版本約束

當前 pyproject.toml 的問題:
1. ❌ langchain 版本約束 `^0.3.0` 實際安裝 1.0.8
2. ❌ 缺少 torch 和 numpy 的特定版本約束
3. ❌ langchain-anthropic 約束 `^0.3.0` 實際安裝 1.1.0

建議更新:
```toml
[tool.poetry.dependencies]
# 深度學習框架 - 需特定版本以避免 Windows DLL 問題
torch = "2.2.0"  # 固定版本，從 PyTorch CPU repo 安裝
numpy = "^1.26.0,<2.0"  # 與 torch 2.2.0 相容

# LangChain 生態系統 - 全面升級到 1.0+
langchain = "^1.0.0"
langchain-core = "^1.0.0"
langchain-community = "^0.4.0"
langchain-anthropic = "^1.0.0"
langchain-openai = "^1.0.0"
langchain-ollama = "^1.0.0"
langchain-huggingface = "^1.0.0"

# LLM 提供商
anthropic = "^0.74.0"
```
