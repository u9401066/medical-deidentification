#!/usr/bin/env python
"""
DSPy PHI Optimization Script
DSPy PHI 優化腳本

Uses DSPy to automatically optimize prompts for PHI detection.
Metrics include FULL Confusion Matrix:
- TP (True Positives): 正確檢測
- FP (False Positives): 過度檢測/誤報  
- FN (False Negatives): 漏檢
- Precision, Recall, F1

Also tracks:
- Detection Time (速度)
- Prompt Length (效率)

Usage:
    python scripts/dspy_phi_optimizer.py
    python scripts/dspy_phi_optimizer.py --model qwen2.5:3b
"""

import sys
import time
import json
import re
from pathlib import Path
from typing import List, Tuple, Optional
from dataclasses import dataclass, asdict, field

# Add project root
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# DSPy
import dspy
from dspy.teleprompt import BootstrapFewShot

# Data loading
import pandas as pd

print("=" * 70)
print("DSPy PHI Optimizer - Full Confusion Matrix Metrics")
print("=" * 70)


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class ConfusionMatrix:
    """Complete Confusion Matrix for PHI Detection"""
    true_positives: int = 0
    false_positives: int = 0  # Over-detection (誤報)
    false_negatives: int = 0  # Missed (漏檢)
    
    @property
    def precision(self) -> float:
        """Precision = TP / (TP + FP)"""
        total = self.true_positives + self.false_positives
        return self.true_positives / total if total > 0 else 0.0
    
    @property
    def recall(self) -> float:
        """Recall = TP / (TP + FN)"""
        total = self.true_positives + self.false_negatives
        return self.true_positives / total if total > 0 else 0.0
    
    @property
    def f1(self) -> float:
        """F1 = 2 * P * R / (P + R)"""
        p, r = self.precision, self.recall
        return 2 * p * r / (p + r) if (p + r) > 0 else 0.0
    
    @property
    def accuracy(self) -> float:
        """Overall accuracy considering all metrics"""
        # For PHI detection, we care most about not missing PHI (recall)
        # but also not over-detecting (precision)
        return self.f1


@dataclass 
class EvalMetrics:
    """Complete evaluation metrics"""
    confusion_matrix: ConfusionMatrix
    detection_time_ms: float = 0.0
    prompt_length: int = 0
    
    @property
    def efficiency_score(self) -> float:
        """
        Combined score: F1 * time_factor * prompt_factor
        
        - F1 accounts for 70%
        - Time factor: 15% (faster is better, baseline 1000ms)
        - Prompt factor: 15% (shorter is better, baseline 500 chars)
        """
        f1 = self.confusion_matrix.f1
        
        # Time factor: 1.0 if <= 1000ms, decreases for slower
        time_factor = min(1.0, 1000.0 / max(self.detection_time_ms, 1.0))
        
        # Prompt factor: 1.0 if <= 500 chars, decreases for longer  
        prompt_factor = min(1.0, 500.0 / max(self.prompt_length, 1.0))
        
        return f1 * (0.7 + 0.15 * time_factor + 0.15 * prompt_factor)


# =============================================================================
# DSPy Signature and Module
# =============================================================================

class PHIDetectionSignature(dspy.Signature):
    """
    Identify Protected Health Information (PHI) in medical text.
    識別醫療文本中的個人健康資訊 (PHI)。
    
    PHI includes:
    - NAME: Patient names, doctor names, family member names
    - DATE: Birth dates, admission/discharge dates, appointment dates  
    - AGE: Patient ages (only ages > 89 need special handling)
    - PHONE: Phone numbers, fax numbers
    - EMAIL: Email addresses
    - ID: Medical record numbers, SSN, insurance numbers
    - LOCATION: Street addresses, city names (smaller than state)
    - FACILITY: Hospital names, clinic names
    
    Return ONLY the PHI text found, one per line.
    Do NOT include explanations or categories.
    If no PHI found, return "NONE".
    """
    medical_text: str = dspy.InputField(desc="Medical text to analyze")
    phi_list: str = dspy.OutputField(desc="List of PHI found, one per line. Return 'NONE' if no PHI.")


