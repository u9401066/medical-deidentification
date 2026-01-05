# 🚀 Deployment Guide | 部署指南

## Overview | 概述

This guide covers installation, configuration, and deployment of the Medical De-identification Toolkit.

本指南涵蓋醫療去識別化工具套件的安裝、配置和部署。

---

## 📋 Prerequisites | 前置需求

### System Requirements | 系統需求

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| **OS** | Windows 10, macOS 10.15, Ubuntu 20.04 | Latest LTS |
| **Python** | 3.11 | 3.11+ |
| **RAM** | 8 GB | 16 GB |
| **Storage** | 5 GB | 20 GB (with models) |
| **GPU** | Not required | NVIDIA RTX 3060+ (for local LLM) |

### Software Dependencies | 軟體依賴

- Python 3.11+
- pip or Poetry (package manager)
- Git (for source installation)
- Ollama (for local LLM) - optional

---

## 📦 Installation Methods | 安裝方式

### Method 1: pip Install (Recommended for Users)

```bash
# Install from PyPI
pip install medical-deidentification

# Verify installation
python -c "import core; print('Success!')"
```

### Method 2: From Source (Recommended for Development)

```bash
# Clone repository
git clone https://github.com/u9401066/medical-deidentification.git
cd medical-deidentification

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# Install in editable mode
pip install -e .
```

### Method 3: Poetry (Recommended for Contributors)

```bash
# Clone repository
git clone https://github.com/u9401066/medical-deidentification.git
cd medical-deidentification

# Install Poetry (if not installed)
pip install poetry

# Install dependencies
poetry install

# Activate virtual environment
poetry shell
```

---

## ⚙️ Configuration | 配置

### Environment Variables | 環境變數

Create a `.env` file in the project root:

```bash
# .env

# ===== LLM API Keys =====
# OpenAI (for GPT-4o, GPT-4o-mini)
OPENAI_API_KEY=sk-your-api-key-here

# Anthropic (for Claude 3)
ANTHROPIC_API_KEY=sk-ant-your-api-key-here

# ===== Ollama Configuration =====
# Ollama server URL (default: http://localhost:11434)
OLLAMA_BASE_URL=http://localhost:11434

# ===== Logging =====
# Log level: DEBUG, INFO, WARNING, ERROR
LOG_LEVEL=INFO
LOG_DIR=./logs

# ===== Processing =====
# Default language for PHI detection
DEFAULT_LANGUAGE=zh-TW

# Maximum tokens for LLM response
MAX_TOKENS=2048
```

### LLM Configuration | LLM 配置

```python
from core.infrastructure.llm import LLMConfig, LLMPresets

# Option 1: Use presets
config = LLMPresets.local_minimind()      # Ultra-light local
config = LLMPresets.local_qwen()          # Balanced local
config = LLMPresets.gpt_4o()              # Best quality cloud

# Option 2: Custom configuration
config = LLMConfig(
    provider="ollama",                    # openai, anthropic, ollama
    model_name="qwen2.5:7b",
    temperature=0.0,                      # 0.0 for deterministic
    max_tokens=2048,
    timeout=120,                          # seconds
    use_gpu=True,                         # Enable GPU acceleration
    num_gpu=1                             # Number of GPUs
)
```

---

## 🤖 LLM Setup | LLM 設置

### Option A: Cloud LLM (OpenAI/Anthropic)

1. **Get API Key**:
   - OpenAI: https://platform.openai.com/api-keys
   - Anthropic: https://console.anthropic.com/

2. **Set Environment Variable**:
   ```bash
   # Windows
   set OPENAI_API_KEY=sk-your-key-here
   
   # macOS/Linux
   export OPENAI_API_KEY=sk-your-key-here
   ```

3. **Test Connection**:
   ```python
   from core.infrastructure.llm import LLMPresets, create_llm
   
   llm = create_llm(LLMPresets.gpt_4o())
   response = llm.invoke("Hello, world!")
   print(response)
   ```

### Option B: Local LLM (Ollama)

1. **Install Ollama**:
   - Download from https://ollama.ai/download
   - Run installer
   - Ollama starts automatically as a service

2. **Pull Models**:
   ```bash
   # Ultra-light model (testing/development)
   ollama pull jingyaogong/minimind2
   
   # Balanced model (recommended for production)
   ollama pull qwen2.5:7b
   
   # Alternative options
   ollama pull llama3.1:8b
   ollama pull mistral:7b
   ```

3. **Verify Setup**:
   ```bash
   # Check Ollama status
   ollama list
   
   # Test model
   ollama run qwen2.5:7b "What is PHI in healthcare?"
   ```

