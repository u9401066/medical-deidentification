# Active Context

## Current Goals

- ## 當前工作焦點 (2025-12-30)
- ### Benchmark 建立計畫
- #### 黃金標準資料集 (Gold Standards)
- 1. **i2b2 2006 De-identification Challenge**
- - 889 份出院摘要 (Discharge Summaries)
- - HIPAA 18 類 PHI 標註
- - 業界標準 baseline
- 2. **i2b2 2014 De-identification Challenge**
- - 1,304 份病歷，更多樣的 PHI 格式
- - 取得方式：DBMI Data Portal (n2c2) 註冊申請
- 3. **CBLUE CMeEE (中文)**
- - 中文醫療實體識別 Benchmark
- - 可測試「醫療機構」、「部位」等欄位
- - GitHub: CBLUE
- #### 合成資料工具
- 1. **Synthea** - 合成病患生成器 (Java)
- - 可生成 HL7/FHIR 標準病歷
- - 英文為主，結構完整
- 2. **Microsoft Presidio Evaluator**
- - 假資料生成 + F1-Score 計算
- - 完整評估流程
- ### 技術棧
- - **Python**: 3.12.12
- - **Package Manager**: uv 0.9.17
- - **LLM**: granite4:1b (131K context)
- - **LangChain**: with_structured_output(method="json_schema")
- - **單元測試**: 85/85 passed (100%)

## Current Session Focus (Dec 30, 2025)

### Lightweight LLM Benchmark Completed ✅
完成 CPU 環境輕量 LLM 效能評測：

| 模型 | F1 Score | 速度 | 推薦 |
|------|----------|------|------|
| **granite4:1b** | 89.4% | ~16s | 🏆 最佳品質 |
| **qwen2.5:1.5b** | 66.7% | ~4s | ⭐ 最佳平衡 |
| llama3.2:1b | 55.0% | ~8s | 可用 |
| smollm2:360m | 0% | ~4s | ❌ 太小 |

### Changes Made
1. **預設模型更新為 `granite4:1b`**
   - `phi_module.py` 已更新
   - LIGHTWEIGHT_MODELS 字典包含 benchmark 數據
2. **新增 Benchmark 腳本**: `scripts/benchmark_lightweight_llms.py`
3. **新增文件**: `docs/llm-benchmark-results.md`

### Previous Issue (Resolved)
- Ollama `with_structured_output` 慢的問題
- 解決方案：使用 `granite4:1b` 替代小模型，JSON 輸出穩定

### Next Steps
1. 使用 `granite4:1b` 進行完整的 PHI 去識別化測試
2. 考慮 DSPy 優化來進一步提升 F1 Score
3. 可選：測試 GPU 環境下的效能

## Current Blockers

- None ✅