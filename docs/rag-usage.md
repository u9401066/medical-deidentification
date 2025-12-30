# RAG 基礎設施使用指南
# RAG Infrastructure Usage Guide

## 架構概覽 | Architecture Overview

本系統使用 LangChain 框架建立 RAG (Retrieval-Augmented Generation) 架構，用於法規導向的醫療去識別化。

This system uses LangChain framework to build RAG (Retrieval-Augmented Generation) architecture for regulation-guided medical de-identification.

### 核心創新 | Core Innovation

**傳統 RAG**: 檢索「需要保留的內容」  
**本系統 RAG**: 檢索「需要遮蔽的內容」（從法規文件中檢索 PHI 定義）

**Traditional RAG**: Retrieve "what to preserve"  
**Our RAG**: Retrieve "what to mask" (retrieve PHI definitions from regulations)

### 隱私設計 | Privacy Design

- ✅ **法規文件**（公開資訊）→ 持久化向量庫 (FAISS)
- ❌ **病歷文件**（個人資料）→ 僅記憶體處理，不持久化

- ✅ **Regulation documents** (public info) → Persistent vector store (FAISS)
- ❌ **Medical documents** (PHI) → In-memory only, no persistence

---

## 系統架構 | System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    RAG Infrastructure                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────────┐      ┌─────────────────────┐         │
│  │ EmbeddingsManager│──────│ HuggingFace Models  │         │
│  │  (多語言支援)      │      │ - Multilingual MPNET│         │
│  └──────────────────┘      │ - BioMedical PubMed │         │
│           │                 │ - MiniLM-L6 (light) │         │
│           │                 └─────────────────────┘         │
│           ▼                                                  │
│  ┌──────────────────────────────────────────────┐          │
│  │     RegulationVectorStore (Persistent)        │          │
│  │  - FAISS index for regulations                │          │
│  │  - Load from regulations/source_documents/    │          │
│  │  - Save to regulations/vectorstore/           │          │
│  └──────────────────────────────────────────────┘          │
│           │                                                  │
│           ▼                                                  │
│  ┌──────────────────────────────────────────────┐          │
│  │          RegulationRetriever                  │          │
│  │  - MMR (Maximal Marginal Relevance)          │          │
│  │  - Similarity search                          │          │
│  │  - Score threshold filtering                  │          │
│  └──────────────────────────────────────────────┘          │
│           │                                                  │
│           ▼                                                  │
│  ┌──────────────────────────────────────────────┐          │
│  │         RegulationRAGChain                    │          │
│  │  - LLM: GPT-4 / Claude 3                     │          │
│  │  - RetrievalQA chain                         │          │
│  │  - PHI identification                         │          │
│  │  - Validation with regulations                │          │
│  └──────────────────────────────────────────────┘          │
│                                                              │
│  ┌──────────────────────────────────────────────┐          │
│  │   InMemoryDocumentProcessor (Ephemeral)      │          │
│  │  - Process medical documents in memory        │          │
│  │  - Destroy after use (no persistence)         │          │
│  └──────────────────────────────────────────────┘          │
└─────────────────────────────────────────────────────────────┘
```

---

## 快速開始 | Quick Start

### 1. 安裝依賴 | Install Dependencies

```bash
# 安裝所有必要套件
pip install -r requirements.txt
```

### 2. 準備法規文件 | Prepare Regulation Documents

在 `regulations/source_documents/` 目錄下創建法規文件（Markdown 或 TXT 格式）：

Create regulation documents (Markdown or TXT format) in `regulations/source_documents/`:

```
regulations/
└── source_documents/
    ├── hipaa_safe_harbor.md      # HIPAA Safe Harbor 18 identifiers
    ├── gdpr_article_4.md          # GDPR Article 4 definitions
    ├── taiwan_pdpa.md             # Taiwan Personal Data Protection Act
    └── custom_hospital_policy.md  # Custom hospital policies
```

**範例檔案格式 | Example File Format**:

```markdown
# HIPAA Safe Harbor: Age Restrictions

## Age Over 89 Years

