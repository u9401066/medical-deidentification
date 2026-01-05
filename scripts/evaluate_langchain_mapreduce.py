#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LangChain MapReduce + DSPy Optimized Prompt Evaluation
LangChain MapReduce + DSPy 優化 Prompt 評估

結合兩者優點：
- LangChain: Map-Reduce pattern 處理長文本（無長度限制）
- DSPy: 優化的 prompt 提高識別準確度

Usage:
    python scripts/evaluate_langchain_mapreduce.py
    python scripts/evaluate_langchain_mapreduce.py --model granite4:1b --limit 3
"""

import re
import sys
import time
import json
import pandas as pd
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent.parent))

from loguru import logger

logger.remove()
logger.add(sys.stderr, level="INFO", format="<green>{time:HH:mm:ss}</green> | <level>{message}</level>")


@dataclass
class PHIInstance:
    """PHI 實例"""
    phi_type: str
    content: str
    phi_id: Optional[str] = None
    
    def __hash__(self):
        return hash((self.phi_type, self.content.strip().lower()))
    
    def __eq__(self, other):
        if not isinstance(other, PHIInstance):
            return False
        return (
            self.phi_type == other.phi_type and 
            self.content.strip().lower() == other.content.strip().lower()
        )


@dataclass
class EvaluationResult:
    """評估結果"""
    case_id: str
    ground_truth: List[PHIInstance]
    detected: List[PHIInstance]
    true_positives: List[PHIInstance] = field(default_factory=list)
    false_positives: List[PHIInstance] = field(default_factory=list)
    false_negatives: List[PHIInstance] = field(default_factory=list)
    processing_time: float = 0.0
    num_chunks: int = 0
    
    @property
    def precision(self) -> float:
        tp = len(self.true_positives)
        fp = len(self.false_positives)
        return tp / (tp + fp) if (tp + fp) > 0 else 0.0
    
    @property
    def recall(self) -> float:
        tp = len(self.true_positives)
        fn = len(self.false_negatives)
        return tp / (tp + fn) if (tp + fn) > 0 else 0.0
    
    @property
    def f1_score(self) -> float:
        p, r = self.precision, self.recall
        return 2 * p * r / (p + r) if (p + r) > 0 else 0.0


def parse_phi_tags(text: str) -> List[PHIInstance]:
    """從帶標記的文本中解析 PHI"""
    pattern = r'【PHI:(\w+):?(\w*)】([^【]+?)【/PHI】'
    instances = []
    
    for match in re.finditer(pattern, text):
        phi_type = match.group(1)
        phi_id = match.group(2) if match.group(2) else None
        content = match.group(3).strip()
        
        instances.append(PHIInstance(
            phi_type=phi_type,
            phi_id=phi_id,
            content=content,
        ))
    
    return instances


def remove_phi_tags(text: str) -> str:
    """移除 PHI 標記"""
    pattern = r'【PHI:\w+:?\w*】([^【]+?)【/PHI】'
    return re.sub(pattern, r'\1', text)


def normalize_phi_type(phi_type: str) -> str:
    """標準化 PHI 類型"""
    mapping = {
        'NAME': 'NAME', 'PATIENT_NAME': 'NAME', 'DOCTOR_NAME': 'NAME',
        'AGE': 'AGE', 'AGE_OVER_89': 'AGE',
        'DATE': 'DATE', 'DOB': 'DATE', 'BIRTHDATE': 'DATE',
        'ID': 'ID', 'ID_NUMBER': 'ID', 'MRN': 'ID',
        'PHONE': 'PHONE', 'TELEPHONE': 'PHONE', 'MOBILE': 'PHONE',
        'EMAIL': 'EMAIL',
        'LOCATION': 'LOCATION', 'ADDRESS': 'LOCATION',
        'FACILITY': 'FACILITY', 'HOSPITAL': 'FACILITY',
    }
    return mapping.get(phi_type.upper(), phi_type.upper())


def evaluate_case(
    case_id: str,
    ground_truth: List[PHIInstance],
    detected: List[PHIInstance]
) -> EvaluationResult:
    """評估單個案例 - 使用模糊匹配"""
    result = EvaluationResult(
        case_id=case_id,
        ground_truth=ground_truth,
        detected=detected
    )
    
    # 標準化並建立集合
    gt_set = {(normalize_phi_type(p.phi_type), p.content.strip().lower()) for p in ground_truth}
    gt_contents = {p.content.strip().lower() for p in ground_truth}
    
    matched_gt = set()
    
    for phi in detected:
        content_lower = phi.content.strip().lower()
        phi_type_norm = normalize_phi_type(phi.phi_type)
        
        # 完全匹配
        if (phi_type_norm, content_lower) in gt_set:
            result.true_positives.append(phi)
            matched_gt.add((phi_type_norm, content_lower))
        # 內容匹配（類型可能不同）
        elif content_lower in gt_contents:
            result.true_positives.append(phi)
            matched_gt.add(content_lower)
        # 子字串匹配
        elif any(content_lower in gt.lower() or gt.lower() in content_lower 
                 for gt in gt_contents if len(content_lower) >= 2):
            result.true_positives.append(phi)
        else:
            result.false_positives.append(phi)
    
    # 漏檢
    for phi in ground_truth:
        content_lower = phi.content.strip().lower()
        phi_type_norm = normalize_phi_type(phi.phi_type)
        
        if (phi_type_norm, content_lower) not in matched_gt and content_lower not in matched_gt:
            found = any(
                content_lower in d.content.strip().lower() or 
                d.content.strip().lower() in content_lower
                for d in detected
            )
            if not found:
                result.false_negatives.append(phi)
    
    return result


def run_langchain_mapreduce(
    text: str,
    llm,
    text_splitter,
) -> Tuple[List[PHIInstance], float, int]:
    """
    使用 LangChain MapReduce 處理文本
    
    Returns:
        (detected_phi_list, elapsed_time, num_chunks)
    """
    from core.infrastructure.rag.chains.map_reduce import (
        identify_phi_with_map_reduce
    )
    
    start_time = time.time()
    
    # 使用現有的 map_reduce 實作
    entities = identify_phi_with_map_reduce(
        text=text,
        llm=llm,
        text_splitter=text_splitter,
    )
    
    elapsed = time.time() - start_time
    
    # 計算 chunk 數量
    chunks = text_splitter.split_text(text)
    num_chunks = len(chunks)
    
    # 轉換為 PHIInstance
    detected = [
        PHIInstance(
            phi_type=e.phi_type.value if hasattr(e.phi_type, 'value') else str(e.phi_type),
            content=e.text,
        )
        for e in entities
    ]
    
    return detected, elapsed, num_chunks


def print_report(results: List[EvaluationResult], model_name: str, method: str):
    """列印評估報告"""
    print("\n" + "=" * 80)
    print(f"📊 PHI Detection Evaluation Report")
    print(f"   Method: {method}")
    print(f"   Model: {model_name}")
    print("=" * 80)
    
    total_gt = sum(len(r.ground_truth) for r in results)
    total_detected = sum(len(r.detected) for r in results)
    total_tp = sum(len(r.true_positives) for r in results)
    total_fp = sum(len(r.false_positives) for r in results)
    total_fn = sum(len(r.false_negatives) for r in results)
    total_time = sum(r.processing_time for r in results)
    total_chunks = sum(r.num_chunks for r in results)
    
    precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0
    recall = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
    
    print(f"\n📈 Overall Metrics | 總體指標")
    print("-" * 40)
    print(f"  Ground Truth PHI:     {total_gt:>5}")
    print(f"  Detected PHI:         {total_detected:>5}")
    print(f"  True Positives (TP):  {total_tp:>5}  ✅")
    print(f"  False Positives (FP): {total_fp:>5}  ⚠️")
    print(f"  False Negatives (FN): {total_fn:>5}  ❌")
    print("-" * 40)
    print(f"  Precision:  {precision:.2%}")
    print(f"  Recall:     {recall:.2%}")
    print(f"  F1 Score:   {f1:.2%}")
    print(f"  Total Chunks: {total_chunks}")
    print(f"  Avg Time:   {total_time/len(results):.2f}s per case")
    
    print(f"\n📋 Per-Case Results")
    print("-" * 90)
    print(f"{'Case ID':<12} {'GT':>4} {'Det':>4} {'TP':>4} {'FP':>4} {'FN':>4} {'Prec':>7} {'Rec':>7} {'F1':>7} {'Chunks':>6} {'Time':>6}")
    print("-" * 90)
    
    for r in results:
        print(f"{r.case_id:<12} {len(r.ground_truth):>4} {len(r.detected):>4} "
              f"{len(r.true_positives):>4} {len(r.false_positives):>4} {len(r.false_negatives):>4} "
              f"{r.precision:>6.1%} {r.recall:>6.1%} {r.f1_score:>6.1%} {r.num_chunks:>6} {r.processing_time:>5.1f}s")
    
    # 漏檢分析
    if total_fn > 0:
        print(f"\n❌ Top Missed PHI Types")
        fn_by_type = defaultdict(int)
        for r in results:
            for fn in r.false_negatives:
                fn_by_type[fn.phi_type] += 1
        
        for phi_type, count in sorted(fn_by_type.items(), key=lambda x: -x[1])[:5]:
            print(f"   {phi_type}: {count} missed")
    
    print("\n" + "=" * 80)
    
    return {"precision": precision, "recall": recall, "f1": f1}


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='LangChain MapReduce PHI Evaluation')
    parser.add_argument('--model', type=str, default='granite4:1b',
                        help='Model name (default: granite4:1b)')
    parser.add_argument('--limit', type=int, default=None,
                        help='Limit number of cases to evaluate')
    parser.add_argument('--chunk-size', type=int, default=400,
                        help='Chunk size for text splitting (default: 400)')
    parser.add_argument('--chunk-overlap', type=int, default=50,
                        help='Chunk overlap (default: 50)')
    args = parser.parse_args()
    
    print(f"[Config] Using model: {args.model}", flush=True)
    print(f"[Config] Chunk size: {args.chunk_size}, overlap: {args.chunk_overlap}", flush=True)
    
    # Import LangChain components
    from core.infrastructure.llm import create_llm, LLMConfig
    from core.infrastructure.rag.text_splitter import MedicalTextSplitter
    
    # Create LLM (LangChain ChatOllama)
    print(f"[Init] Creating LangChain LLM...", flush=True)
    config = LLMConfig(
        provider="ollama",
        model_name=args.model,
        temperature=0.0,
        max_tokens=2048,
    )
    llm = create_llm(config)
    
    # Create text splitter
    print(f"[Init] Creating MedicalTextSplitter...", flush=True)
    text_splitter = MedicalTextSplitter(
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap,
    )
    
    # Load test data
    test_file = Path("data/test/test_phi_tagged_cases.xlsx")
    if not test_file.exists():
        logger.error(f"Test file not found: {test_file}")
        return
    
    print(f"[Data] Loading {test_file}...", flush=True)
    df = pd.read_excel(test_file)
    
    if args.limit:
        df = df.head(args.limit)
    
    print(f"[Info] Evaluating {len(df)} cases", flush=True)
    
    results = []
    
    for idx, row in df.iterrows():
        case_id = row['Case ID']
        
        # 合併文本欄位
        text_columns = [
            'Clinical Summary\n(含標記的 PHI)',
            'Contact Info\n(含標記的聯絡資訊)',
            'Medical History\n(含標記的時間/地點)',
            'Treatment Notes\n(含標記的醫師/日期)'
        ]
        
        full_text_with_tags = ""
        for col in text_columns:
            if col in df.columns and pd.notna(row[col]):
                full_text_with_tags += str(row[col]) + "\n"
        
        ground_truth = parse_phi_tags(full_text_with_tags)
        clean_text = remove_phi_tags(full_text_with_tags)
        
        print(f"\n🔍 {case_id} ({len(ground_truth)} PHI, {len(clean_text)} chars)...", flush=True)
        
        try:
            detected, elapsed, num_chunks = run_langchain_mapreduce(
                clean_text, llm, text_splitter
            )
            result = evaluate_case(case_id, ground_truth, detected)
            result.processing_time = elapsed
            result.num_chunks = num_chunks
            results.append(result)
            
            print(f"   → {len(detected)} detected in {num_chunks} chunks, "
                  f"TP={len(result.true_positives)}, F1={result.f1_score:.1%}, {elapsed:.1f}s", flush=True)
            
        except Exception as e:
            logger.error(f"   → Error: {e}")
            import traceback
            traceback.print_exc()
    
    if not results:
        print("No results to report")
        return
    
    # Print report
    metrics = print_report(results, args.model, "LangChain MapReduce")
    
    # Save results
    output_file = Path(f"data/output/reports/langchain_mapreduce_{args.model.replace(':', '_')}_eval.json")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    report = {
        "model": args.model,
        "method": "LangChain MapReduce",
        "chunk_size": args.chunk_size,
        "chunk_overlap": args.chunk_overlap,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "metrics": metrics,
        "cases": [
            {
                "case_id": r.case_id,
                "gt": len(r.ground_truth),
                "detected": len(r.detected),
                "tp": len(r.true_positives),
                "fp": len(r.false_positives),
                "fn": len(r.false_negatives),
                "f1": r.f1_score,
                "chunks": r.num_chunks,
                "time": r.processing_time,
            }
            for r in results
        ]
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"\n📄 Report saved: {output_file}")


if __name__ == "__main__":
    main()
