# ⚠️ Ollama 未安裝 - 需要安裝才能繼續

## 當前狀態
測試腳本無法連接到 Ollama 服務（錯誤 404）。

這表示：
1. Ollama 服務未運行
2. 或者 Ollama 根本未安裝

---

## 📦 立即安裝 Ollama

### 步驟 1: 下載 Ollama

訪問: **https://ollama.ai/download**

下載 Windows 版本並安裝。

### 步驟 2: 驗證安裝

安裝完成後，打開 PowerShell 輸入：

```powershell
ollama --version
```

應該看到版本號（如 `ollama version is 0.4.0`）

### 步驟 3: 下載模型

```powershell
# 下載 llama3.1 8B 模型（約 4.7 GB）
ollama pull llama3.1:8b
```

這需要 5-15 分鐘，取決於網速。

### 步驟 4: 驗證模型

```powershell
# 查看已下載的模型
ollama list

# 應該看到 llama3.1:8b
```

### 步驟 5: 重新執行測試

```powershell
cd d:\workspace251122
python test_phi_batch_ollama.py
```

---

## 🔍 替代方案：使用已下載的其他模型

如果你已經有其他 Ollama 模型，可以檢查：

```powershell
ollama list
```

然後修改測試腳本使用你已有的模型（編輯 `test_phi_batch_ollama.py` 第 82 行）。

---

## ❓ 故障排除

### 問題：安裝後仍然 404

**解決**：
1. 重新啟動 Ollama 服務
2. 檢查 Ollama 是否在運行：
   ```powershell
   Get-Process ollama
   ```

### 問題：下載太慢

**解決**：
- 使用較小的模型：`ollama pull qwen2.5:3b`（約 2 GB）
- 或繼續等待

---

## 💡 快速決定

**選項 A**: 安裝 Ollama（推薦）
- 優勢：本地運行，快速，免費
- 時間：首次安裝 20-30 分鐘

**選項 B**: 使用 OpenAI API（備用）
- 修改腳本使用 OpenAI
- 缺點：可能很慢（之前遇到 >5分鐘/請求）

---

## 📝 當前工作成果

已完成：
- ✅ Ollama LLM 整合（config, factory）
- ✅ 測試腳本準備好
- ✅ 批次處理邏輯實現
- ⏳ **等待 Ollama 安裝**

**下一步**：安裝 Ollama 並下載模型，然後重新執行測試。
