# 🦙 Ollama 連線設定指引

> 本文檔說明如何讓 fastMAG Agent 連接 Ollama LLM 服務，包含常見問題排除

## 📋 目錄

1. [網路架構概覽](#網路架構概覽)
2. [環境變數設定](#環境變數設定)
3. [連線方式](#連線方式)
4. [常見問題排除](#常見問題排除)
5. [驗證連線](#驗證連線)

---

## 🌐 網路架構概覽

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           網路拓撲                                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────────┐         ┌──────────────────┐         ┌──────────────┐ │
│  │ 192.168.1.112    │         │ 192.168.1.2      │         │ 192.168.1.111│ │
│  │ (fastMAG Agent)  │ ──────▶ │ (Windows 中繼)   │ ──────▶ │ (Ollama主機) │ │
│  │                  │         │ Port Forward     │         │ :11434       │ │
│  └──────────────────┘         │ :30133→111:11434 │         └──────────────┘ │
│                               └──────────────────┘                          │
│                                                                              │
│  或直連:                                                                     │
│  ┌──────────────────┐                              ┌──────────────────┐     │
│  │ 192.168.1.112    │ ──────────────────────────▶ │ 192.168.1.111    │     │
│  │ (fastMAG Agent)  │         直接連線            │ (Ollama :11434)  │     │
│  └──────────────────┘                              └──────────────────┘     │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 主機角色

| IP | 角色 | 服務 |
|-----|------|------|
| `192.168.1.111` | Ollama 主機 | Ollama API `:11434` |
| `192.168.1.2` | Windows 中繼 | Port Forward `:30133` → `111:11434` |
| `192.168.1.112` | Agent 主機 | fastMAG Agent |

---

## 🔧 環境變數設定

### 核心環境變數

```bash
# LLM 設定
export LLM_PROVIDER=ollama          # 必須設為 "ollama"
export LLM_BASE_URL=http://192.168.1.111:11434   # Ollama API 端點
export LLM_MODEL=gpt-oss:120b       # 模型名稱 (依實際可用模型)
export LLM_TIMEOUT=300              # 超時秒數 (大模型需較長時間)

# MCP 設定 (可選)
export MCP_SSE_URL=http://192.168.1.111:8765/sse  # MCP Server 端點
```

### 常用模型名稱

| 模型 | 名稱 | 說明 |
|------|------|------|
| GPT-OSS 120B | `gpt-oss:120b` | 高性能醫療模型 |
| Llama 3.3 70B | `llama3.3:70b` | Meta Llama 3.3 |
| Llama Taiwan 8B | `llama3-taiwan:8b` | 繁體中文優化 |
| Gemma 3 27B | `gemma3:27b` | Google Gemma |

---

## 📡 連線方式

### 方式 1: 直接連線 (推薦)

如果 `192.168.1.112` 可以直接連到 `192.168.1.111`:

```bash
# 測試連線
curl http://192.168.1.111:11434/api/tags

# 啟動 Agent
LLM_PROVIDER=ollama \
LLM_BASE_URL=http://192.168.1.111:11434 \
LLM_MODEL=gpt-oss:120b \
LLM_TIMEOUT=300 \
python main.py
```

### 方式 2: 透過 Windows Port Forward

如果直連不通，需要透過 `192.168.1.2` 中繼:

```bash
# 測試連線 (透過中繼)
curl http://192.168.1.2:30133/api/tags

# 啟動 Agent
LLM_PROVIDER=ollama \
LLM_BASE_URL=http://192.168.1.2:30133 \
LLM_MODEL=gpt-oss:120b \
LLM_TIMEOUT=300 \
python main.py
```

### Windows Port Forward 設定

在 Windows 中繼機 (`192.168.1.2`) 執行:

```powershell
# 添加 Port Forward 規則
netsh interface portproxy add v4tov4 listenport=30133 listenaddress=0.0.0.0 connectport=11434 connectaddress=192.168.1.111

# 防火牆允許 30133 端口
netsh advfirewall firewall add rule name="Ollama Proxy" dir=in action=allow protocol=tcp localport=30133

# 查看現有規則
netsh interface portproxy show all

# 刪除規則 (如需)
netsh interface portproxy delete v4tov4 listenport=30133 listenaddress=0.0.0.0
```

---

## 🔍 常見問題排除

### 問題 1: Connection Refused

**現象:**
```
httpx.ConnectError: [Errno 111] Connection refused
```

**排除步驟:**

1. **確認 Ollama 服務運行中**
   ```bash
   # 在 Ollama 主機 (192.168.1.111) 執行
   systemctl status ollama
   # 或
   ollama list
   ```

2. **確認 Ollama 監聽所有介面**
   ```bash
   # 檢查 Ollama 是否只監聽 localhost
   ss -tlnp | grep 11434
   
   # 如果只顯示 127.0.0.1:11434，需要修改設定
   # 編輯 /etc/systemd/system/ollama.service
   # 添加環境變數:
   Environment="OLLAMA_HOST=0.0.0.0:11434"
   
   # 重啟服務
   sudo systemctl daemon-reload
   sudo systemctl restart ollama
   ```

3. **測試網路連通性**
   ```bash
   # 從 Agent 主機測試
   ping 192.168.1.111
   nc -zv 192.168.1.111 11434
   curl http://192.168.1.111:11434/api/tags
   ```

### 問題 2: Timeout

**現象:**
```
httpx.ReadTimeout: timed out
```

**解決:**

```bash
# 增加超時時間 (大模型需要更長時間)
export LLM_TIMEOUT=300  # 5 分鐘

# 或在啟動時指定
LLM_TIMEOUT=300 python main.py
```

### 問題 3: Model Not Found

**現象:**
```
Error: model 'xxx' not found
```

**解決:**

```bash
# 在 Ollama 主機查看可用模型
ollama list

# 拉取模型
ollama pull gpt-oss:120b

# 使用正確的模型名稱
export LLM_MODEL=gpt-oss:120b
```

### 問題 4: langchain-ollama 未安裝

**現象:**
```
RuntimeError: langchain-ollama 未安裝
```

**解決:**

```bash
pip install langchain-ollama
```

### 問題 5: 中繼 Port Forward 不通

**排除步驟:**

```powershell
# 1. 在 Windows 中繼機確認 Port Forward 規則
netsh interface portproxy show all

# 預期輸出:
# Listen on ipv4:             Connect to ipv4:
# Address         Port        Address         Port
# --------------- ----------  --------------- ----------
# 0.0.0.0         30133       192.168.1.111   11434

# 2. 確認防火牆規則
netsh advfirewall firewall show rule name="Ollama Proxy"

# 3. 測試從 Windows 本機連到 Ollama
curl http://192.168.1.111:11434/api/tags

# 4. 測試 Port Forward 是否生效
curl http://localhost:30133/api/tags
```

---

## ✅ 驗證連線

### 1. API 連線測試

```bash
# 測試 Ollama API
curl -s http://${LLM_BASE_URL}/api/tags | jq

# 預期輸出: 模型列表 JSON
```

### 2. 模型列表

```bash
# 查看可用模型
curl -s http://${LLM_BASE_URL}/api/tags | jq '.models[].name'
```

### 3. 簡單推理測試

```bash
# 測試生成
curl -X POST http://${LLM_BASE_URL}/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-oss:120b",
    "messages": [{"role": "user", "content": "你好"}],
    "stream": false
  }' | jq '.message.content'
```

### 4. fastMAG 連線測試

```python
# test_ollama_connection.py
import asyncio
import os
import sys
sys.path.insert(0, "src")

from infrastructure.llm import OllamaAdapter

async def test():
    adapter = OllamaAdapter(
        base_url=os.getenv("LLM_BASE_URL", "http://192.168.1.111:11434"),
        model=os.getenv("LLM_MODEL", "gpt-oss:120b"),
        timeout=float(os.getenv("LLM_TIMEOUT", "300")),
    )
    
    from infrastructure.llm import LLMRequest
    request = LLMRequest(
        prompt="你是誰?",
        system_prompt="你是一個醫療助理",
        temperature=0.7,
    )
    
    response = await adapter.generate(request)
    print(f"回應: {response.content}")
    print(f"Token: {response.usage}")

asyncio.run(test())
```

執行:
```bash
LLM_PROVIDER=ollama \
LLM_BASE_URL=http://192.168.1.111:11434 \
LLM_MODEL=gpt-oss:120b \
LLM_TIMEOUT=300 \
python test_ollama_connection.py
```

---

## 📝 完整啟動範例

### .env 檔案 (推薦)

```bash
# .env
LLM_PROVIDER=ollama
LLM_BASE_URL=http://192.168.1.111:11434
LLM_MODEL=gpt-oss:120b
LLM_TIMEOUT=300
LLM_TEMPERATURE=0.7

MCP_SSE_URL=http://192.168.1.111:8765/sse
MCP_TIMEOUT=30
```

### 直接執行

```bash
# 使用 .env 檔案
python main.py

# 或直接指定環境變數
LLM_PROVIDER=ollama \
LLM_BASE_URL=http://192.168.1.111:11434 \
LLM_MODEL=gpt-oss:120b \
LLM_TIMEOUT=300 \
MCP_SSE_URL=http://192.168.1.111:8765/sse \
python main.py
```

---

## 📊 程式碼參考

### OllamaAdapter 位置

```
src/infrastructure/llm/__init__.py  # OllamaAdapter 類別
src/interfaces/api/container.py     # 根據 LLM_PROVIDER 選擇 adapter
src/infrastructure/config/__init__.py  # 環境變數載入
```

### 關鍵程式碼

```python
# container.py - LLM Adapter 選擇邏輯
if provider == "ollama":
    # Ollama 使用原生 API，不需要 /v1 後綴
    base_url = cfg.base_url.rstrip("/")
    self._llm = OllamaAdapter(
        base_url=base_url,
        model=cfg.model,
        timeout=cfg.timeout,
        temperature=cfg.temperature,
    )
```

---

## 🔄 故障恢復流程

```
連線失敗?
    │
    ├── 1. 確認 Ollama 服務運行
    │       └── systemctl status ollama
    │
    ├── 2. 確認網路連通
    │       └── curl http://192.168.1.111:11434/api/tags
    │
    ├── 3. 確認監聽介面
    │       └── OLLAMA_HOST=0.0.0.0:11434
    │
    ├── 4. 嘗試 Port Forward
    │       └── 透過 192.168.1.2:30133
    │
    └── 5. 檢查防火牆
            └── 開放 11434 / 30133 端口
```

---

## 📅 更新記錄

| 日期 | 更新內容 |
|------|----------|
| 2025-12-10 | 初版建立 |
| 2025-12-09 | 確認 192.168.1.2 Port Forward 方案可行 |

---

## 📞 聯絡資訊

如有問題，請檢查:
1. `docs/TECHNICAL_SPEC.md` - 技術規格
2. `README.md` - 專案說明
3. Memory Bank (`memory-bank/`) - 開發記錄
