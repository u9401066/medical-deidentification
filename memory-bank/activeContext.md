# Active Context

## Current Goals

- 發現 regulation_chain.py 架構問題：混淆了法規檢索 (RegulationRetriever) 和醫療文本 PHI 識別 (MedicalTextRetriever) 兩個不同職責。需要重構拆分為兩個獨立 Chain，共用 LLM 和 Prompts 模組。716 行代碼太長難以維護。

## Current Blockers

- None yet