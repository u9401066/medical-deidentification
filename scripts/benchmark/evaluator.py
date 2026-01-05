"""
PHI Evaluator | PHI 識別評估器

整合 PHI 識別系統與 benchmark 資料進行評估
支援 Presidio Evaluator 風格的評估流程
"""

import json
import logging
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from .data_loader import (
    BenchmarkSample,
    load_benchmark_data,
)
from .metrics import (
    ConfusionMatrix,
    EvaluationMetrics,
    calculate_metrics,
    calculate_metrics_by_type,
)

logger = logging.getLogger(__name__)


@dataclass
class EvaluationResult:
    """
    單個樣本的評估結果
    
    Attributes:
        sample_id: 樣本 ID
        ground_truth: 標準答案
        predictions: 預測結果
        confusion_matrix: 混淆矩陣
        inference_time: 推論時間 (秒)
        error: 錯誤訊息 (如有)
    """
    sample_id: str
    ground_truth: list[tuple]
    predictions: list[tuple]
    confusion_matrix: ConfusionMatrix
    inference_time: float = 0.0
    error: str | None = None

    @property
    def is_success(self) -> bool:
        return self.error is None

    def to_dict(self) -> dict:
        return {
            "sample_id": self.sample_id,
            "ground_truth": self.ground_truth,
            "predictions": self.predictions,
            "metrics": self.confusion_matrix.to_dict(),
            "inference_time": self.inference_time,
            "error": self.error,
        }


@dataclass
class EvaluationReport:
    """
    完整評估報告
    
    Attributes:
        metrics: 評估指標
        results: 各樣本結果
        config: 評估設定
        timestamp: 評估時間
    """
    metrics: EvaluationMetrics
    results: list[EvaluationResult]
    config: dict[str, Any]
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    @property
    def success_rate(self) -> float:
        if not self.results:
            return 0.0
        return sum(1 for r in self.results if r.is_success) / len(self.results)

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "config": self.config,
            "metrics": self.metrics.to_dict(),
            "success_rate": self.success_rate,
            "total_samples": len(self.results),
            "results": [r.to_dict() for r in self.results],
        }

    def save(self, path: str | Path):
        """儲存報告為 JSON"""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)

    def print_summary(self):
        """印出摘要"""
        m = self.metrics
        print("\n" + "=" * 60)
        print("📊 PHI 識別評估報告")
        print("=" * 60)
        print(f"⏰ 時間: {self.timestamp}")
        print(f"📁 樣本數: {m.total_samples}")
        print(f"✅ 成功率: {self.success_rate:.1%}")
        print(f"⏱️  平均時間: {m.avg_time_per_sample:.2f}s/sample")
        print("-" * 60)
        print("📈 整體指標:")
        print(f"   Precision: {m.overall.precision:.3f}")
        print(f"   Recall:    {m.overall.recall:.3f}")
        print(f"   F1 Score:  {m.overall.f1:.3f}")
        print("-" * 60)
        print("📋 按 PHI 類型:")
        for phi_type, cm in sorted(m.by_type.items()):
            print(f"   {phi_type:12} | P={cm.precision:.3f} R={cm.recall:.3f} F1={cm.f1:.3f}")
        print("=" * 60)


# Type alias for PHI detector function
PHIDetector = Callable[[str], list[tuple]]


