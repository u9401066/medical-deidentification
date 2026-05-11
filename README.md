# 🏥 Medical De-identification Toolkit

<div align="center">

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![LangChain](https://img.shields.io/badge/LangChain-1.0+-orange.svg)](https://langchain.com/)
[![uv](https://img.shields.io/badge/uv-package%20manager-blueviolet.svg)](https://github.com/astral-sh/uv)

**🔒 LLM-Native Medical PHI De-identification | LLM 原生醫療 PHI 去識別化**

[English](#-why-this-tool) | [繁體中文](#-為何選擇這個工具)

</div>

---

## ⚡ Highlights | 核心亮點

```
🧠 LLM-Native      語義理解驅動，非傳統 NER/Regex 規則匹配
🎯 DSPy 優化       自動 prompt 工程，無需手動調參
💻 CPU 友好        支援 1B 參數輕量模型，無需 GPU
🔐 隱私優先        100% 本地運行，資料不離開你的設備
🌏 多語言          繁中/簡中/英/日/韓 等 10+ 語言
⚡ 高效混合        SpaCy + Regex + LLM 三層策略
```

---

## 🆚 Why This Tool? | 為何選擇這個工具？

### 與現有方案的比較

| 特性 | **本專案** | Microsoft Presidio | SpaCy NER | Cloud APIs |
|------|-----------|-------------------|-----------|------------|
| **技術核心** | 🧠 LLM 語義理解 | Rule + NER | NER 模型 | LLM API |
| **Prompt 優化** | ✅ DSPy 自動化 | ❌ 手動規則 | ❌ N/A | ❌ 手動 |
| **本地運行** | ✅ 100% 離線 | ✅ 可離線 | ✅ 可離線 | ❌ 需網路 |
| **CPU 推理** | ✅ 1B 模型 | ✅ | ✅ | ❌ |
| **隱私保護** | 🔐 資料不外傳 | 🔐 | 🔐 | ⚠️ 資料上雲 |
| **中文支援** | ✅ 繁/簡中優化 | ⚠️ 基本 | ⚠️ 需額外模型 | ✅ |
| **醫療專用** | ✅ PHI 20+ 類型 | ⚠️ 通用 PII | ⚠️ 通用 NER | ⚠️ 通用 |
| **上下文理解** | ✅ 語義分析 | ❌ 規則匹配 | ⚠️ 有限 | ✅ |

### 本專案的核心優勢

```
┌─────────────────────────────────────────────────────────────┐
│  🎯 核心差異化                                               │
├─────────────────────────────────────────────────────────────┤
│  1. LLM-Native: 用語義理解取代規則匹配                       │
│     - "王醫師" vs "王大明" 能正確區分                        │
│     - 上下文感知：「聯絡家屬王先生」→ NAME                  │
│                                                              │
│  2. DSPy 自動優化: 無需手動調 prompt                         │
│     - BootstrapFewShot: 自動選擇最佳 few-shot 範例          │
│     - MIPRO: 多階段指令優化                                  │
│                                                              │
│  3. 本地 CPU 推理: 無需 GPU，隱私優先                        │
│     - granite4:1b (3.3GB) → F1=89.4%                        │
│     - qwen2.5:1.5b (986MB) → 4 秒/請求                      │
│                                                              │
│  4. 醫療專用 PHI: 20+ 類型，符合 HIPAA/台灣 PDPA            │
│     - 罕見疾病名稱識別                                       │
│     - 高齡 (>89歲) 特殊處理                                  │
└─────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start | 30 秒上手

### 1. 安裝

```bash
# Clone
git clone https://github.com/u9401066/medical-deidentification.git
cd medical-deidentification

# Install with uv (推薦，需要 Python 3.12+)
uv sync

# 或使用 pip (需先建立虛擬環境)
python -m venv .venv && source .venv/bin/activate
pip install -e .
```

### 2. 設定本地 LLM (Ollama)

```bash
# 安裝 Ollama (https://ollama.ai)
curl -fsSL https://ollama.com/install.sh | sh

# 下載推薦模型
ollama pull granite4:1b    # 🏆 推薦 (1.6B, F1=89.4%, 131K context)

# 啟動 Ollama 服務 (如果未自動啟動)
ollama serve
```

### 3. 執行範例

```bash
python examples/quick_start.py
```

```python
# 或在程式碼中使用
from core.infrastructure.rag import PHIIdentificationChain

chain = PHIIdentificationChain()
entities = chain.identify_phi("""
    病患王大明，身分證 A123456789，
    電話 0912-345-678
""")

for entity in entities:
    print(f"[{entity.phi_type}] {entity.text}")
# Output:
# [NAME] 王大明
# [ID] A123456789  
# [PHONE] 0912-345-678
```

---

## 🤖 Recommended Models | 推薦模型

經過 benchmark 測試的 CPU 友好模型：

| 模型 | 大小 | F1 Score | 速度 | JSON 成功率 | 推薦場景 |
|------|------|----------|------|-------------|----------|
| **granite4:1b** | 3.3GB | **89.4%** | ~16s | 100% | 🏆 生產環境 |
| **qwen2.5:1.5b** | 986MB | 66.7% | ~4s | 100% | ⭐ 開發測試 |
| llama3.2:1b | 1.3GB | 55.0% | ~8s | 100% | 高召回需求 |
| smollm2:360m | 725MB | 0% | ~4s | 87.5% | ❌ 不推薦 |

> 📊 完整 benchmark 報告：[docs/llm-benchmark-results.md](docs/llm-benchmark-results.md)

---

## 🛡️ Supported PHI Types | 支援的 PHI 類型

| 類別 | PHI 類型 | 範例 |
|------|----------|------|
| **身份** | NAME, ID, SSN | 王大明, A123456789 |
| **聯絡** | PHONE, EMAIL, FAX | 0912-345-678 |
| **地點** | LOCATION, ADDRESS | 台北市信義區 |
| **日期** | DATE, DOB, ADMISSION_DATE | 2024-01-15 |
| **年齡** | AGE, AGE_OVER_89 | 92歲 |
| **醫療** | FACILITY, MRN, DEVICE_ID | 台北榮總, A12345 |
| **其他** | URL, IP_ADDRESS, VEHICLE | http://..., 192.168.1.1 |

---

## 🧠 DSPy Integration | DSPy 整合

本專案使用 [DSPy](https://github.com/stanfordnlp/dspy) 實現自動 prompt 優化：

```python
from core.infrastructure.dspy import (
    PHIIdentifier,
    PHIPromptOptimizer,
    configure_dspy_ollama,
)

# 配置 DSPy
configure_dspy_ollama(model_name="granite4:1b")

# 創建識別器
identifier = PHIIdentifier()

# (可選) 使用訓練資料優化
optimizer = PHIPromptOptimizer()
result = optimizer.optimize(trainset=your_data, method="bootstrap")

# 使用優化後的模組
optimized = result.best_module
entities = optimized.forward(medical_text="...")
```

---

## 📁 Project Structure | 專案結構

```
medical-deidentification/
├── examples/                    # 📚 使用範例
│   ├── quick_start.py          # 30 秒上手
│   ├── batch_example.py        # 批次處理
│   └── dspy_optimization.py    # DSPy 優化
├── core/
│   ├── application/            # 應用層
│   │   └── processing/         # 批次處理器
│   ├── domain/                 # 領域層 (DDD)
│   │   ├── entities.py         # PHI 實體定義
│   │   └── phi_types.py        # PHI 類型
│   └── infrastructure/         # 基礎設施層
│       ├── dspy/               # 🧠 DSPy 整合
│       ├── llm/                # LLM 配置
│       ├── rag/                # RAG 鏈
│       └── loader/             # 文件載入器
├── web/
│   ├── backend/                # 🖥️ FastAPI 後端 (DDD)
│   │   ├── api/                # Routers (files, results, settings, llm, health)
│   │   ├── services/           # 業務邏輯 (Singleton pattern)
│   │   └── models/             # Pydantic 模型
│   └── frontend/               # 🎨 React + Vite (DDD)
│       ├── src/                # domain/, application/, infrastructure/, presentation/
│       └── e2e/                # 🎭 Playwright E2E 測試 (58 tests)
├── scripts/
│   └── services/               # 🚀 Systemd 部署腳本
├── docs/                       # 📖 文檔
└── data/                       # 測試資料
```

---

## 📊 Architecture | 系統架構

### 混合 PHI 檢測管道

```
┌─────────────────────────────────────────────────────────────┐
│              Hybrid PHI Detection Pipeline                   │
├─────────────────────────────────────────────────────────────┤
│  Level 1: Regex Fast Scan (~0.001s)                         │
│  ├── ID Numbers, Phone, Email, Date patterns                │
│  └── Coverage: ~30% of PHI                                  │
├─────────────────────────────────────────────────────────────┤
│  Level 2: SpaCy NER (~0.01-0.05s)                          │
│  ├── PERSON, DATE, ORG, GPE, LOC entities                  │
│  └── Coverage: ~40% of PHI                                  │
├─────────────────────────────────────────────────────────────┤
│  Level 3: LLM Semantic Analysis (~1-15s)                   │
│  ├── Context-aware PHI detection                            │
│  ├── granite4:1b / qwen2.5:1.5b                            │
│  └── DSPy optimized prompts                                 │
└─────────────────────────────────────────────────────────────┘
```

---

## 📚 Documentation | 文檔

| 文檔 | 說明 |
|------|------|
| [Architecture](docs/ARCHITECTURE.md) | 系統設計與 DDD 架構 |
| [Deployment](docs/DEPLOYMENT.md) | 安裝與配置指南 |
| [LLM Benchmark](docs/llm-benchmark-results.md) | 模型效能測試報告 |
| [Ollama Setup](docs/ollama-setup.md) | 本地 LLM 設定 |
| [Batch Processing](docs/batch-processing.md) | 批次處理指南 |

---

## 🤝 Contributing | 貢獻

歡迎貢獻！請參閱 [CONTRIBUTING.md](CONTRIBUTING.md)。

```bash
# 開發安裝
git clone https://github.com/u9401066/medical-deidentification.git
cd medical-deidentification
uv sync --dev

# 執行測試（請固定使用 uv 管理的環境）
uv run pytest tests/unit

# 前端單元測試
npm run test:run --workspace web/frontend

# 前端 E2E 測試 (Playwright)
npm --prefix web/frontend run test:e2e

# 程式碼格式化
uv run ruff format .
uv run ruff check . --fix
```

---

## 🚀 Deployment | 部署

### 內部測試：systemd + 同源 `/api` proxy

```bash
# 安裝/更新前後端為系統服務
sudo ./scripts/services/install-services.sh

# 驗證服務與同源 API proxy
systemctl status medical-deid-backend medical-deid-frontend --no-pager
curl -i http://127.0.0.1:5173/api/health

# 跑 8 步驟 smoke test。也可把 --url 改成 http://<LAN-IP>:5173
uv run python scripts/check_workflow.py --url http://127.0.0.1:5173 --frontend-proxy --process-timeout 240

# 卸載服務
sudo ./scripts/services/uninstall-services.sh
```

正式瀏覽器入口只需要開 `http://<server-ip>:5173`。前端會呼叫同源 `/api`，再由 `scripts/services/frontend-server.mjs` 代理到本機後端 `127.0.0.1:8000`；不要把前端重新 build 成 `http://<ip>:8000/api`，否則 NAT/LAN/瀏覽器 cookie 會再次踩雷。

### LAN 與 HTTPS production

```bash
# 信任內網測試，不需要帳密；每個瀏覽器仍有 HttpOnly session 隔離
sudo ./scripts/services/configure-lan-access.sh 192.168.1.201

# HTTPS + 帳密/RBAC production skeleton
sudo ./scripts/services/configure-production-proxy.sh deid.example.org admin
```

HTTPS 正式上線請用 Caddy 或 nginx 將所有流量反向代理到 `127.0.0.1:5173`，讓前端服務繼續代理 `/api`。範例見 [deploy/reverse-proxy](deploy/reverse-proxy) 與 [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)。

---

## 📄 License | 授權

[Apache 2.0 License](LICENSE) - 可商用、可修改、可分發

---

## ⚠️ Privacy Notice | 隱私聲明

- 🔐 所有資料處理 **100% 本地**，不外傳任何資料
- 🧹 Web UI 會先將上傳檔短暫暫存在 server 本機磁碟，處理完成後預設刪除原始內容；若服務中斷，啟動清理與 TTL 會補償清除
- 🚫 **永遠不要** 將真實 PHI 提交到版本控制
- ✅ 設計符合 **HIPAA** 和 **台灣個資法 (PDPA)**
- 👤 使用者需自行確保在其使用情境中的合規性

---

<div align="center">

**Built with ❤️ for Healthcare Privacy**

[⬆ Back to Top](#-medical-de-identification-toolkit)

</div>
