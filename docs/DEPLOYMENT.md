# 🚀 Deployment Guide | 部署指南

## Overview | 概述

This guide covers installation, configuration, and deployment of the Medical De-identification Toolkit.

本指南涵蓋醫療去識別化工具套件的安裝、配置和部署。

---

## Current Web Deployment | 目前建議的 Web 部署

目前 Web 服務的建議拓樸是：

```text
Browser
  │
  ▼
Frontend service :5173
  ├─ static assets from web/frontend/dist
  └─ /api/* proxy → FastAPI backend 127.0.0.1:8000
                         └─ Ollama / local LLM
```

重點：

- 瀏覽器只連 `http://<server>:5173` 或正式 TLS 網域。
- 前端 API base 預設必須是 `/api`，不要重新 build 成 `http://<server>:8000/api`。
- 後端建議只 bind `127.0.0.1:8000`，外部流量由前端 service 或 HTTPS reverse proxy 進入。
- 內部測試可使用 `anonymous_session`：不需要帳密，但每個瀏覽器仍會拿到 HttpOnly session cookie，資料依 session/user 隔離。
- 正式多人上線請使用 HTTPS reverse proxy + `password` auth + admin/user RBAC。

### Install Or Update systemd Services

```bash
cd /home/eric/workspace260113/medical-deidentification
sudo ./scripts/services/backup-runtime-state.sh
sudo ./scripts/services/install-services.sh

systemctl status medical-deid-backend medical-deid-frontend --no-pager
curl -i http://127.0.0.1:5173/api/health
```

`medical-deid-frontend` 應顯示：

```text
node .../scripts/services/frontend-server.mjs
Frontend listening on http://0.0.0.0:5173
Proxying /api to http://127.0.0.1:8000
```

如果看到 `serve -s dist -l 5173`，代表仍是舊版前端服務，請重新執行安裝腳本或重啟 frontend service。

### Trusted LAN Testing

```bash
sudo ./scripts/services/configure-lan-access.sh 192.168.1.201
uv run python scripts/check_workflow.py --url http://192.168.1.201:5173 --frontend-proxy --process-timeout 240
```

LAN helper 會使用 `anonymous_session`，適合封閉內網測試。它不等同於公開 production security boundary。

### Backup And Rollback

每次更新服務、切換認證模式或調整 LLM 設定前，先備份 runtime 狀態：

```bash
sudo ./scripts/services/backup-runtime-state.sh
ls -lh /var/backups/medical-deid/
```

若更新後要回復上一版 runtime/systemd/env/data/log 狀態：

```bash
sudo ./scripts/services/restore-runtime-state.sh /var/backups/medical-deid/medical-deid-runtime-YYYYmmddTHHMMSSZ.tar.gz
```

備份檔包含 `/etc/medical-deid`、systemd unit、`/var/lib/medical-deid`、`/var/log/medical-deid`，權限預設為 root-only。

### HTTPS Reverse Proxy Production

```bash
sudo ./scripts/services/configure-production-proxy.sh deid.example.org admin
```

Reverse proxy 請將所有路徑轉到 frontend service：

```text
https://deid.example.org/* → http://127.0.0.1:5173
```

不要把 `/api` 直接轉到 `127.0.0.1:8000`，除非你也同步設定 `MEDICAL_DEID_CORS_ORIGINS` 與 origin guard；預設最佳路徑是讓 frontend service 統一代理 `/api`。

範例：

- `deploy/reverse-proxy/Caddyfile.example`
- `deploy/reverse-proxy/nginx-medical-deid.conf.example`

### Runtime Environment

核心 production env 位於 `/etc/medical-deid/medical-deid.env`：

```bash
MEDICAL_DEID_AUTH_MODE=anonymous_session   # 內測免帳密
# MEDICAL_DEID_AUTH_MODE=password          # 正式多人上線
VITE_API_BASE_URL=/api
MEDICAL_DEID_BACKEND_HOST=127.0.0.1
MEDICAL_DEID_SESSION_COOKIE_SECURE=0       # HTTP LAN
# MEDICAL_DEID_SESSION_COOKIE_SECURE=1     # HTTPS production
MEDICAL_DEID_SESSION_COOKIE_SAMESITE=lax
MEDICAL_DEID_DELETE_UPLOAD_AFTER_PROCESS=1
MEDICAL_DEID_STORE_RAW_PHI=0              # production: 不保留命中原始 PHI 值
MEDICAL_DEID_ALLOW_PHI_REVEAL=0           # production: 不允許 API/UI 揭露原始 PHI
MEDICAL_DEID_UPLOAD_TTL_HOURS=2
MEDICAL_DEID_RESULT_TTL_HOURS=24
MEDICAL_DEID_PROCESSING_WORKERS=1
OLLAMA_BASE_URL=http://192.168.1.2:30133
OLLAMA_MODEL=gemma3:27b
```

