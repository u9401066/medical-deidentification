#!/usr/bin/env python
"""
PHI Model Comparison with DSPy Optimization
PHI 模型比較與 DSPy 優化

Compare different models on PHI detection task:
1. MiniMind (104M) - Baseline (too small)
2. Qwen2.5:1.5b (1.5B) - Larger but still fast
3. Qwen2.5:1.5b + DSPy - Optimized with automatic prompt tuning

Metrics:
- F1 Score (accuracy)
- Detection Time (speed)
- Prompt Length (efficiency)
- Efficiency Score (combined)

Usage:
    python scripts/compare_phi_models.py
    python scripts/compare_phi_models.py --optimize  # With DSPy optimization
"""

import sys
import time
import json
import argparse
from pathlib import Path
from typing import List, Tuple, Dict, Any
from dataclasses import dataclass, asdict
import re

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Third party
import pandas as pd
from loguru import logger

# Configure logging
logger.remove()
logger.add(sys.stderr, level="INFO", format="<green>{time:HH:mm:ss}</green> | <level>{message}</level>")


@dataclass
class ModelResult:
    """Single model evaluation result"""
    model_name: str
    total_phi: int
    detected_phi: int
    true_positives: int
    false_positives: int
    false_negatives: int
    precision: float
    recall: float
    f1_score: float
    avg_time_ms: float
    prompt_length: int
    efficiency_score: float
    grade: str


def load_test_data(file_path: str) -> List[Tuple[str, List[Tuple[str, str]]]]:
    """
    Load test data from Excel file with PHI tags
    從帶有 PHI 標籤的 Excel 文件加載測試數據
    
    Returns:
        List of (clean_text, ground_truth_list)
    """
    df = pd.read_excel(file_path)
    test_cases = []
    
    # PHI tag pattern: 【PHI:TYPE:ID】content【/PHI】
    tag_pattern = r'【PHI:(\w+):[\w-]+】([^【]+)【/PHI】'
    
    # Find text columns (contain "PHI" or have tagged content)
    text_columns = []
    for col in df.columns:
        if 'PHI' in col or 'Summary' in col or 'Contact' in col or 'History' in col or 'Notes' in col:
            # Check if column has tagged content
            for val in df[col].dropna():
                if '【PHI:' in str(val):
                    text_columns.append(col)
                    break
    
    logger.info(f"Found text columns: {text_columns}")
    
    for _, row in df.iterrows():
        for col in text_columns:
            if col in row and pd.notna(row[col]):
                text = str(row[col])
                
                # Extract ground truth PHI
                matches = re.findall(tag_pattern, text)
                ground_truth = [(content.strip(), phi_type) for phi_type, content in matches]
                
                if ground_truth:  # Only include if has PHI
                    # Remove tags to get clean text
                    clean_text = re.sub(r'【PHI:\w+:[\w-]+】', '', text)
                    clean_text = re.sub(r'【/PHI】', '', clean_text)
                    
                    test_cases.append((clean_text.strip(), ground_truth))
    
    logger.info(f"Loaded {len(test_cases)} test cases from {file_path}")
    return test_cases


