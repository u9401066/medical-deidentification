# Batch PHI Identification Processing

## 概述 Overview

`BatchPHIProcessor` 是一個專門用於批次處理 Excel 檔案中多行醫療文本的 PHI 識別模組。它將測試腳本中的批次處理功能正式整合到 pipeline 架構中。

## 核心功能 Core Features

1. **Excel 批次讀取** - 載入並處理整個 Excel 檔案
2. **行文本合併** - 智能合併每行的所有欄位，保留欄位名稱標記
3. **進度追蹤** - 實時記錄處理進度和統計資訊
4. **錯誤處理** - 單行失敗不影響整體處理
5. **結果聚合** - 自動生成 PHI 類型分布、信心度統計
6. **Excel 輸出** - 將所有識別結果匯出為結構化 Excel

## 架構設計 Architecture

```
BatchPHIProcessor
├── Configuration
│   ├── BatchProcessingConfig (批次處理參數)
│   └── PHIIdentificationConfig (PHI識別參數)
├── Processing
│   ├── Excel Loading (載入數據)
│   ├── Row Iteration (逐行處理)
│   └── PHI Identification (調用PHIIdentificationChain)
└── Results
    ├── RowProcessingResult (單行結果)
    ├── BatchProcessingResult (批次結果)
    └── Excel Export (結果輸出)
```

## 使用方法 Usage

### 基本使用

```python
from medical_deidentification.application.processing import (
    BatchPHIProcessor,
    BatchProcessingConfig,
    save_batch_results
)
from medical_deidentification.infrastructure.rag import PHIIdentificationChain
from medical_deidentification.infrastructure.llm import LLMConfig

# 1. 配置 LLM（使用 Ollama）
llm_config = LLMConfig(
    provider="ollama",
    model_name="llama3.1:8b",
    temperature=0.0,
    timeout=120
)

# 2. 初始化 PHI identification chain
phi_chain = PHIIdentificationChain(regulation_chain, config)

# 3. 配置批次處理器
batch_config = BatchProcessingConfig(
    max_rows=None,  # 處理所有行
    language="zh-TW",
    skip_empty_rows=True,
    combine_columns=True,
    log_progress_interval=10  # 每10行記錄一次進度
)

# 4. 創建批次處理器
processor = BatchPHIProcessor(phi_chain, batch_config)

# 5. 處理 Excel 檔案
result = processor.process_excel_file(
    "data/medical_cases.xlsx",
    case_id_column="案例編號"
)

# 6. 儲存結果
save_batch_results([result], "output_results.xlsx")
```

### 完整範例

參見 `test_batch_processor.py`：

```bash
python test_batch_processor.py
```

## 配置選項 Configuration Options

### BatchProcessingConfig

| 參數 | 類型 | 預設值 | 說明 |
|------|------|--------|------|
| `max_rows` | `Optional[int]` | `None` | 限制處理行數（None=全部） |
| `language` | `str` | `"zh-TW"` | 文本語言 |
| `skip_empty_rows` | `bool` | `True` | 跳過空行 |
| `combine_columns` | `bool` | `True` | 合併所有欄位為單一文本 |
| `log_progress_interval` | `int` | `10` | 每N行記錄一次進度 |

### PHIIdentificationConfig

| 參數 | 類型 | 預設值 | 說明 |
|------|------|--------|------|
| `llm_config` | `LLMConfig` | - | LLM 配置 |
| `retrieve_regulation_context` | `bool` | `True` | 是否檢索法規上下文 |
| `use_structured_output` | `bool` | `True` | 使用結構化輸出 |

**Ollama 特殊配置：**
```python
PHIIdentificationConfig(
    llm_config=ollama_config,
    retrieve_regulation_context=False,  # ⚠️ 避免 FAISS 維度不匹配
    use_structured_output=False,  # ⚠️ Ollama 不支援
)
```

## 結果結構 Result Structure

### BatchProcessingResult

```python
@dataclass
class BatchProcessingResult:
    file_name: str              # 檔案名稱
    total_rows: int             # 總行數
    processed_rows: int         # 成功處理行數
    total_entities: int         # 總 PHI 實體數
    total_time: float           # 總處理時間（秒）
    average_time_per_row: float # 平均每行時間
    row_results: List[RowProcessingResult]  # 各行詳細結果
```

**可用方法：**
- `get_phi_type_distribution()` - 獲取 PHI 類型分布
- `get_confidence_statistics()` - 獲取信心度統計
- `to_dataframe()` - 轉換為 pandas DataFrame

### RowProcessingResult

