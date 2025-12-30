# DSPy 與 YAML Prompt 配置指南

本文檔說明如何使用 DSPy 進行自動 prompt 優化，以及如何使用 YAML 格式管理 prompt 配置。

## 目錄

1. [概述](#概述)
2. [YAML Prompt 配置](#yaml-prompt-配置)
3. [DSPy 整合](#dspy-整合)
4. [優化工作流程](#優化工作流程)
5. [API 參考](#api-參考)

---

## 概述

本專案使用兩種互補的方式管理 PHI 識別的 prompts：

| 方式 | 用途 | 優點 |
|------|------|------|
| **YAML 配置** | 儲存 prompt 模板、PHI 類型定義、few-shot 範例 | 版本控制、易於修改、無需重新部署 |
| **DSPy 優化** | 自動尋找最佳 prompt 和 few-shot 範例 | 自動化、基於指標優化 |

### 工作流程

```
┌─────────────────────────────────────────────────────────────┐
│  YAML Prompt Config (phi_identification.yaml)               │
│  ├── PHI 類型定義                                            │
│  ├── Prompt 模板 (system, user, simplified, cot)            │
│  ├── Few-shot 範例                                          │
│  └── 優化設定 (targets, weights)                            │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  DSPy Optimization                                          │
│  ├── BootstrapFewShot: 自動選擇最佳 few-shot 範例           │
│  └── MIPRO: 多階段指令優化                                  │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  Save Optimized Config (phi_identification.v1.1.0.yaml)     │
│  ├── 新的 few-shot 範例                                     │
│  └── Benchmark 結果 (F1, 時間)                              │
└─────────────────────────────────────────────────────────────┘
```

---

## YAML Prompt 配置

### 配置檔案結構

配置檔案位於 `medical_deidentification/infrastructure/prompts/` 目錄：

```
prompts/
├── phi_identification.yaml      # 主配置
├── phi_identification.v1.1.0.yaml  # 優化後版本
└── schema.yaml                  # 配置 Schema
```

### 基本結構

```yaml
# metadata: 基本資訊與版本
metadata:
  name: phi_identification
  version: "1.0.0"
  description: "PHI 識別 Prompt 配置"

# phi_types: PHI 類型定義
phi_types:
  NAME:
    description: 病患姓名、醫師姓名、家屬姓名
    examples:
      - 王大明
      - Dr. John Smith
    priority: high

# prompts: Prompt 模板
prompts:
  simplified:
    template: |
      識別醫療文本中的 PHI...
      文本：{{ medical_text }}
    variables:
      - medical_text

# few_shot_examples: Few-shot 範例
few_shot_examples:
  - input: "病患王大明，身分證A123456789"
    output: '[{"text": "王大明", "phi_type": "NAME"}, ...]'

# optimization: DSPy 優化設定
optimization:
  targets:
    min_f1_score: 0.80
    max_response_time_ms: 5000

# model_configs: 模型特定設定
model_configs:
  granite4:1b:
    prompt_style: simplified
    temperature: 0.1
```

### 使用配置

```python
from medical_deidentification.infrastructure.prompts import (
    load_prompt_config,
    PromptManager,
)

# 方法 1: 使用便捷函數
config = load_prompt_config("phi_identification")

# 方法 2: 使用 PromptManager
manager = PromptManager()
config = manager.load("phi_identification", version="1.0.0")

# 取得 prompt
prompt = config.get_prompt(
    model_name="granite4:1b",
    medical_text="病患王大明..."
)

# 取得 PHI 類型列表
phi_types = config.get_phi_type_list()
# ['NAME', 'ID', 'PHONE', 'DATE', ...]

# 取得 few-shot 範例
examples = config.get_few_shot_examples(n=3)
```

---

## DSPy 整合

### 基本使用

```python
from medical_deidentification.infrastructure.dspy import (
    configure_dspy_ollama,
    PHIIdentifier,
    PHIIdentifierWithConfig,
    create_phi_identifier_from_yaml,
)

# 1. 配置 DSPy 使用 Ollama
configure_dspy_ollama(model_name="granite4:1b")

# 2a. 使用基本識別器
identifier = PHIIdentifier()
entities = identifier.forward("病患王大明...")

# 2b. 使用 YAML 配置的識別器 (推薦)
identifier = create_phi_identifier_from_yaml(
    config_name="phi_identification",
    model_name="granite4:1b",
)
entities = identifier("病患王大明...")

# 3. 處理結果
for entity in entities:
    print(f"[{entity.phi_type}] {entity.text} (reason: {entity.reason})")
```

### 支援的模型

| 模型 | 大小 | F1 Score | 推薦 |
|------|------|----------|------|
| granite4:1b | 3.3GB | 89.4% | 🏆 生產環境 |
| qwen2.5:1.5b | 986MB | 66.7% | ⭐ 開發測試 |
| llama3.2:1b | 1.3GB | 55.0% | 高召回需求 |

```python
from medical_deidentification.infrastructure.dspy import LIGHTWEIGHT_MODELS

for name, info in LIGHTWEIGHT_MODELS.items():
    if info["recommended"]:
        print(f"{name}: {info['description']}")
```

---

## 優化工作流程

### 準備訓練資料

訓練資料使用標記格式：`【PHI:TYPE:ID】content【/PHI】`

```python
tagged_texts = [
    "病患【PHI:NAME:1】王大明【/PHI】，男性，65歲，"
    "身分證字號【PHI:ID:2】A123456789【/PHI】。",
    
    "主治醫師：【PHI:NAME:3】張明華【/PHI】醫師\n"
    "入院日期：【PHI:DATE:4】2024年5月15日【/PHI】",
    
    "【PHI:AGE_OVER_89:5】92歲【/PHI】女性，"
    "於【PHI:FACILITY:6】台北榮民總醫院【/PHI】急診就醫。",
]
```

### 執行優化

```python
from medical_deidentification.infrastructure.dspy import (
    optimize_and_save_to_yaml,
    PHIPromptOptimizer,
)

# 方法 1: 一鍵優化並保存到 YAML (推薦)
result, yaml_path = optimize_and_save_to_yaml(
    tagged_texts=tagged_texts,
    model_name="granite4:1b",
    config_name="phi_identification",
    method="bootstrap",  # 或 "mipro"
)

print(f"F1 improvement: {result.improvement:.2%}")
print(f"Saved to: {yaml_path}")

# 方法 2: 手動控制優化流程
optimizer = PHIPromptOptimizer(
    target_f1=0.85,
    max_time_ms=3000,
)

trainset = optimizer.create_trainset_from_tagged_data(tagged_texts)

result = optimizer.optimize(
    trainset=trainset,
    method="bootstrap",
    max_bootstrapped_demos=5,
)
```

### 使用優化後的配置

```python
from medical_deidentification.infrastructure.dspy import (
    load_optimized_identifier,
)

# 載入最新版本
identifier = load_optimized_identifier(
    config_name="phi_identification",
    model_name="granite4:1b",
)

# 或指定版本
identifier = load_optimized_identifier(
    config_name="phi_identification",
    version="1.1.0",
    model_name="granite4:1b",
)

# 使用
entities = identifier("病患王大明...")
```

---

## API 參考

### PromptManager

```python
class PromptManager:
    """Prompt 配置管理器"""
    
    def load(name: str, version: str = None) -> PromptConfig:
        """載入 YAML 配置"""
        
    def save(config: PromptConfig, path: str = None) -> Path:
        """保存配置到 YAML"""
        
    def save_optimized(
        config: PromptConfig,
        new_version: str = None,
        benchmark_results: dict = None,
        new_examples: list = None,
    ) -> Path:
        """保存優化後的配置"""
        
    def list_prompts() -> List[dict]:
        """列出所有可用的 prompts"""
        
    def validate(config: PromptConfig) -> List[str]:
        """驗證配置"""
```

### PHIIdentifierWithConfig

```python
class PHIIdentifierWithConfig(dspy.Module):
    """使用 YAML 配置的 PHI 識別器"""
    
    def __init__(config: PromptConfig, model_name: str):
        """初始化"""
        
    def forward(medical_text: str) -> List[PHIEntity]:
        """識別 PHI"""
        
    def get_few_shot_examples() -> List[dict]:
        """取得 few-shot 範例"""
        
    def get_optimization_settings() -> dict:
        """取得優化設定"""
```

### PHIPromptOptimizer

```python
class PHIPromptOptimizer:
    """DSPy Prompt 優化器"""
    
    def create_trainset_from_tagged_data(
        tagged_texts: List[str]
    ) -> List[dspy.Example]:
        """從標記資料創建訓練集"""
        
    def optimize(
        trainset: List,
        valset: List = None,
        method: str = "bootstrap",
        max_bootstrapped_demos: int = 3,
        save_path: str = None,
    ) -> OptimizationResult:
        """執行優化"""
```

---

## 最佳實踐

### 1. 版本控制 Prompts

```bash
# 追蹤 YAML 配置變更
git add medical_deidentification/infrastructure/prompts/*.yaml
git commit -m "feat(prompts): update PHI identification v1.2.0"
```

### 2. 模型特定配置

在 YAML 中為不同模型設定最佳參數：

```yaml
model_configs:
  granite4:1b:
    prompt_style: simplified
    temperature: 0.1
    use_cot: false
    
  llama3.2:1b:
    prompt_style: cot  # 使用 Chain-of-Thought
    temperature: 0.2
    use_cot: true
```

### 3. 持續優化

```python
# 定期用新資料優化
result, path = optimize_and_save_to_yaml(
    tagged_texts=new_training_data,
    config_name="phi_identification",
)

# 比較版本
manager = PromptManager()
v1 = manager.load("phi_identification", version="1.0.0")
v2 = manager.load("phi_identification", version="1.1.0")

print(f"v1 F1: {v1.benchmark.get('f1_score')}")
print(f"v2 F1: {v2.benchmark.get('f1_score')}")
```

---

## 疑難排解

### DSPy 未安裝

```bash
pip install dspy-ai
# 或
uv add dspy-ai
```

### Ollama 連線失敗

```bash
# 確認 Ollama 正在運行
ollama list

# 啟動 Ollama
ollama serve
```

### YAML 配置載入失敗

```python
# 驗證配置
manager = PromptManager()
config = manager.load("phi_identification")
errors = manager.validate(config)

if errors:
    for error in errors:
        print(f"Error: {error}")
```