def evaluate_with_ollama(
    model_name: str,
    test_cases: List[Tuple[str, List[Tuple[str, str]]]],
    max_cases: int = 10,
) -> ModelResult:
    """
    Evaluate a model using Ollama directly
    使用 Ollama 直接評估模型
    """
    from langchain_ollama import ChatOllama
    
    logger.info(f"\n{'='*60}")
    logger.info(f"Evaluating model: {model_name}")
    logger.info(f"{'='*60}")
    
    # Initialize model
    llm = ChatOllama(
        model=model_name,
        temperature=0.1,
        num_predict=1024,
    )
    
    # Simple prompt for PHI detection
    prompt_template = """Identify all Protected Health Information (PHI) in this medical text.

PHI Types to find:
- NAME: Patient/doctor names
- DATE: Birth dates, admission dates
- AGE: Ages (only >89 needs special handling)
- PHONE: Phone numbers
- EMAIL: Email addresses
- ID: Medical record numbers, SSN
- LOCATION: Addresses, cities
- FACILITY: Hospital/clinic names

Medical Text:
{text}

Return ONLY a JSON array of found PHI:
[{{"text": "...", "phi_type": "NAME|DATE|AGE|PHONE|EMAIL|ID|LOCATION|FACILITY"}}]

If no PHI found, return: []"""
    
    prompt_length = len(prompt_template)
    
    # Evaluate
    all_predictions = []
    all_ground_truth = []
    total_time_ms = 0
    
    for i, (text, ground_truth) in enumerate(test_cases[:max_cases]):
        logger.info(f"  Case {i+1}/{min(len(test_cases), max_cases)}...")
        
        prompt = prompt_template.format(text=text[:1000])  # Limit text length
        
        start_time = time.time()
        try:
            response = llm.invoke(prompt)
            elapsed_ms = (time.time() - start_time) * 1000
            total_time_ms += elapsed_ms
            
            # Parse response
            content = response.content
            predictions = parse_phi_response(content, text)
            
            all_predictions.extend(predictions)
            all_ground_truth.extend(ground_truth)
            
            logger.info(f"    Found {len(predictions)} PHI, expected {len(ground_truth)}, time: {elapsed_ms:.0f}ms")
            
        except Exception as e:
            logger.error(f"    Error: {e}")
            all_ground_truth.extend(ground_truth)
    
    # Calculate metrics
    result = calculate_metrics(
        model_name=model_name,
        predictions=all_predictions,
        ground_truth=all_ground_truth,
        avg_time_ms=total_time_ms / max_cases if max_cases > 0 else 0,
        prompt_length=prompt_length,
    )
    
    return result


def parse_phi_response(response: str, original_text: str) -> List[Tuple[str, str]]:
    """
    Parse LLM response to extract PHI predictions
    解析 LLM 響應以提取 PHI 預測
    """
    predictions = []
    
    # Try to find JSON array
    json_match = re.search(r'\[.*?\]', response, re.DOTALL)
    if not json_match:
        return predictions
    
    try:
        items = json.loads(json_match.group())
        if not isinstance(items, list):
            items = [items]
        
        for item in items:
            if isinstance(item, dict):
                text = item.get('text', item.get('entity_text', ''))
                phi_type = item.get('phi_type', item.get('type', 'UNKNOWN'))
                if text and text in original_text:
                    predictions.append((text, phi_type))
    except json.JSONDecodeError:
        pass
    
    return predictions


def calculate_metrics(
    model_name: str,
    predictions: List[Tuple[str, str]],
    ground_truth: List[Tuple[str, str]],
    avg_time_ms: float,
    prompt_length: int,
) -> ModelResult:
    """
    Calculate evaluation metrics
    計算評估指標
    """
    # Normalize for comparison
    pred_texts = {text.lower().strip() for text, _ in predictions}
    gt_texts = {text.lower().strip() for text, _ in ground_truth}
    
    # Calculate TP, FP, FN with fuzzy matching
    true_positives = 0
    matched_gt = set()
    
    for pred in pred_texts:
        for gt in gt_texts:
            if gt not in matched_gt:
                # Fuzzy match: either contains the other
                if pred in gt or gt in pred or pred == gt:
                    true_positives += 1
                    matched_gt.add(gt)
                    break
    
    false_positives = len(pred_texts) - true_positives
    false_negatives = len(gt_texts) - true_positives
    
    # Metrics
    precision = true_positives / len(pred_texts) if pred_texts else (1.0 if not gt_texts else 0.0)
    recall = true_positives / len(gt_texts) if gt_texts else 1.0
    f1_score = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    
    # Efficiency score
    time_factor = min(1.0, 1000.0 / max(avg_time_ms, 1.0))
    prompt_factor = min(1.0, 500.0 / max(prompt_length, 1.0))
    efficiency_score = f1_score * (0.7 + 0.15 * time_factor + 0.15 * prompt_factor)
    
    # Grade
    if f1_score >= 0.9:
        grade = "A (Excellent)"
    elif f1_score >= 0.8:
        grade = "B (Good)"
    elif f1_score >= 0.7:
        grade = "C (Acceptable)"
    elif f1_score >= 0.5:
        grade = "D (Poor)"
    else:
        grade = "F (Fail)"
    
    return ModelResult(
        model_name=model_name,
        total_phi=len(gt_texts),
        detected_phi=len(pred_texts),
        true_positives=true_positives,
        false_positives=false_positives,
        false_negatives=false_negatives,
        precision=precision,
        recall=recall,
        f1_score=f1_score,
        avg_time_ms=avg_time_ms,
        prompt_length=prompt_length,
        efficiency_score=efficiency_score,
        grade=grade,
    )


