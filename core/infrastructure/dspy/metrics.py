"""
DSPy Metrics for PHI Identification
DSPy PHI 識別指標

Defines evaluation metrics for automatic prompt optimization:
- Precision: Avoid false positives (過度檢測)
- Recall: Avoid false negatives (遺漏檢測)
- F1 Score: Balance between precision and recall

定義用於自動 prompt 優化的評估指標：
- 精確率: 避免誤報（過度檢測）
- 召回率: 避免漏報（遺漏檢測）
- F1 分數: 精確率和召回率的平衡
"""

import re
from dataclasses import dataclass

from loguru import logger

from .phi_module import PHIEntity


@dataclass
class EvaluationResult:
    """
    PHI evaluation result
    PHI 評估結果
    """
    # Core metrics (required)
    true_positives: int
    false_positives: int
    false_negatives: int
    precision: float
    recall: float
    f1_score: float

    # Details (required)
    matched_entities: list[tuple[str, str]]  # (predicted, ground_truth)
    over_detected: list[str]  # False positives
    missed: list[str]  # False negatives

    # Performance metrics (optional, with defaults)
    detection_time_ms: float = 0.0  # Detection time in milliseconds (越短越好)
    prompt_length: int = 0  # Prompt character length (越短越好)
    tokens_per_second: float = 0.0  # Processing speed

    @property
    def efficiency_score(self) -> float:
        """
        Combined efficiency score considering F1, time, and prompt length
        綜合效率分數，考慮 F1、時間和 prompt 長度
        
        Formula: F1 * time_factor * prompt_factor
        - time_factor: 1.0 if < 1s, decreases for slower
        - prompt_factor: 1.0 if < 500 chars, decreases for longer
        """
        # Time factor: penalize if > 1000ms
        time_factor = min(1.0, 1000.0 / max(self.detection_time_ms, 1.0))

        # Prompt factor: penalize if > 500 chars
        prompt_factor = min(1.0, 500.0 / max(self.prompt_length, 1.0))

        return self.f1_score * (0.7 + 0.15 * time_factor + 0.15 * prompt_factor)


def normalize_text(text: str) -> str:
    """
    Normalize text for comparison
    標準化文本以進行比較
    """
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text.strip())
    # Lowercase for comparison
    return text.lower()


def extract_phi_from_tags(text: str) -> list[tuple[str, str]]:
    """
    Extract PHI from tagged text format: 【PHI:TYPE:ID】content【/PHI】
    從標記文本格式中提取 PHI
    
    Args:
        text: Tagged text
        
    Returns:
        List of (content, phi_type) tuples
    """
    pattern = r'【PHI:(\w+):[\w-]+】([^【]+)【/PHI】'
    matches = re.findall(pattern, text)
    return [(content.strip(), phi_type) for phi_type, content in matches]


def phi_precision(
    predicted: list[PHIEntity],
    ground_truth: list[tuple[str, str]],
    fuzzy_match: bool = True,
) -> float:
    """
    Calculate precision: TP / (TP + FP)
    計算精確率：正確預測 / 總預測數
    
    Precision measures how many predicted PHI are actually correct.
    Higher precision = less false positives (fewer over-detections)
    
    精確率衡量預測的 PHI 中有多少是正確的。
    高精確率 = 較少誤報（較少過度檢測）
    
    Args:
        predicted: List of predicted PHI entities
        ground_truth: List of (content, phi_type) ground truth
        fuzzy_match: Use fuzzy matching for text comparison
        
    Returns:
        Precision score (0.0 - 1.0)
    """
    if not predicted:
        return 1.0 if not ground_truth else 0.0

    # Create set of ground truth texts
    gt_texts = {normalize_text(text) for text, _ in ground_truth}

    # Count true positives
    tp = 0
    for entity in predicted:
        pred_text = normalize_text(entity.text)

        if fuzzy_match:
            # Check if predicted text is contained in any ground truth
            matched = any(
                pred_text in gt or gt in pred_text
                for gt in gt_texts
            )
        else:
            matched = pred_text in gt_texts

        if matched:
            tp += 1

    return tp / len(predicted)


def phi_recall(
    predicted: list[PHIEntity],
    ground_truth: list[tuple[str, str]],
    fuzzy_match: bool = True,
) -> float:
    """
    Calculate recall: TP / (TP + FN)
    計算召回率：正確預測 / 實際 PHI 總數
    
    Recall measures how many actual PHI were detected.
    Higher recall = less false negatives (fewer missed PHI)
    
    召回率衡量實際 PHI 中有多少被檢測到。
    高召回率 = 較少漏報（較少遺漏 PHI）
    
    Args:
        predicted: List of predicted PHI entities
        ground_truth: List of (content, phi_type) ground truth
        fuzzy_match: Use fuzzy matching for text comparison
        
    Returns:
        Recall score (0.0 - 1.0)
    """
    if not ground_truth:
        return 1.0

    # Create set of predicted texts
    pred_texts = {normalize_text(e.text) for e in predicted}

    # Count true positives (from ground truth perspective)
    tp = 0
    for text, _ in ground_truth:
        gt_text = normalize_text(text)

        if fuzzy_match:
            # Check if any predicted text matches this ground truth
            matched = any(
                gt_text in pred or pred in gt_text
                for pred in pred_texts
            )
        else:
            matched = gt_text in pred_texts

        if matched:
            tp += 1

    return tp / len(ground_truth)


