#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LangChain PHI Detection Evaluation (使用專案內部 chain)

使用專案內部的 LangChain structured output chain 進行評估
- 只使用 LangChain with_structured_output（不用 Ollama JSON mode）
- 支援多 worker 並行處理
- 使用專案已有的 identify_phi 函數

Usage:
    python scripts/evaluate_langchain_phi.py
    python scripts/evaluate_langchain_phi.py --model granite4:1b --workers 4 --limit 3
"""

import re
import sys
import time
import json
import pandas as pd
from pathlib import Path
from typing import List, Tuple, Optional
from dataclasses import dataclass, field
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, str(Path(__file__).parent.parent))

from loguru import logger

logger.remove()
logger.add(sys.stderr, level="INFO", format="<green>{time:HH:mm:ss}</green> | <level>{message}</level>")


# ============================================================
# Evaluation Data Classes
# ============================================================

@dataclass
class PHIInstance:
    """PHI 實例"""
    phi_type: str
    content: str
    phi_id: Optional[str] = None


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
        tp, fp = len(self.true_positives), len(self.false_positives)
        return tp / (tp + fp) if (tp + fp) > 0 else 0.0
    
    @property
    def recall(self) -> float:
        tp, fn = len(self.true_positives), len(self.false_negatives)
        return tp / (tp + fn) if (tp + fn) > 0 else 0.0
    
    @property
    def f1_score(self) -> float:
        p, r = self.precision, self.recall
        return 2 * p * r / (p + r) if (p + r) > 0 else 0.0


# ============================================================
# Helper Functions
# ============================================================

def parse_phi_tags(text: str) -> List[PHIInstance]:
    """從帶標記的文本中解析 PHI"""
    pattern = r'【PHI:(\w+):?(\w*)】([^【]+?)【/PHI】'
    return [
        PHIInstance(phi_type=m.group(1), phi_id=m.group(2) or None, content=m.group(3).strip())
        for m in re.finditer(pattern, text)
    ]


def remove_phi_tags(text: str) -> str:
    """移除 PHI 標記"""
    return re.sub(r'【PHI:\w+:?\w*】([^【]+?)【/PHI】', r'\1', text)


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


def evaluate_case(case_id: str, ground_truth: List[PHIInstance], detected: List[PHIInstance]) -> EvaluationResult:
    """評估單個案例"""
    result = EvaluationResult(case_id=case_id, ground_truth=ground_truth, detected=detected)
    
    gt_set = {(normalize_phi_type(p.phi_type), p.content.strip().lower()) for p in ground_truth}
    gt_contents = {p.content.strip().lower() for p in ground_truth}
    matched_gt = set()
    
    for phi in detected:
        content_lower = phi.content.strip().lower()
        phi_type_norm = normalize_phi_type(phi.phi_type)
        
        if (phi_type_norm, content_lower) in gt_set:
            result.true_positives.append(phi)
            matched_gt.add((phi_type_norm, content_lower))
        elif content_lower in gt_contents:
            result.true_positives.append(phi)
            matched_gt.add(content_lower)
        elif any(content_lower in gt or gt in content_lower for gt in gt_contents if len(content_lower) >= 2):
            result.true_positives.append(phi)
        else:
            result.false_positives.append(phi)
    
    for phi in ground_truth:
        content_lower = phi.content.strip().lower()
        phi_type_norm = normalize_phi_type(phi.phi_type)
        if (phi_type_norm, content_lower) not in matched_gt and content_lower not in matched_gt:
            if not any(content_lower in d.content.lower() or d.content.lower() in content_lower for d in detected):
                result.false_negatives.append(phi)
    
    return result


def split_into_chunks(text: str, max_length: int = 400) -> List[str]:
    """將文本分成較小的段落"""
    lines = text.split('\n')
    chunks, current_chunk, current_length = [], [], 0
    
    for line in lines:
        if current_length + len(line) > max_length and current_chunk:
            chunks.append('\n'.join(current_chunk))
            current_chunk, current_length = [line], len(line)
        else:
            current_chunk.append(line)
            current_length += len(line) + 1
    
    if current_chunk:
        chunks.append('\n'.join(current_chunk))
    return chunks if chunks else [text]


# ============================================================
# Detection using Project's LangChain Chain
# ============================================================

def process_chunk_with_chain(chain, chunk: str, chunk_idx: int, timeout: int = 60) -> Tuple[int, List[PHIInstance], float]:
    """
    處理單個 chunk（使用專案的 LangChain chain）+ timeout 防卡住
    """
    import signal
    
    start = time.time()
    
    def timeout_handler(signum, frame):
        raise TimeoutError(f"Chunk {chunk_idx} timeout after {timeout}s")
    
    # 設定 timeout (只在主線程有效)
    try:
        old_handler = signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(timeout)
    except (ValueError, AttributeError):
        # 在子線程中無法使用 signal
        old_handler = None
    
    try:
        # 使用專案的 chain（已經是 with_structured_output）
        result = chain.invoke({
            "context": "Identify all PHI in the medical text.",
            "text": chunk
        })
        
        entities = [
            PHIInstance(
                phi_type=e.phi_type.value if hasattr(e.phi_type, 'value') else str(e.phi_type),
                content=e.entity_text
            )
            for e in (result.entities if result else [])
        ]
        return chunk_idx, entities, time.time() - start
    except TimeoutError as e:
        logger.warning(f"⏱️ {e}")
        return chunk_idx, [], time.time() - start
    except Exception as e:
        logger.warning(f"Chunk {chunk_idx} failed: {e}")
        return chunk_idx, [], time.time() - start
    finally:
        if old_handler is not None:
            signal.alarm(0)
            signal.signal(signal.SIGALRM, old_handler)


def run_detection(
    text: str,
    chain,
    chunk_size: int = 400,
    max_workers: int = 1,
    timeout: int = 60,
) -> Tuple[List[PHIInstance], float, int]:
    """
    使用專案的 LangChain chain 執行 PHI 檢測
    """
    start_time = time.time()
    
    # 分段
    chunks = split_into_chunks(text, max_length=chunk_size)
    num_chunks = len(chunks)
    
    all_detected = []
    
    # 順序處理（避免多線程 signal 問題）
    for i, chunk in enumerate(chunks):
        if not chunk.strip():
            continue
        _, entities, _ = process_chunk_with_chain(chain, chunk, i, timeout=timeout)
        all_detected.extend(entities)
    
    # 去重
    seen = set()
    unique_detected = []
    for phi in all_detected:
        key = (phi.phi_type, phi.content.strip().lower())
        if key not in seen:
            seen.add(key)
            unique_detected.append(phi)
    
    return unique_detected, time.time() - start_time, num_chunks


def print_report(results: List[EvaluationResult], model_name: str):
    """列印評估報告"""
    print("\n" + "=" * 80)
    print(f"📊 LangChain Structured Output PHI Evaluation")
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
    
    print(f"\n📈 Overall Metrics")
    print("-" * 40)
    print(f"  Ground Truth:   {total_gt:>5}")
    print(f"  Detected:       {total_detected:>5}")
    print(f"  True Positives: {total_tp:>5} ✅")
    print(f"  False Positives:{total_fp:>5} ⚠️")
    print(f"  False Negatives:{total_fn:>5} ❌")
    print("-" * 40)
    print(f"  Precision:  {precision:.2%}")
    print(f"  Recall:     {recall:.2%}")
    print(f"  F1 Score:   {f1:.2%}")
    print(f"  Total Time: {total_time:.1f}s ({total_chunks} chunks)")
    print(f"  Avg Time:   {total_time/len(results):.1f}s/case")
    
    print(f"\n📋 Per-Case Results")
    print("-" * 85)
    print(f"{'Case':<10} {'GT':>4} {'Det':>4} {'TP':>4} {'FP':>4} {'FN':>4} {'Prec':>7} {'Rec':>7} {'F1':>7} {'Time':>7}")
    print("-" * 85)
    
    for r in results:
        print(f"{r.case_id:<10} {len(r.ground_truth):>4} {len(r.detected):>4} "
              f"{len(r.true_positives):>4} {len(r.false_positives):>4} {len(r.false_negatives):>4} "
              f"{r.precision:>6.1%} {r.recall:>6.1%} {r.f1_score:>6.1%} {r.processing_time:>6.1f}s")
    
    if total_fn > 0:
        print(f"\n❌ Top Missed PHI Types")
        fn_by_type = defaultdict(int)
        for r in results:
            for fn in r.false_negatives:
                fn_by_type[fn.phi_type] += 1
        for phi_type, count in sorted(fn_by_type.items(), key=lambda x: -x[1])[:5]:
            print(f"   {phi_type}: {count}")
    
    print("=" * 80)
    return {"precision": precision, "recall": recall, "f1": f1}


def main():
    import argparse
    import os
    
    parser = argparse.ArgumentParser(description='LangChain PHI Evaluation')
    parser.add_argument('--model', type=str, default='granite4:1b')
    parser.add_argument('--limit', type=int, default=None)
    parser.add_argument('--chunk-size', type=int, default=400)
    parser.add_argument('--workers', type=int, default=1, help='(deprecated, sequential only)')
    parser.add_argument('--num-ctx', type=int, default=8192, help='Ollama context size')
    parser.add_argument('--timeout', type=int, default=60, help='Timeout per chunk (seconds)')
    parser.add_argument('--keep-alive', type=str, default='30m', help='Keep model loaded (e.g., 30m, 1h, -1=forever)')
    parser.add_argument('--use-parser', action='store_true', help='Use PydanticOutputParser instead of with_structured_output (more stable)')
    args = parser.parse_args()
    
    # 顯示配置
    cpu_count = os.cpu_count() or 4
    print(f"[Config] Model: {args.model}", flush=True)
    print(f"[Config] Chunk size: {args.chunk_size} chars", flush=True)
    print(f"[Config] Timeout: {args.timeout}s per chunk", flush=True)
    print(f"[Config] Method: LangChain with_structured_output", flush=True)
    
    # 使用專案的 LLM factory 和 chain builder
    from medical_deidentification.infrastructure.llm import create_llm, LLMConfig
    from medical_deidentification.infrastructure.rag.chains.processors import build_phi_identification_chain
    
    # 創建 LLM（含 keep_alive 保持熱載入）
    print(f"[Init] Creating LangChain LLM (keep_alive={args.keep_alive})...", flush=True)
    config = LLMConfig(
        provider="ollama",
        model_name=args.model,
        temperature=0.0,
        num_ctx=args.num_ctx,
        keep_alive=args.keep_alive,  # 保持模型熱載入
    )
    llm = create_llm(config)
    
    # 創建 PHI 識別 chain
    # with_structured_output 有時會卡住，可用 --use-parser 改用 PydanticOutputParser
    use_structured = not args.use_parser
    method = "with_structured_output" if use_structured else "PydanticOutputParser"
    print(f"[Init] Building PHI identification chain ({method})...", flush=True)
    chain = build_phi_identification_chain(
        llm=llm,
        language="zh-TW",
        use_structured_output=use_structured,
    )
    
    # 測試連接
    print(f"[Test] Testing model connection...", flush=True)
    test_start = time.time()
    try:
        test_result = chain.invoke({
            "context": "Test PHI identification",
            "text": "Patient John, age 45, phone 0912-345-678"
        })
        test_time = time.time() - test_start
        entity_count = len(test_result.entities) if test_result else 0
        print(f"[Test] Found {entity_count} entities in {test_time:.1f}s ✓", flush=True)
    except Exception as e:
        print(f"[Test] Failed: {e}", flush=True)
        return
    
    # 載入測試資料
    test_file = Path("data/test/test_phi_tagged_cases.xlsx")
    if not test_file.exists():
        logger.error(f"Test file not found: {test_file}")
        return
    
    print(f"[Data] Loading {test_file}...", flush=True)
    df = pd.read_excel(test_file)
    
    if args.limit:
        df = df.head(args.limit)
    
    print(f"[Info] Evaluating {len(df)} cases\n", flush=True)
    
    results = []
    
    for idx, row in df.iterrows():
        case_id = row['Case ID']
        
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
        
        print(f"🔍 {case_id} ({len(ground_truth)} PHI, {len(clean_text)} chars)...", flush=True)
        
        try:
            detected, elapsed, num_chunks = run_detection(
                clean_text, chain,
                chunk_size=args.chunk_size,
                timeout=args.timeout,
            )
            result = evaluate_case(case_id, ground_truth, detected)
            result.processing_time = elapsed
            result.num_chunks = num_chunks
            results.append(result)
            
            print(f"   → {len(detected)} detected, TP={len(result.true_positives)}, "
                  f"F1={result.f1_score:.1%}, {elapsed:.1f}s ({num_chunks} chunks)", flush=True)
            
        except Exception as e:
            logger.error(f"   → Error: {e}")
            import traceback
            traceback.print_exc()
    
    if not results:
        print("No results")
        return
    
    metrics = print_report(results, args.model)
    
    # 儲存結果
    output_file = Path(f"data/output/reports/langchain_{args.model.replace(':', '_')}_eval.json")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            "model": args.model,
            "method": "LangChain with_structured_output",
            "chunk_size": args.chunk_size,
            "timeout": args.timeout,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "metrics": metrics,
            "cases": [
                {"case_id": r.case_id, "gt": len(r.ground_truth), "detected": len(r.detected),
                 "tp": len(r.true_positives), "fp": len(r.false_positives), "fn": len(r.false_negatives),
                 "f1": r.f1_score, "time": r.processing_time}
                for r in results
            ]
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n📄 Report saved: {output_file}")


if __name__ == "__main__":
    main()
