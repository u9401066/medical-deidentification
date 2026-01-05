# 後端改善文件

## 已完成
- ✅ 移除 mock 處理，直接使用真正的 DeidentificationEngine
- ✅ PHI 詳細資訊提取 - 引擎現在返回完整的 PHI 實體列表
- ✅ 處理後輸出檔案路徑 - 引擎現在返回 output_path
- ✅ 原始內容與遮罩內容 - 引擎現在返回 original_content 和 masked_content
- ✅ 按 PHI 類型統計 - summary 中新增 phi_by_type

## 引擎改進詳情

### ProcessingResult 新增欄位

**documents[] 新增:**
```python
{
    "document_id": "...",
    "filename": "...",
    "phi_entities_count": 5,
    "phi_entities": [  # 新增！PHI 詳細列表
        {
            "type": "NAME",
            "text": "王小明",
            "start_pos": 10,
            "end_pos": 13,
            "confidence": 0.95,
            "reason": "Personal name identified",
            "regulation_source": "HIPAA"
        },
        ...
    ],
    "masked_content": "...",  # 新增！遮罩後內容
    "original_content": "...", # 新增！原始內容（前10000字元）
    "output_path": "data/output/results/...",  # 新增！輸出檔案路徑
    ...
}
```

**summary 新增:**
```python
{
    "phi_entities": [...],  # 新增！所有 PHI 實體彙總
    "phi_by_type": {        # 新增！按類型統計
        "NAME": 3,
        "DATE": 2,
        "PHONE": 1
    },
    ...
}
```

## 待改善項目

### 1. 處理速度優化 (Low Priority)

**問題描述:**
每次處理都重新初始化引擎，效率較低。

**建議解決方案:**
- 使用單例模式或全域引擎實例
- 實作引擎池 (Engine Pool)
- 懶載入 RAG 組件

### 2. Excel/CSV 結構化 Diff (Enhancement)

**問題描述:**
目前 diff 顯示是基於文字內容，對於 Excel/CSV 檔案，應該提供欄位級別的 diff。

**建議解決方案:**
- 在處理 Excel/CSV 時，記錄每個 PHI 的 row/column 位置
- 提供 cell-by-cell 的 diff 資料

---

## 測試方法

```bash
# 測試引擎處理並檢查新欄位
cd /home/eric/workspace251230/medical-deidentification
source .venv/bin/activate
python -c "
from core.application.processing.engine import DeidentificationEngine, EngineConfig
config = EngineConfig(llm_provider='ollama', llm_model='qwen2.5:1.5b', use_rag=False)
engine = DeidentificationEngine(config)
result = engine.process_file('data/test/test_phi.csv')

print('=== 基本資訊 ===')
print(f'Total PHI: {result.total_phi_entities}')
print(f'Documents count: {len(result.documents)}')

print('\\n=== Document 詳情 ===')
if result.documents:
    doc = result.documents[0]
    print(f'Filename: {doc.get(\"filename\")}')
    print(f'PHI count: {doc.get(\"phi_entities_count\")}')
    print(f'PHI entities: {doc.get(\"phi_entities\", [])[:3]}...')  # 前3個
    print(f'Output path: {doc.get(\"output_path\")}')
    print(f'Has masked_content: {bool(doc.get(\"masked_content\"))}')

print('\\n=== Summary ===')
print(f'PHI by type: {result.summary.get(\"phi_by_type\", {})}')
print(f'Total PHI in summary: {len(result.summary.get(\"phi_entities\", []))}')
"
```
