# 安全政策 | Security Policy

## 支援版本 | Supported Versions

| 版本 Version | 支援狀態 Status |
| ------------ | --------------- |
| 0.1.x        | ✅ 支援中 |

## 安全考量 | Security Considerations

此專案處理醫療文本去識別化，涉及敏感的個人健康資訊 (PHI)。請注意以下安全要點：

This project handles medical text de-identification involving sensitive Protected Health Information (PHI). Please note the following security considerations:

### 資料處理 | Data Handling

1. **永不提交真實 PHI** - 測試資料應使用合成或模擬資料
2. **本地處理優先** - 優先使用本地 LLM (Ollama) 以避免敏感資料外洩
3. **日誌審查** - 確保日誌不會記錄實際 PHI 內容
4. **輸出檔案保護** - 輸出資料夾已在 .gitignore 中排除

### API 金鑰安全 | API Key Security

1. 使用 `.env` 檔案儲存 API 金鑰（已在 .gitignore 中）
2. 永不在程式碼中硬編碼金鑰
3. 生產環境使用 secrets manager 或環境變數

## 回報漏洞 | Reporting Vulnerabilities

如果你發現安全漏洞，請**不要**公開在 Issues 中回報。

If you discover a security vulnerability, please **DO NOT** report it publicly in Issues.

### 回報方式 | How to Report

1. 使用 GitHub 的私人漏洞回報功能 (Security Advisories)
2. 或發送郵件至專案維護者

### 回報內容 | What to Include

請包含以下資訊：

- 漏洞描述
- 重現步驟
- 可能的影響範圍
- 建議的修復方式（如果有）

### 回應時程 | Response Timeline

- 48 小時內確認收到回報
- 7 天內初步評估
- 90 天內修復（視嚴重程度調整）

## 安全最佳實踐 | Security Best Practices

### 開發者 | For Developers

```bash
# 安裝安全掃描工具
uv add --dev bandit

# 執行安全掃描
uv run bandit -r medical_deidentification/

# 使用 ruff 的安全規則
uv run ruff check --select S .
```

### 部署者 | For Deployers

1. 使用最新版本的依賴套件
2. 定期執行 `uv lock --upgrade` 更新依賴
3. 在隔離的網路環境中處理 PHI
4. 啟用稽核日誌

## 感謝 | Acknowledgments

我們感謝所有負責任地回報安全問題的研究人員。

We thank all researchers who responsibly report security issues.
