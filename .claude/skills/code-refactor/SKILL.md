---
name: code-refactor
description: Proactively suggest and execute code refactoring to maintain clean architecture. Triggers: refactor, 重構, 優化程式碼, clean up, 整理程式碼.
---

# 程式碼重構技能

## 描述

主動建議並執行程式碼重構，維持乾淨架構。

## 觸發條件

- 「refactor」「重構」「優化程式碼」
- AI 偵測到程式碼需要重構時主動建議

## 重構原則

> 依據憲法第 7.3 條「主動重構原則」

1. **持續重構**：程式碼應隨時保持可重構狀態
2. **單一職責**：一個模組/類別/函數只做一件事
3. **適時拆分**：當檔案/函數過長時必須拆分
4. **架構守護**：重構時必須維持 DDD 分層架構

## 觸發閾值

| 指標 | 建議閾值 | 硬性上限 |
|------|----------|----------|
| 檔案行數 | 200 行 | 400 行 |
| 函數行數 | 30 行 | 50 行 |
| 類別行數 | 150 行 | 300 行 |
| 圈複雜度 | 10 | 15 |

## 重構模式

| 問題 | 重構模式 | 說明 |
|------|----------|------|
| 函數過長 | Extract Method | 提取私有方法 |
| 類別過大 | Extract Class | 提取新類別 |
| 重複程式碼 | Extract Superclass | 抽取共用邏輯 |
| 過多參數 | Parameter Object | 建立參數物件 |
| 條件過複雜 | Polymorphism | 用多態取代條件 |

## 安全網

### 重構前
1. ✅ 確保測試覆蓋
2. ✅ 執行現有測試
3. ✅ 記錄到 decisionLog.md

### 重構後
1. ✅ 執行全部測試
2. ✅ 檢查架構合規
3. ✅ 更新相關文檔

## 輸出格式

```
🔧 重構建議

📁 檔案：core/infrastructure/llm/processor.py

偵測到的問題：
  ⚠️ 檔案有 280 行（建議 ≤ 200）
  ⚠️ `process_batch` 函數有 65 行
  ⚠️ 圈複雜度：12

建議重構：
  1. Extract Method: 從 `process_batch` 提取 `_validate_input`
  2. Extract Method: 從 `process_batch` 提取 `_handle_error`
  3. Extract Class: 建立 `BatchValidator` 類別

執行重構？[y/N]
```