隱私語義請精確理解：系統不把資料送到雲端；Web UI 會短暫把上傳檔寫入本機磁碟供背景 worker 處理，完成後預設刪除原始檔內容並保留非原文 metadata、去識別化輸出與報告。若服務在處理中重啟，啟動時會把中斷任務標為 failed，並由 cleanup/TTL 補償清除暫存檔。

若要驗收 `test_phi_tagged_cases.xlsx` 這類標註資料的偵測對錯，需要讓上傳者能看見「命中的原始 PHI 值」。內測 LAN helper 會設定 `MEDICAL_DEID_STORE_RAW_PHI=1` 與 `MEDICAL_DEID_ALLOW_PHI_REVEAL=1`，前端則以「校對模式」按需查詢 `reveal_phi=true`。這不會保留整份上傳原檔，但會在結果/報告 artifact 中暫存命中的 PHI 值，直到 `MEDICAL_DEID_RESULT_TTL_HOURS` 清理；正式 production 請維持兩者為 `0`。

### Smoke Test Matrix

```bash
# 前端同源 proxy 路徑，最接近使用者瀏覽器
uv run python scripts/check_workflow.py --url http://127.0.0.1:5173 --frontend-proxy --process-timeout 240

# password/RBAC production 路徑，會先登入並沿用 session cookie
MEDICAL_DEID_SMOKE_USERNAME=admin MEDICAL_DEID_SMOKE_PASSWORD='your-password' \
  uv run python scripts/check_workflow.py --url https://deid.example.org --frontend-proxy --process-timeout 240

# 後端本機路徑，適合 debug backend/CORS
uv run python scripts/check_workflow.py --url http://127.0.0.1:8000 --frontend-origin http://127.0.0.1:5173 --process-timeout 240

# 前端與後端測試
npm run lint --workspace web/frontend
npm run test:run --workspace web/frontend
npm run build --workspace web/frontend
uv run ruff check core web/backend scripts/check_workflow.py tests --select F,E9
uv run pytest tests/unit
```

請固定使用 `uv run pytest`，不要用系統 Python 直接跑 pytest；系統 Python 可能沒有本專案依賴。

目前 health check 會確認 configured `OLLAMA_MODEL` 存在於 Ollama `/api/tags`，不是只檢查 Ollama port 可連。若 smoke test 在 LLM 步驟失敗，請先確認 `/etc/medical-deid/medical-deid.env` 的 `OLLAMA_BASE_URL` 與 `OLLAMA_MODEL` 和 Ollama 實際模型一致。

### Result Correctness Notes

- 表格下載會保留 CSV/XLSX 的列欄結構，並輸出完整去識別化資料，不再只輸出 `masked_content` 前 5000 字。
- 報告 CSV/Markdown 會包含 PHI 詳細列表；一般模式隱藏原始值，校對模式才揭露命中原值。
- Generic `AGE` 會保留；只有 `AGE_OVER_89`/`AGE_OVER_90` 會套用 `<89` 移除規則，避免測試標註資料被錯誤扣掉。
- Production log 不應保存 PHI/模型輸出片段；例外訊息、前端錯誤、loader 路徑與 masking debug 已改為安全摘要。

---

## 📋 Prerequisites | 前置需求

### System Requirements | 系統需求

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| **OS** | Windows 10, macOS 10.15, Ubuntu 20.04 | Latest LTS |
| **Python** | 3.11 | 3.11+ |
| **RAM** | 8 GB | 16 GB |
| **Storage** | 5 GB | 20 GB (with models) |
| **GPU** | Not required | NVIDIA RTX 3060+ (for local LLM) |

### Software Dependencies | 軟體依賴