According to HIPAA Safe Harbor Rule §164.514(b)(2)(i)(C):

All elements of dates (except year) for dates that are directly related to an individual, 
including birth date, admission date, discharge date, death date; and all ages over 89 
and all elements of dates (including year) indicative of such age, except that such ages 
and elements may be aggregated into a single category of age 90 or older.

### Masking Strategy

- Ages 90 and above → Mask as "90歲以上" or "≥90 years"
- Birth dates with year indicating age >89 → Redact year
- Dates that could calculate age >89 → Redact or generalize

### Examples

- ❌ "Patient is 94 years old" → ✅ "Patient is ≥90 years old"
- ❌ "Born in 1930" → ✅ "Born in 19XX"
```

### 3. 建立向量庫 | Build Vector Store

```python
from medical_deidentification.infrastructure.rag import (
    create_embeddings_manager,
    RegulationVectorStore
)

# 創建嵌入管理器
embeddings = create_embeddings_manager(
    preset="multilingual",  # 推薦用於多語言醫療文件
    device="cpu"  # 如有 GPU 可用 "cuda"
)

# 創建並建立向量庫
store = RegulationVectorStore(embeddings_manager=embeddings)
store.build_from_source()

# 查看統計資訊
print(store.get_stats())
```

### 4. 搜索法規 | Search Regulations

```python
# 相似度搜索
docs = store.similarity_search("age over 89 years old", k=5)

for doc in docs:
    print(doc.page_content)
    print(doc.metadata)
```

### 5. 使用完整 RAG 鏈 | Use Full RAG Chain

```python
from medical_deidentification.infrastructure.rag import create_regulation_rag_chain
import os

# 設置 API Key
os.environ["OPENAI_API_KEY"] = "your-api-key"

# 創建 RAG 鏈
chain = create_regulation_rag_chain(
    vector_store=store,
    llm_provider="openai",
    model_name="gpt-4",
    search_type="mmr"
)

# 識別 PHI
medical_text = """
患者張三，94歲男性，患有法布瑞氏症（Fabry Disease）。
聯絡電話：02-2345-6789
住址：台北市信義區忠孝東路五段123號
"""

result = chain.identify_phi(
    text=medical_text,
    language="zh-TW",
    return_source=True
)

print(result["result"])  # PHI 識別結果
```

---

## 核心組件 | Core Components

### 1. EmbeddingsManager

**用途 | Purpose**: 管理嵌入模型，支援多語言和生物醫學領域

```python
from medical_deidentification.infrastructure.rag import create_embeddings_manager

# 選項 1: 使用預設配置
embeddings = create_embeddings_manager(
    preset="multilingual",  # 多語言支援
    device="cpu"
)

# 選項 2: 生物醫學領域
embeddings = create_embeddings_manager(
    preset="biomedical",  # 針對醫學文獻訓練
    device="cuda"
)

# 選項 3: 輕量級（快速）
embeddings = create_embeddings_manager(
    preset="lightweight",  # 較小模型，更快速度
    device="cpu"
)

# 嵌入文本
query_embedding = embeddings.embed_query("age over 89 years")
doc_embeddings = embeddings.embed_documents([
    "HIPAA Safe Harbor rules",
    "GDPR personal data definition"
])
```

**可用預設配置 | Available Presets**:

| Preset | Model | Dimension | Use Case |
|--------|-------|-----------|----------|
| `multilingual` | `paraphrase-multilingual-mpnet-base-v2` | 768 | **推薦** 多語言醫療文件 |
| `biomedical` | `pritamdeka/PubMedBERT-mnli-snli-scinli-scitail-mednli-stsb` | 768 | 生物醫學領域特化 |
| `lightweight` | `all-MiniLM-L6-v2` | 384 | 快速處理，較小模型 |
| `english` | `all-mpnet-base-v2` | 768 | 僅英文，高品質 |

### 2. RegulationVectorStore

**用途 | Purpose**: 持久化法規文件向量庫

```python
from medical_deidentification.infrastructure.rag import (
    RegulationVectorStore,
    RegulationStoreConfig
)

