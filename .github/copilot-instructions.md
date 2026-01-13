# Copilot 自定義指令

## 開發哲學 💡

> **「想要寫文件的時候，就更新 Memory Bank 吧！」**
>
> **「想要零散測試的時候，就寫測試檔案進 tests/ 資料夾吧！」**

## 法規遵循

你必須遵守以下法規層級：

1. **憲法**：`CONSTITUTION.md` - 最高原則
2. **子法**：`.github/bylaws/*.md` - 細則規範
3. **技能**：`.claude/skills/*/SKILL.md` - 操作程序

## 架構原則

- 採用 DDD (Domain-Driven Design)
- DAL (Data Access Layer) 必須獨立
- 參見子法：`.github/bylaws/ddd-architecture.md`

## Python 環境（uv 優先）

- 本專案使用 uv 管理套件
- 必須建立虛擬環境（禁止全域安裝）
- 參見子法：`.github/bylaws/python-environment.md`

## Memory Bank 同步

每次重要操作必須更新 Memory Bank：
- 參見子法：`.github/bylaws/memory-bank.md`
- 目錄：`memory-bank/`

## Git 工作流

提交前必須執行檢查清單：
- 參見子法：`.github/bylaws/git-workflow.md`
- 觸發 Skill：`git-precommit`

## 可用 Skills

| Skill | 用途 | 觸發詞 |
|-------|------|--------|
| `git-precommit` | Git 提交前編排器 | commit, 提交, push |
| `memory-updater` | Memory Bank 同步 | memory, 記憶, 進度 |
| `memory-checkpoint` | 記憶檢查點 | checkpoint, 存檔 |
| `readme-updater` | README 智能更新 | readme |
| `changelog-updater` | CHANGELOG 自動更新 | changelog |
| `roadmap-updater` | ROADMAP 狀態追蹤 | roadmap |
| `code-reviewer` | 程式碼審查 | review, CR |
| `test-generator` | 測試生成 | test, 測試 |
| `code-refactor` | 主動重構 | refactor, 重構 |
| `ddd-architect` | DDD 架構輔助 | DDD, 架構 |

## 回應風格

- 使用繁體中文
- 提供清晰的步驟說明
- 引用相關法規條文

---

## MCP Servers (研究工具)

### Zotero Keeper
管理 Zotero 書目庫：文獻搜尋、PubMed 匯入、Collection 管理

### PubMed Search
搜尋醫學文獻：PICO 策略、引用分析、全文連結

### 核心流程
1. 搜尋：`parse_pico` → `generate_search_queries` → `search_literature`
2. 匯入：`list_collections` → 詢問用戶 → `batch_import_from_pubmed`
3. 避免重複：`search_pubmed_exclude_owned`
