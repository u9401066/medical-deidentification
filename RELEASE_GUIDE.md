# GitHub 發佈指南 | GitHub Release Guide

## ✅ 發佈前檢查清單

### 已完成項目
- ✅ LICENSE 文件 (MIT)
- ✅ README.md (完整說明、安裝、快速開始)
- ✅ CHANGELOG.md (版本歷史)
- ✅ CONTRIBUTING.md (貢獻指南)
- ✅ .gitignore (排除敏感和測試文件)
- ✅ 專案版本設定 (0.1.0-beta)
- ✅ 測試通過 (15/15 rows, 265 PHI entities)
- ✅ 代碼提交完成
- ✅ 測試輸出文件清理

### 待完成項目（發佈到 GitHub 後）
- ⏳ 更新 README.md 中的 YOUR_USERNAME 為實際 GitHub 用戶名
- ⏳ 更新 pyproject.toml 中的倉庫 URL
- ⏳ 更新 CHANGELOG.md 中的 URL

## 🚀 發佈步驟

### 1. 在 GitHub 創建新倉庫

1. 訪問 https://github.com/new
2. 倉庫名稱：`medical-deidentification`
3. 描述：`LLM-powered medical text de-identification toolkit | 基於 LLM 的醫療文本去識別化工具`
4. 設定為 Public（如果要開源）或 Private
5. **不要**勾選 "Add a README file"（我們已經有了）
6. **不要**勾選 "Add .gitignore"（我們已經有了）
7. **不要**選擇 License（我們已經有了）
8. 點擊 "Create repository"

### 2. 推送到 GitHub

在本地倉庫執行：

```bash
# 添加 GitHub 遠端倉庫（替換 YOUR_USERNAME）
git remote add origin https://github.com/YOUR_USERNAME/medical-deidentification.git

# 或如果使用 SSH
git remote add origin git@github.com:YOUR_USERNAME/medical-deidentification.git

# 推送到 GitHub
git push -u origin master

# 檢查推送結果
git remote -v
```

### 3. 更新倉庫 URL

推送成功後，在本地更新文件中的 YOUR_USERNAME：

```bash
# 在 README.md 中替換（3 處）
# 在 pyproject.toml 中替換（2 處）
# 在 CHANGELOG.md 中替換（2 處）
# 在 CONTRIBUTING.md 中替換（1 處）

# 可以使用文本編輯器批量替換，或使用命令：
# (PowerShell)
(Get-Content README.md) -replace 'YOUR_USERNAME', '實際用戶名' | Set-Content README.md
(Get-Content pyproject.toml) -replace 'YOUR_USERNAME', '實際用戶名' | Set-Content pyproject.toml
(Get-Content CHANGELOG.md) -replace 'YOUR_USERNAME', '實際用戶名' | Set-Content CHANGELOG.md
(Get-Content CONTRIBUTING.md) -replace 'YOUR_USERNAME', '實際用戶名' | Set-Content CONTRIBUTING.md

# 提交更新
git add -A
git commit -m "docs: Update repository URLs with actual GitHub username"
git push
```

### 4. 創建 Release

在 GitHub 倉庫頁面：

1. 點擊右側 "Releases"
2. 點擊 "Create a new release"
3. Tag version: `v0.1.0-beta`
4. Release title: `v0.1.0-beta - Initial Beta Release`
5. Description:
   ```markdown
   ## 🎉 Initial Beta Release

   This is the first beta release of the Medical De-identification Toolkit.

   ### ✨ Features
   - LLM-powered PHI identification (Ollama/OpenAI)
   - Batch processing for Excel files
   - 20+ PHI types support
   - Multi-language support
   - Token counting and performance statistics
   - GPU acceleration support

   ### 📊 Performance
   - Processing Speed: ~27 seconds per document
   - PHI Detection Confidence: Average 95%
   - Tested on 15 complex medical cases

   ### ⚠️ Note
   This is a **beta release** for research and development purposes.
   Not recommended for production use with real PHI data.

   ### 📖 Documentation
   - [README](./README.md)
   - [Contributing Guide](./CONTRIBUTING.md)
   - [Changelog](./CHANGELOG.md)

   ### 🙏 Feedback
   Please report issues or suggestions via GitHub Issues.
   ```
6. 勾選 "This is a pre-release"（Beta 版本）
7. 點擊 "Publish release"

### 5. 設定倉庫

在 GitHub 倉庫設定：

1. **About 區塊**（右上角）
   - Description: `LLM-powered medical text de-identification toolkit`
   - Website: 可選
   - Topics: `medical` `deidentification` `phi` `hipaa` `nlp` `llm` `python` `healthcare`

2. **README Badges**（可選）
   - GitHub Stars
   - Python Version
   - License
   - Build Status（如果有 CI/CD）

3. **Branch Protection**（可選）
   - 設定 master 分支保護
   - 要求 PR review

4. **Issues**
   - 啟用 Issues
   - 可以創建 Issue templates

## 📋 發佈後檢查

- [ ] 倉庫在 GitHub 上可見
- [ ] README 顯示正常
- [ ] LICENSE 文件存在
- [ ] 所有文件都已推送
- [ ] Release 已創建並標記為 pre-release
- [ ] 倉庫 URL 已更新
- [ ] Topics/Tags 已設定

## 🎯 後續工作

### 立即（發佈後）
1. 更新 Memory Bank 記錄發佈資訊
2. 測試從 GitHub clone 並安裝
3. 檢查所有連結是否正常

### 短期（1-2 週）
1. 加入 GitHub Actions CI/CD
2. 加入測試覆蓋率報告
3. 加入更多使用範例
4. 改善效能（目標：<20s/document）

### 中期（1-2 月）
1. 加入 Web UI
2. 支援更多 LLM providers
3. 加入 API server
4. 改善文件和教學

## 🔗 相關連結

- GitHub Docs: https://docs.github.com/
- Semantic Versioning: https://semver.org/
- Keep a Changelog: https://keepachangelog.com/
- Conventional Commits: https://www.conventionalcommits.org/

## ❓ 常見問題

**Q: 是否要設為 Public？**
A: 如果想開源分享，設為 Public。如果包含機密資訊，設為 Private。

**Q: 是否要加入 CI/CD？**
A: 建議加入，但可以發佈後再加。GitHub Actions 免費。

**Q: 如何處理敏感的測試數據？**
A: 確保 .gitignore 正確設定，不要推送 data/test/ 中的實際醫療數據。

**Q: 版本號如何決定？**
A: 遵循 Semantic Versioning (主版本.次版本.修訂版本)
- Beta/Alpha 加上 `-beta` 或 `-alpha` 後綴
- 第一個穩定版本建議是 1.0.0

---

**準備完成！🎉 可以開始發佈了！**
