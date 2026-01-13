---
name: roadmap-updater
description: Update ROADMAP.md to track feature completion and planning. Triggers: roadmap, 更新路線圖, update roadmap, 功能規劃.
---

# ROADMAP 更新技能

## 描述

追蹤功能完成狀態，更新 ROADMAP.md。

## 觸發條件

- 「更新 roadmap」
- 被 git-precommit 編排器調用
- 完成重要功能後

## 功能

1. 標記已完成的功能
2. 更新進行中項目
3. 調整優先順序

## 輸出格式

```
🗺️ ROADMAP 更新

匹配到的項目：
  ✅ 用戶認證 → 標記為已完成
  🚧 API 文檔 → 保持進行中

建議新增：
  - 新增「密碼重設」到已完成

預覽：
## 已完成 ✅
+ - [x] 用戶認證 (2025-01-13)
```
