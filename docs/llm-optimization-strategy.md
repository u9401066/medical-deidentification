# 🚀 LLM PHI 偵測優化策略

> 針對 8B 小模型效能和正確率問題的優化方案

## 📊 問題診斷

### 現況
- **模型規模**: 8B 參數 (如 llama3.1:8b, qwen2.5:7b)
- **效能問題**: 推理速度可能不夠快
- **正確率問題**: F1 可能低於預期

### 診斷步驟

```bash
# 1. 先執行 benchmark 了解現狀
export OLLAMA_BASE_URL=http://172.18.11.101:30133
python scripts/benchmark/llm_benchmark.py --models "qwen2.5:7b,llama3.1:8b"

# 2. 查看可用模型
curl -s $OLLAMA_BASE_URL/api/tags | jq '.models[].name'
```

---

## ⚡ 效能優化策略

### 策略 1: 換更小的模型 (速度優先)

| 模型 | 參數量 | 預估速度 | 適用場景 |
|------|--------|----------|----------|
| `smollm2:360m` | 0.36B | 極快 | 簡單 PHI |
| `qwen2.5:1.5b` | 1.5B | 很快 | 基本 PHI |
| `granite4:1b` | 1B | 很快 | 平衡選擇 ✅ |
| `llama3.2:3b` | 3B | 快 | 較複雜文本 |

```python
# config.py 設定
LLM_MODEL = "granite4:1b"  # 我們 benchmark 最佳 F1=89.4%
```

### 策略 2: 批次處理 (Batching)

```python
# 不要一次處理一份文件，而是批次處理
# 減少模型載入/卸載開銷

# Bad: 逐筆處理
for doc in documents:
    result = llm.invoke(doc)

# Good: 批次處理 (利用 keep_alive)
from langchain_ollama import ChatOllama

llm = ChatOllama(
    model="qwen2.5:7b",
    keep_alive="30m",  # 保持模型在記憶體 30 分鐘
    num_ctx=4096,      # 減少 context window 加速
)

# 連續處理，模型不會被卸載
for doc in documents:
    result = llm.invoke(doc)
```

### 策略 3: Streaming + 早停

```python
# 對於結構化輸出，一旦收到完整 JSON 就停止
import json

def stream_until_json_complete(llm, prompt):
    buffer = ""
    for chunk in llm.stream(prompt):
        buffer += chunk.content
        try:
            # 嘗試解析 JSON
            result = json.loads(buffer)
            return result  # 成功就提早返回
        except json.JSONDecodeError:
            continue
    return json.loads(buffer)
```

### 策略 4: 量化模型

```bash
# 使用量化版本 (如果可用)
ollama pull qwen2.5:7b-instruct-q4_K_M  # 4-bit 量化，速度更快
```

---

## 🎯 正確率優化策略

### 策略 1: 優化 Prompt

```python
# 差的 Prompt
prompt = "找出 PHI: {text}"

# 好的 Prompt (Few-shot + 結構化)
prompt = '''你是醫療資料去識別化專家。

## 任務
識別以下醫療文本中的個人健康資訊(PHI)。

## PHI 類型定義
- NAME: 姓名（患者、醫師、家屬）
- DATE: 日期（就診日、出生日）
- AGE_OVER_89: 超過 89 歲的年齡
- LOCATION: 地址、地點
- PHONE: 電話號碼
- EMAIL: 電子郵件
- ID: 身分證字號
- MEDICAL_RECORD_NUMBER: 病歷號
- HOSPITAL_NAME: 醫療機構名稱
- RARE_DISEASE: 罕見疾病名稱

## 範例
輸入: "患者張三，45歲，病歷號A123"
輸出: {{"phi_entities": [
  {{"text": "張三", "type": "NAME"}},
  {{"text": "45歲", "type": "AGE"}},
  {{"text": "A123", "type": "MEDICAL_RECORD_NUMBER"}}
]}}

## 待處理文本
{text}

## 輸出 (JSON 格式)
'''
```

### 策略 2: 使用更大模型 (正確率優先)

| 模型 | 參數量 | 預估 F1 | 適用場景 |
|------|--------|---------|----------|
| `qwen2.5:14b` | 14B | ~92% | 高準確需求 |
| `llama3.3:70b` | 70B | ~95% | 關鍵文件 |
| `gpt-oss:120b` | 120B | ~97% | 最高準確 |

### 策略 3: 多階段驗證

```python
# 第一階段：快速模型初篩
fast_llm = ChatOllama(model="granite4:1b")
initial_result = fast_llm.invoke(prompt)

# 第二階段：大模型驗證可疑項目
if needs_verification(initial_result):
    big_llm = ChatOllama(model="qwen2.5:14b")
    verified_result = big_llm.invoke(verification_prompt)
```

### 策略 4: Ensemble 多模型投票

```python
models = ["qwen2.5:7b", "llama3.1:8b", "granite4:1b"]
results = []

for model in models:
    llm = ChatOllama(model=model)
    result = llm.invoke(prompt)
    results.append(result)

# 多數決
final_phi = vote(results)  # 至少 2/3 模型同意才算
```

---

## 📈 效能 vs 正確率權衡

```
正確率 (F1)
    ^
    │
95% │                        ● gpt-oss:120b
    │                  ● llama3.3:70b
    │            ● qwen2.5:14b
90% │      ● granite4:1b ← 推薦平衡點
    │    ● llama3.1:8b
    │  ● qwen2.5:7b
85% │● llama3.2:3b
    │
    └─────────────────────────────────────> 速度 (tok/s)
         10    50   100   200   500
```

### 推薦配置

| 場景 | 推薦模型 | 理由 |
|------|----------|------|
| **開發測試** | `granite4:1b` | 快速迭代 |
| **一般處理** | `qwen2.5:7b` | 平衡 |
| **高準確需求** | `qwen2.5:14b` | 重要文件 |
| **關鍵資料** | `llama3.3:70b` | 不容許錯誤 |

---

## 🔧 實作建議

### 1. 先跑 Benchmark
```bash
python scripts/benchmark/llm_benchmark.py
```

### 2. 根據結果選擇策略
- F1 < 85%: 換大模型或優化 Prompt
- 延遲 > 5s: 換小模型或批次處理
- 兩者都有問題: 考慮多階段處理

### 3. 持續監控
```python
# 加入監控
from loguru import logger

@monitor_performance
def process_document(doc):
    start = time.time()
    result = llm.invoke(doc)
    logger.info(f"處理時間: {time.time()-start:.2f}s, PHI數量: {len(result)}")
    return result
```

---

## 📅 下一步行動

1. [ ] 在可連線的機器上執行 `llm_benchmark.py`
2. [ ] 記錄各模型的 F1/延遲數據
3. [ ] 根據需求選擇最佳模型
4. [ ] 如果正確率不足，優化 Prompt
5. [ ] 如果速度不足，考慮批次處理或更小模型
