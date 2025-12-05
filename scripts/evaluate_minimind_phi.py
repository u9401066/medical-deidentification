#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MiniMind PHI Detection Evaluation | MiniMind PHI 檢測評估

使用帶標記的測試資料評估 MiniMind 的 PHI 檢測效能
Evaluate MiniMind's PHI detection performance using tagged test data

Metrics:
- Precision: 檢測正確率（避免過度檢測）
- Recall: 召回率（避免漏檢）
- F1 Score: 綜合評分
- Over-detection: 過度檢測分析
"""

import re
import sys
import time
import json
import pandas as pd
from pathlib import Path
from typing import List, Dict, Tuple, Set, Optional
from dataclasses import dataclass, field
from collections import defaultdict

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from loguru import logger

# Configure logging
logger.remove()
logger.add(sys.stderr, level="INFO", format="<green>{time:HH:mm:ss}</green> | <level>{message}</level>")


@dataclass
class PHIInstance:
    """單個 PHI 實例"""
    phi_type: str
    content: str
    phi_id: Optional[str] = None
    start: int = 0
    end: int = 0
    
    def __hash__(self):
        return hash((self.phi_type, self.content.strip()))
    
    def __eq__(self, other):
        if not isinstance(other, PHIInstance):
            return False
        return self.phi_type == other.phi_type and self.content.strip() == other.content.strip()


@dataclass
class EvaluationResult:
    """評估結果"""
    case_id: str
    ground_truth: List[PHIInstance]
    detected: List[PHIInstance]
    
    # Metrics
    true_positives: List[PHIInstance] = field(default_factory=list)
    false_positives: List[PHIInstance] = field(default_factory=list)  # 過度檢測
    false_negatives: List[PHIInstance] = field(default_factory=list)  # 漏檢
    
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


def parse_phi_tags(text: str) -> List[PHIInstance]:
    """從帶標記的文本中解析 PHI 標準答案"""
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
            start=match.start(),
            end=match.end()
        ))
    
    return instances


def remove_phi_tags(text: str) -> str:
    """移除 PHI 標記，保留內容（用於送給 LLM 分析）"""
    pattern = r'【PHI:\w+:?\w*】([^【]+?)【/PHI】'
    return re.sub(pattern, r'\1', text)


def normalize_phi_type(phi_type: str) -> str:
    """標準化 PHI 類型名稱"""
    type_mapping = {
        # 姓名相關
        'NAME': 'NAME',
        'PATIENT_NAME': 'NAME',
        'DOCTOR_NAME': 'NAME',
        'PHYSICIAN': 'NAME',
        
        # 年齡相關
        'AGE': 'AGE',
        'AGE_OVER_89': 'AGE',
        
        # 日期相關
        'DATE': 'DATE',
        'BIRTHDATE': 'DATE',
        'DOB': 'DATE',
        'ADMISSION_DATE': 'DATE',
        
        # ID 相關
        'ID': 'ID',
        'ID_NUMBER': 'ID',
        'NATIONAL_ID': 'ID',
        'MRN': 'MEDICAL_RECORD_NUMBER',
        'MEDICAL_RECORD': 'MEDICAL_RECORD_NUMBER',
        
        # 聯絡資訊
        'PHONE': 'PHONE',
        'TELEPHONE': 'PHONE',
        'MOBILE': 'PHONE',
        'EMAIL': 'EMAIL',
        'ADDRESS': 'ADDRESS',
        'LOCATION': 'LOCATION',
        
        # 其他
        'FACILITY': 'FACILITY',
        'HOSPITAL': 'FACILITY',
        'DEVICE_ID': 'DEVICE_ID',
        'ACCOUNT': 'ACCOUNT',
    }
    return type_mapping.get(phi_type.upper(), phi_type.upper())


def parse_llm_response(response_text: str) -> List[PHIInstance]:
    """解析 LLM 的 PHI 檢測回應"""
    detected = []
    
    # 嘗試解析 JSON 格式
    try:
        # 尋找 JSON 區塊
        json_match = re.search(r'\[[\s\S]*?\]', response_text)
        if json_match:
            data = json.loads(json_match.group())
            for item in data:
                if isinstance(item, dict):
                    phi_type = item.get('type', item.get('phi_type', 'UNKNOWN'))
                    content = item.get('text', item.get('content', item.get('value', '')))
                    if content:
                        detected.append(PHIInstance(
                            phi_type=normalize_phi_type(phi_type),
                            content=str(content).strip()
                        ))
            return detected
    except (json.JSONDecodeError, TypeError):
        pass
    
    # 嘗試解析列表格式
    # 例如: "- NAME: 王大明" 或 "1. 姓名: 王大明"
    patterns = [
        r'[-•*]\s*(\w+)\s*[:：]\s*(.+?)(?=\n|$)',
        r'\d+[.、]\s*(\w+)\s*[:：]\s*(.+?)(?=\n|$)',
        r'(\w+)\s*[:：]\s*[「『""]?(.+?)[」』""]?(?=\n|$)',
    ]
    
    for pattern in patterns:
        for match in re.finditer(pattern, response_text):
            phi_type = match.group(1).strip()
            content = match.group(2).strip()
            
            # 過濾掉非 PHI 的項目
            if phi_type.upper() in ['PHI', 'TYPE', 'VALUE', 'TEXT', '類型', '內容']:
                continue
            
            if content and len(content) < 100:  # 避免過長的誤判
                detected.append(PHIInstance(
                    phi_type=normalize_phi_type(phi_type),
                    content=content
                ))
    
    return detected


def evaluate_case(
    case_id: str,
    ground_truth: List[PHIInstance],
    detected: List[PHIInstance]
) -> EvaluationResult:
    """評估單個案例"""
    result = EvaluationResult(
        case_id=case_id,
        ground_truth=ground_truth,
        detected=detected
    )
    
    # 標準化類型
    gt_normalized = {
        PHIInstance(normalize_phi_type(phi.phi_type), phi.content.strip())
        for phi in ground_truth
    }
    det_normalized = {
        PHIInstance(normalize_phi_type(phi.phi_type), phi.content.strip())
        for phi in detected
    }
    
    # 也用內容模糊匹配
    gt_contents = {phi.content.strip().lower() for phi in ground_truth}
    det_contents = {phi.content.strip().lower() for phi in detected}
    
    # 計算 TP, FP, FN
    for phi in detected:
        content_lower = phi.content.strip().lower()
        if phi in gt_normalized or content_lower in gt_contents:
            result.true_positives.append(phi)
        else:
            result.false_positives.append(phi)
    
    for phi in ground_truth:
        content_lower = phi.content.strip().lower()
        matched = any(
            d.content.strip().lower() == content_lower
            for d in detected
        )
        if not matched:
            result.false_negatives.append(phi)
    
    return result


def run_minimind_detection(text: str, llm, timeout: int = 120) -> Tuple[List[PHIInstance], float]:
    """使用 LLM 執行 PHI 檢測"""
    prompt = f"""請從以下醫療文本中識別所有個人健康資訊 (PHI)。