4. **Test in Python**:
   ```python
   from core.infrastructure.llm import LLMPresets, create_llm
   
   llm = create_llm(LLMPresets.local_qwen())
   response = llm.invoke("Identify PHI in: Patient John Doe")
   print(response)
   ```

> 📖 See [Ollama Setup Guide](./ollama-setup.md) for detailed instructions.

---

## 🏃 Running the Application | 運行應用

### Basic Usage | 基本使用

```python
from core.application.processing import DeidentificationEngine
from core.infrastructure.llm import LLMPresets, create_llm

# Initialize
llm = create_llm(LLMPresets.local_minimind())
engine = DeidentificationEngine(llm=llm)

# Process text
text = "病患姓名：王大明，身分證字號：A123456789"
result = engine.process(text)

print(result.deidentified_text)
print(f"Found {len(result.entities)} PHI entities")
```

### Batch Processing | 批次處理

```python
from core.application.processing import (
    BatchPHIProcessor,
    BatchProcessingConfig
)

# Configure
config = BatchProcessingConfig(
    max_rows=100,
    language="zh-TW",
    skip_empty_rows=True
)

# Process Excel file
processor = BatchPHIProcessor(phi_chain, config)
result = processor.process_excel_file("data/patients.xlsx")

# Save results
result.to_excel("output/phi_results.xlsx")
```

---

## 📁 Directory Structure | 目錄結構

Recommended project structure for deployment:

```
your-project/
├── .env                      # Environment variables (DO NOT commit!)
├── data/
│   ├── raw/                  # Input files (NEVER commit real PHI!)
│   ├── output/
│   │   ├── results/          # Processing results
│   │   └── reports/          # Generated reports
│   └── regulations/          # Regulation documents for RAG
├── logs/                     # Application logs
├── scripts/                  # Custom scripts
└── config/                   # Configuration files
```

### Data Directory Setup

```bash
# Create directories
mkdir -p data/raw data/output/results data/output/reports data/regulations logs
```

---

## 🔧 Troubleshooting | 故障排除

### Common Issues | 常見問題

#### 1. Ollama Connection Error

```
Error: Failed to connect to Ollama at http://localhost:11434
```

**Solution**:
```bash
# Check if Ollama is running
ollama list

# If not running, start it
ollama serve
```

#### 2. Model Not Found

```
Error: model "qwen2.5:7b" not found
```

**Solution**:
```bash
# Pull the model
ollama pull qwen2.5:7b
```

#### 3. GPU Not Detected

```
Warning: CUDA not available, using CPU
```

**Solution**:
1. Install NVIDIA drivers
2. Install CUDA Toolkit
3. Verify with `nvidia-smi`
4. Reinstall PyTorch with CUDA support

#### 4. Memory Error

```
Error: Out of memory
```

**Solution**:
- Use smaller model (e.g., MiniMind instead of Qwen 7B)
- Reduce `max_tokens`
- Process smaller batches
- Enable `use_gpu=True` if GPU available

#### 5. API Key Error

```
Error: OpenAI API key not found
```

**Solution**:
```bash
# Set environment variable
export OPENAI_API_KEY=sk-your-key-here

# Or use .env file
echo "OPENAI_API_KEY=sk-your-key-here" >> .env
```

---

## 📊 Performance Optimization | 效能優化

### Tips for Better Performance

1. **Use GPU** when available:
   ```python
   config = LLMConfig(provider="ollama", model_name="qwen2.5:7b", use_gpu=True)
   ```

2. **Choose appropriate model**:
   - Testing: MiniMind (fast, lightweight)
   - Production: Qwen 2.5 7B (balanced)
   - High accuracy: GPT-4o (best quality)

3. **Batch processing** for multiple documents:
   ```python
   processor.process_excel_file("data.xlsx")  # More efficient than row-by-row
   ```

4. **Adjust timeout** for large documents:
   ```python
   config = LLMConfig(timeout=180)  # 3 minutes
   ```

---

## 🔒 Security Best Practices | 安全最佳實踐

1. **Never commit**:
   - `.env` files with API keys
   - Real PHI data
   - Test results containing PHI

2. **Use `.gitignore`**:
   ```gitignore
   .env
   data/raw/
   data/output/
   logs/
   *.xlsx
   *.csv
   ```

3. **Rotate API keys** regularly

4. **Audit logs** periodically

5. **Use encryption** for sensitive outputs

---

## 📞 Support | 支援

- **GitHub Issues**: [Report bugs](https://github.com/u9401066/medical-deidentification/issues)
- **Documentation**: [Full docs](./README.md)
- **Discussions**: [Community forum](https://github.com/u9401066/medical-deidentification/discussions)

---

**[← Back to README](../README.md)**
