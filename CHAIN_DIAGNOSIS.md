# PHI Identification Chain 診斷報告

## 🔍 問題診斷

### 1. **沒有使用 LangChain 的 Chain 機制**

**現況：**
```python
# phi_identification_chain.py
class PHIIdentificationChain:  # ❌ 只是普通 Python class
    def __init__(self, ...):
        self.llm = create_llm(...)  # 直接持有 LLM
    
    def identify_phi(self, text):
        prompt = template.format(context=context, text=text)  # ❌ 字串拼接
        response = self.llm.invoke(prompt)  # ❌ 直接調用
```

**問題：**
- 沒有繼承 `Chain` 或使用 LCEL (LangChain Expression Language)
- 沒有使用 `PromptTemplate` 或 `ChatPromptTemplate`
- 沒有 token 限制或自動 truncation
- 沒有使用 LangChain 的 document processing chains

### 2. **Context 冗餘問題**

**現況：**
```python
# 即使 retrieve_regulation_context=False
context = DEFAULT_HIPAA_SAFE_HARBOR_RULES  # 800 字元

# 每次請求都發送：
prompt = f"""
Regulations:
{context}  # 800 字元

Medical Text:
{text}  # 1400+ 字元

Instructions: ...  # 200+ 字元
"""
# 總計: 2000+ 字元 (~1500 tokens)
```

**實際測試結果：**
- 簡單 prompt（253 字元）：✅ 6.5 秒
- 實際 prompt（1579 字元）：❌ >150 秒（超時）

### 3. **分塊策略問題**

**現況：**
```python
def _identify_phi_chunked(self, text, ...):
    # 獲取 context 一次
    context = DEFAULT_HIPAA_SAFE_HARBOR_RULES  # 800 字元
    
    # 但每個 chunk 都要帶著完整 context
    for chunk in chunks:
        entities = self._identify_phi_structured(
            text=chunk,      # 例如 300 字元
            context=context, # ❌ 每次都是 800 字元
            language=language
        )
        # 每次請求 = 800 (context) + 300 (chunk) + 200 (instructions)
        #           = 1300+ 字元
```

**問題：**
- 分塊無法減少 prompt 長度（context 仍然很長）
- 沒有使用 LangChain 的 MapReduce 或 Refine 模式
- 無法利用 LangChain 的文檔壓縮或摘要功能

## ✅ 解決方案

### 方案 1：簡化 Context（立即修復）

**修改 `phi_identification_chain.py`：**

```python
# 第 215-216 行
else:
    # 使用極簡 context
    context = "Identify PHI: names, dates, IDs, locations, ages >89."
    # 從 800 字元 → 60 字元（減少 ~92%）
```

**預期效果：**
- Prompt 從 1579 字元 → ~839 字元
- 處理時間從 >150 秒 → ~10-15 秒

### 方案 2：重構為 LangChain LCEL Chain（中期優化）

**建議實現：**

```python
from langchain.chains import LLMChain
from langchain.prompts import ChatPromptTemplate
from langchain.schema.runnable import RunnablePassthrough

class PHIIdentificationChain:
    def __init__(self, ...):
        # 使用 ChatPromptTemplate
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a PHI identification expert."),
            ("user", "Identify PHI in: {text}")  # 簡化 prompt
        ])
        
        # 使用 LCEL chain
        self.chain = (
            RunnablePassthrough.assign(
                context=lambda x: self._get_context(x["text"])  # 動態 context
            )
            | self.prompt
            | self.llm.with_structured_output(PHIDetectionResponse)
        )
    
    def identify_phi(self, text):
        return self.chain.invoke({"text": text})
```

### 方案 3：使用 LangChain Document Chains（長期優化）

**正確的 MapReduce 流程：**

