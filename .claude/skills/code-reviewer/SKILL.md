---
name: code-reviewer
description: Perform code review with DDD architecture compliance check. Triggers: review, 程式碼審查, code review, 審查, CR.
---

# 程式碼審查技能

## 描述

執行程式碼審查，包含 DDD 架構合規性檢查。

## 觸發條件

- 「review code」「程式碼審查」「CR」
- 提交 PR 時

## 檢查項目

### 1. DDD 架構合規
- [ ] 依賴方向正確（不能反向依賴）
- [ ] Domain 層無外部依賴
- [ ] Repository 介面在 Domain，實作在 Infrastructure

### 2. 程式碼品質
- [ ] 函數長度 ≤ 30 行
- [ ] 類別長度 ≤ 150 行
- [ ] 圈複雜度 ≤ 10

### 3. 命名慣例
- [ ] 符合 DDD 命名規範
- [ ] 變數名稱有意義

### 4. 測試覆蓋
- [ ] 新功能有對應測試
- [ ] 測試覆蓋率 ≥ 70%

## 輸出格式

```
🔍 程式碼審查報告

📁 檔案：core/domain/entities.py

## DDD 合規性 ✅
  └─ 依賴方向：正確
  └─ 無外部依賴：是

## 程式碼品質 ⚠️
  └─ 函數 `process_phi` 有 45 行（建議 ≤ 30）
  └─ 建議拆分為更小的方法

## 命名 ✅
  └─ 符合規範

## 測試 ⚠️
  └─ 缺少 `test_process_phi` 測試

---
總評：通過，但有 2 項建議改善
```
