# Product Context

## Overview | 專案概述

A Python-based medical text de-identification toolkit that leverages LLM/Agent technology to automatically identify and remove Protected Health Information (PHI) from clinical records.

本專案為基於 Python 的醫療文本去識別化工具套件,透過 LLM/Agent 技術自動識別並移除臨床病歷中的個人健康資訊。

## Core Features | 核心功能

### MVP Phase 1 (Core De-identification)
- **PHI Detection Engine | 個資檢測引擎**
  - Name, date, location, identifier detection
  - 姓名、日期、地點、識別碼檢測
  - LLM-powered entity recognition
  - 基於 LLM 的實體識別

- **Multi-language Support | 多語言支援**
  - 10+ supported languages (extensible)
  - 支援 10+ 種語言（可擴充）
  - Languages: Traditional Chinese (繁體中文), Simplified Chinese (简体中文), 
    English, Japanese (日本語), Korean (한국어), Spanish (Español), 
    French (Français), German (Deutsch), Thai (ไทย), Vietnamese (Tiếng Việt)
  - Language-aware PHI detection rules
  - 語言感知的個資檢測規則

- **De-identification Strategies | 去識別化策略**
  - Redaction (removal) | 移除
  - Masking (replacement with placeholder) | 遮罩
  - Generalization (date shifting, location generalization) | 泛化
  - Custom user-defined strategies | 用戶自定義策略

- **Batch Processing | 批次處理**
  - Single file processing
  - Batch directory processing
  - Progress tracking and reporting
  - 進度追蹤與報告

### MVP Phase 2 (Enhanced Features)
- Multiple LLM provider support (OpenAI, Anthropic, local models)
- Customizable PHI detection rules
- Validation and quality metrics
- Export in multiple formats (JSON, CSV, plain text)

## Technical Stack | 技術堆疊

### Core Technologies
- **Language**: Python 3.11+
- **Package Manager**: Poetry
- **Testing**: pytest, pytest-cov

### LLM Integration
- **LLM Framework**: LangChain / LlamaIndex
- **Supported Providers**: 
  - OpenAI (GPT-4, GPT-3.5)
  - Anthropic (Claude)
  - Local models (via Ollama/LlamaCPP)

### Data Processing
- **Text Processing**: spaCy, NLTK
- **Structured Data**: Pydantic (data validation)
- **Batch Processing**: asyncio, concurrent.futures

### Development Tools
- **Version Control**: Git + GitHub
- **CI/CD**: GitHub Actions
- **Code Quality**: black, isort, mypy, pylint
- **Documentation**: Sphinx, MkDocs

## Architecture | 系統架構

Following DDD (Domain-Driven Design) principles:

### Bounded Contexts | 限界上下文
1. **De-identification Context** | 去識別化上下文
2. **LLM Integration Context** | LLM 整合上下文
3. **Batch Processing Context** | 批次處理上下文
4. **Validation Context** | 驗證上下文

### Core Domain Model | 核心領域模型
- Medical Document (Aggregate Root)
- PHI Entity (Value Object)
- De-identification Strategy (Strategy Pattern)
- Processing Pipeline (Chain of Responsibility)

## Libraries | 相依套件

```toml
[tool.poetry.dependencies]
python = "^3.11"
langchain = "^0.1.0"
openai = "^1.0.0"
anthropic = "^0.8.0"
pydantic = "^2.0"
spacy = "^3.7"
typer = "^0.9.0"  # CLI interface
rich = "^13.0"    # Terminal UI
```

## Development Environment | 開發環境

- IDE: VS Code with Python extensions
- Python Virtual Environment: Poetry
- Git workflow: Feature branch + PR review
- Documentation: Inline docstrings (Google style) + MkDocs