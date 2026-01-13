---
name: memory-updater
description: Update and maintain Memory Bank files (activeContext, progress, decisionLog). Triggers: MB, memory, 記憶, 進度, 更新記憶, update memory, 記錄進度, 更新上下文.
---

# Memory Bank 更新技能

## 描述

維護和更新專案的 Memory Bank 記憶系統。

## 觸發條件

- 「更新 memory bank」
- 「記錄進度」
- 「更新上下文」
- 工作階段結束時

## 更新的檔案

### activeContext.md

當前工作焦點，包含：
- 正在處理的任務
- 相關檔案
- 待解決問題

### progress.md

進度追蹤：
- Done: 已完成項目
- Doing: 進行中
- Next: 下一步

### decisionLog.md

重要決策記錄：
- 決策內容
- 原因/理由
- 日期

## 更新原則

1. 增量更新，不覆蓋歷史
2. 日期格式：YYYY-MM-DD
3. 條目格式保持一致
4. 優先更新：progress > activeContext > decisionLog

## 輸出格式

```
📝 Memory Bank 更新

✅ activeContext.md
  └─ 當前焦點：[任務名稱]
  └─ 相關檔案：新增 3 個

✅ progress.md
  └─ Done: +1 項目
  └─ Doing: 已更新

⏭️ decisionLog.md (無新決策)

🕐 更新時間：2025-01-13 10:30
```
