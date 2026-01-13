---
name: changelog-updater
description: Automatically update CHANGELOG.md based on code changes following Keep a Changelog format. Triggers: changelog, 更新 changelog, update changelog, 變更紀錄.
---

# CHANGELOG 更新技能

## 描述

根據變更內容自動更新 CHANGELOG.md。

## 觸發條件

- 「更新 changelog」
- 被 git-precommit 編排器調用

## 法規依據

- 憲法：CONSTITUTION.md 第 7 條
- 格式：Keep a Changelog

## 分類規則

| 類型 | 關鍵字偵測 |
|------|------------|
| Added | 新增、add、feat |
| Changed | 變更、修改、update、change |
| Deprecated | 棄用、deprecate |
| Removed | 移除、刪除、remove、delete |
| Fixed | 修復、fix、bug |
| Security | 安全、security、漏洞 |

## 輸出格式

```
📋 CHANGELOG 更新

偵測到的變更：
  ✅ feat: 新增用戶認證 → Added
  ✅ fix: 修復登入 bug → Fixed

建議條目：
## [Unreleased]

### Added
- 用戶認證模組

### Fixed
- 修復登入時的 session 問題
```
