---
name: ddd-architect
description: Assist with DDD architecture design and compliance checking. Triggers: DDD, 架構, architecture, 領域設計, domain design.
---

# DDD 架構輔助技能

## 描述

協助 DDD 架構設計與合規性檢查。

## 觸發條件

- 「DDD」「架構」「architecture」
- 建立新功能模組時
- 程式碼審查時

## 法規依據

- 憲法：CONSTITUTION.md 第一章
- 子法：.github/bylaws/ddd-architecture.md

## 功能

### 1. 架構檢查

驗證依賴方向：
```
interface → application → domain
                ↓
          infrastructure
```

### 2. 模組建議

為新功能建議正確的檔案位置：

| 類型 | 位置 |
|------|------|
| 實體 | `core/domain/entities.py` |
| 值物件 | `core/domain/value_objects.py` |
| 用例 | `core/application/processing/` |
| 外部服務 | `core/infrastructure/` |
| API | `core/interface/` |

### 3. 違規偵測

偵測並警告：
- Domain 層導入 Infrastructure
- Application 層直接存取資料庫
- 循環依賴

## 輸出格式

```
🏗️ DDD 架構檢查

📁 掃描範圍：core/

## 依賴方向 ✅
  └─ domain → 無外部依賴
  └─ application → domain ✓
  └─ infrastructure → domain ✓

## 違規偵測 ⚠️
  └─ core/domain/entities.py:15
     └─ 發現導入 `from core.infrastructure.llm import...`
     └─ 建議：移至 application 層或使用依賴注入

## 建議
  1. 在 domain 層定義介面 `ILLMService`
  2. 在 infrastructure 層實作
  3. 在 application 層注入

需要我協助修正嗎？
```