class PHIEvaluator:
    """
    PHI 識別評估器
    
    整合 PHI 識別系統與 benchmark 資料進行評估。
    支援 Presidio Evaluator 風格的評估流程。
    
    使用範例:
    ```python
    # 定義 PHI detector 函數
    def my_detector(text: str) -> List[tuple]:
        # 呼叫你的 PHI 識別系統
        result = your_phi_system.identify(text)
        return [(entity.text, entity.type) for entity in result]
    
    # 建立評估器
    evaluator = PHIEvaluator(detector=my_detector)
    
    # 執行評估
    report = evaluator.evaluate("data/benchmark/test.jsonl")
    report.print_summary()
    report.save("results/evaluation.json")
    ```
    """

    def __init__(
        self,
        detector: PHIDetector | None = None,
        match_type: str = "partial",
        verbose: bool = True,
    ):
        """
        初始化評估器
        
        Args:
            detector: PHI 識別函數，接收文字，返回 [(text, type), ...]
            match_type: 匹配方式 (exact, partial, overlap)
            verbose: 是否顯示進度
        """
        self.detector = detector
        self.match_type = match_type
        self.verbose = verbose

    def set_detector(self, detector: PHIDetector):
        """設定 PHI 識別器"""
        self.detector = detector

    def evaluate(
        self,
        data_path: str | Path,
        format: str = "auto",
        limit: int | None = None,
        save_path: str | Path | None = None,
    ) -> EvaluationReport:
        """
        執行評估
        
        Args:
            data_path: benchmark 資料路徑
            format: 資料格式
            limit: 限制樣本數 (debug 用)
            save_path: 結果儲存路徑
        
        Returns:
            EvaluationReport
        """
        if self.detector is None:
            raise ValueError("No detector set. Use set_detector() first.")

        # 載入資料
        samples = list(load_benchmark_data(data_path, format))
        if limit:
            samples = samples[:limit]

        if self.verbose:
            print(f"📂 載入 {len(samples)} 個樣本")

        # 評估
        results = []
        metrics = EvaluationMetrics()
        total_time = 0.0

        for i, sample in enumerate(samples):
            if self.verbose and (i + 1) % 10 == 0:
                print(f"⏳ 進度: {i + 1}/{len(samples)}")

            result = self._evaluate_sample(sample)
            results.append(result)

            if result.is_success:
                metrics.overall = metrics.overall + result.confusion_matrix
                total_time += result.inference_time

                # 按類型統計
                type_metrics = calculate_metrics_by_type(
                    sample.ground_truth,
                    result.predictions,
                    self.match_type,
                )
                for phi_type, cm in type_metrics.items():
                    metrics.add_type_result(phi_type, cm)

        metrics.total_samples = len(samples)
        metrics.total_time = total_time

        # 建立報告
        report = EvaluationReport(
            metrics=metrics,
            results=results,
            config={
                "data_path": str(data_path),
                "format": format,
                "match_type": self.match_type,
                "limit": limit,
            },
        )

        if save_path:
            report.save(save_path)
            if self.verbose:
                print(f"💾 報告已儲存至 {save_path}")

        if self.verbose:
            report.print_summary()

        return report

    def _evaluate_sample(self, sample: BenchmarkSample) -> EvaluationResult:
        """評估單個樣本"""
        try:
            start_time = time.time()
            predictions = self.detector(sample.text)
            inference_time = time.time() - start_time

            cm = calculate_metrics(
                sample.ground_truth,
                predictions,
                self.match_type,
            )

            return EvaluationResult(
                sample_id=sample.id,
                ground_truth=sample.ground_truth,
                predictions=predictions,
                confusion_matrix=cm,
                inference_time=inference_time,
            )

        except Exception as e:
            logger.error(f"Error evaluating sample {sample.id}: {e}")
            return EvaluationResult(
                sample_id=sample.id,
                ground_truth=sample.ground_truth,
                predictions=[],
                confusion_matrix=ConfusionMatrix(),
                error=str(e),
            )

    def evaluate_samples(
        self,
        samples: list[BenchmarkSample],
        save_path: str | Path | None = None,
    ) -> EvaluationReport:
        """
        評估已載入的樣本列表
        
        Args:
            samples: BenchmarkSample 列表
            save_path: 結果儲存路徑
        
        Returns:
            EvaluationReport
        """
        if self.detector is None:
            raise ValueError("No detector set. Use set_detector() first.")

        results = []
        metrics = EvaluationMetrics()
        total_time = 0.0

        for sample in samples:
            result = self._evaluate_sample(sample)
            results.append(result)

            if result.is_success:
                metrics.overall = metrics.overall + result.confusion_matrix
                total_time += result.inference_time

        metrics.total_samples = len(samples)
        metrics.total_time = total_time

        report = EvaluationReport(
            metrics=metrics,
            results=results,
            config={"source": "samples", "match_type": self.match_type},
        )

        if save_path:
            report.save(save_path)

        return report


def create_detector_from_engine(engine) -> PHIDetector:
    """
    從 DeidentificationEngine 建立 detector
    
    Args:
        engine: DeidentificationEngine 實例
    
    Returns:
        PHIDetector 函數
    """
    def detector(text: str) -> list[tuple]:
        result = engine.process(text)
        # 假設 engine.process 返回有 phi_entities 屬性的物件
        if hasattr(result, 'phi_entities'):
            return [(e.text, e.phi_type) for e in result.phi_entities]
        elif hasattr(result, 'entities'):
            return [(e.text, e.type) for e in result.entities]
        else:
            return []

    return detector


def quick_evaluate(
    detector: PHIDetector,
    data_path: str | Path,
    match_type: str = "partial",
) -> dict:
    """
    快速評估
    
    Returns:
        {"precision": float, "recall": float, "f1": float}
    """
    evaluator = PHIEvaluator(detector=detector, match_type=match_type, verbose=False)
    report = evaluator.evaluate(data_path)

    return {
        "precision": report.metrics.overall.precision,
        "recall": report.metrics.overall.recall,
        "f1": report.metrics.overall.f1,
        "total_samples": report.metrics.total_samples,
    }