# 自定義配置
config = RegulationStoreConfig(
    source_dir=Path("regulations/source_documents"),
    vectorstore_dir=Path("regulations/vectorstore"),
    chunk_size=1000,       # 文本分塊大小
    chunk_overlap=200,     # 分塊重疊
)

store = RegulationVectorStore(
    embeddings_manager=embeddings,
    config=config
)

# 建立向量庫（首次）
store.build_from_source()

# 或載入已存在的向量庫
store = RegulationVectorStore.load(embeddings_manager=embeddings)

# 新增文件
new_docs = [...]  # LangChain Document objects
store.add_documents(new_docs)
store.save()

# 搜索
docs = store.similarity_search("rare disease", k=5)
docs_with_scores = store.similarity_search_with_score("genetic information", k=3)
```

### 3. RegulationRetriever

**用途 | Purpose**: 高級檢索，支援 MMR（最大邊際相關性）確保多樣性

```python
from medical_deidentification.infrastructure.rag import (
    RegulationRetriever,
    RetrieverConfig
)

# MMR 檢索（平衡相關性與多樣性）
config = RetrieverConfig(
    search_type="mmr",
    k=5,              # 返回 5 個文件
    fetch_k=20,       # 先取 20 個候選
    lambda_mult=0.7   # 0=最大多樣性, 1=最大相關性
)

retriever = RegulationRetriever(vector_store=store, config=config)

# 基本檢索
docs = retriever.retrieve("age restrictions")

# 帶分數檢索
docs_with_scores = retriever.retrieve_with_scores("rare disease")

# 多 PHI 類型檢索
docs = retriever.retrieve_multi_phi(
    phi_types=["AGE_OVER_89", "RARE_DISEASE", "GENETIC_INFO"],
    combine_strategy="union"  # or "intersection"
)

# 針對特定 PHI 類型
docs = retriever.retrieve_by_phi_type(
    phi_type="AGE_OVER_89",
    context="Taiwan regulations"
)
```

**搜索策略 | Search Strategies**:

- **Similarity**: 純餘弦相似度，找最相關文件
- **MMR**: 平衡相關性與多樣性，避免結果重複
- **Score Threshold**: 設置最低相關性分數過濾

### 4. RegulationRAGChain

**用途 | Purpose**: 完整 RAG 鏈，整合 LLM 進行 PHI 識別

```python
from medical_deidentification.infrastructure.rag import (
    create_regulation_rag_chain,
    RAGChainConfig
)

# 使用 OpenAI GPT-4
chain = create_regulation_rag_chain(
    vector_store=store,
    llm_provider="openai",
    model_name="gpt-4",
    search_type="mmr"
)

# 或使用 Anthropic Claude
chain = create_regulation_rag_chain(
    vector_store=store,
    llm_provider="anthropic",
    model_name="claude-3-opus-20240229",
    search_type="similarity"
)

# PHI 識別
result = chain.identify_phi(
    text="患者李四，92歲，患有龐貝氏症...",
    language="zh-TW",
    return_source=True  # 返回引用的法規文件
)

# 批次處理
results = chain.batch_identify(
    texts=[text1, text2, text3],
    language="zh-TW"
)

# 獲取遮蔽策略
strategies = chain.get_masking_strategy(phi_type="AGE_OVER_89", k=3)

# 驗證實體
validation = chain.validate_with_regulations(
    entity_text="94歲",
    phi_type="AGE_OVER_89",
    retrieve_evidence=True
)
```

### 5. InMemoryDocumentProcessor

**用途 | Purpose**: 臨時處理病歷文件（不持久化）

```python
from medical_deidentification.infrastructure.rag import InMemoryDocumentProcessor

processor = InMemoryDocumentProcessor(
    embeddings_manager=embeddings,
    chunk_size=1000,
    chunk_overlap=200
)

# 處理並立即銷毀
medical_text = "患者病歷內容..."
results = processor.process_and_destroy(
    text=medical_text,
    query="age and rare disease information",
    k=3
)

