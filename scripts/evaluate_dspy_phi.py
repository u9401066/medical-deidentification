#!/usr/bin/env python3
"""
DSPy PHI Detection Evaluation | DSPy PHI 檢測評估

使用 DSPy 模組評估 PHI 檢測效能
Evaluate PHI detection using DSPy module

DSPy 優勢:
- ChainOfThought: 讓模型逐步推理
- 結構化輸出: 更好的 JSON 解析
- 可優化: 可以用訓練資料自動改進 prompt

Usage:
    python scripts/evaluate_dspy_phi.py
    python scripts/evaluate_dspy_phi.py --model qwen2.5:1.5b
    python scripts/evaluate_dspy_phi.py --optimize  # 使用訓練資料優化
"""

import json
import re
import sys
import time
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))

from loguru import logger

logger.remove()
logger.add(sys.stderr, level="INFO", format="<green>{time:HH:mm:ss}</green> | <level>{message}</level>")


@dataclass
class PHIInstance:
    """PHI 實例"""
    phi_type: str
    content: str
    phi_id: str | None = None

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
    ground_truth: list[PHIInstance]
    detected: list[PHIInstance]
    true_positives: list[PHIInstance] = field(default_factory=list)
    false_positives: list[PHIInstance] = field(default_factory=list)
    false_negatives: list[PHIInstance] = field(default_factory=list)
    processing_time: float = 0.0

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


def parse_phi_tags(text: str) -> list[PHIInstance]:
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
    ground_truth: list[PHIInstance],
    detected: list[PHIInstance]
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
        # 子字串匹配（檢測結果是標準答案的一部分）
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
            # 檢查是否有子字串匹配
            found = any(
                content_lower in d.content.strip().lower() or
                d.content.strip().lower() in content_lower
                for d in detected
            )
            if not found:
                result.false_negatives.append(phi)

    return result


def get_model_context_length(model_name: str) -> int:
    """從 Ollama API 取得模型的 context length"""
    import requests
    try:
        resp = requests.post(
            'http://localhost:11434/api/show',
            json={'name': model_name},
            timeout=5
        )
        if resp.status_code == 200:
            data = resp.json()
            model_info = data.get('model_info', {})
            for key, value in model_info.items():
                if 'context' in key.lower():
                    return int(value)
    except Exception:
        pass
    return 4096  # 保守預設值


def estimate_tokens(text: str) -> int:
    """估計文本的 token 數量（中文約 1.5 token/字，英文約 0.75 token/word）"""
    # 簡單估計：中文字數 * 1.5 + 英文 word 數 * 1.3
    chinese_chars = len([c for c in text if '\u4e00' <= c <= '\u9fff'])
    other_chars = len(text) - chinese_chars
    return int(chinese_chars * 1.5 + other_chars * 0.5)


def split_into_chunks(text: str, max_length: int = 500) -> list[str]:
    """將文本分成較小的段落"""
    # 按行分割
    lines = text.split('\n')
    chunks = []
    current_chunk = []
    current_length = 0

    for line in lines:
        line_length = len(line)
        if current_length + line_length > max_length and current_chunk:
            chunks.append('\n'.join(current_chunk))
            current_chunk = [line]
            current_length = line_length
        else:
            current_chunk.append(line)
            current_length += line_length + 1

    if current_chunk:
        chunks.append('\n'.join(current_chunk))

    return chunks


def run_dspy_detection(
    text: str,
    identifier,
    context_length: int = 4096,
    force_chunk_size: int = None,  # 強制分段大小
    timeout: int = 120
) -> tuple[list[PHIInstance], float, int]:
    """
    使用 DSPy 執行 PHI 檢測
    
    Args:
        text: 要分析的文本
        identifier: DSPy PHIIdentifier
        context_length: 模型的 context window 大小
        force_chunk_size: 強制分段大小（即使 context 夠大也分段）
        
    Returns:
        (detected_list, elapsed_time, num_chunks)
    """
    start_time = time.time()
    all_detected = []

    # 估計 token 數量
    estimated_tokens = estimate_tokens(text)
    # 保留一半 context 給 prompt + output
    safe_limit = context_length // 2

    # 決定是否需要分段
    # 1. 如果指定了 force_chunk_size，強制分段
    # 2. 如果 token 超過 safe_limit，需要分段
    need_chunking = force_chunk_size is not None or estimated_tokens > safe_limit
    num_chunks = 1

    try:
        if need_chunking:
            # 計算每個 chunk 的最大字數
            if force_chunk_size:
                max_chars_per_chunk = force_chunk_size
            else:
                chars_per_token = len(text) / estimated_tokens
                max_chars_per_chunk = int(safe_limit * chars_per_token * 0.8)  # 80% 安全邊際

            chunks = split_into_chunks(text, max_length=max_chars_per_chunk)
            num_chunks = len(chunks)
            logger.info(f"Splitting into {num_chunks} chunks (max {max_chars_per_chunk} chars each)")

            for i, chunk in enumerate(chunks):
                if not chunk.strip():
                    continue
                entities = identifier(medical_text=chunk)
                for e in entities:
                    all_detected.append(PHIInstance(
                        phi_type=e.phi_type,
                        content=e.text,
                    ))
        else:
            # Context window 夠大，直接處理整份文本
            logger.info(f"Text fits in context ({estimated_tokens} tokens < {safe_limit}), processing directly")
            entities = identifier(medical_text=text)
            all_detected = [
                PHIInstance(
                    phi_type=e.phi_type,
                    content=e.text,
                )
                for e in entities
            ]

        elapsed = time.time() - start_time

        # 去重
        seen = set()
        unique_detected = []
        for phi in all_detected:
            key = (phi.phi_type, phi.content.strip().lower())
            if key not in seen:
                seen.add(key)
                unique_detected.append(phi)

        return unique_detected, elapsed, num_chunks

    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"DSPy detection failed: {e}")
        raise