class PHIDetector(dspy.Module):
    """DSPy Module for PHI Detection"""
    
    def __init__(self):
        super().__init__()
        self.detect = dspy.Predict(PHIDetectionSignature)
    
    def forward(self, medical_text: str) -> List[str]:
        """Detect PHI in text, return list of PHI strings"""
        result = self.detect(medical_text=medical_text)
        
        # Parse output
        output = result.phi_list.strip()
        if output.upper() == "NONE" or not output:
            return []
        
        # Split by newlines and clean
        phi_list = []
        for line in output.split('\n'):
            line = line.strip()
            # Remove common prefixes like "- ", "* ", "1. "
            line = re.sub(r'^[\-\*\d\.]+\s*', '', line)
            # Remove category labels like "NAME: "
            line = re.sub(r'^[A-Z_]+:\s*', '', line)
            if line and line.upper() != "NONE":
                phi_list.append(line)
        
        return phi_list


# =============================================================================
# Metric Function (Full Confusion Matrix)
# =============================================================================

def calculate_confusion_matrix(
    predicted: List[str],
    ground_truth: List[str],
    fuzzy_match: bool = True
) -> ConfusionMatrix:
    """
    Calculate full confusion matrix
    計算完整混淆矩陣
    
    Args:
        predicted: List of predicted PHI strings
        ground_truth: List of ground truth PHI strings
        fuzzy_match: Use fuzzy matching (substring match)
    """
    # Normalize texts
    pred_set = {p.lower().strip() for p in predicted if p.strip()}
    gt_set = {g.lower().strip() for g in ground_truth if g.strip()}
    
    # Match predictions to ground truth
    matched_gt = set()
    tp = 0
    
    for pred in pred_set:
        matched = False
        for gt in gt_set:
            if gt not in matched_gt:
                if fuzzy_match:
                    # Fuzzy: either contains the other
                    is_match = pred in gt or gt in pred or pred == gt
                else:
                    is_match = pred == gt
                
                if is_match:
                    tp += 1
                    matched_gt.add(gt)
                    matched = True
                    break
    
    fp = len(pred_set) - tp  # Over-detection
    fn = len(gt_set) - len(matched_gt)  # Missed
    
    return ConfusionMatrix(
        true_positives=tp,
        false_positives=fp,
        false_negatives=fn,
    )


def phi_metric(example, prediction, trace=None) -> float:
    """
    DSPy metric function using full Confusion Matrix
    使用完整混淆矩陣的 DSPy 指標函數
    
    This is called by DSPy optimizers to score predictions.
    Returns a score from 0.0 to 1.0.
    """
    # Get ground truth
    gt = example.ground_truth if hasattr(example, 'ground_truth') else []
    
    # Get predictions
    if isinstance(prediction, list):
        pred = prediction
    elif hasattr(prediction, 'phi_list'):
        # Parse from output
        output = prediction.phi_list.strip()
        if output.upper() == "NONE":
            pred = []
        else:
            pred = [line.strip() for line in output.split('\n') if line.strip()]
            pred = [re.sub(r'^[\-\*\d\.]+\s*', '', p) for p in pred]
            pred = [re.sub(r'^[A-Z_]+:\s*', '', p) for p in pred]
            pred = [p for p in pred if p and p.upper() != "NONE"]
    else:
        pred = []
    
    # Calculate confusion matrix
    cm = calculate_confusion_matrix(pred, gt)
    
    # Return F1 as the optimization target
    # DSPy will maximize this
    return cm.f1


# =============================================================================
# Data Loading
# =============================================================================

def load_tagged_data(file_path: str) -> List[dspy.Example]:
    """
    Load test data and create DSPy examples
    載入測試資料並創建 DSPy 範例
    """
    df = pd.read_excel(file_path)
    
    # PHI tag pattern: 【PHI:TYPE:ID】content【/PHI】
    tag_pattern = r'【PHI:(\w+):[\w-]+】([^【]+)【/PHI】'
    
    # Find text columns (handle newlines in column names)
    text_columns = []
    for col in df.columns:
        col_clean = col.replace('\n', ' ').strip()
        if any(x in col_clean for x in ['Summary', 'Contact', 'History', 'Treatment', 'Notes']):
            text_columns.append(col)
    
    print(f"Found text columns: {text_columns}")
    
    examples = []
    for _, row in df.iterrows():
        for col in text_columns:
            if col in row and pd.notna(row[col]):
                text = str(row[col])
                
                # Extract ground truth PHI
                matches = re.findall(tag_pattern, text)
                ground_truth = [content.strip() for _, content in matches]
                
                if ground_truth:  # Only include if has PHI
                    # Remove tags to get clean text
                    clean_text = re.sub(r'【PHI:\w+:[\w-]+】', '', text)
                    clean_text = re.sub(r'【/PHI】', '', clean_text)
                    
                    example = dspy.Example(
                        medical_text=clean_text.strip(),
                        ground_truth=ground_truth,
                    ).with_inputs("medical_text")
                    
                    examples.append(example)
    
    print(f"Loaded {len(examples)} examples with PHI")
    return examples


