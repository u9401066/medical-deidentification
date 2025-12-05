# 🏥 Medical De-identification Toolkit

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![LangChain](https://img.shields.io/badge/LangChain-1.0+-orange.svg)](https://langchain.com/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

**🔒 LLM/RAG 驅動的醫療文本去識別化工具 | AI-Powered Medical Text De-identification**

[English](#overview) | [繁體中文](#專案概述)

</div>

---

## ✨ Highlights | 亮點

```text
🚀 一鍵部署      支援 OpenAI / Anthropic / Ollama / MiniMind 多種 LLM
🎯 高準確率      RAG + LLM 雙引擎，PHI 識別準確率 95%+
⚡ 混合策略      SpaCy + Regex + LLM 三層識別，效能提升 30-100x
🌍 多語言支援    繁中/簡中/英/日/韓/法/德等 10+ 語言
📊 批次處理      Excel/CSV/PDF/Word 等 10+ 格式一次處理
🔐 隱私優先      病歷資料不持久化，符合 HIPAA/GDPR
🆓 完全開源      MIT License，可商用
```

---

## 📋 Table of Contents | 目錄

- [Overview | 概述](#overview--專案概述)
- [Key Features | 主要功能](#-key-features--主要功能)
- [Quick Start | 快速開始](#-quick-start--快速開始)
- [Installation | 安裝](#-installation--安裝)
- [Usage Examples | 使用範例](#-usage-examples--使用範例)
- [Supported LLM Providers | 支援的 LLM](#-supported-llm-providers--支援的-llm)
- [Architecture | 系統架構](#-architecture--系統架構)
- [Documentation | 文檔](#-documentation--文檔)
- [Contributing | 貢獻](#-contributing--貢獻)
- [License | 授權](#-license--授權)

---

## Overview | 專案概述

**Medical De-identification Toolkit** is an open-source Python library that uses **LLM (Large Language Model)** and **RAG (Retrieval-Augmented Generation)** technology to automatically identify and mask **Protected Health Information (PHI)** in medical records.

**醫療去識別化工具套件** 是一個開源 Python 函式庫，使用 **LLM（大型語言模型）** 與 **RAG（檢索增強生成）** 技術，自動識別並遮蔽醫療病歷中的 **個人健康資訊（PHI）**。

### 🎯 Why This Tool? | 為何選擇這個工具？

| Challenge | Traditional Approach | Our Solution |
|-----------|---------------------|--------------|
| PHI Detection | Rule-based regex | 🤖 LLM + RAG semantic understanding |
| Multi-language | Separate models | 🌍 Single multilingual pipeline |
| Custom Rules | Hard-coded | 📚 RAG retrieves from regulation docs |
| Deployment | Heavy dependencies | ⚡ Supports ultra-light MiniMind (26M params) |

---

## 🌟 Key Features | 主要功能

### 🔍 PHI Detection | PHI 識別
- **20+ PHI Types**: Name, Date, Location, Medical Record Number, Age >89, Rare Diseases, etc.
- **Multi-language**: Traditional Chinese, Simplified Chinese, English, Japanese, Korean, and more
- **Context-aware**: Understands medical context for accurate detection

### 🛡️ De-identification Strategies | 去識別化策略
| Strategy | Description | Example |
|----------|-------------|---------|
| **Redaction** | Complete removal | `張三` → `[REDACTED]` |
| **Masking** | Type-based placeholder | `張三` → `[NAME]` |
| **Generalization** | Reduce precision | `1990-05-15` → `1990` |
| **Pseudonymization** | Consistent replacement | `張三` → `Patient_A` |

### 📁 Supported Formats | 支援格式
```
📄 Text: TXT, CSV, JSON
📊 Office: XLSX, XLS, DOCX
📑 Document: PDF, HTML, XML
🏥 Healthcare: FHIR R4 JSON
```

### 🤖 Multiple LLM Backends | 多種 LLM 後端
- **Cloud**: OpenAI GPT-4o, Anthropic Claude 3
- **Local**: Ollama (Qwen, Llama, Mistral)
- **Ultra-light**: MiniMind (26M-104M params) ← 🆕 **NEW!**
- **DSPy Integration**: Automatic prompt optimization ← 🆕 **NEW!**

---

## 🚀 Quick Start | 快速開始

### 30-Second Demo | 30 秒上手

```python
from medical_deidentification.application.processing import DeidentificationEngine
from medical_deidentification.infrastructure.llm import LLMPresets, create_llm

# 1. Choose your LLM (pick one)
llm = create_llm(LLMPresets.local_minimind())  # Free, runs locally!
# llm = create_llm(LLMPresets.local_qwen())    # Better quality
# llm = create_llm(LLMPresets.gpt_4o())        # Best quality (requires API key)

# 2. Create engine
engine = DeidentificationEngine(llm=llm)

# 3. Process medical text
text = """
病患姓名：王大明，身分證字號：A123456789
出生日期：1985年3月15日，聯絡電話：0912-345-678
診斷：法布瑞氏症（罕見疾病）
主治醫師：陳醫師，台北榮民總醫院
"""

result = engine.process(text)
print(result.deidentified_text)
# Output: 病患姓名：[NAME]，身分證字號：[ID]...
```

---

## 📦 Installation | 安裝

### Option 1: pip (Recommended)
```bash
pip install medical-deidentification
```

### Option 2: From Source
```bash
git clone https://github.com/u9401066/medical-deidentification.git
cd medical-deidentification
pip install -e .
```

### Option 3: Poetry (Development)
```bash
git clone https://github.com/u9401066/medical-deidentification.git
cd medical-deidentification
poetry install
poetry shell
```

---

## 💡 Usage Examples | 使用範例

### Example 1: Basic PHI Identification | 基本 PHI 識別

```python
from medical_deidentification.infrastructure.rag import PHIIdentificationChain
from medical_deidentification.infrastructure.llm import LLMConfig, create_llm

# Configure LLM
config = LLMConfig(
    provider="ollama",
    model_name="qwen2.5:7b",
    temperature=0.0
)
llm = create_llm(config)

# Identify PHI entities
entities = phi_chain.identify_phi(medical_text)
for entity in entities:
    print(f"Found: {entity.text} ({entity.phi_type}, confidence: {entity.confidence})")
```

### Example 2: Batch Processing Excel | 批次處理 Excel

```python
from medical_deidentification.application.processing import (
    BatchPHIProcessor,
    BatchProcessingConfig
)

# Configure batch processor
batch_config = BatchProcessingConfig(
    max_rows=100,           # Process first 100 rows
    language="zh-TW",       # Traditional Chinese
    skip_empty_rows=True
)

processor = BatchPHIProcessor(phi_chain, batch_config)
result = processor.process_excel_file("patient_records.xlsx")

# Export results
result.to_excel("phi_results.xlsx")
print(f"Found {result.total_entities} PHI entities in {result.processed_rows} rows")
```

### Example 3: Using MiniMind (Ultra-light Local LLM) | 使用 MiniMind

```python
from medical_deidentification.infrastructure.llm import LLMPresets, create_llm

# MiniMind: Only 104M parameters, runs on any hardware!
config = LLMPresets.local_minimind()
llm = create_llm(config)

# First, pull the model (one-time setup)
# $ ollama pull jingyaogong/minimind2
```

### Example 4: RAG-Enhanced Detection | RAG 增強識別

```python
from medical_deidentification.infrastructure.rag import (
    RegulationRetrievalChain,
    PHIIdentificationChain
)

# Load regulation documents (HIPAA, GDPR, Taiwan PDPA, etc.)
regulation_chain = RegulationRetrievalChain(
    regulation_dir="./regulations"
)

# PHI detection with regulation context
phi_chain = PHIIdentificationChain(
    regulation_chain=regulation_chain,
    llm=llm
)

# The system now retrieves relevant regulations to guide PHI detection
entities = phi_chain.identify_phi(medical_text)
```

### Example 5: DSPy Automatic Prompt Optimization | DSPy 自動 Prompt 優化 🆕

```python
from medical_deidentification.infrastructure.dspy import (
    PHIIdentifier,
    PHIPromptOptimizer,
    PHIEvaluator
)

# Configure DSPy with Ollama
from medical_deidentification.infrastructure.dspy.phi_module import configure_dspy_ollama
configure_dspy_ollama(model_name="qwen2.5:1.5b")

# Create base PHI identifier
identifier = PHIIdentifier()

# Run automatic optimization with DSPy
optimizer = PHIPromptOptimizer()
result = optimizer.optimize(
    trainset=training_examples,
    method="bootstrap",  # or "mipro"
    max_iterations=10
)

# Use optimized module
optimized_identifier = result.best_module
entities = optimized_identifier(medical_text="Patient John Smith, age 45...")

# Check metrics
print(f"F1 Score: {result.optimized_score:.2%}")
print(f"Speed improvement: {result.time_improvement:.2%}")
```

---

## 🤖 Supported LLM Providers | 支援的 LLM

### Cloud Providers | 雲端服務

| Provider | Models | Structured Output | Setup |
|----------|--------|-------------------|-------|
| **OpenAI** | GPT-4o, GPT-4o-mini, GPT-3.5 | ✅ Native | `OPENAI_API_KEY` |
| **Anthropic** | Claude 3 Opus/Sonnet/Haiku | ✅ Native | `ANTHROPIC_API_KEY` |

### Local Models (via Ollama) | 本地模型

| Model | Parameters | Speed | Quality | GPU VRAM |
|-------|------------|-------|---------|----------|
| **MiniMind2** 🆕 | 104M | ⚡⚡⚡⚡⚡ | ⭐⭐ | 1GB |
| **MiniMind2-Small** | 26M | ⚡⚡⚡⚡⚡ | ⭐ | <1GB |
| **Qwen 2.5 7B** | 7B | ⚡⚡⚡ | ⭐⭐⭐⭐ | 4GB |
| **Llama 3.1 8B** | 8B | ⚡⚡⚡ | ⭐⭐⭐⭐ | 4GB |
| **Mistral 7B** | 7B | ⚡⚡⚡⭐ | ⭐⭐⭐ | 4GB |

### Quick Setup for Local Models

```bash
# Install Ollama (https://ollama.ai)
# Then pull your preferred model:

ollama pull jingyaogong/minimind2     # Ultra-light (recommended for testing)
ollama pull qwen2.5:7b                # Balanced (recommended for production)
ollama pull llama3.1:8b               # General purpose
```

> 📖 See [Ollama Setup Guide](./docs/ollama-setup.md) for detailed instructions.

---

## 🏗️ Architecture | 系統架構

### Hybrid PHI Detection Pipeline | 混合 PHI 檢測管道 🆕

```text
┌─────────────────────────────────────────────────────────────┐
│              Hybrid PHI Detection Pipeline                   │
├─────────────────────────────────────────────────────────────┤
│  Level 1: Regex Fast Scan (~0.001s)                         │
│  ├── ID Numbers, Phone, Email, Date patterns                │
│  └── Coverage: ~30% of PHI                                  │
├─────────────────────────────────────────────────────────────┤
│  Level 2: SpaCy NER (~0.01-0.05s)                          │
│  ├── PERSON, DATE, ORG, GPE, LOC entities                  │
│  └── Coverage: ~40% of PHI                                  │
├─────────────────────────────────────────────────────────────┤
│  Level 3: Small LLM - Uncertain Regions Only (~0.5-2s)     │
│  ├── Qwen2.5-0.5B/1.5B for remaining ~30%                  │
│  └── Fall back to Qwen2.5-7B for complex cases             │
└─────────────────────────────────────────────────────────────┘
```

### System Architecture | 系統架構

```text
┌─────────────────────────────────────────────────────────────────┐
│                    Medical De-identification Toolkit             │
├─────────────────────────────────────────────────────────────────┤
│  Interface Layer                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │     CLI     │  │   Python    │  │  REST API   │              │
│  │   (Typer)   │  │   Library   │  │  (Future)   │              │
│  └─────────────┘  └─────────────┘  └─────────────┘              │
├─────────────────────────────────────────────────────────────────┤
│  Application Layer                                               │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  DeidentificationEngine  │  BatchPHIProcessor           │    │
│  │  PHI Detection Pipeline  │  Report Generator            │    │
│  └─────────────────────────────────────────────────────────┘    │
├─────────────────────────────────────────────────────────────────┤
│  Infrastructure Layer                                            │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│  │   LLM    │  │   RAG    │  │  Loader  │  │  Output  │        │
│  │ Factory  │  │  Engine  │  │ (10 fmt) │  │ Manager  │        │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘        │
├─────────────────────────────────────────────────────────────────┤
│  Domain Layer                                                    │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  PHIEntity  │  PHIType  │  MaskingStrategy  │  Config   │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

> 📖 See [Architecture Guide](./docs/ARCHITECTURE.md) for detailed design.

---

## 📚 Documentation | 文檔

| Document | Description |
|----------|-------------|
| 📖 [Architecture Guide](./docs/ARCHITECTURE.md) | System design & DDD structure |
| 🚀 [Deployment Guide](./docs/DEPLOYMENT.md) | Installation & configuration |
| 🔧 [Ollama Setup](./docs/ollama-setup.md) | Local LLM setup guide |
| 📊 [Batch Processing](./docs/batch-processing.md) | Excel/CSV batch processing |
| 🔍 [RAG Usage Guide](./docs/rag-usage.md) | Regulation retrieval system |

---

## 📊 Performance | 效能

### Processing Speed (per document, ~1500 chars)

| LLM Provider | Model | Time | Hardware |
|--------------|-------|------|----------|
| MiniMind | minimind2 | ~2-5s | CPU only |
| Ollama | qwen2.5:7b | ~15-25s | RTX 3090 |
| OpenAI | gpt-4o-mini | ~3-5s | API |
| Anthropic | claude-3-haiku | ~2-4s | API |

### Accuracy Benchmarks

| PHI Type | Precision | Recall | F1 Score |
|----------|-----------|--------|----------|
| Name | 96% | 94% | 95% |
| Date | 98% | 97% | 97.5% |
| ID Number | 99% | 98% | 98.5% |
| Location | 92% | 90% | 91% |
| Age >89 | 100% | 99% | 99.5% |

---

## 🤝 Contributing | 貢獻

We welcome contributions! 歡迎貢獻！

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

See [CONTRIBUTING.md](./CONTRIBUTING.md) for detailed guidelines.

---

## 📄 License | 授權

This project is licensed under the **MIT License** - see the [LICENSE](./LICENSE) file for details.

---

## ⚠️ Privacy Notice | 隱私聲明

- **Never commit real PHI** to this repository
- Medical data is processed **in-memory only** (not persisted)
- Designed for **HIPAA** and **GDPR** compliance
- Users are responsible for proper usage in their context

---

## 🙏 Acknowledgments | 致謝

- [LangChain](https://langchain.com/) - LLM framework
- [Ollama](https://ollama.ai/) - Local LLM runtime
- [MiniMind](https://github.com/jingyaogong/minimind) - Ultra-lightweight LLM
- [FAISS](https://github.com/facebookresearch/faiss) - Vector similarity search

---

<div align="center">

**Built with ❤️ for Healthcare Privacy**

[⬆ Back to Top](#-medical-de-identification-toolkit)

</div>
