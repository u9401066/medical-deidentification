# GPU 加速配置指南

## 概述

本系統已支援 GPU 加速，特別是針對使用 Ollama 的本地模型（如 llama3.1:8b）。GPU 加速可顯著提升推理速度，將處理時間從 30-50 秒/行減少到 5-15 秒/行（取決於硬體配置）。

## 系統要求

### 硬體要求
- **NVIDIA GPU**: GTX 1060 6GB 或更高（推薦 RTX 3060 12GB 以上）
- **VRAM**: 至少 6GB（llama3.1:8b 需要約 5.5GB）
- **系統記憶體**: 建議 16GB 以上

### 軟體要求
- **CUDA**: 11.8 或更高版本
- **Ollama**: 已自動使用 GPU（無需額外配置）
- **驅動程式**: 最新的 NVIDIA 驅動

## 驗證 GPU 狀態

### 檢查 Ollama GPU 使用情況
```powershell
ollama ps
```

預期輸出：
```
NAME           ID              SIZE      PROCESSOR    UNTIL
llama3.1:8b    46e0c10c039e    5.5 GB    100% GPU     4 minutes from now
```

**關鍵指標**:
- `PROCESSOR: 100% GPU` → GPU 正在使用 ✅
- `PROCESSOR: 100% CPU` → 僅使用 CPU ⚠️

### 檢查 NVIDIA GPU
```powershell
nvidia-smi
```

預期應看到 Ollama 進程佔用 GPU 記憶體。

## 配置選項

### 1. 自動模式（推薦）

系統默認自動檢測並使用所有可用的 GPU：

```python
llm_config = LLMConfig(
    provider="ollama",
    model_name="llama3.1:8b",
    temperature=0.0,
    use_gpu=True,  # 默認值，可省略
)
```

### 2. 指定 GPU 數量

如果你有多個 GPU，可以指定使用的數量：

```python
llm_config = LLMConfig(
    provider="ollama",
    model_name="llama3.1:8b",
    temperature=0.0,
    use_gpu=True,
    num_gpu=1,  # 只使用 1 個 GPU
)
```

### 3. CPU-only 模式

如果需要測試或比較 CPU 性能：

```python
llm_config = LLMConfig(
    provider="ollama",
    model_name="llama3.1:8b",
    temperature=0.0,
    use_gpu=False,  # 強制使用 CPU
)

# 或者
llm_config = LLMConfig(
    provider="ollama",
    model_name="llama3.1:8b",
    temperature=0.0,
    num_gpu=0,  # 強制使用 CPU
)
```

### 4. 控制 GPU 層數（進階）

對於記憶體受限的情況，可以指定卸載到 GPU 的層數：

```python
llm_config = LLMConfig(
    provider="ollama",
    model_name="llama3.1:8b",
    temperature=0.0,
    use_gpu=True,
    gpu_layers=20,  # 只卸載 20 層到 GPU，其餘使用 CPU
)
```

## 性能基準

### 測試環境
- **模型**: llama3.1:8b
- **輸入**: 1400 字醫療文本
- **任務**: PHI 識別 + structured output

### 性能對比

| 配置 | 處理時間/行 | 相對速度 | VRAM 使用 |
|------|------------|---------|----------|
| **GPU (auto)** | **5-15 秒** | **1x** | **5.5 GB** |
| GPU (layers=20) | 10-20 秒 | 0.5x | 3 GB |
| CPU only | 30-50 秒 | 0.2x | 0 GB |

**結論**: GPU 加速可提升 **3-5x** 性能！

## 故障排除

### 問題 1: Ollama 未使用 GPU

**症狀**: `ollama ps` 顯示 `PROCESSOR: 100% CPU`

**解決方案**:
1. 確認 NVIDIA 驅動已安裝: `nvidia-smi`
2. 重啟 Ollama 服務:
   ```powershell
   ollama serve
   ```
3. 重新載入模型:
   ```powershell
   ollama pull llama3.1:8b
   ```

### 問題 2: VRAM 不足

**症狀**: 
```
Error: CUDA out of memory
```

**解決方案**:
1. 使用較小的模型 (如 `llama3.2:3b`)
2. 減少 GPU 層數:
   ```python
   gpu_layers=20  # 或更小
   ```
3. 關閉其他使用 GPU 的程式

### 問題 3: 性能未改善

**可能原因**:
1. 模型未完全載入到 GPU
2. 系統瓶頸在其他地方（如磁碟 I/O）
3. Prompt 過長導致推理時間長

**診斷步驟**:
1. 檢查 `ollama ps` 確認 GPU 使用
2. 使用 `nvidia-smi` 監控 GPU 利用率
3. 查看日誌中的處理時間分解

## 最佳實踐

### 生產環境建議

```python
# 生產環境配置（平衡性能和穩定性）
llm_config = LLMConfig(
    provider="ollama",
    model_name="llama3.1:8b",  # 或 llama3.2:3b（更快但略低準確度）
    temperature=0.0,
    max_tokens=8192,
    timeout=60,  # GPU 模式下可以縮短 timeout
    use_gpu=True,  # 啟用 GPU
    num_gpu=None,  # 自動檢測所有 GPU
)
```

### 開發/測試環境

```python
# 開發環境配置（快速迭代）
llm_config = LLMConfig(
    provider="ollama",
    model_name="llama3.2:3b",  # 更快的小模型
    temperature=0.0,
    timeout=30,
    use_gpu=True,
)
```

### 批次處理優化

對於大批量數據處理：

1. **確保 GPU 空閒**: 關閉瀏覽器、遊戲等
2. **預熱模型**: 先處理 1-2 行讓模型載入到 GPU
3. **監控溫度**: 長時間運行時注意 GPU 溫度
4. **批次大小**: 考慮將 15 行分成 3 批×5 行，避免超時

## 環境變數

系統會自動設定以下環境變數：

```bash
# 自動設定（根據 num_gpu 參數）
OLLAMA_NUM_GPU=auto  # 或 0, 1, 2...
```

如需手動覆蓋，可在啟動前設定：

```powershell
# Windows PowerShell
$env:OLLAMA_NUM_GPU = "1"

# 或在 .env 文件中
echo "OLLAMA_NUM_GPU=1" >> .env
```

## 日誌輸出

啟用 GPU 後，你會在日誌中看到：

```
2025-11-22 21:24:35 | INFO | Ollama will auto-detect and use all available GPUs
2025-11-22 21:24:35 | SUCCESS | Created ChatOllama: llama3.1:8b (timeout=120s, processor=GPU (auto))
```

關鍵字：
- `processor=GPU (auto)` → 使用所有 GPU
- `processor=GPU×1` → 使用 1 個 GPU
- `processor=CPU-only` → 僅使用 CPU

## 相關資源

- [Ollama GPU Support](https://github.com/ollama/ollama/blob/main/docs/gpu.md)
- [NVIDIA CUDA Toolkit](https://developer.nvidia.com/cuda-downloads)
- [Model Performance Comparison](https://ollama.com/library/llama3.1)

## 貢獻者

如有問題或建議，請提交 Issue 或 Pull Request。