```python
@dataclass
class RowProcessingResult:
    row_number: int             # 行號
    case_id: str                # 案例 ID
    text_length: int            # 文本長度
    entities: List[PHIEntity]   # 識別的 PHI 實體
    processing_time: float      # 處理時間
    success: bool               # 是否成功
    error_message: Optional[str]  # 錯誤訊息
```

## 輸出格式 Output Format

### Excel 輸出欄位

| 欄位 | 說明 |
|------|------|
| `file` | 源檔案名稱 |
| `row` | 行號 |
| `case_id` | 案例 ID |
| `phi_type` | PHI 類型（如 NAME, AGE_OVER_89） |
| `phi_text` | 識別的 PHI 文本 |
| `start_pos` | 起始位置 |
| `end_pos` | 結束位置 |
| `confidence` | 信心度 (0.0-1.0) |
| `reason` | 識別原因說明 |
| `regulation_source` | 法規來源 |

### 範例輸出

```
file                    row  case_id  phi_type        phi_text  confidence  reason
----                    ---  -------  --------        --------  ----------  ------
case_details.xlsx       1    A001     NAME            張三      0.95        患者姓名
case_details.xlsx       1    A001     AGE_OVER_89     94歲      1.00        年齡超過89歲
case_details.xlsx       1    A001     RARE_DISEASE    法布瑞氏症 0.90       罕見疾病診斷
```

## 性能考量 Performance Considerations

### 處理時間估算

- **Ollama (llama3.1:8b)**: ~15-25 秒/行（中文醫療文本，1000-1500字）
- **OpenAI GPT-4**: ~3-5 秒/行
- **Anthropic Claude**: ~2-4 秒/行

### 優化建議

1. **限制行數測試**：先用 `max_rows=5` 測試配置
2. **調整日誌頻率**：大批次處理時增加 `log_progress_interval`
3. **並行處理**：未來可考慮實現多執行緒版本
4. **批次大小**：建議每批次 100-500 行

## 錯誤處理 Error Handling

BatchPHIProcessor 採用「繼續執行」策略：

```python
# 單行失敗不影響整體處理
try:
    entities = identify_phi(row_text)
except Exception as e:
    logger.error(f"Row {row_num} failed: {e}")
    # 記錄錯誤但繼續處理下一行
    continue
```

失敗行會在結果中標記：
```python
RowProcessingResult(
    success=False,
    error_message="Timeout after 120s",
    entities=[]
)
```

## 與舊測試腳本比較

| 功能 | 舊腳本 (test_phi_batch_ollama.py) | 新模組 (BatchPHIProcessor) |
|------|-----------------------------------|----------------------------|
| **架構** | 獨立測試腳本 | 正式 pipeline 模組 |
| **可重用性** | ❌ 不可重用 | ✅ 可在專案任何地方導入 |
| **配置** | 硬編碼 | ✅ 靈活的 Config 類 |
| **結果結構** | 臨時 dict | ✅ 結構化 dataclass |
| **統計資訊** | 手動計算 | ✅ 自動聚合 |
| **錯誤處理** | 基本 try-catch | ✅ 完整錯誤追蹤 |
| **日誌** | 分散的 logger | ✅ 結構化日誌 |
| **測試** | ❌ 無單元測試 | ✅ 可測試設計 |

## 後續規劃 Future Enhancements

1. **並行處理**：支援多執行緒/多進程批次處理
2. **進度條**：添加 tqdm 進度條視覺化
3. **斷點續傳**：保存中間結果，支援中斷後恢復
4. **多檔案批次**：一次處理整個目錄的檔案
5. **結果驗證**：添加人工審核介面
6. **性能監控**：記錄詳細的性能指標

## 相關文件 Related Documentation

- [PHI Identification Chain](./phi_identification.md)
- [LLM Configuration](./llm_config.md)
- [Regulation Retrieval](./regulation_retrieval.md)

## 問題排查 Troubleshooting

### 問題：Ollama 處理掛起

**原因**：Ollama 有內容安全過濾機制

**解決**：
```python
# 使用 "data redaction" 替代 "PHI identification"
# 已在 prompts/templates.py 中修改
```

### 問題：FAISS 維度不匹配

**原因**：Vector store 使用不同的 embedding 模型

**解決**：
```python
PHIIdentificationConfig(
    retrieve_regulation_context=False  # 禁用檢索，使用默認規則
)
```

### 問題：處理速度慢

**解決方案**：
1. 使用更快的 LLM（OpenAI GPT-4-turbo）
2. 限制 `max_rows` 進行測試
3. 考慮批次處理優化（未來功能）

---

**最後更新**: 2024-12-XX  
**維護者**: Medical Deidentification Team
