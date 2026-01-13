---
name: memory-checkpoint
description: Save comprehensive memory checkpoint before context loss or summarization. Triggers: checkpoint, save memory, 檢查點, 存檔, 記憶檢查點, save state, 保存狀態.
---

# Memory Checkpoint 技能 (記憶檢查點)

## 描述

在 AI 對話即將被 Summarize（摘要壓縮）前，或長時間對話可能遺失細節時，主動建立完整的記憶檢查點。

## 🎯 核心目的

**解決 LLM Context Window 限制**：當對話太長，系統會自動 Summarize，導致細節遺失。此技能讓重要資訊「外部化」到檔案系統，確保跨對話記憶。

## 觸發條件

### 用戶觸發
- 「checkpoint」「存檔」「記憶檢查點」
- 「保存進度」「save state」

### AI 主動觸發（建議）
當偵測到以下情況，AI 應主動詢問是否建立 checkpoint：
- 對話輪數超過 10 輪
- 修改檔案數超過 5 個
- 做出重大架構決策
- 用戶即將結束對話

## 📋 Checkpoint 內容

### 1️⃣ activeContext.md - 當前工作焦點

```markdown
## 當前工作焦點
<!-- 當前正在做什麼 -->

## 進行中的變更
<!-- 具體的檔案和修改 -->

## 待處理事項
<!-- 下一步要做什麼 -->

## 關鍵決策
<!-- 本次對話做的重要決定 -->

## 相關檔案
<!-- 涉及的檔案路徑列表 -->
```

### 2️⃣ progress.md - 進度追蹤

```markdown
## Done
- [x] 已完成項目 (YYYY-MM-DD)

## Doing
- [ ] 進行中項目

## Next
- [ ] 待處理項目
```

### 3️⃣ decisionLog.md - 決策日誌

```markdown
## YYYY-MM-DD

### 決策：[決策標題]
- **背景**：為什麼需要這個決定
- **選項**：考慮過的方案
- **決定**：最終選擇
- **原因**：選擇的理由
```

## 🔄 與其他 Skills 整合

### 搭配 git-precommit
```
git commit 前 → 觸發 memory-checkpoint → 同步 Memory Bank → commit
```

### 搭配 memory-updater
```
memory-checkpoint = 批次更新
memory-updater = 增量更新
```

## 💬 對話範例

### 使用者觸發
```
用戶：checkpoint
AI：好的，我來建立記憶檢查點...
    [更新 Memory Bank 檔案]
    ✅ 檢查點已保存！下次對話可以從這裡繼續。
```

### AI 主動觸發
```
AI：我注意到我們已經討論了很多內容，建議建立一個檢查點。
    要我現在保存進度嗎？
用戶：好
AI：[建立檢查點...]
```
