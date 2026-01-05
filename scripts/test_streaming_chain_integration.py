#!/usr/bin/env python3
"""
Streaming PHI Chain Integration Test
串流 PHI Chain 整合測試

使用 tagged test data 測試 streaming chain 的完整運作流程
"""

import json
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
from loguru import logger

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.infrastructure.llm.factory import create_llm
from core.infrastructure.rag.chains.streaming_phi_chain import (
    StreamingPHIChain,
    StreamingPHIConfig,
)
from scripts.generators.phi_tag_parser import calculate_metrics, parse_phi_tags

# Configure output paths
OUTPUT_DIR = PROJECT_ROOT / "data" / "output" / "streaming_results"
REPORT_DIR = PROJECT_ROOT / "data" / "output" / "reports"
CHECKPOINT_DIR = PROJECT_ROOT / "data" / "output" / "checkpoints"

# Test data path
TEST_DATA_PATH = PROJECT_ROOT / "data" / "test" / "test_phi_tagged_cases.xlsx"


def setup_directories():
    """Create necessary output directories"""
    for dir_path in [OUTPUT_DIR, REPORT_DIR, CHECKPOINT_DIR]:
        dir_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created/verified directory: {dir_path}")


def load_test_data() -> pd.DataFrame:
    """Load tagged PHI test data"""
    logger.info(f"Loading test data from: {TEST_DATA_PATH}")
    df = pd.read_excel(TEST_DATA_PATH)
    logger.info(f"Loaded {len(df)} test cases")
    return df


def extract_case_text(row: pd.Series) -> str:
    """
    Extract all text columns from a test case row
    合併所有文本列
    """
    text_columns = [
        'Clinical Summary\n(含標記的 PHI)',
        'Contact Info\n(含標記的聯絡資訊)',
        'Medical History\n(含標記的時間/地點)',
        'Treatment Notes\n(含標記的醫師/日期)',
    ]

    parts = []
    for col in text_columns:
        if col in row and pd.notna(row[col]):
            parts.append(str(row[col]))

    return "\n\n".join(parts)


def remove_phi_tags(text: str) -> tuple[str, list[dict]]:
    """
    Remove PHI tags from text and return clean text with ground truth
    移除 PHI 標記，返回乾淨文本和標準答案
    """
    # First extract ground truth
    ground_truth = parse_phi_tags(text)

    # Remove tags but keep content
    pattern = r'【PHI:(\w+):?(\w*)】([^【]+?)【/PHI】'
    clean_text = re.sub(pattern, r'\3', text)

    # Update positions for clean text
    for i, phi in enumerate(ground_truth):
        content = phi['content']
        # Find actual position in clean text
        pos = clean_text.find(content)
        if pos >= 0:
            ground_truth[i]['clean_start'] = pos
            ground_truth[i]['clean_end'] = pos + len(content)

    return clean_text, ground_truth


def create_streaming_chain(enable_rag: bool = False, enable_tools: bool = False) -> StreamingPHIChain:
    """
    Create streaming PHI chain with qwen2.5:1.5b model
    使用 qwen2.5:1.5b 模型創建 streaming chain
    
    Note: minimind is too small (104M) for PHI identification
    """
    # Use qwen2.5:1.5b - small but capable for structured tasks
    from core.infrastructure.llm.config import LLMConfig
    llm_config = LLMConfig(
        provider="ollama",
        model_name="qwen2.5:1.5b",
        temperature=0.0,
        timeout=120.0,
    )
    llm = create_llm(llm_config)

    config = StreamingPHIConfig(
        chunk_size=1500,  # Smaller chunks for better granularity
        chunk_overlap=100,
        llm_config=llm_config,
        use_structured_output=True,  # Use LangChain with_structured_output
        enable_rag=enable_rag,
        enable_tools=enable_tools,
        checkpoint_dir=str(CHECKPOINT_DIR),
        checkpoint_interval=1,
        output_dir=str(OUTPUT_DIR),
        output_format="jsonl",
    )

    chain = StreamingPHIChain(
        llm=llm,
        config=config,
        regulation_chain=None,  # No RAG for now
        tools=[],  # No tools for now
    )

    return chain