def print_report(results: list[EvaluationResult], model_name: str):
    """列印評估報告"""
    print("\n" + "=" * 80)
    print("📊 DSPy PHI Detection Evaluation Report")
    print(f"   Model: {model_name}")
    print("=" * 80)

    total_gt = sum(len(r.ground_truth) for r in results)
    total_detected = sum(len(r.detected) for r in results)
    total_tp = sum(len(r.true_positives) for r in results)
    total_fp = sum(len(r.false_positives) for r in results)
    total_fn = sum(len(r.false_negatives) for r in results)
    total_time = sum(r.processing_time for r in results)

    precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0
    recall = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

    print("\n📈 Overall Metrics | 總體指標")
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
    print(f"  Avg Time:   {total_time/len(results):.2f}s per case")

    print("\n📋 Per-Case Results")
    print("-" * 80)
    print(f"{'Case ID':<12} {'GT':>4} {'Det':>4} {'TP':>4} {'FP':>4} {'FN':>4} {'Prec':>7} {'Rec':>7} {'F1':>7} {'Time':>6}")
    print("-" * 80)

    for r in results:
        print(f"{r.case_id:<12} {len(r.ground_truth):>4} {len(r.detected):>4} "
              f"{len(r.true_positives):>4} {len(r.false_positives):>4} {len(r.false_negatives):>4} "
              f"{r.precision:>6.1%} {r.recall:>6.1%} {r.f1_score:>6.1%} {r.processing_time:>5.1f}s")

    # 漏檢分析
    if total_fn > 0:
        print("\n❌ Top Missed PHI Types")
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

    parser = argparse.ArgumentParser(description='DSPy PHI Detection Evaluation')
    parser.add_argument('--model', type=str, default='granite4:1b',
                        help='Model name (default: granite4:1b)')
    parser.add_argument('--limit', type=int, default=None,
                        help='Limit number of cases to evaluate')
    parser.add_argument('--optimize', action='store_true',
                        help='Run DSPy optimization')
    parser.add_argument('--cot', action='store_true',
                        help='Use ChainOfThought (slower but better reasoning)')
    args = parser.parse_args()

    # Import DSPy module
    from core.infrastructure.dspy import (
        LIGHTWEIGHT_MODELS,
        PHIIdentifier,
        configure_dspy_ollama,
    )

    print(f"[Config] Using model: {args.model}", flush=True)
    if args.model in LIGHTWEIGHT_MODELS:
        info = LIGHTWEIGHT_MODELS[args.model]
        print(f"         {info['description']}", flush=True)

    mode = "ChainOfThought" if args.cot else "Predict (fast)"
    print(f"[Config] DSPy mode: {mode}", flush=True)

    # Get model context length
    context_length = get_model_context_length(args.model)
    print(f"[Config] Context window: {context_length:,} tokens", flush=True)

    # Configure DSPy with Ollama + JSON mode for 3-4x speedup
    print("[Init] Configuring DSPy with Ollama (JSON mode)...", flush=True)
    configure_dspy_ollama(
        model_name=args.model,
        temperature=0.0,  # Deterministic
        max_tokens=4096,  # 增加輸出 token 限制
        use_json_mode=True,  # 3-4x faster
    )

    # Create DSPy identifier
    print(f"[Init] Creating PHIIdentifier ({mode})...", flush=True)
    identifier = PHIIdentifier(use_cot=args.cot)

    # Test connection - 使用 module() 而不是 module.forward()
    print("[Test] Testing model connection...", flush=True)
    test_result = identifier("Patient John, age 45, phone 0912-345-678")
    print(f"[Test] Found {len(test_result)} entities in test: {[e.text for e in test_result]}", flush=True)

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

        estimated_tokens = estimate_tokens(clean_text)
        print(f"\n🔍 {case_id} ({len(ground_truth)} PHI, ~{estimated_tokens} tokens)...", flush=True)

        try:
            detected, elapsed, num_chunks = run_dspy_detection(
                clean_text, identifier, context_length=context_length
            )
            result = evaluate_case(case_id, ground_truth, detected)
            result.processing_time = elapsed
            results.append(result)

            chunk_info = f", {num_chunks} chunks" if num_chunks > 1 else ""
            print(f"   → {len(detected)} detected, TP={len(result.true_positives)}, "
                  f"F1={result.f1_score:.1%}, {elapsed:.1f}s{chunk_info}", flush=True)

        except Exception as e:
            logger.error(f"   → Error: {e}")
            import traceback
            traceback.print_exc()

    # Print report
    metrics = print_report(results, args.model)

    # Save results
    output_file = Path(f"data/output/reports/dspy_{args.model.replace(':', '_')}_eval.json")
    output_file.parent.mkdir(parents=True, exist_ok=True)

    report = {
        "model": args.model,
        "method": f"DSPy {mode}",
        "context_length": context_length,
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