# =============================================================================
# Main Optimization
# =============================================================================

def evaluate_model(
    detector: PHIDetector,
    examples: List[dspy.Example],
    verbose: bool = True
) -> EvalMetrics:
    """
    Evaluate model on examples with full metrics
    使用完整指標評估模型
    """
    total_cm = ConfusionMatrix()
    total_time = 0.0
    
    for i, example in enumerate(examples):
        start = time.time()
        
        try:
            # Run detection
            predictions = detector(medical_text=example.medical_text)
            elapsed_ms = (time.time() - start) * 1000
            total_time += elapsed_ms
            
            # Calculate CM for this example
            cm = calculate_confusion_matrix(predictions, example.ground_truth)
            
            # Accumulate
            total_cm.true_positives += cm.true_positives
            total_cm.false_positives += cm.false_positives
            total_cm.false_negatives += cm.false_negatives
            
            if verbose:
                print(f"  Example {i+1}: TP={cm.true_positives}, FP={cm.false_positives}, FN={cm.false_negatives}, Time={elapsed_ms:.0f}ms")
                print(f"    Ground Truth: {example.ground_truth[:3]}...")
                print(f"    Predictions:  {predictions[:5]}...")
                
        except Exception as e:
            print(f"  Example {i+1}: ERROR - {e}")
            # Count all ground truth as missed
            total_cm.false_negatives += len(example.ground_truth)
    
    avg_time = total_time / len(examples) if examples else 0.0
    
    # Estimate prompt length from signature docstring
    prompt_length = len(PHIDetectionSignature.__doc__ or "")
    
    return EvalMetrics(
        confusion_matrix=total_cm,
        detection_time_ms=avg_time,
        prompt_length=prompt_length,
    )