def convert_detected_to_comparable(entities: list[Any]) -> list[dict]:
    """
    Convert detected PHI entities to comparable format
    轉換檢測結果為可比較格式
    """
    detected = []
    for entity in entities:
        if hasattr(entity, 'type') and hasattr(entity, 'text'):
            phi_type = entity.type.value if hasattr(entity.type, 'value') else str(entity.type)
            detected.append({
                'type': phi_type,
                'content': entity.text,
                'start': getattr(entity, 'start_pos', 0),
                'end': getattr(entity, 'end_pos', 0),
                'confidence': getattr(entity, 'confidence', 0.8),
            })
    return detected


def run_single_case_test(
    chain: StreamingPHIChain,
    case_id: str,
    raw_text: str,
) -> dict[str, Any]:
    """
    Run streaming chain on a single test case
    對單個測試案例執行 streaming chain
    """
    logger.info(f"\n{'='*60}")
    logger.info(f"Processing Case: {case_id}")
    logger.info(f"{'='*60}")

    # Clean text and get ground truth
    clean_text, ground_truth = remove_phi_tags(raw_text)
    logger.info(f"Ground truth PHI count: {len(ground_truth)}")
    logger.info(f"Clean text length: {len(clean_text)} chars")

    # Process with streaming chain
    start_time = time.time()
    all_entities = []
    chunk_count = 0
    total_tool_calls = 0

    try:
        for result in chain.process_text(clean_text, text_id=case_id, resume=False):
            chunk_count += 1
            logger.info(
                f"  Chunk {result.chunk_id}: "
                f"entities={len(result.entities)}, "
                f"success={result.success}, "
                f"time={result.processing_time_ms:.1f}ms"
            )

            if result.success:
                all_entities.extend(result.entities)
                total_tool_calls += result.tool_calls_made
            else:
                logger.warning(f"  Chunk {result.chunk_id} failed: {result.error}")

    except Exception as e:
        logger.error(f"Error processing case {case_id}: {e}")
        import traceback
        traceback.print_exc()
        return {
            "case_id": case_id,
            "success": False,
            "error": str(e),
        }

    processing_time = time.time() - start_time

    # Convert detected entities for comparison
    detected = convert_detected_to_comparable(all_entities)

    # Calculate metrics
    metrics = calculate_metrics(ground_truth, detected)

    # Build result
    result = {
        "case_id": case_id,
        "success": True,
        "text_length": len(clean_text),
        "chunk_count": chunk_count,
        "processing_time_sec": round(processing_time, 2),
        "ground_truth_count": len(ground_truth),
        "detected_count": len(detected),
        "tool_calls_total": total_tool_calls,
        "metrics": metrics,
        "ground_truth": ground_truth,
        "detected": detected,
    }

    # Log summary
    logger.info(f"\n--- Case {case_id} Summary ---")
    logger.info(f"  Ground Truth: {len(ground_truth)} PHI")
    logger.info(f"  Detected: {len(detected)} PHI")
    logger.info(f"  Precision: {metrics['Precision']:.2%}")
    logger.info(f"  Recall: {metrics['Recall']:.2%}")
    logger.info(f"  F1: {metrics['F1']:.2%}")
    logger.info(f"  Processing Time: {processing_time:.2f}s")

    return result


