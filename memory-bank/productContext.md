# Product Context

## Overview

LLM-powered medical text de-identification toolkit with RAG-enhanced regulation retrieval. Supports multi-language medical records and automated PHI identification and masking.

基於 LLM/RAG 的醫療文本去識別化工具套件，自動識別並遮蔽臨床病歷中的 PHI。

## Core Features

- **PHI Detection Engine**: Hybrid pipeline — Regex → SpaCy NER → LLM (for uncertain regions)
- **Multi-language Support**: 10+ languages (TW/CN/EN/JA/KO/ES/FR/DE/TH/VI)
- **De-identification Strategies**: Redaction, Masking, Generalization, Custom
- **Batch Processing**: Single file + batch directory, progress tracking
- **Web UI**: React + TanStack Query, DDD architecture
- **RAG Regulation Retrieval**: Retrieves "what to mask" from regulations (privacy-first: in-memory for medical docs, persistent for regulations)

## Technical Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.12, TypeScript |
| Package Manager | uv (Python), npm (Frontend) |
| LLM | Ollama (gemma3:27b), OpenAI, Anthropic |
| Framework | LangChain 1.0+, DSPy |
| NLP | SpaCy 3.8 (zh_core_web_sm) |
| Vector Store | FAISS (in-memory) |
| Embeddings | sentence-transformers |
| Frontend | React, TanStack Query, Zustand, Radix UI, Tailwind |
| Testing | pytest, Vitest, Playwright, RTL |
| Quality | Ruff (lint/format) |

## Architecture

DDD (Domain-Driven Design) with 4 layers:

**Backend (Python)**
```
core/domain/         → 核心領域（實體、值物件、PHI 類型）
core/application/    → 應用層（批次處理、Pipeline）
core/infrastructure/ → 基礎設施（RAG、LLM、Loaders、Tools）
core/interface/      → 介面層（CLI）
```

**Frontend (TypeScript/React)**
```
web/frontend/src/domain/         → 領域層（實體、值物件）
web/frontend/src/application/    → 應用層（Hooks）
web/frontend/src/infrastructure/ → 基礎設施（API、Store、Logger）
web/frontend/src/presentation/   → 呈現層（Components）
```

**Backend API (FastAPI)**
```
web/backend/routers/  → API 路由
web/backend/services/ → 業務服務
web/backend/config.py → 設定管理
```

