# 架構修正：StrategyType 移至 Domain 層

## 問題發現

用戶正確指出：`StrategyType` 被放在 `application/processing/strategies.py` 中，違反了 DDD 架構原則。

### ❌ 原本的錯誤架構

```
application/processing/
└── strategies.py
    ├── class StrategyType(str, Enum)  # ❌ 類型定義不應在 application 層
    ├── class RedactionStrategy
    ├── class GeneralizationStrategy
    └── ...
```

### 問題分析

根據 **DDD (Domain-Driven Design)** 原則：

- **Domain Layer**: 業務概念、類型定義、領域規則（不依賴其他層）
- **Application Layer**: 業務邏輯的實作（可以依賴 Domain）

`StrategyType` 是**業務概念**（遮蔽策略的類型），就像 `PHIType` 一樣，應該屬於 Domain 層。

## 修正方案

### ✅ 正確的架構

```
domain/
├── phi_types.py          # PHI 類型定義 (已正確)
└── masking_types.py      # ✅ 新增：遮蔽策略類型定義

application/processing/
└── strategies.py         # ✅ 只包含實作類別
    ├── class RedactionStrategy
    ├── class GeneralizationStrategy
    └── ...
```

## 修正內容

### 1. 創建 `domain/masking_types.py`

```python
from enum import Enum

class StrategyType(str, Enum):
    """遮蔽策略類型 | Masking strategy types"""
    REDACTION = "redaction"
    GENERALIZATION = "generalization"
    PSEUDONYMIZATION = "pseudonymization"
    DATE_SHIFTING = "date_shifting"
    PARTIAL_MASKING = "partial_masking"
    SUPPRESSION = "suppression"
```

### 2. 更新 `domain/__init__.py`

```python
from .masking_types import StrategyType

__all__ = [
    "PHIType",
    "CustomPHIType",
    "StrategyType",  # ✅ 新增
    ...
]
```

### 3. 更新所有導入路徑

修改前：
```python
# ❌ 從 application 層導入
from medical_deidentification.application.processing.strategies import StrategyType
```

修改後：
```python
# ✅ 從 domain 層導入
from medical_deidentification.domain import StrategyType
```

### 4. 更新的文件清單

- ✅ `domain/masking_types.py` - 新建
- ✅ `domain/__init__.py` - 導出 StrategyType
- ✅ `application/processing/strategies.py` - 移除定義，改為導入
- ✅ `application/processing/__init__.py` - 更新導入路徑
- ✅ `application/processing/engine/config.py` - 更新導入路徑
- ✅ `application/processing/engine/masking.py` - 更新導入路徑
- ✅ `application/processing/engine/core.py` - 更新文檔
- ✅ `examples/deidentification_engine_example.py` - 更新導入路徑

## 測試結果

```bash
$ python test_strategy_type_fix.py

✓ Test 1: Import from domain layer successful
  StrategyType.REDACTION = redaction
  StrategyType.GENERALIZATION = generalization

✓ Test 2: Import strategies successful

✓ Test 3: Create strategy successful
  Strategy type: redaction
  Strategy class: RedactionStrategy

✓ Test 4: All strategy types:
  redaction            → RedactionStrategy
  generalization       → GeneralizationStrategy
  pseudonymization     → PseudonymizationStrategy
  date_shifting        → DateShiftingStrategy
  partial_masking      → PartialMaskingStrategy
  suppression          → SuppressionStrategy

✅ 架構修正成功！
```

## 架構優勢

### 符合 DDD 原則

```
Domain Layer (領域層)
├── PHIType          - PHI 的類型定義
├── StrategyType     - 遮蔽策略的類型定義
└── PHIEntity        - PHI 實體

Application Layer (應用層)
├── Strategies       - 遮蔽策略的實作
├── Engine           - 去識別化引擎
└── Pipeline         - 處理流程
```

### 清晰的依賴關係

- ✅ Domain 層不依賴任何其他層
- ✅ Application 層依賴 Domain 層
- ✅ 類型定義集中在 Domain 層
- ✅ 實作細節在 Application 層

### 更好的可測試性

```python
# 測試時只需導入 domain 層
from medical_deidentification.domain import StrategyType, PHIType

# 不需要載入整個 application 層
```

## 使用範例

### 正確的導入方式

```python
# 導入類型定義（從 domain）
from medical_deidentification.domain import (
    PHIType,           # PHI 類型
    StrategyType,      # 遮蔽策略類型
    PHIEntity          # PHI 實體
)

# 導入實作類別（從 application）
from medical_deidentification.application.processing import (
    RedactionStrategy,          # 刪除策略實作
    GeneralizationStrategy,     # 泛化策略實作
    create_masking_strategy,    # 工廠函數
)

# 使用
config = EngineConfig(
    default_strategy=StrategyType.GENERALIZATION,  # 從 domain 導入
    phi_specific_strategies={
        PHIType.NAME: StrategyType.PSEUDONYMIZATION  # 兩者都從 domain
    }
)
```

## 總結

✅ **修正完成**
- `StrategyType` 已正確放置在 `domain` 層
- 所有導入路徑已更新
- 符合 DDD 架構原則
- 測試通過

🙏 **感謝用戶指出這個架構問題！**
