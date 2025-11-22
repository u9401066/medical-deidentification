# Ollama 本地 LLM 整合說明

## 📦 為什麼使用 Ollama？

OpenAI API 在測試中回應極度緩慢（>5分鐘/請求），因此整合本地 LLM 方案：

**優勢**:
- 🚀 **快速**: 本地推理，無網路延遲
- 💰 **免費**: 開源模型，無 API 費用
- 🔒 **隱私**: 醫療敏感數據不上傳雲端
- 🎯 **準確**: Qwen 2.5, Llama 3.1 等高品質模型

---

## 🛠️ 安裝 Ollama

### 1. 下載並安裝
訪問 [https://ollama.ai/download](https://ollama.ai/download) 下載適合你系統的版本。

### 2. 啟動 Ollama 服務
```bash
ollama serve
```
（在 Windows 上，安裝後會自動啟動服務）

### 3. 下載推薦模型

```bash
# Qwen 2.5 7B (推薦) - 中英文優秀，PHI 識別準確
ollama pull qwen2.5:7b

# Llama 3.1 8B - 通用性強
ollama pull llama3.1:8b

# Mistral 7B - 速度快
ollama pull mistral:7b
```

### 4. 驗證安裝
```bash
ollama list
```
應該能看到你下載的模型。

---

## 💻 使用方式

### 方法 1: 使用預設配置

```python
from medical_deidentification.infrastructure.llm.config import LLMPresets
from medical_deidentification.infrastructure.llm.factory import create_llm

# 使用 Qwen 2.5 7B
config = LLMPresets.local_qwen()
llm = create_llm(config)

response = llm.invoke("你的 prompt")
```

### 方法 2: 自訂配置

```python
from medical_deidentification.infrastructure.llm.config import LLMConfig
from medical_deidentification.infrastructure.llm.factory import create_llm

config = LLMConfig(
    provider="ollama",
    model_name="qwen2.5:7b",
    temperature=0.0,
    max_tokens=2048,
)

llm = create_llm(config)
```

### 方法 3: 在 PHI 識別中使用

```python
from medical_deidentification.infrastructure.rag.phi_identification_chain import (
    PHIIdentificationConfig,
    PHIIdentificationChain
)
from medical_deidentification.infrastructure.llm.config import LLMConfig

# 配置使用 Ollama
llm_config = LLMConfig(
    provider="ollama",
    model_name="qwen2.5:7b",
    temperature=0.0,
)

phi_config = PHIIdentificationConfig(
    llm_config=llm_config,
    retrieve_regulation_context=False,
    use_structured_output=False,  # ⚠️ Ollama 可能不支援 structured output
)

phi_chain = PHIIdentificationChain(regulation_chain, phi_config)
```

---

## 🧪 測試整合

執行測試腳本：

```bash
python test_ollama_llm.py
```

測試包含：
1. ✅ 基本連接測試
2. ✅ PHI 識別測試
3. ✅ 模型比較測試

---

## 📊 支援的模型

| 模型 | 大小 | 特點 | 推薦用途 |
|------|------|------|---------|
| `qwen2.5:7b` | 7B | 中英文優秀 | ⭐ PHI 識別 |
| `qwen2.5:14b` | 14B | 更高準確率 | 複雜醫療文本 |
| `llama3.1:8b` | 8B | 通用性強 | 通用 NLP |
| `mistral:7b` | 7B | 速度快 | 快速推理 |
| `gemma2:9b` | 9B | Google 出品 | 實驗性 |

---

## ⚙️ 配置選項

```python
LLMConfig(
    provider="ollama",
    model_name="qwen2.5:7b",       # 模型名稱
    temperature=0.0,                # 0.0 = 確定性, 1.0 = 創造性
    max_tokens=2048,                # 最大輸出長度
    timeout=30.0,                   # 請求超時（秒）
    api_base="http://localhost:11434",  # Ollama API 地址（可選）
)
```

---

## ⚠️ 限制與注意事項

### Structured Output 支援
Ollama 目前**可能不完全支援** LangChain 的 `with_structured_output()`。

**解決方案**:
1. 使用 `use_structured_output=False` 配置
2. 改用 JSON mode 或手動解析
3. 在 prompt 中明確要求 JSON 格式輸出

### 記憶體需求
- 7B 模型: ~4-6 GB RAM
- 14B 模型: ~8-10 GB RAM
- 32B 模型: ~20+ GB RAM

### GPU 加速
有 GPU 的話會自動使用，推理速度可提升 10-50 倍。

---

## 🔧 故障排除

### 問題 1: "Connection refused"
**原因**: Ollama 服務未啟動  
**解決**: 執行 `ollama serve` 或檢查服務狀態

### 問題 2: "Model not found"
**原因**: 模型未下載  
**解決**: `ollama pull qwen2.5:7b`

### 問題 3: 推理太慢
**原因**: 
- CPU 推理較慢（正常）
- 模型太大

**解決**:
- 使用較小模型 (7B 而非 14B)
- 使用 GPU
- 減少 `max_tokens`

### 問題 4: "langchain_community not installed"
**原因**: 缺少依賴  
**解決**: `pip install langchain-community`

---

## 📈 效能比較

基於內部測試（非正式）:

| Provider | 模型 | 回應時間 | 成本 | 隱私 |
|----------|------|---------|------|------|
| OpenAI | gpt-4o-mini | 3-5秒* | $$ | ⚠️ 雲端 |
| OpenAI | gpt-4o-mini | >5分鐘** | $$ | ⚠️ 雲端 |
| Ollama | qwen2.5:7b | 2-10秒 | 免費 | ✅ 本地 |
| Ollama | llama3.1:8b | 2-10秒 | 免費 | ✅ 本地 |

\* 正常情況  
\*\* 測試時遇到的異常緩慢

---

## 🎯 最佳實踐

### PHI 識別推薦配置

```python
# 快速測試用
config_fast = LLMConfig(
    provider="ollama",
    model_name="mistral:7b",
    temperature=0.0,
    max_tokens=1024,
)

# 準確度優先
config_accurate = LLMConfig(
    provider="ollama",
    model_name="qwen2.5:14b",
    temperature=0.0,
    max_tokens=2048,
)

# 平衡性（推薦）
config_balanced = LLMPresets.local_qwen()  # qwen2.5:7b
```

---

## 📚 參考資源

- [Ollama 官網](https://ollama.ai/)
- [Ollama GitHub](https://github.com/ollama/ollama)
- [支援的模型列表](https://ollama.ai/library)
- [LangChain Ollama 文檔](https://python.langchain.com/docs/integrations/chat/ollama)

---

## 🆘 需要幫助？

1. 查看 `test_ollama_llm.py` 測試腳本
2. 執行 `ollama --help` 查看命令
3. 訪問 Ollama Discord 社群

---

**Last Updated**: 2024-11-22  
**Version**: 1.0.0