```
輸入: 長文本 (例如 10000 字元)
  ↓
分段: [Chunk1, Chunk2, Chunk3, ...]
  ↓
Map 階段: 每個 chunk → PHI 實體列表
  Chunk1 → [PHI1, PHI2, PHI3]          # 只輸出 PHI，不包含原文
  Chunk2 → [PHI4, PHI5]
  Chunk3 → [PHI6]
  ↓
Reduce 階段: 彙整所有 PHI
  合併 → [PHI1, PHI2, PHI3, PHI4, PHI5, PHI6]
  去重 → 移除重複實體
  調整位置 → 修正 start_pos/end_pos 為原文中的絕對位置
  ↓
輸出: 完整 PHI 實體列表
```

**實現代碼：**

```python
from langchain.prompts import ChatPromptTemplate
from langchain.schema import Document
from langchain.schema.runnable import RunnablePassthrough, RunnableLambda
from typing import List

class PHIIdentificationChain:
    def _build_map_chain(self):
        """Map: 從單個 chunk 識別 PHI（只輸出 PHI 實體）"""
        map_prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a PHI identification expert. Extract ONLY PHI entities."),
            ("user", """Identify all PHI in this text section:

{page_content}

Return ONLY the PHI entities found, not the full text.""")
        ])
        
        # Map chain: Document → PHIDetectionResponse
        return (
            map_prompt 
            | self.llm.with_structured_output(PHIDetectionResponse)
        )
    
    def _merge_phi_results(
        self, 
        chunk_results: List[Tuple[PHIDetectionResponse, int, str]]
    ) -> List[PHIEntity]:
        """Reduce: 彙整所有 chunk 的 PHI 實體"""
        all_entities = []
        
        for detection_response, chunk_start_pos, chunk_text in chunk_results:
            for result in detection_response.entities:
                # 在原文中找到實體的絕對位置
                entity_start = chunk_text.find(result.entity_text, 0)
                if entity_start != -1:
                    absolute_start = chunk_start_pos + entity_start
                    absolute_end = absolute_start + len(result.entity_text)
                    
                    # 創建調整位置後的實體
                    entity = result.to_phi_entity()
                    adjusted_entity = replace(
                        entity,
                        start_pos=absolute_start,
                        end_pos=absolute_end
                    )
                    all_entities.append(adjusted_entity)
        
        # 去重
        unique_entities = self._deduplicate_entities(all_entities)
        return unique_entities
    
    def _identify_phi_with_map_reduce(
        self,
        text: str,
        language: Optional[str] = None
    ) -> List[PHIEntity]:
        """使用 MapReduce 模式處理長文本"""
        
        # 1. 分段
        chunks = self.medical_retriever._split_text(text)
        logger.info(f"Split into {len(chunks)} chunks for MapReduce processing")
        
        # 2. 獲取 context（只需一次）
        context = self._get_minimal_context()
        
        # 3. Map: 處理每個 chunk
        map_chain = self._build_map_chain()
        chunk_results = []
        current_pos = 0
        
        for i, chunk in enumerate(chunks):
            logger.debug(f"Map: Processing chunk {i+1}/{len(chunks)}")
            
            # 創建 Document（LangChain 標準格式）
            doc = Document(
                page_content=chunk,
                metadata={"chunk_index": i, "start_position": current_pos}
            )
            
            # 執行 map chain（只輸出 PHI）
            detection_response = map_chain.invoke({"page_content": chunk})
            chunk_results.append((detection_response, current_pos, chunk))
            
            current_pos += len(chunk)
        
        # 4. Reduce: 彙整結果
        logger.debug(f"Reduce: Merging {len(chunk_results)} chunk results")
        unique_entities = self._merge_phi_results(chunk_results)
        
        logger.success(f"MapReduce complete: {len(unique_entities)} unique PHI entities")
        return unique_entities
```

**關鍵改進：**