def print_metrics(metrics: EvalMetrics, title: str = "Evaluation Results"):
    """Print metrics in a nice format"""
    cm = metrics.confusion_matrix
    
    print(f"\n{'='*60}")
    print(f"{title}")
    print(f"{'='*60}")
    
    print(f"\n📊 Confusion Matrix:")
    print(f"  ┌─────────────────────┬────────────┐")
    print(f"  │ True Positives (TP) │ {cm.true_positives:>10} │  ✓ 正確檢測")
    print(f"  ├─────────────────────┼────────────┤")
    print(f"  │ False Positives(FP) │ {cm.false_positives:>10} │  ⚠ 過度檢測/誤報")
    print(f"  ├─────────────────────┼────────────┤")
    print(f"  │ False Negatives(FN) │ {cm.false_negatives:>10} │  ❌ 漏檢")
    print(f"  └─────────────────────┴────────────┘")
    
    print(f"\n📈 Metrics:")
    print(f"  • Precision: {cm.precision:>7.1%}  (避免誤報)")
    print(f"  • Recall:    {cm.recall:>7.1%}  (避免漏檢)")
    print(f"  • F1 Score:  {cm.f1:>7.1%}  (綜合指標)")
    
    print(f"\n⚡ Performance:")
    print(f"  • Avg Time:     {metrics.detection_time_ms:>7.0f} ms")
    print(f"  • Prompt Length:{metrics.prompt_length:>7} chars")
    print(f"  • Efficiency:   {metrics.efficiency_score:>7.1%}")
    
    # Grade
    f1 = cm.f1
    if f1 >= 0.9:
        grade = "A (Excellent) ⭐⭐⭐"
    elif f1 >= 0.8:
        grade = "B (Good) ⭐⭐"
    elif f1 >= 0.7:
        grade = "C (Acceptable) ⭐"
    elif f1 >= 0.5:
        grade = "D (Poor)"
    else:
        grade = "F (Fail) ❌"
    
    print(f"\n🎯 Grade: {grade}")
    print(f"{'='*60}")


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=str, default="qwen2.5:1.5b", help="Ollama model")
    parser.add_argument("--test-file", type=str, default="data/test/test_phi_tagged_cases.xlsx")
    parser.add_argument("--max-examples", type=int, default=5)
    parser.add_argument("--optimize", action="store_true", help="Run DSPy optimization")
    parser.add_argument("--num-demos", type=int, default=2, help="Number of few-shot demos")
    args = parser.parse_args()
    
    # Configure DSPy with Ollama
    print(f"\n🔧 Configuring DSPy with Ollama model: {args.model}")
    
    lm = dspy.LM(
        model=f"ollama_chat/{args.model}",
        api_base="http://localhost:11434",
        temperature=0.1,
        max_tokens=512,
    )
    dspy.configure(lm=lm)
    print("✓ DSPy configured successfully!")
    
    # Load data
    test_file = project_root / args.test_file
    print(f"\n📂 Loading test data from: {test_file}")
    
    examples = load_tagged_data(str(test_file))
    if not examples:
        print("ERROR: No examples loaded!")
        return
    
    # Limit examples
    examples = examples[:args.max_examples]
    print(f"Using {len(examples)} examples for evaluation")
    
    # Create detector
    detector = PHIDetector()
    
    # Evaluate baseline
    print(f"\n🔍 Evaluating BASELINE (no optimization)...")
    baseline_metrics = evaluate_model(detector, examples)
    print_metrics(baseline_metrics, "BASELINE Results")
    
    # DSPy Optimization
    if args.optimize:
        print(f"\n🚀 Running DSPy Optimization...")
        print(f"   Method: BootstrapFewShot")
        print(f"   Demos: {args.num_demos}")
        
        # Split data
        if len(examples) > 3:
            trainset = examples[:-2]
            valset = examples[-2:]
        else:
            trainset = examples
            valset = examples
        
        # Optimize
        optimizer = BootstrapFewShot(
            metric=phi_metric,
            max_bootstrapped_demos=args.num_demos,
            max_labeled_demos=args.num_demos,
        )
        
        print(f"\n   Training on {len(trainset)} examples...")
        start_time = time.time()
        
        try:
            optimized_detector = optimizer.compile(
                detector,
                trainset=trainset,
            )
            
            opt_time = time.time() - start_time
            print(f"   ✓ Optimization completed in {opt_time:.1f}s")
            
            # Evaluate optimized
            print(f"\n🔍 Evaluating OPTIMIZED model...")
            optimized_metrics = evaluate_model(optimized_detector, valset)
            print_metrics(optimized_metrics, "OPTIMIZED Results")
            
            # Comparison
            print(f"\n📊 COMPARISON:")
            print(f"  {'Metric':<20} {'Baseline':>12} {'Optimized':>12} {'Change':>12}")
            print(f"  {'-'*56}")
            
            b_f1 = baseline_metrics.confusion_matrix.f1
            o_f1 = optimized_metrics.confusion_matrix.f1
            print(f"  {'F1 Score':<20} {b_f1:>11.1%} {o_f1:>11.1%} {(o_f1-b_f1):>+11.1%}")
            
            b_p = baseline_metrics.confusion_matrix.precision
            o_p = optimized_metrics.confusion_matrix.precision
            print(f"  {'Precision':<20} {b_p:>11.1%} {o_p:>11.1%} {(o_p-b_p):>+11.1%}")
            
            b_r = baseline_metrics.confusion_matrix.recall
            o_r = optimized_metrics.confusion_matrix.recall
            print(f"  {'Recall':<20} {b_r:>11.1%} {o_r:>11.1%} {(o_r-b_r):>+11.1%}")
            
            b_t = baseline_metrics.detection_time_ms
            o_t = optimized_metrics.detection_time_ms
            print(f"  {'Avg Time (ms)':<20} {b_t:>11.0f} {o_t:>11.0f} {(o_t-b_t):>+11.0f}")
            
        except Exception as e:
            print(f"   ❌ Optimization failed: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n✅ Done!")


if __name__ == "__main__":
    main()