def phi_f1_score(
    predicted: list[PHIEntity],
    ground_truth: list[tuple[str, str]],
    fuzzy_match: bool = True,
) -> float:
    """
    Calculate F1 score: 2 * (precision * recall) / (precision + recall)
    計算 F1 分數
    
    F1 is the harmonic mean of precision and recall.
    Use this as the main optimization metric for DSPy.
    
    F1 是精確率和召回率的調和平均值。
    將此作為 DSPy 的主要優化指標。
    
    Args:
        predicted: List of predicted PHI entities
        ground_truth: List of (content, phi_type) ground truth
        fuzzy_match: Use fuzzy matching
        
    Returns:
        F1 score (0.0 - 1.0)
    """
    p = phi_precision(predicted, ground_truth, fuzzy_match)
    r = phi_recall(predicted, ground_truth, fuzzy_match)

    if p + r == 0:
        return 0.0

    return 2 * (p * r) / (p + r)


class PHIEvaluator:
    """
    Comprehensive PHI evaluator for DSPy optimization
    用於 DSPy 優化的綜合 PHI 評估器
    
    This evaluator provides detailed metrics and can be used
    as a DSPy metric function for automatic optimization.
    
    這個評估器提供詳細指標，可用作 DSPy 的指標函數進行自動優化。
    
    Usage:
        evaluator = PHIEvaluator()
        
        # For DSPy optimization
        optimized = optimizer.compile(
            module, 
            trainset=trainset,
            metric=evaluator.dspy_metric
        )
        
        # For detailed evaluation
        result = evaluator.evaluate(predicted, ground_truth)
        print(f"F1: {result.f1_score:.2%}")
    """

    def __init__(
        self,
        fuzzy_match: bool = True,
        weight_precision: float = 1.0,
        weight_recall: float = 1.0,
        optimize_efficiency: bool = True,
        max_time_ms: float = 2000.0,
        max_prompt_length: int = 1000,
    ):
        """
        Initialize evaluator
        
        Args:
            fuzzy_match: Use fuzzy text matching
            weight_precision: Weight for precision in combined score
            weight_recall: Weight for recall in combined score
            optimize_efficiency: Include time/prompt length in score
            max_time_ms: Maximum acceptable detection time (ms)
            max_prompt_length: Maximum acceptable prompt length (chars)
        """
        self.fuzzy_match = fuzzy_match
        self.weight_precision = weight_precision
        self.weight_recall = weight_recall
        self.optimize_efficiency = optimize_efficiency
        self.max_time_ms = max_time_ms
        self.max_prompt_length = max_prompt_length

    def evaluate(
        self,
        predicted: list[PHIEntity],
        ground_truth: list[tuple[str, str]],
    ) -> EvaluationResult:
        """
        Comprehensive evaluation with detailed results
        詳細結果的綜合評估
        
        Args:
            predicted: Predicted PHI entities
            ground_truth: Ground truth (content, type) pairs
            
        Returns:
            EvaluationResult with all metrics and details
        """
        # Normalize texts
        pred_texts = {normalize_text(e.text): e for e in predicted}
        gt_texts = {normalize_text(text): phi_type for text, phi_type in ground_truth}

        # Calculate matches
        matched = []
        over_detected = []
        missed = []

        # Check predicted against ground truth
        matched_gt = set()
        for pred_norm, entity in pred_texts.items():
            found_match = False
            for gt_norm, gt_type in gt_texts.items():
                if self.fuzzy_match:
                    is_match = pred_norm in gt_norm or gt_norm in pred_norm
                else:
                    is_match = pred_norm == gt_norm

                if is_match and gt_norm not in matched_gt:
                    matched.append((entity.text, next(
                        text for text, _ in ground_truth
                        if normalize_text(text) == gt_norm
                    )))
                    matched_gt.add(gt_norm)
                    found_match = True
                    break

            if not found_match:
                over_detected.append(entity.text)

        # Find missed ground truth
        for text, phi_type in ground_truth:
            if normalize_text(text) not in matched_gt:
                missed.append(text)

        # Calculate metrics
        tp = len(matched)
        fp = len(over_detected)
        fn = len(missed)

        precision = tp / (tp + fp) if (tp + fp) > 0 else (1.0 if fn == 0 else 0.0)
        recall = tp / (tp + fn) if (tp + fn) > 0 else 1.0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

        return EvaluationResult(
            true_positives=tp,
            false_positives=fp,
            false_negatives=fn,
            precision=precision,
            recall=recall,
            f1_score=f1,
            matched_entities=matched,
            over_detected=over_detected,
            missed=missed,
        )

    def dspy_metric(
        self,
        example,
        prediction,
        trace=None,
    ) -> float:
        """
        DSPy-compatible metric function for optimization
        用於優化的 DSPy 兼容指標函數
        
        This function is called by DSPy optimizers to evaluate
        the quality of predictions. Includes:
        - F1 Score (accuracy)
        - Detection time (speed)
        - Prompt length (efficiency)
        
        此函數由 DSPy 優化器調用以評估預測質量。包括：
        - F1 分數（準確度）
        - 檢測時間（速度）
        - Prompt 長度（效率）
        
        Args:
            example: DSPy Example with ground truth
            prediction: Module prediction output
            trace: Optional trace (may contain timing info)
            
        Returns:
            Score (0.0 - 1.0) where higher is better
        """
        # Extract ground truth from example
        if hasattr(example, 'ground_truth'):
            ground_truth = example.ground_truth
        elif hasattr(example, 'phi_entities'):
            # Parse from tagged text
            ground_truth = extract_phi_from_tags(example.phi_entities)
        else:
            logger.warning("No ground truth in example")
            return 0.0

        # Extract predicted entities
        if isinstance(prediction, list):
            predicted = prediction
        elif hasattr(prediction, 'phi_entities'):
            # Parse string output using standalone function
            from .phi_module import parse_phi_entities
            predicted = parse_phi_entities(
                prediction.phi_entities,
                example.medical_text if hasattr(example, 'medical_text') else ""
            )
        else:
            logger.warning(f"Cannot extract predicted entities from: {type(prediction)}")
            return 0.0
            return 0.0

        # Calculate weighted F1
        result = self.evaluate(predicted, ground_truth)

        # Extract timing and prompt info from trace if available
        detection_time_ms = 0.0
        prompt_length = 0

        if trace:
            # DSPy trace contains call information
            for step in trace:
                if hasattr(step, 'elapsed_time'):
                    detection_time_ms += step.elapsed_time * 1000
                if hasattr(step, 'prompt'):
                    prompt_length += len(str(step.prompt))

        # Update result with timing info
        result.detection_time_ms = detection_time_ms
        result.prompt_length = prompt_length

        # Calculate final score with efficiency factors
        if self.optimize_efficiency:
            return result.efficiency_score

        # Weighted combination (default: standard F1)
        if self.weight_precision == self.weight_recall:
            return result.f1_score

        # Custom weighted score
        total_weight = self.weight_precision + self.weight_recall
        weighted_score = (
            self.weight_precision * result.precision +
            self.weight_recall * result.recall
        ) / total_weight

        return weighted_score

    def print_report(self, result: EvaluationResult) -> None:
        """
        Print detailed evaluation report
        打印詳細評估報告
        """
        print("\n" + "=" * 60)
        print("PHI Detection Evaluation Report")
        print("=" * 60)

        print("\n📊 Accuracy Metrics:")
        print(f"  • Precision: {result.precision:.2%} (over-detection control)")
        print(f"  • Recall:    {result.recall:.2%} (detection coverage)")
        print(f"  • F1 Score:  {result.f1_score:.2%} (overall accuracy)")

        print("\n⚡ Performance Metrics:")
        print(f"  • Detection Time: {result.detection_time_ms:.1f} ms", end="")
        if result.detection_time_ms > 0:
            if result.detection_time_ms < 1000:
                print(" ✅ Fast")
            elif result.detection_time_ms < 2000:
                print(" ⚠️ Acceptable")
            else:
                print(" ❌ Slow")
        else:
            print()

        print(f"  • Prompt Length:  {result.prompt_length} chars", end="")
        if result.prompt_length > 0:
            if result.prompt_length < 500:
                print(" ✅ Concise")
            elif result.prompt_length < 1000:
                print(" ⚠️ Acceptable")
            else:
                print(" ❌ Too Long")
        else:
            print()

        if result.tokens_per_second > 0:
            print(f"  • Speed:          {result.tokens_per_second:.1f} tokens/sec")

        print(f"\n🎯 Efficiency Score: {result.efficiency_score:.2%}")
        print("   (Combines F1 + Time + Prompt Length)")

        print("\n📈 Counts:")
        print(f"  • True Positives:  {result.true_positives}")
        print(f"  • False Positives: {result.false_positives} (over-detected)")
        print(f"  • False Negatives: {result.false_negatives} (missed)")

        if result.over_detected:
            print("\n⚠️  Over-detected (False Positives):")
            for text in result.over_detected[:10]:
                print(f"    - '{text}'")
            if len(result.over_detected) > 10:
                print(f"    ... and {len(result.over_detected) - 10} more")

        if result.missed:
            print("\n❌ Missed (False Negatives):")
            for text in result.missed[:10]:
                print(f"    - '{text}'")
            if len(result.missed) > 10:
                print(f"    ... and {len(result.missed) - 10} more")

        print("\n" + "=" * 60)