1. ✅ **Map 階段只輸出 PHI**：每個 chunk 的處理結果是 `PHIDetectionResponse`（PHI 列表），不包含原文
2. ✅ **減少 prompt 長度**：每次只處理一個 chunk（~500-2000 字元），不需要完整文檔
3. ✅ **Reduce 階段純數據處理**：合併 PHI 列表，去重，調整位置（不需要 LLM）
4. ✅ **位置修正**：追蹤每個 chunk 的起始位置，將相對位置轉換為絕對位置

## 📊 效能對比

| 方案 | Prompt 長度 | 預期時間 | 實現難度 | 推薦度 |
|------|------------|----------|---------|--------|
| 方案 1: 簡化 Context | ~839 字元 | ~10-15 秒 | ⭐ 簡單 | ⭐⭐⭐⭐⭐ |
| 方案 2: LCEL Chain | ~500 字元 | ~5-8 秒 | ⭐⭐⭐ 中等 | ⭐⭐⭐⭐ |
| 方案 3: MapReduce | ~300 字元/chunk | ~8-12 秒 | ⭐⭐⭐⭐⭐ 複雜 | ⭐⭐⭐ |

## 🎯 建議執行順序

### 立即執行（方案 1）

**修改 2 處：**

1. `phi_identification_chain.py:216`（`_identify_phi_direct`）
2. `phi_identification_chain.py:297`（`_identify_phi_chunked`）

```python
context = "Identify PHI: names, dates, IDs, locations, ages >89."
```

**測試：**
```bash
python examples/simple_batch_test.py
```

### 後續優化（方案 2）

1. 重構為 LCEL chain
2. 使用 `ChatPromptTemplate`
3. 添加 token counting 和 truncation
4. 使用 LangChain 的 callbacks 進行監控

### 未來增強（方案 3）

1. 實現 MapReduce pattern for long documents
2. 添加 intermediate result caching
3. 支援 streaming output
4. 使用 LangSmith 進行 tracing

## 🔧 立即修復代碼

**檔案：** `medical_deidentification/infrastructure/rag/phi_identification_chain.py`

**位置 1（第 186-216 行）：**
```python
def _identify_phi_direct(self, text, language, return_source, return_entities):
    regulation_docs = []
    context = ""
    
    if self.config.retrieve_regulation_context and self.regulation_chain:
        # ... 原有邏輯 ...
        context = "\n\n".join([...])
    else:
        # ✅ 修改這裡
        context = "Identify PHI according to HIPAA Safe Harbor: names, dates, geographic locations, phone numbers, email addresses, SSNs, medical record numbers, account numbers, certificate numbers, vehicle/device IDs, URLs, IP addresses, biometric identifiers, photos, unique identifying codes, and ages over 89 years."
```

**位置 2（第 276-297 行）：**
```python
def _identify_phi_chunked(self, text, language, return_source, return_entities):
    regulation_docs = []
    context = ""
    
    if self.config.retrieve_regulation_context and self.regulation_chain:
        # ... 原有邏輯 ...
        context = "\n\n".join([...])
    else:
        # ✅ 修改這裡
        context = "Identify PHI according to HIPAA Safe Harbor: names, dates, geographic locations, phone numbers, email addresses, SSNs, medical record numbers, account numbers, certificate numbers, vehicle/device IDs, URLs, IP addresses, biometric identifiers, photos, unique identifying codes, and ages over 89 years."
```

## 📈 預期改善

**修改前：**
- Prompt: 1579 字元
- 時間: >150 秒（超時）
- 成功率: 0%

**修改後：**
- Prompt: ~800-900 字元（減少 45%）
- 時間: ~10-20 秒
- 成功率: ~90%+

## 🚀 執行修復

```bash
# 1. 應用修復
# 編輯 phi_identification_chain.py（見上方代碼）

# 2. 測試
python test_batch_scenario.py  # 應該在 10-20 秒內完成

# 3. 執行實際批次處理
python examples/simple_batch_test.py  # 應該能成功完成

# 4. 提交修復
git add medical_deidentification/infrastructure/rag/phi_identification_chain.py
git commit -m "fix: Reduce context length to fix Ollama timeout issue"
```