# ✅ 向量庫已被銷毀，無持久化
```

---

## 配置選項 | Configuration Options

### EmbeddingsConfig

```python
from medical_deidentification.infrastructure.rag import EmbeddingsConfig

config = EmbeddingsConfig(
    model_name="sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
    model_kwargs={"device": "cpu"},
    encode_kwargs={"normalize_embeddings": True},
    cache_folder="./models/embeddings"
)
```

### RegulationStoreConfig

```python
from medical_deidentification.infrastructure.rag import RegulationStoreConfig
from pathlib import Path

config = RegulationStoreConfig(
    source_dir=Path("regulations/source_documents"),
    vectorstore_dir=Path("regulations/vectorstore"),
    chunk_size=1000,
    chunk_overlap=200,
    file_patterns=["**/*.md", "**/*.txt"]
)
```

### RetrieverConfig

```python
from medical_deidentification.infrastructure.rag import RetrieverConfig

config = RetrieverConfig(
    search_type="mmr",              # "similarity" or "mmr"
    k=5,                            # 返回文件數
    fetch_k=20,                     # MMR 候選數
    lambda_mult=0.5,                # MMR 多樣性因子
    score_threshold=0.7,            # 最低相關性分數
    use_compression=False           # LLM 壓縮過濾
)
```

### RAGChainConfig

```python
from medical_deidentification.infrastructure.rag import RAGChainConfig

config = RAGChainConfig(
    llm_provider="openai",          # "openai" or "anthropic"
    model_name="gpt-4",
    temperature=0.0,                # 0=確定性輸出
    max_tokens=2000,
    retriever_config=RetrieverConfig(...)
)
```

---

## 使用範例 | Usage Examples

完整範例請參考 `examples/rag_usage_examples.py`：

```bash
# 運行所有範例
python examples/rag_usage_examples.py

# 運行特定範例
python examples/rag_usage_examples.py 5  # 範例 5: RAG 鏈 PHI 識別
```

**8 個範例 | 8 Examples**:
1. 基本設置與向量庫建立
2. 從法規文件建立向量庫
3. 搜索相關法規
4. 使用 MMR 的高級檢索
5. 完整 RAG 鏈進行 PHI 識別
6. 為多個 PHI 類型檢索法規
7. 根據法規驗證實體
8. 病歷文件的臨時記憶體處理

---

## 法規文件結構建議 | Regulation Document Structure

### 建議格式 | Recommended Format

```markdown
# [Regulation Name]: [Topic]

## [PHI Type or Section]

### Definition | 定義

[Clear definition of what constitutes PHI according to this regulation]

### Scope | 範圍

[When and where this applies]

### Masking Strategy | 遮蔽策略

[How to mask this type of PHI]

### Examples | 範例

- ❌ Original: [example]
- ✅ Masked: [example]

### Special Cases | 特殊情況

[Edge cases and exceptions]

### References | 參考

[Legal citations]
```

### 多語言支援 | Multilingual Support

建議使用雙語（中英）撰寫法規文件，提高檢索準確性：

```markdown
# HIPAA Safe Harbor: Rare Diseases | HIPAA 安全港：罕見疾病

## Definition | 定義

Rare diseases that could potentially identify individuals must be masked according to 
HIPAA regulations when the prevalence is less than 1 in 10,000.

罕見疾病若患病率低於萬分之一，根據 HIPAA 規定必須遮蔽以避免識別個人身份。

## Examples | 範例

