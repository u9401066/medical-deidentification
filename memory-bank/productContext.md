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

## Architecture

DDD (Domain-Driven Design) with 4 layers: Domain, Application, Infrastructure, Interface. The core logic is now located in the 'core/' directory (formerly 'medical_deidentification/'). Uses a hybrid PHI detection pipeline (Regex + SpaCy + LLM) and RAG for regulation retrieval.



DDD (Domain-Driven Design) with streaming FIFO chunk processing for unlimited file sizes



DDD (Domain-Driven Design) 架構：Interface → Application → Infrastructure → Domain 四層。新增 DSPy 整合層 (infrastructure/dspy/) 用於自動 prompt 優化，metrics.py 追蹤完整混淆矩陣 (TP/FP/FN)。評估腳本在 scripts/ 目錄下。



DDD (Domain-Driven Design) with 4 layers. Hybrid PHI Detection Pipeline: Level 1 (Regex) → Level 2 (SpaCy NER) → Level 3 (Small LLM for uncertain regions). RAG for regulation retrieval. Multi-provider LLM support.



DDD (Domain-Driven Design) with 4 layers: Domain (models, entities, configs), Application (batch processing, pipelines), Infrastructure (RAG, LLM, loaders), Interface (CLI). 6 core modules: (1) Document Loader - multi-format support, (2) RAG Regulation Engine - retrieves 'what to mask' from regulations, (3) Core Processing Engine - pipeline orchestration, (4) LLM Integration - multi-provider support, (5) Output Module - multiple export formats, (6) Validation Module - quality metrics.



Domain-Driven Design with clean architecture layers. Infrastructure layer handles RAG (embeddings, vector stores, retrievers) and LLM integration. Application layer provides batch processing and PHI identification chains. Domain layer defines PHI types, entities, and masking strategies. Uses LangChain for unified LLM/RAG management, with support for multiple LLM providers (Anthropic, OpenAI, Ollama).



DDD (Domain-Driven Design) with 4 layers: Domain, Application, Infrastructure, Interface. 6 core modules: (1) Document Loader, (2) RAG Regulation Engine with LangChain, (3) Core Processing, (4) LLM Integration, (5) Output, (6) Validation. RAG innovation: retrieves 'what to mask' from regulations instead of traditional 'what to preserve'. Privacy-first: in-memory vector store for medical documents (no persistence), persistent vector store only for public regulations.



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

## Technologies

- Python 3.12
- uv (Package Manager)
- Ruff (Linter/Formatter)
- Ollama (Local LLM)
- LangChain
- DSPy
- FAISS



- Python 3.10
- LangChain
- DSPy
- FAISS
- Pydantic



- Python 3.11+
- LangChain
- Ollama
- DSPy
- FAISS
- SpaCy
- Pydantic
- Multiprocessing



- Python 3.10
- LangChain 1.0+
- SpaCy 3.8+ (NER)
- FAISS (vector store)
- Ollama (local LLM)
- Qwen2.5-0.5B/1.5B (fast LLM)
- Qwen2.5-7B (precise LLM)
- OpenAI GPT-4o (cloud)
- HuggingFace Transformers
- Pydantic 2.x



- Python 3.11+
- LangChain 1.0+
- Ollama (Local LLM)
- PyTorch 2.2.0+cpu
- NumPy 1.26.4
- HuggingFace Transformers
- Sentence Transformers
- FAISS
- Spacy
- Pandas
- Pydantic 2.x
- Loguru



- Python 3.10
- LangChain 1.0+
- Anthropic Claude
- OpenAI GPT
- Ollama (Local LLM)
- PyTorch 2.2.0+cpu
- NumPy 1.26.4
- HuggingFace Transformers
- Sentence Transformers
- FAISS
- ChromaDB
- Spacy
- Pandas
- Pydantic 2.x



- Python 3.10+
- LangChain (RAG/LLM/Agent framework)
- FAISS (in-memory vector store)
- HuggingFace Embeddings (sentence-transformers)
- OpenAI API
- Anthropic Claude API
- ChromaDB (ephemeral mode option)
- Pydantic (data validation)
- spaCy (NLP)
- pandas (data processing)
- openpyxl (Excel I/O)
- python-docx (Word I/O)
- typer (CLI)
- rich (terminal UI)
- pytest (testing)
- Git (version control)



