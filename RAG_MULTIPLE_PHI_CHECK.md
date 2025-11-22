# RAG Structured Output 多個 PHI 識別能力檢查報告

## 📋 檢查目的
驗證 RAG 回傳的 structured output 是否能**正確產出多個 PHI 類型識別**。

## ✅ 代碼架構檢查結果

### 1. PHIDetectionResponse 結構 ✅ 正確

**位置**: `medical_deidentification/infrastructure/rag/phi_identification_chain.py:148`

```python
class PHIDetectionResponse(BaseModel):
    """Complete PHI detection response (multiple entities)"""
    
    entities: List[PHIIdentificationResult] = Field(
        default_factory=list,
        description="List of detected PHI entities"  # ✅ 使用 List，支援多個
    )
    total_entities: int = Field(
        ge=0,
        description="Total number of entities detected"
    )
    has_phi: bool = Field(
        description="Whether any PHI was detected"
    )
```

**結論**: ✅ **結構正確**，使用 `List[PHIIdentificationResult]` 可以包含多個 PHI entities。

---

### 2. PHIIdentificationResult 結構 ✅ 正確

**位置**: `medical_deidentification/infrastructure/rag/phi_identification_chain.py:37`

```python
class PHIIdentificationResult(BaseModel):
    """單個 PHI 實體的結構化識別結果"""
    
    entity_text: str          # PHI 文本
    phi_type: PHIType         # PHI 類型枚舉
    start_position: int       # 起始位置
    end_position: int         # 結束位置
    confidence: float         # 信心度 (0.0-1.0)
    reason: str              # 識別原因
    regulation_source: Optional[str]  # 法規來源
    # ... 其他欄位
```

**結論**: ✅ **結構完整**，包含所有必要的 PHI 資訊。

---

### 3. 識別邏輯 ✅ 正確

**位置**: `medical_deidentification/infrastructure/rag/phi_identification_chain.py:340`

```python
def _identify_phi_structured(...) -> Tuple[List[PHIEntity], List[PHIIdentificationResult]]:
    # Create structured output LLM
    llm_structured = self.llm.with_structured_output(PHIDetectionResponse)
    
    # Get structured response
    detection_response: PHIDetectionResponse = llm_structured.invoke(prompt)
    
    # Convert to domain entities (處理整個 List)
    entities = [result.to_phi_entity() for result in detection_response.entities]
    
    return entities, detection_response.entities
```

**關鍵點**:
- ✅ 使用 `detection_response.entities` 遍歷所有識別到的 PHI
- ✅ 返回完整的 `List[PHIEntity]` 而非單一實體
- ✅ 包含 fallback 機制 (`_identify_phi_json_fallback`)

**結論**: ✅ **邏輯正確**，代碼設計為處理多個 PHI entities。

---

### 4. Prompt 設計 ✅ 正確

**位置**: `medical_deidentification/infrastructure/prompts/templates.py:90`

```python
PHI_IDENTIFICATION_STRUCTURED_PROMPT_V1 = """
Based on these regulations, identify all PHI in the medical text.

...

Instructions:
1. Identify ALL PHI entities according to regulations  # ✅ 明確要求「ALL」
2. Pay special attention to:
   - Ages over 89 (HIPAA) or 90 (Taiwan)
   - Rare diseases that could identify individuals
   - Specific location information
   - Names and identifiers
3. Provide entity_text, phi_type, start_position, end_position, confidence, reason
4. Return structured response with all detected entities  # ✅ 要求「all detected」
"""
```

**結論**: ✅ **Prompt 正確**，明確指示 LLM 識別**所有** PHI entities。

---

## 🧪 測試驗證

### 測試腳本
創建了 `test_multiple_phi_detection.py` 來驗證多個 PHI 識別能力。

### 測試案例

| Test | 文本內容 | 期望 PHI 數量 | PHI 類型 |
|------|---------|--------------|---------|
| Test 1 | 簡單案例：姓名、年齡、電話、地址 | ≥3 | NAME, AGE, PHONE, ADDRESS |
| Test 2 | 複雜案例：94歲、罕病、多個ID、醫師名 | ≥7 | NAME, AGE_OVER_89, DISEASE, ID, DATE, DOCTOR, ADDRESS, PHONE |
| Test 3 | 邊界案例：92歲、龐貝氏症 | ≥3 | ID, AGE_OVER_89, DISEASE, ADDRESS |

### 測試狀態
⏳ **測試執行中** - 等待 OpenAI API 回應（API 回應較慢，約 3-5秒/請求）

---

## 📊 代碼架構總結

```
文本輸入
    ↓
PHIIdentificationChain.identify_phi()
    ↓
_identify_phi_structured()
    ↓
llm_structured.invoke(prompt)  ← 使用 PHIDetectionResponse schema
    ↓
PHIDetectionResponse {
    entities: [
        PHIIdentificationResult {...},  ← PHI #1
        PHIIdentificationResult {...},  ← PHI #2
        PHIIdentificationResult {...},  ← PHI #3
        ...                              ← 可以有更多
    ],
    total_entities: N,
    has_phi: true
}
    ↓
轉換為 List[PHIEntity]
    ↓
返回多個 PHI entities
```

---

## ✅ 結論

### 代碼設計層面
**✅ 完全正確** - RAG structured output 的代碼架構完全支援識別多個 PHI：

1. ✅ **資料結構**: `List[PHIIdentificationResult]` 支援多個 entities
2. ✅ **處理邏輯**: 遍歷所有 entities 並轉換
3. ✅ **Prompt 設計**: 明確要求識別「ALL PHI entities」
4. ✅ **返回格式**: 返回完整的 `List[PHIEntity]`

### 實際執行層面
⏳ **待驗證** - 需要等待測試完成以確認：
- LLM (gpt-4o-mini) 是否正確理解並返回多個 PHI
- Structured output 是否正確解析多個 entities
- 所有 PHI 類型是否都能被識別

---

## 🔍 潛在問題（如果測試失敗）

### 如果只識別到 1 個 PHI：

**可能原因**:
1. **LLM 限制**: gpt-4o-mini 可能只返回第一個找到的 PHI
2. **Prompt 不夠明確**: 需要加強「list all」的指示
3. **Token 限制**: 回應被截斷

**解決方案**:
```python
# 加強 prompt
prompt += "\n\nIMPORTANT: Return ALL PHI entities found in the text as a list. Do not stop after finding one entity."

# 或使用更強大的模型
model_name="gpt-4"  # 而非 gpt-4o-mini
```

### 如果 structured output 解析失敗：

**可能原因**:
1. LLM 返回格式不符合 schema
2. 欄位名稱不匹配

**解決方案**:
- 使用 fallback 機制 (`_identify_phi_json_fallback`)
- 檢查 LLM 原始回應

---

## 📝 建議

1. **等待測試完成** 查看實際執行結果
2. **如果成功**: 代碼無需修改，可以處理多個 PHI
3. **如果失敗**: 根據錯誤訊息調整 prompt 或 model
4. **優化建議**: 可以添加範例到 prompt 中展示多個 PHI 的格式

---

## 🎯 快速驗證命令

```bash
# 查看測試結果
python test_multiple_phi_detection.py

# 或查看 log
Get-Content test_multi_phi.log | Select-String -Pattern "識別到|PASS|FAIL"
```
