"""
PHI Detection Benchmark Module | PHI 識別基準測試模組

提供 PHI 識別系統的評估功能：
- 支援多種 benchmark 資料格式 (i2b2, CBLUE, Presidio Evaluator)
- 計算精確率、召回率、F1 Score
- 按 PHI 類型分類統計
- 產生評估報告

使用範例:
```python
from scripts.benchmark import PHIEvaluator, load_benchmark_data

# 定義 PHI 識別器
def my_detector(text: str):
    # 你的 PHI 識別邏輯
    return [("John Doe", "NAME"), ("2024-01-15", "DATE")]

# 建立評估器並執行
evaluator = PHIEvaluator(detector=my_detector)
report = evaluator.evaluate("data/benchmark/test.jsonl")
report.print_summary()
```
"""

from .data_loader import (
    BenchmarkSample,
    CBLUELoader,
    I2B2Loader,
    JSONLoader,
    PHIAnnotation,
    PresidioEvaluatorLoader,
    load_all,
    load_benchmark_data,
)
from .evaluator import (
    EvaluationReport,
    EvaluationResult,
    PHIEvaluator,
    create_detector_from_engine,
    quick_evaluate,
)
from .metrics import (
    ConfusionMatrix,
    EvaluationMetrics,
    calculate_f1,
    calculate_metrics,
    calculate_metrics_by_type,
    calculate_precision,
    calculate_recall,
    match_entities,
    normalize_phi_type,
)

__all__ = [
    # Metrics
    "calculate_precision",
    "calculate_recall",
    "calculate_f1",
    "calculate_metrics",
    "calculate_metrics_by_type",
    "match_entities",
    "normalize_phi_type",
    "ConfusionMatrix",
    "EvaluationMetrics",
    # Evaluator
    "PHIEvaluator",
    "EvaluationResult",
    "EvaluationReport",
    "create_detector_from_engine",
    "quick_evaluate",
    # Data Loader
    "load_benchmark_data",
    "load_all",
    "BenchmarkSample",
    "PHIAnnotation",
    "JSONLoader",
    "I2B2Loader",
    "CBLUELoader",
    "PresidioEvaluatorLoader",
]
