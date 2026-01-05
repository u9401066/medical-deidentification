# Python 環境管理子法

> 依據專案開發最佳實踐訂定

---

## 第 1 條：套件管理器優先順序

```
uv > pip-tools > pip
```

### 1.1 uv 優先原則
1. **本專案使用 uv** 作為套件管理器
2. uv 速度比 pip 快 10-100 倍
3. 原生支援 lockfile 和虛擬環境

### 1.2 降級條件
僅在以下情況可使用 pip：
- CI 環境不支援 uv
- 特殊依賴衝突

---

## 第 2 條：虛擬環境規範

### 2.1 必須使用虛擬環境
```bash
# ✅ 正確
uv venv
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate     # Windows

# ❌ 禁止全域安裝
pip install package  # 在系統 Python 中
```

### 2.2 虛擬環境位置
```
medical-deidentification/
├── .venv/           # 虛擬環境（gitignore）
├── pyproject.toml   # 專案配置
└── uv.lock          # 依賴鎖定（可選，不納入版控）
```

### 2.3 Python 版本
- 本專案使用 Python 3.10+
- 版本在 `pyproject.toml` 中明確指定

---

## 第 3 條：依賴管理

### 3.1 檔案結構
```
pyproject.toml       # 主要依賴定義（必須）
uv.lock              # 依賴鎖定檔（可選）
```

### 3.2 常用 uv 指令
```bash
# 建立虛擬環境
uv venv

# 安裝依賴（包含開發依賴）
uv pip install -e ".[dev]"

# 或使用 sync
uv sync --all-extras

# 新增依賴
uv add langchain
uv add --dev pytest

# 移除依賴
uv remove package-name

# 更新依賴
uv lock --upgrade

# 執行命令
uv run pytest
uv run ruff check .
```

---

## 第 4 條：開發環境設定

### 4.1 首次設定
```bash
# 1. 安裝 uv
curl -LsSf https://astral.sh/uv/install.sh | sh
# 或 Windows:
# powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# 2. 建立虛擬環境
cd medical-deidentification
uv venv

# 3. 啟動虛擬環境
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# 4. 安裝依賴
uv pip install -e ".[dev]"

# 5. 驗證安裝
uv run pytest tests/unit/ -v
```

### 4.2 PyTorch 特殊安裝
由於 torch 需要特殊索引，請執行：
```bash
# CPU 版本
uv pip install torch==2.2.0 --index-url https://download.pytorch.org/whl/cpu

# 或 CUDA 版本
uv pip install torch==2.2.0 --index-url https://download.pytorch.org/whl/cu118
```

---

## 第 5 條：程式碼品質工具

### 5.1 Ruff（取代 black + isort + flake8）
```bash
# 檢查
uv run ruff check .

# 自動修復
uv run ruff check --fix .

# 格式化
uv run ruff format .
```

### 5.2 MyPy（型別檢查）
```bash
uv run mypy core/
```

### 5.3 Bandit（安全掃描）
```bash
uv run bandit -r core/
```

### 5.4 測試
```bash
# 全部測試
uv run pytest

# 單元測試
uv run pytest tests/unit/ -v

# 整合測試
uv run pytest tests/integration/ -v

# 含覆蓋率
uv run pytest --cov=core --cov-report=html
```

---

## 第 6 條：uvx 工具執行（類似 npx）

```bash
# 臨時執行工具（不安裝）
uvx ruff check .
uvx bandit -r src/
uvx mypy src/

# 執行特定版本
uvx ruff@0.8.0 check .
```

---

## 附錄：快速參考卡

| 操作 | uv 指令 | pip 對應 |
|------|---------|----------|
| 建立 venv | `uv venv` | `python -m venv .venv` |
| 安裝套件 | `uv add package` | `pip install package` |
| 安裝開發依賴 | `uv add --dev package` | `pip install package` |
| 安裝全部 | `uv sync --all-extras` | `pip install -e ".[dev]"` |
| 更新 lock | `uv lock` | `pip-compile` |
| 執行命令 | `uv run pytest` | `pytest` |
| 查看依賴 | `uv pip list` | `pip list` |

---

*本子法版本：v1.0.0*
