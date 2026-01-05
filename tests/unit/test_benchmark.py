"""
Benchmark Module Tests | 評估模組測試
"""

import json

# Import benchmark module
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.benchmark import (
    # Data loader
    BenchmarkSample,
    # Metrics
    ConfusionMatrix,
    EvaluationMetrics,
    EvaluationReport,
    JSONLoader,
    PHIAnnotation,
    # Evaluator
    PHIEvaluator,
    PresidioEvaluatorLoader,
    calculate_f1,
    calculate_metrics,
    calculate_precision,
    calculate_recall,
    match_entities,
    normalize_phi_type,
    quick_evaluate,
)


class TestConfusionMatrix:
    """測試混淆矩陣"""

    def test_precision_perfect(self):
        cm = ConfusionMatrix(true_positives=10, false_positives=0, false_negatives=0)
        assert cm.precision == 1.0

    def test_recall_perfect(self):
        cm = ConfusionMatrix(true_positives=10, false_positives=0, false_negatives=0)
        assert cm.recall == 1.0

    def test_f1_perfect(self):
        cm = ConfusionMatrix(true_positives=10, false_positives=0, false_negatives=0)
        assert cm.f1 == 1.0

    def test_precision_with_fp(self):
        cm = ConfusionMatrix(true_positives=8, false_positives=2, false_negatives=0)
        assert cm.precision == 0.8

    def test_recall_with_fn(self):
        cm = ConfusionMatrix(true_positives=8, false_positives=0, false_negatives=2)
        assert cm.recall == 0.8

    def test_zero_division(self):
        cm = ConfusionMatrix(true_positives=0, false_positives=0, false_negatives=0)
        assert cm.precision == 0.0
        assert cm.recall == 0.0
        assert cm.f1 == 0.0

    def test_add(self):
        cm1 = ConfusionMatrix(true_positives=5, false_positives=2, false_negatives=1)
        cm2 = ConfusionMatrix(true_positives=3, false_positives=1, false_negatives=2)
        combined = cm1 + cm2
        assert combined.true_positives == 8
        assert combined.false_positives == 3
        assert combined.false_negatives == 3


class TestMetricFunctions:
    """測試指標計算函數"""

    def test_calculate_precision(self):
        assert calculate_precision(8, 2) == 0.8
        assert calculate_precision(0, 0) == 0.0

    def test_calculate_recall(self):
        assert calculate_recall(8, 2) == 0.8
        assert calculate_recall(0, 0) == 0.0

    def test_calculate_f1(self):
        assert calculate_f1(0.8, 0.8) == pytest.approx(0.8)
        assert calculate_f1(1.0, 0.5) == pytest.approx(0.6667, rel=0.01)
        assert calculate_f1(0.0, 0.0) == 0.0


class TestNormalizePHIType:
    """測試 PHI 類型標準化"""

    def test_name_variations(self):
        assert normalize_phi_type("NAME") == "NAME"
        assert normalize_phi_type("PATIENT") == "NAME"
        assert normalize_phi_type("DOCTOR") == "NAME"
        assert normalize_phi_type("PERSON") == "NAME"

    def test_date_variations(self):
        assert normalize_phi_type("DATE") == "DATE"
        assert normalize_phi_type("DOB") == "DATE"
        assert normalize_phi_type("BIRTHDATE") == "DATE"

    def test_case_insensitive(self):
        assert normalize_phi_type("name") == "NAME"
        assert normalize_phi_type("Name") == "NAME"

    def test_unknown_type(self):
        assert normalize_phi_type("UNKNOWN_TYPE") == "UNKNOWN_TYPE"


class TestMatchEntities:
    """測試實體匹配"""

    def test_exact_match(self):
        gt = [("John Doe", "NAME"), ("2024-01-15", "DATE")]
        pred = [("John Doe", "NAME"), ("2024-01-15", "DATE")]

        tp, fp, fn = match_entities(gt, pred, "exact")

        assert len(tp) == 2
        assert len(fp) == 0
        assert len(fn) == 0

    def test_partial_match(self):
        gt = [("John Doe", "NAME")]
        pred = [("John", "NAME")]  # 部分匹配

        tp, fp, fn = match_entities(gt, pred, "partial")

        assert len(tp) == 1
        assert len(fp) == 0
        assert len(fn) == 0

    def test_false_positive(self):
        gt = [("John Doe", "NAME")]
        pred = [("John Doe", "NAME"), ("Extra", "NAME")]

        tp, fp, fn = match_entities(gt, pred, "exact")

        assert len(tp) == 1
        assert len(fp) == 1
        assert len(fn) == 0

    def test_false_negative(self):
        gt = [("John Doe", "NAME"), ("Jane Doe", "NAME")]
        pred = [("John Doe", "NAME")]

        tp, fp, fn = match_entities(gt, pred, "exact")

        assert len(tp) == 1
        assert len(fp) == 0
        assert len(fn) == 1