- Python 3.11+
- pip or Poetry (package manager)
- Git (for source installation)
- Ollama (for local LLM) - optional

---

## 📦 Installation Methods | 安裝方式

### Method 1: pip Install (Recommended for Users)

```bash
# Install from PyPI
pip install medical-deidentification

# Verify installation
python -c "import core; print('Success!')"
```

### Method 2: From Source (Recommended for Development)

```bash
# Clone repository
git clone https://github.com/u9401066/medical-deidentification.git
cd medical-deidentification

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# Install in editable mode
pip install -e .
```

### Method 3: Poetry (Recommended for Contributors)

```bash
# Clone repository
git clone https://github.com/u9401066/medical-deidentification.git
cd medical-deidentification

# Install Poetry (if not installed)
pip install poetry

# Install dependencies
poetry install

# Activate virtual environment
poetry shell
```

---

## ⚙️ Configuration | 配置

### Environment Variables | 環境變數

Create a `.env` file in the project root:

```bash
# .env

# ===== LLM API Keys =====
# OpenAI (for GPT-4o, GPT-4o-mini)
OPENAI_API_KEY=sk-your-api-key-here

# Anthropic (for Claude 3)
ANTHROPIC_API_KEY=sk-ant-your-api-key-here

# ===== Ollama Configuration =====
# Ollama server URL (default: http://localhost:11434)
OLLAMA_BASE_URL=http://localhost:11434

# ===== Logging =====
# Log level: DEBUG, INFO, WARNING, ERROR
LOG_LEVEL=INFO
LOG_DIR=./logs

# ===== Processing =====
# Default language for PHI detection
DEFAULT_LANGUAGE=zh-TW

# Maximum tokens for LLM response
MAX_TOKENS=2048
```

### LLM Configuration | LLM 配置

```python
from core.infrastructure.llm import LLMConfig, LLMPresets

# Option 1: Use presets
config = LLMPresets.local_minimind()      # Ultra-light local
config = LLMPresets.local_qwen()          # Balanced local
config = LLMPresets.gpt_4o()              # Best quality cloud

# Option 2: Custom configuration
config = LLMConfig(
    provider="ollama",                    # openai, anthropic, ollama
    model_name="qwen2.5:7b",
    temperature=0.0,                      # 0.0 for deterministic
    max_tokens=2048,
    timeout=120,                          # seconds
    use_gpu=True,                         # Enable GPU acceleration
    num_gpu=1                             # Number of GPUs
)
```

---

## 🤖 LLM Setup | LLM 設置

### Option A: Cloud LLM (OpenAI/Anthropic)

1. **Get API Key**:
   - OpenAI: https://platform.openai.com/api-keys
   - Anthropic: https://console.anthropic.com/

2. **Set Environment Variable**:
   ```bash
   # Windows
   set OPENAI_API_KEY=sk-your-key-here
   
   # macOS/Linux
   export OPENAI_API_KEY=sk-your-key-here
   ```

3. **Test Connection**:
   ```python
   from core.infrastructure.llm import LLMPresets, create_llm
   
   llm = create_llm(LLMPresets.gpt_4o())
   response = llm.invoke("Hello, world!")
   print(response)
   ```

### Option B: Local LLM (Ollama)

1. **Install Ollama**:
   - Download from https://ollama.ai/download
   - Run installer
   - Ollama starts automatically as a service

2. **Pull Models**:
   ```bash
   # Ultra-light model (testing/development)
   ollama pull jingyaogong/minimind2
   
   # Balanced model (recommended for production)
   ollama pull qwen2.5:7b
   
   # Alternative options
   ollama pull llama3.1:8b
   ollama pull mistral:7b
   ```

3. **Verify Setup**:
   ```bash
   # Check Ollama status
   ollama list
   
   # Test model
   ollama run qwen2.5:7b "What is PHI in healthcare?"
   ```

4. **Test in Python**:
   ```python
   from core.infrastructure.llm import LLMPresets, create_llm
   
   llm = create_llm(LLMPresets.local_qwen())
   response = llm.invoke("Identify PHI in: Patient John Doe")
   print(response)
   ```

> 📖 See [Ollama Setup Guide](./ollama-setup.md) for detailed instructions.

---

## 🏃 Running the Application | 運行應用

### Basic Usage | 基本使用

