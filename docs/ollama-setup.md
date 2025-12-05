# Ollama 安裝與設置指南

## ⚠️ 目前狀態
Ollama 服務未運行。需要先安裝並啟動 Ollama 才能使用本地 LLM。

---

## 📦 快速安裝步驟

### 步驟 1: 下載並安裝 Ollama

**Windows**:
1. 訪問 [https://ollama.ai/download](https://ollama.ai/download)
2. 下載 Windows 版本 (OllamaSetup.exe)
3. 執行安裝程式
4. 安裝完成後會自動啟動 Ollama 服務

**驗證安裝**:
```powershell
# 檢查 Ollama 版本
ollama --version

# 應該看到類似: ollama version is 0.x.x
```

---

### 步驟 2: 下載推薦模型

打開 PowerShell 或 CMD，執行：

```powershell
# Qwen 2.5 7B (推薦用於 PHI 識別，中英文優秀)
ollama pull qwen2.5:7b

# 或使用 Llama 3.1 8B (通用性強)
ollama pull llama3.1:8b
```

**下載時間**: 
- 7B 模型約 4-5 GB，取決於網速需要 5-15 分鐘
- 有 GPU 的話推理會快很多！

---

### 步驟 3: 驗證模型

```powershell
# 查看已下載的模型
ollama list

# 應該看到:
# NAME                ID              SIZE      MODIFIED
# qwen2.5:7b         abc123...       4.7 GB    2 minutes ago
```

---

### 步驟 4: 測試 Ollama

```powershell
# 簡單測試
ollama run qwen2.5:7b "What is PHI in healthcare?"

# 應該會看到模型的回答
```

---

## 🚀 執行 PHI 識別測試

完成上述步驟後，執行：

```powershell
# 進入專案目錄
cd d:\workspace251122

# 執行 Ollama PHI 批次測試
python test_phi_batch_ollama.py
```

---

## 🎮 GPU 加速

如果你有 NVIDIA GPU (GTX/RTX 系列):

1. **自動檢測**: Ollama 會自動使用 GPU（無需額外配置）
2. **驗證 GPU 使用**: 
   ```powershell
   # 執行時開啟另一個終端機
   nvidia-smi
   
   # 應該會看到 ollama 進程在使用 GPU
   ```

**效能提升**:
- CPU: 2-10 秒/請求
- GPU (RTX 3060+): 0.5-2 秒/請求 (快 5-10 倍！)

---

## 📊 記憶體需求

| 模型 | 最小 RAM | 推薦 RAM | GPU VRAM |
|------|---------|---------|----------|
| qwen2.5:7b | 8 GB | 16 GB | 4 GB |
| llama3.1:8b | 8 GB | 16 GB | 4 GB |
| qwen2.5:14b | 16 GB | 32 GB | 8 GB |

---

## 🔧 故障排除

### 問題 1: "ollama: command not found"
**原因**: Ollama 未安裝或未加入 PATH  
**解決**: 
1. 重新安裝 Ollama
2. 重新啟動 PowerShell
3. 檢查環境變數

### 問題 2: 無法連接到 localhost:11434
**原因**: Ollama 服務未啟動  
**解決**:
```powershell
# Windows: Ollama 應該會自動啟動
# 如果沒有，手動啟動:
ollama serve
```

### 問題 3: 模型下載失敗
**原因**: 網路問題或磁碟空間不足  
**解決**:
1. 檢查網路連接
2. 確保至少有 10 GB 可用空間
3. 使用較小的模型 (如 qwen2.5:7b 而非 14b)

### 問題 4: 推理太慢
**原因**: 使用 CPU 推理  
**解決**:
1. 如果有 GPU，確保驅動程式已安裝
2. 使用較小的模型
3. 減少 `max_tokens` 設定

---

## 🎯 模型推薦

### PHI 識別任務:
1. **首選**: `qwen2.5:7b` - 中英文優秀，準確率高
2. **備選**: `llama3.1:8b` - 通用性強
3. **快速**: `mistral:7b` - 速度優先

### 下載命令:
```powershell
ollama pull qwen2.5:7b
ollama pull llama3.1:8b
ollama pull mistral:7b
```

---

## 📝 使用範例

安裝完成後，你可以：

```powershell
# 1. 測試 Ollama 連接
python test_ollama_llm.py

# 2. 執行 PHI 批次識別（兩個 Excel 檔案）
python test_phi_batch_ollama.py

# 3. 查看結果
# 結果會儲存在: phi_ollama_results.xlsx
```

---

## 💡 提示

1. **首次執行**: 第一次使用時模型需要載入，會比較慢（10-30秒）
2. **後續執行**: 模型會保持在記憶體中，速度會快很多
3. **GPU 優勢**: 有 GPU 的話推理速度提升 5-10 倍
4. **多模型**: 可以同時下載多個模型，根據需求切換

---

## 📞 需要幫助？

- Ollama 官網: [https://ollama.ai](https://ollama.ai)
- Ollama GitHub: [https://github.com/ollama/ollama](https://github.com/ollama/ollama)
- 模型庫: [https://ollama.ai/library](https://ollama.ai/library)

---

**準備好後，執行**: `python test_phi_batch_ollama.py`