def generate_report(results: list[dict], output_path: Path) -> dict[str, Any]:
    """
    Generate comprehensive test report
    生成完整測試報告
    """
    total_cases = len(results)
    successful_cases = sum(1 for r in results if r.get("success", False))

    # Aggregate metrics
    total_gt = sum(r.get("ground_truth_count", 0) for r in results if r.get("success"))
    total_detected = sum(r.get("detected_count", 0) for r in results if r.get("success"))
    total_tp = sum(r.get("metrics", {}).get("TP", 0) for r in results if r.get("success"))
    total_fp = sum(r.get("metrics", {}).get("FP", 0) for r in results if r.get("success"))
    total_fn = sum(r.get("metrics", {}).get("FN", 0) for r in results if r.get("success"))

    overall_precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0
    overall_recall = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0
    overall_f1 = 2 * overall_precision * overall_recall / (overall_precision + overall_recall) if (overall_precision + overall_recall) > 0 else 0

    total_time = sum(r.get("processing_time_sec", 0) for r in results if r.get("success"))
    avg_time = total_time / successful_cases if successful_cases > 0 else 0

    report = {
        "test_run_info": {
            "timestamp": datetime.now().isoformat(),
            "test_data_path": str(TEST_DATA_PATH),
            "output_dir": str(OUTPUT_DIR),
        },
        "summary": {
            "total_cases": total_cases,
            "successful_cases": successful_cases,
            "failed_cases": total_cases - successful_cases,
            "total_ground_truth_phi": total_gt,
            "total_detected_phi": total_detected,
        },
        "overall_metrics": {
            "true_positives": total_tp,
            "false_positives": total_fp,
            "false_negatives": total_fn,
            "precision": round(overall_precision, 4),
            "recall": round(overall_recall, 4),
            "f1_score": round(overall_f1, 4),
        },
        "performance": {
            "total_processing_time_sec": round(total_time, 2),
            "average_time_per_case_sec": round(avg_time, 2),
        },
        "case_details": results,
    }

    # Write report
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False, default=str)

    logger.info(f"\nReport saved to: {output_path}")

    return report


def print_final_summary(report: dict[str, Any]):
    """Print final test summary"""
    print("\n" + "="*70)
    print("STREAMING PHI CHAIN INTEGRATION TEST - FINAL SUMMARY")
    print("="*70)

    summary = report["summary"]
    metrics = report["overall_metrics"]
    perf = report["performance"]

    print("\n📊 Test Cases:")
    print(f"   Total: {summary['total_cases']}")
    print(f"   Successful: {summary['successful_cases']}")
    print(f"   Failed: {summary['failed_cases']}")

    print("\n📋 PHI Detection:")
    print(f"   Ground Truth PHI: {summary['total_ground_truth_phi']}")
    print(f"   Detected PHI: {summary['total_detected_phi']}")

    print("\n📈 Overall Metrics:")
    print(f"   Precision: {metrics['precision']:.2%}")
    print(f"   Recall: {metrics['recall']:.2%}")
    print(f"   F1 Score: {metrics['f1_score']:.2%}")

    print("\n⏱️  Performance:")
    print(f"   Total Time: {perf['total_processing_time_sec']:.2f}s")
    print(f"   Avg per Case: {perf['average_time_per_case_sec']:.2f}s")

    print("\n📁 Output Files:")
    print(f"   Results: {OUTPUT_DIR}")
    print(f"   Report: {REPORT_DIR}")
    print("="*70)


def main():
    """Main test runner"""
    logger.info("="*70)
    logger.info("Starting Streaming PHI Chain Integration Test")
    logger.info("="*70)

    # Setup
    setup_directories()

    # Load test data
    df = load_test_data()

    # Create streaming chain
    logger.info("\nInitializing Streaming PHI Chain with minimind...")
    chain = create_streaming_chain(enable_rag=False, enable_tools=False)

    # Run tests
    results = []

    for idx, row in df.iterrows():
        case_id = row['Case ID']
        raw_text = extract_case_text(row)

        result = run_single_case_test(chain, case_id, raw_text)
        results.append(result)

        # Small delay between cases to avoid overwhelming the LLM
        time.sleep(0.5)

    # Generate report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = REPORT_DIR / f"streaming_chain_test_{timestamp}.json"
    report = generate_report(results, report_path)

    # Print final summary
    print_final_summary(report)

    # Also save latest report reference
    latest_report_path = REPORT_DIR / "streaming_chain_test_latest.json"
    with open(latest_report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False, default=str)

    logger.info(f"\nLatest report also saved to: {latest_report_path}")
    logger.info("\n✅ Integration test completed!")

    return report


if __name__ == "__main__":
    main()