def print_comparison_table(results: List[ModelResult]) -> None:
    """
    Print comparison table
    打印比較表格
    """
    print("\n" + "=" * 100)
    print("PHI Detection Model Comparison")
    print("=" * 100)
    
    # Header
    print(f"\n{'Model':<25} {'F1':>8} {'Prec':>8} {'Recall':>8} {'Time(ms)':>10} {'Prompt':>8} {'Eff':>8} {'Grade':<15}")
    print("-" * 100)
    
    for r in results:
        print(f"{r.model_name:<25} {r.f1_score:>7.1%} {r.precision:>7.1%} {r.recall:>7.1%} {r.avg_time_ms:>9.0f} {r.prompt_length:>7} {r.efficiency_score:>7.1%} {r.grade:<15}")
    
    print("-" * 100)
    
    # Details
    print("\n📊 Detailed Results:")
    for r in results:
        print(f"\n  {r.model_name}:")
        print(f"    • Ground Truth PHI: {r.total_phi}")
        print(f"    • Detected PHI:     {r.detected_phi}")
        print(f"    • True Positives:   {r.true_positives}")
        print(f"    • False Positives:  {r.false_positives} (over-detection)")
        print(f"    • False Negatives:  {r.false_negatives} (missed)")
    
    # Recommendation
    print("\n" + "=" * 100)
    print("📌 Recommendation:")
    
    best = max(results, key=lambda r: r.efficiency_score)
    print(f"   Best overall: {best.model_name} (Efficiency: {best.efficiency_score:.1%})")
    
    fastest = min(results, key=lambda r: r.avg_time_ms if r.avg_time_ms > 0 else float('inf'))
    print(f"   Fastest:      {fastest.model_name} ({fastest.avg_time_ms:.0f}ms)")
    
    most_accurate = max(results, key=lambda r: r.f1_score)
    print(f"   Most accurate: {most_accurate.model_name} (F1: {most_accurate.f1_score:.1%})")
    
    print("=" * 100)


def main():
    parser = argparse.ArgumentParser(description="Compare PHI detection models")
    parser.add_argument(
        "--test-file",
        type=str,
        default="data/test/test_phi_tagged_cases.xlsx",
        help="Path to test data file"
    )
    parser.add_argument(
        "--max-cases",
        type=int,
        default=5,
        help="Maximum test cases per model"
    )
    parser.add_argument(
        "--models",
        type=str,
        nargs="+",
        default=["jingyaogong/minimind2", "qwen2.5:1.5b"],
        help="Models to compare"
    )
    parser.add_argument(
        "--optimize",
        action="store_true",
        help="Include DSPy optimized version"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/output/reports/model_comparison.json",
        help="Output report path"
    )
    
    args = parser.parse_args()
    
    # Load test data
    test_file = project_root / args.test_file
    if not test_file.exists():
        logger.error(f"Test file not found: {test_file}")
        sys.exit(1)
    
    test_cases = load_test_data(str(test_file))
    
    if not test_cases:
        logger.error("No test cases loaded")
        sys.exit(1)
    
    # Evaluate each model
    results = []
    
    for model_name in args.models:
        try:
            result = evaluate_with_ollama(
                model_name=model_name,
                test_cases=test_cases,
                max_cases=args.max_cases,
            )
            results.append(result)
        except Exception as e:
            logger.error(f"Failed to evaluate {model_name}: {e}")
    
    # DSPy optimization (if requested)
    if args.optimize:
        try:
            logger.info("\n" + "=" * 60)
            logger.info("Running DSPy Optimization...")
            logger.info("=" * 60)
            
            # This would require DSPy to be installed and configured
            # For now, we'll skip this in the comparison
            logger.warning("DSPy optimization requires 'pip install dspy-ai'")
            logger.warning("Skipping DSPy optimization in this run")
            
        except Exception as e:
            logger.error(f"DSPy optimization failed: {e}")
    
    # Print comparison
    if results:
        print_comparison_table(results)
        
        # Save results
        output_path = project_root / args.output
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(
                {
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "test_cases": len(test_cases),
                    "max_cases_evaluated": args.max_cases,
                    "results": [asdict(r) for r in results],
                },
                f,
                indent=2,
                ensure_ascii=False,
            )
        
        logger.info(f"\nResults saved to: {output_path}")
    else:
        logger.error("No results to compare")


if __name__ == "__main__":
    main()