```python
from core.application.processing import DeidentificationEngine
from core.infrastructure.llm import LLMPresets, create_llm

# Initialize
llm = create_llm(LLMPresets.local_minimind())
engine = DeidentificationEngine(llm=llm)

# Process text
text = "病患姓名：王大明，身分證字號：A123456789"
result = engine.process(text)

print(result.deidentified_text)
print(f"Found {len(result.entities)} PHI entities")
```

### Batch Processing | 批次處理

```python
from core.application.processing import (
    BatchPHIProcessor,
    BatchProcessingConfig
)

# Configure
config = BatchProcessingConfig(
    max_rows=100,
    language="zh-TW",
    skip_empty_rows=True
)

# Process Excel file
processor = BatchPHIProcessor(phi_chain, config)
result = processor.process_excel_file("data/patients.xlsx")

# Save results
result.to_excel("output/phi_results.xlsx")
```

---

## 📁 Directory Structure | 目錄結構

Recommended project structure for deployment:

```
your-project/
├── .env                      # Environment variables (DO NOT commit!)
├── data/
│   ├── raw/                  # Input files (NEVER commit real PHI!)
│   ├── output/
│   │   ├── results/          # Processing results
│   │   └── reports/          # Generated reports
│   └── regulations/          # Regulation documents for RAG
├── logs/                     # Application logs
├── scripts/                  # Custom scripts
└── config/                   # Configuration files
```

### Data Directory Setup

```bash
# Create directories
mkdir -p data/raw data/output/results data/output/reports data/regulations logs
```

---

## 🔧 Troubleshooting | 故障排除

### Common Issues | 常見問題

#### 1. Ollama Connection Error

```
Error: Failed to connect to Ollama at http://localhost:11434
```

**Solution**:
```bash
# Check if Ollama is running
ollama list

# If not running, start it
ollama serve
```

#### 2. Model Not Found

```
Error: model "qwen2.5:7b" not found
```

**Solution**:
```bash
# Pull the model
ollama pull qwen2.5:7b
```

#### 3. GPU Not Detected

```
Warning: CUDA not available, using CPU
```

**Solution**:
1. Install NVIDIA drivers
2. Install CUDA Toolkit
3. Verify with `nvidia-smi`
4. Reinstall PyTorch with CUDA support

#### 4. Memory Error

```
Error: Out of memory
```

**Solution**:
- Use smaller model (e.g., MiniMind instead of Qwen 7B)
- Reduce `max_tokens`
- Process smaller batches
- Enable `use_gpu=True` if GPU available

#### 5. API Key Error

```
Error: OpenAI API key not found
```

**Solution**:
```bash
# Set environment variable
export OPENAI_API_KEY=sk-your-key-here

# Or use .env file
echo "OPENAI_API_KEY=sk-your-key-here" >> .env
```

---

## 📊 Performance Optimization | 效能優化

### Tips for Better Performance

1. **Use GPU** when available:
   ```python
   config = LLMConfig(provider="ollama", model_name="qwen2.5:7b", use_gpu=True)
   ```

2. **Choose appropriate model**:
   - Testing: MiniMind (fast, lightweight)
   - Production: Qwen 2.5 7B (balanced)
   - High accuracy: GPT-4o (best quality)

3. **Batch processing** for multiple documents:
   ```python
   processor.process_excel_file("data.xlsx")  # More efficient than row-by-row
   ```

4. **Adjust timeout** for large documents:
   ```python
   config = LLMConfig(timeout=180)  # 3 minutes
   ```

---

## 🔒 Security Best Practices | 安全最佳實踐

1. **Never commit**:
   - `.env` files with API keys
   - Real PHI data
   - Test results containing PHI

2. **Use `.gitignore`**:
   ```gitignore
   .env
   data/raw/
   data/output/
   logs/
   *.xlsx
   *.csv
   ```

3. **Rotate API keys** regularly

4. **Audit logs** periodically

5. **Use encryption** for sensitive outputs

---

## 📞 Support | 支援

- **GitHub Issues**: [Report bugs](https://github.com/u9401066/medical-deidentification/issues)
- **Documentation**: [Full docs](./README.md)
- **Discussions**: [Community forum](https://github.com/u9401066/medical-deidentification/discussions)

---

**[← Back to README](../README.md)**
