# Progress (Updated: 2025-12-30)

## Done

- Python 3.12 升級完成
- LangChain json_schema 方法修復
- License 更新為 Apache 2.0
- Author 修正為 u9401066
- Benchmark 計畫文件 (docs/benchmark-plan.md)
- 建立 benchmark 評估模組 (scripts/benchmark/)
- 安裝 presidio-evaluator + spacy + langchain-community
- 產生 100 筆 Presidio 合成 PHI 資料
- 執行 granite4:1b benchmark: F1=0.69, 9.57s/sample
- 執行 qwen2.5:1.5b benchmark: F1=0.37, 3.49s/sample
- 建立 optimized_evaluator.py 優化版評估器

## Doing

- Git commit 和 push

## Next

- 建立台灣 PHI 產生器
- 取得 i2b2 資料集 (需 DUA)
- 考慮 GPU 加速或更小模型