## Libraries and Dependencies

- langchain-core>=1.0.0
- langchain-ollama>=1.0.0
- dspy>=2.5.0
- faiss-cpu>=1.7.4
- sentence-transformers>=2.3.1
- pydantic>=2.6.0
- ruff>=0.8.0
- uv>=0.9.17



- langchain
- langchain-ollama
- dspy
- faiss-cpu
- pydantic
- loguru
- pytest
- pytest-cov



- langchain
- langchain-ollama
- dspy-ai
- faiss-cpu
- spacy
- pandas
- openpyxl
- pydantic
- loguru
- pytest



- langchain==1.0.8
- langchain-ollama==1.0.0
- langchain-openai==1.0.3
- langchain-anthropic==1.1.0
- langchain-huggingface==1.0.1
- spacy==3.8.11 (zh_core_web_sm model)
- faiss-cpu==1.13.0
- sentence-transformers==2.7.0
- pydantic==2.12.4
- pandas==2.3.3
- loguru==0.7.3
- ollama==0.6.1



- langchain==1.0.8
- langchain-anthropic==1.1.0
- langchain-openai==1.0.3
- langchain-ollama==1.0.0
- langchain-huggingface==1.0.1
- torch==2.2.0+cpu
- numpy==1.26.4
- transformers==4.57.1
- sentence-transformers==2.7.0
- faiss-cpu==1.13.0
- spacy==3.8.11
- pydantic==2.12.4
- pandas==2.3.3
- loguru==0.7.3
- ollama==0.6.1



- langchain==1.0.8
- langchain-anthropic==1.1.0
- langchain-openai==1.0.3
- langchain-ollama==1.0.0
- langchain-huggingface==1.0.1
- anthropic==0.74.1
- torch==2.2.0+cpu
- numpy==1.26.4
- transformers==4.57.1
- sentence-transformers==2.7.0
- faiss-cpu==1.13.0
- chromadb==0.4.24
- spacy==3.8.11
- pydantic==2.12.4
- pandas==2.3.3
- loguru==0.7.3



- langchain (>=0.1.0) - Core RAG/LLM framework
- langchain-openai - OpenAI integration
- langchain-anthropic - Anthropic integration
- langchain-community - Community integrations
- chromadb (>=0.4.0) - Vector database
- faiss-cpu - Fast similarity search
- sentence-transformers - Embeddings
- openai (>=1.0.0) - OpenAI API
- anthropic - Claude API
- pydantic (>=2.0) - Data validation
- spacy (>=3.0) - NLP
- pandas - Data manipulation
- openpyxl - Excel files
- python-docx - Word files
- typer - CLI framework
- rich - Terminal formatting
- tqdm - Progress bars
- tenacity - Retry logic
- loguru - Logging
- pytest - Testing



## Project Description

LLM-powered medical text de-identification toolkit with RAG-enhanced regulation retrieval. Supports multi-language medical records and automated PHI identification and masking. Optimized for Python 3.12 and local LLM execution (Ollama).



Medical de-identification toolkit using LLM-based PHI detection with DSPy integration



Medical De-identification Toolkit - LLM/RAG 驅動的醫療文本去識別化工具，使用 DSPy 進行自動 prompt 優化，支援 HIPAA/GDPR 合規



LLM-powered medical text de-identification toolkit with hybrid PHI detection (SpaCy + Regex + LLM). 基於混合策略的醫療文本去識別化工具套件，結合傳統 NER (SpaCy)、正則表達式和 LLM 技術。



Python-based medical text de-identification toolkit using LLM/RAG technology to automatically identify and mask Protected Health Information (PHI) from clinical records. 基於 Python 的醫療文本去識別化工具套件，透過 LLM/RAG 技術自動識別並遮蔽個人健康資訊。



LLM-powered medical text de-identification toolkit with RAG-enhanced regulation retrieval. 基於 LLM 與 RAG 的醫療文本去識別化工具套件。支援多語言醫療記錄處理、PHI 自動識別與遮蔽。