class TestCalculateMetrics:
    """測試指標計算"""

    def test_perfect_detection(self):
        gt = [("John", "NAME"), ("2024", "DATE")]
        pred = [("John", "NAME"), ("2024", "DATE")]

        cm = calculate_metrics(gt, pred, "exact")

        assert cm.precision == 1.0
        assert cm.recall == 1.0
        assert cm.f1 == 1.0

    def test_partial_detection(self):
        gt = [("John", "NAME"), ("Jane", "NAME")]
        pred = [("John", "NAME")]

        cm = calculate_metrics(gt, pred, "exact")

        assert cm.precision == 1.0  # 1/1
        assert cm.recall == 0.5  # 1/2


class TestBenchmarkSample:
    """測試 BenchmarkSample"""

    def test_ground_truth(self):
        sample = BenchmarkSample(
            id="test",
            text="Hello John",
            annotations=[
                PHIAnnotation(text="John", phi_type="NAME"),
            ]
        )

        gt = sample.ground_truth
        assert gt == [("John", "NAME")]

    def test_to_dict(self):
        sample = BenchmarkSample(
            id="test",
            text="Hello",
            annotations=[PHIAnnotation(text="John", phi_type="NAME")],
        )

        d = sample.to_dict()
        assert d["id"] == "test"
        assert d["text"] == "Hello"
        assert len(d["annotations"]) == 1


class TestJSONLoader:
    """測試 JSON 載入器"""

    def test_load_jsonl(self, tmp_path):
        # 建立測試檔案
        data_file = tmp_path / "test.jsonl"
        with open(data_file, "w") as f:
            f.write('{"id": "1", "text": "Hello John", "annotations": [{"text": "John", "phi_type": "NAME"}]}\n')
            f.write('{"id": "2", "text": "Date: 2024", "annotations": [{"text": "2024", "phi_type": "DATE"}]}\n')

        loader = JSONLoader()
        samples = list(loader.load(data_file))

        assert len(samples) == 2
        assert samples[0].id == "1"
        assert samples[0].annotations[0].text == "John"

    def test_load_json_array(self, tmp_path):
        data_file = tmp_path / "test.json"
        with open(data_file, "w") as f:
            json.dump([
                {"id": "1", "text": "Hello", "annotations": []},
                {"id": "2", "text": "World", "annotations": []},
            ], f)

        loader = JSONLoader()
        samples = list(loader.load(data_file))

        assert len(samples) == 2


class TestPresidioLoader:
    """測試 Presidio Evaluator 格式載入器"""

    def test_load(self, tmp_path):
        data_file = tmp_path / "presidio.jsonl"
        with open(data_file, "w") as f:
            f.write(json.dumps({
                "template_id": "t1",
                "full_text": "My name is John Doe",
                "spans": [
                    {"entity_type": "PERSON", "entity_value": "John Doe", "start_position": 11, "end_position": 19}
                ]
            }) + "\n")

        loader = PresidioEvaluatorLoader()
        samples = list(loader.load(data_file))

        assert len(samples) == 1
        assert samples[0].text == "My name is John Doe"
        assert samples[0].annotations[0].text == "John Doe"
        assert samples[0].annotations[0].phi_type == "PERSON"


class TestPHIEvaluator:
    """測試 PHI 評估器"""

    def test_evaluate_perfect(self, tmp_path):
        # 建立測試資料
        data_file = tmp_path / "test.jsonl"
        with open(data_file, "w") as f:
            f.write('{"id": "1", "text": "Hello John", "annotations": [{"text": "John", "phi_type": "NAME"}]}\n')

        # 完美 detector
        def perfect_detector(text):
            return [("John", "NAME")]

        evaluator = PHIEvaluator(detector=perfect_detector, verbose=False)
        report = evaluator.evaluate(data_file)

        assert report.metrics.overall.precision == 1.0
        assert report.metrics.overall.recall == 1.0
        assert report.metrics.overall.f1 == 1.0

    def test_evaluate_no_detector(self, tmp_path):
        data_file = tmp_path / "test.jsonl"
        with open(data_file, "w") as f:
            f.write('{"id": "1", "text": "Hello", "annotations": []}\n')

        evaluator = PHIEvaluator(verbose=False)

        with pytest.raises(ValueError, match="No detector set"):
            evaluator.evaluate(data_file)

    def test_quick_evaluate(self, tmp_path):
        data_file = tmp_path / "test.jsonl"
        with open(data_file, "w") as f:
            f.write('{"id": "1", "text": "Hello John", "annotations": [{"text": "John", "phi_type": "NAME"}]}\n')

        def detector(text):
            return [("John", "NAME")]

        result = quick_evaluate(detector, data_file)

        assert result["precision"] == 1.0
        assert result["recall"] == 1.0
        assert result["f1"] == 1.0


class TestEvaluationReport:
    """測試評估報告"""

    def test_save_and_load(self, tmp_path):
        metrics = EvaluationMetrics(
            overall=ConfusionMatrix(true_positives=10, false_positives=2, false_negatives=1),
            total_samples=5,
            total_time=10.0,
        )

        report = EvaluationReport(
            metrics=metrics,
            results=[],
            config={"test": True},
        )

        save_path = tmp_path / "report.json"
        report.save(save_path)

        assert save_path.exists()

        with open(save_path) as f:
            data = json.load(f)

        assert data["metrics"]["overall"]["true_positives"] == 10
        assert data["config"]["test"] == True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