- Fabry Disease | 法布瑞氏症
- Pompe Disease | 龐貝氏症
- Gaucher Disease | 高雪氏症
```

---

## 效能優化 | Performance Optimization

### 1. 使用 GPU 加速 | Use GPU Acceleration

```python
embeddings = create_embeddings_manager(
    preset="multilingual",
    device="cuda"  # 需要 CUDA 支援的 GPU
)
```

### 2. 調整分塊大小 | Adjust Chunk Size

```python
config = RegulationStoreConfig(
    chunk_size=500,      # 較小分塊：更精確但更多向量
    chunk_overlap=100    # 減少重疊：更快處理
)
```

### 3. 使用輕量級模型 | Use Lightweight Model

```python
embeddings = create_embeddings_manager(
    preset="lightweight",  # MiniLM-L6: 384 維度，更快速
    device="cpu"
)
```

### 4. MMR 參數調整 | MMR Parameter Tuning

```python
config = RetrieverConfig(
    fetch_k=10,         # 減少候選數
    lambda_mult=0.8     # 增加相關性權重（減少計算）
)
```

---

## 故障排除 | Troubleshooting

### 問題 1: 向量庫未找到 | Vector store not found

```
FileNotFoundError: Vector store not found at regulations/vectorstore
```

**解決方法 | Solution**:
```python
store.build_from_source()  # 首次建立向量庫
```

### 問題 2: 沒有法規文件 | No regulation documents

```
ValueError: No documents found in regulations/source_documents
```

**解決方法 | Solution**:
在 `regulations/source_documents/` 目錄下新增 `.md` 或 `.txt` 法規文件

### 問題 3: API Key 未設置 | API key not set

```
Error: OPENAI_API_KEY not set in environment
```

**解決方法 | Solution**:
```python
import os
os.environ["OPENAI_API_KEY"] = "your-api-key-here"
```

或在 `.env` 文件中設置：
```
OPENAI_API_KEY=your-api-key-here
ANTHROPIC_API_KEY=your-api-key-here
```

### 問題 4: 記憶體不足 | Out of memory

**解決方法 | Solution**:
1. 使用輕量級模型
2. 減少 chunk_size 和 k 值
3. 批次處理而非一次性處理

---

## 最佳實踐 | Best Practices

### 1. 法規文件組織 | Regulation Document Organization

```
regulations/
└── source_documents/
    ├── hipaa/
    │   ├── safe_harbor.md
    │   ├── expert_determination.md
    │   └── identifiers.md
    ├── gdpr/
    │   ├── article_4.md
    │   ├── article_9.md
    │   └── recitals.md
    ├── taiwan/
    │   ├── pdpa.md
    │   └── moh_guidelines.md
    └── hospital/
        └── custom_policies.md
```

### 2. 版本控制 | Version Control

- ✅ 版本控制法規文件（regulations/source_documents/）
- ❌ 不要版本控制向量庫（regulations/vectorstore/）- 可重建

### 3. 定期更新 | Regular Updates

```python
# 法規更新後重建向量庫
store.build_from_source(force_rebuild=True)
```

### 4. 記錄與監控 | Logging and Monitoring

```python
import logging
from loguru import logger

# 配置日誌
logger.add("logs/rag_system.log", rotation="1 day")

# 追蹤檢索統計
result = chain.identify_phi(text, language="zh-TW")
logger.info(f"PHI identification completed: {len(result)} entities found")
```

---

## 進階主題 | Advanced Topics

### 自定義 Prompt Template

```python
custom_prompt = """You are an expert in {domain}. 
Analyze the following text based on {regulations}.

Text: {question}
Regulations: {context}

Provide detailed PHI identification...
"""

# 創建自定義鏈（需修改 regulation_chain.py）
```

### 多模型 Ensemble

```python
# 使用多個模型提高準確性
chains = [
    create_regulation_rag_chain(store, llm_provider="openai", model_name="gpt-4"),
    create_regulation_rag_chain(store, llm_provider="anthropic", model_name="claude-3-opus-20240229")
]

# 比較結果
results = [chain.identify_phi(text) for chain in chains]
```

---

## API 參考 | API Reference

完整 API 文檔請參考各模組的 docstring：

```python
help(EmbeddingsManager)
help(RegulationVectorStore)
help(RegulationRetriever)
help(RegulationRAGChain)
```

---

## 授權與貢獻 | License and Contributing

本項目採用 Apache 2.0 授權。歡迎提交 Issue 和 Pull Request！

This project is licensed under Apache 2.0. Issues and Pull Requests are welcome!

---

**更新日期 | Last Updated**: 2024-11-22  
**版本 | Version**: 0.1.0