PHI 類型包括：
- NAME: 姓名（病患、醫師、家屬等）
- AGE: 年齡
- DATE: 日期（出生日期、就診日期等）
- ID: 身分證字號、病歷號
- PHONE: 電話號碼
- EMAIL: 電子郵件
- ADDRESS: 地址
- LOCATION: 地點、機構名稱
- FACILITY: 醫療機構

請以 JSON 格式列出所有 PHI，格式如下：
[
  {{"type": "NAME", "text": "實際內容"}},
  ...
]

醫療文本：
{text[:2000]}

請列出所有 PHI："""
    
    start_time = time.time()
    try:
        response = llm.invoke(prompt)
        content = response.content if hasattr(response, 'content') else str(response)
        elapsed = time.time() - start_time
        
        detected = parse_llm_response(content)
        return detected, elapsed
    except Exception as e:
        logger.warning(f"LLM error (will retry): {e}")
        elapsed = time.time() - start_time
        return [], elapsed


def print_evaluation_report(results: List[EvaluationResult], model_name: str):
    """列印評估報告"""
    print("\n" + "=" * 80)
    print(f"📊 MiniMind PHI Detection Evaluation Report")
    print(f"   Model: {model_name}")
    print("=" * 80)
    
    total_gt = sum(len(r.ground_truth) for r in results)
    total_detected = sum(len(r.detected) for r in results)
    total_tp = sum(len(r.true_positives) for r in results)
    total_fp = sum(len(r.false_positives) for r in results)
    total_fn = sum(len(r.false_negatives) for r in results)
    total_time = sum(r.processing_time for r in results)
    
    # 總體指標
    precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0
    recall = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
    
    print(f"\n📈 Overall Metrics | 總體指標")
    print("-" * 40)
    print(f"  Ground Truth PHI:     {total_gt:>5}")
    print(f"  Detected PHI:         {total_detected:>5}")
    print(f"  True Positives (TP):  {total_tp:>5}  ✅ 正確檢測")
    print(f"  False Positives (FP): {total_fp:>5}  ⚠️  過度檢測")
    print(f"  False Negatives (FN): {total_fn:>5}  ❌ 漏檢")
    print("-" * 40)
    print(f"  Precision:  {precision:.2%}  (避免過度檢測)")
    print(f"  Recall:     {recall:.2%}  (避免漏檢)")
    print(f"  F1 Score:   {f1:.2%}  (綜合評分)")
    print(f"  Avg Time:   {total_time/len(results):.2f}s per case")
    
    # 各案例詳情
    print(f"\n📋 Per-Case Results | 各案例結果")
    print("-" * 80)
    print(f"{'Case ID':<12} {'GT':>4} {'Det':>4} {'TP':>4} {'FP':>4} {'FN':>4} {'Prec':>7} {'Rec':>7} {'F1':>7} {'Time':>6}")
    print("-" * 80)
    
    for r in results:
        print(f"{r.case_id:<12} {len(r.ground_truth):>4} {len(r.detected):>4} "
              f"{len(r.true_positives):>4} {len(r.false_positives):>4} {len(r.false_negatives):>4} "
              f"{r.precision:>6.1%} {r.recall:>6.1%} {r.f1_score:>6.1%} {r.processing_time:>5.1f}s")
    
    # 過度檢測分析
    if total_fp > 0:
        print(f"\n⚠️  Over-Detection Analysis | 過度檢測分析")
        print("-" * 60)
        fp_by_type = defaultdict(list)
        for r in results:
            for fp in r.false_positives:
                fp_by_type[fp.phi_type].append((r.case_id, fp.content))
        
        for phi_type, items in sorted(fp_by_type.items(), key=lambda x: -len(x[1])):
            print(f"\n  {phi_type}: {len(items)} 次過度檢測")
            for case_id, content in items[:5]:  # 只顯示前 5 個
                print(f"    - [{case_id}] \"{content[:30]}{'...' if len(content) > 30 else ''}\"")
            if len(items) > 5:
                print(f"    ... 還有 {len(items)-5} 個")
    
    # 漏檢分析
    if total_fn > 0:
        print(f"\n❌ Missed Detection Analysis | 漏檢分析")
        print("-" * 60)
        fn_by_type = defaultdict(list)
        for r in results:
            for fn in r.false_negatives:
                fn_by_type[fn.phi_type].append((r.case_id, fn.content))
        
        for phi_type, items in sorted(fn_by_type.items(), key=lambda x: -len(x[1])):
            print(f"\n  {phi_type}: {len(items)} 次漏檢")
            for case_id, content in items[:5]:
                print(f"    - [{case_id}] \"{content[:30]}{'...' if len(content) > 30 else ''}\"")
            if len(items) > 5:
                print(f"    ... 還有 {len(items)-5} 個")
    
    # 評分等級
    print(f"\n🏆 Performance Grade | 效能等級")
    print("-" * 40)
    if f1 >= 0.9:
        grade = "A+ (Excellent)"
    elif f1 >= 0.8:
        grade = "A (Very Good)"
    elif f1 >= 0.7:
        grade = "B (Good)"
    elif f1 >= 0.6:
        grade = "C (Acceptable)"
    elif f1 >= 0.5:
        grade = "D (Needs Improvement)"
    else:
        grade = "F (Poor)"
    
    print(f"  Overall Grade: {grade}")
    print(f"  Note: MiniMind is a 104M parameter model")
    print(f"        For production, consider Qwen 2.5 7B+")
    
    print("\n" + "=" * 80)


def main():
    """主函數"""
    # Fix Windows encoding
    import io
    import argparse
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    
    # Parse arguments
    parser = argparse.ArgumentParser(description='Evaluate PHI detection performance')
    parser.add_argument('--model', type=str, default='minimind', 
                        choices=['minimind', 'llama', 'qwen'],
                        help='Model to evaluate: minimind, llama, qwen')
    args = parser.parse_args()
    
    print(f"[Loading] {args.model} model...")
    
    # Import and create LLM
    from medical_deidentification.infrastructure.llm import LLMPresets, create_llm
    
    try:
        if args.model == 'minimind':
            llm = create_llm(LLMPresets.local_minimind())
            model_name = "jingyaogong/minimind2 (104M)"
        elif args.model == 'llama':
            llm = create_llm(LLMPresets.local_llama())
            model_name = "llama3.1:8b (8B)"
        elif args.model == 'qwen':
            llm = create_llm(LLMPresets.local_qwen())
            model_name = "qwen2.5:7b (7B)"
        else:
            llm = create_llm(LLMPresets.local_minimind())
            model_name = "jingyaogong/minimind2 (104M)"
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        logger.info("Make sure Ollama is running and model is installed")
        return
    
    # Load test data
    test_file = Path("data/test/test_phi_tagged_cases.xlsx")
    if not test_file.exists():
        logger.error(f"Test file not found: {test_file}")
        return
    
    print(f"[Data] Loading test data from {test_file}")
    df = pd.read_excel(test_file)
    
    print(f"[Info] Testing ALL {len(df)} cases for complete evaluation")
    
    results = []
    
    # Process each case
    for idx, row in df.iterrows():
        case_id = row['Case ID']
        
        # 合併所有文本欄位
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
        
        # 解析標準答案
        ground_truth = parse_phi_tags(full_text_with_tags)
        
        # 移除標記，準備送給 LLM
        clean_text = remove_phi_tags(full_text_with_tags)
        
        print(f"\n🔍 Processing {case_id} ({len(ground_truth)} PHI in ground truth)...")
        
        # 執行 MiniMind 檢測
        detected, elapsed = run_minimind_detection(clean_text, llm)
        
        # 評估結果
        result = evaluate_case(case_id, ground_truth, detected)
        result.processing_time = elapsed
        results.append(result)
        
        print(f"   Detected: {len(detected)}, TP: {len(result.true_positives)}, "
              f"FP: {len(result.false_positives)}, FN: {len(result.false_negatives)}, "
              f"Time: {elapsed:.1f}s")
    
    # 列印完整報告
    print_evaluation_report(results, model_name)
    
    # 儲存結果
    output_file = Path(f"data/output/reports/{args.model}_evaluation_report.json")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    report_data = {
        "model": model_name,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "summary": {
            "total_cases": len(results),
            "total_ground_truth": sum(len(r.ground_truth) for r in results),
            "total_detected": sum(len(r.detected) for r in results),
            "total_tp": sum(len(r.true_positives) for r in results),
            "total_fp": sum(len(r.false_positives) for r in results),
            "total_fn": sum(len(r.false_negatives) for r in results),
            "precision": sum(len(r.true_positives) for r in results) / max(1, sum(len(r.detected) for r in results)),
            "recall": sum(len(r.true_positives) for r in results) / max(1, sum(len(r.ground_truth) for r in results)),
        },
        "cases": [
            {
                "case_id": r.case_id,
                "ground_truth_count": len(r.ground_truth),
                "detected_count": len(r.detected),
                "tp": len(r.true_positives),
                "fp": len(r.false_positives),
                "fn": len(r.false_negatives),
                "precision": r.precision,
                "recall": r.recall,
                "f1": r.f1_score,
                "time": r.processing_time,
                "false_positives": [{"type": p.phi_type, "content": p.content} for p in r.false_positives],
                "false_negatives": [{"type": p.phi_type, "content": p.content} for p in r.false_negatives],
            }
            for r in results
        ]
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(report_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n📄 Report saved to: {output_file}")


if __name__ == "__main__":
    main()
