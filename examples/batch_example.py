#!/usr/bin/env python3
"""
📦 Batch Processing Example - 批次處理範例
==========================================

處理 Excel/CSV 檔案中的多筆醫療記錄。

Prerequisites:
    1. pip install -e .
    2. ollama pull granite4:1b
    
Usage:
    python examples/batch_example.py
    python examples/batch_example.py --file your_data.xlsx
    python examples/batch_example.py --rows 10  # Only first 10 rows
"""

import argparse
from pathlib import Path

from loguru import logger
from core.infrastructure.llm import LLMConfig
from core.infrastructure.rag import PHIIdentificationChain, PHIIdentificationConfig
from core.application.processing import (
    BatchPHIProcessor,
    BatchProcessingConfig,
    save_batch_results,
)


def main():
    parser = argparse.ArgumentParser(description="Batch PHI Processing")
    parser.add_argument("--file", type=str, default="data/test/test_complex_phi_cases.xlsx")
    parser.add_argument("--rows", type=int, default=None, help="Max rows to process")
    parser.add_argument("--model", type=str, default="granite4:1b", help="Ollama model")
    args = parser.parse_args()
    
    print("=" * 60)
    print("📦 Batch PHI Processing")
    print("=" * 60)
    
    # Check file
    test_file = Path(args.file)
    if not test_file.exists():
        logger.error(f"❌ File not found: {test_file}")
        return 1
    
    print(f"\n📁 File: {test_file}")
    print(f"🤖 Model: {args.model}")
    print(f"📊 Max rows: {args.rows or 'All'}")
    
    # ============= Configuration =============
    
    # LLM config (local Ollama)
    llm_config = LLMConfig(
        provider="ollama",
        model_name=args.model,
        temperature=0.0,
        timeout=180,
    )
    
    # PHI identification config
    phi_config = PHIIdentificationConfig(
        llm_config=llm_config,
        retrieve_regulation_context=False,
        use_structured_output=True,
    )
    
    # Batch processing config
    batch_config = BatchProcessingConfig(
        max_rows=args.rows,
        language="zh-TW",
        skip_empty_rows=True,
        combine_columns=True,
        log_progress_interval=1,
    )
    
    # ============= Initialize =============
    
    print("\n🔧 Initializing...")
    phi_chain = PHIIdentificationChain(config=phi_config, max_text_length=4000)
    processor = BatchPHIProcessor(phi_chain, batch_config)
    
    # ============= Process =============
    
    print("\n" + "=" * 60)
    print("🚀 Processing...")
    print("=" * 60)
    
    result = processor.process_excel_file(str(test_file), case_id_column="case_id")
    
    # ============= Results =============
    
    print("\n" + "=" * 60)
    print("✅ RESULTS")
    print("=" * 60)
    
    print(f"""
📊 Processing Statistics:
   Total rows:      {result.total_rows}
   Processed:       {result.processed_rows}
   PHI entities:    {result.total_entities}
   Total time:      {result.total_time:.2f}s
   Avg per row:     {result.average_time_per_row:.2f}s
""")
    
    # PHI type distribution
    print("📈 PHI Type Distribution:")
    distribution = result.get_phi_type_distribution()
    for phi_type, count in sorted(distribution.items(), key=lambda x: -x[1]):
        print(f"   {phi_type:25s}: {count:3d}")
    
    # Save results
    if result.processed_rows > 0:
        saved_paths = save_batch_results([result], generate_report=True)
        print(f"\n💾 Results saved:")
        print(f"   Excel:  {saved_paths.get('result')}")
        if 'report' in saved_paths:
            print(f"   Report: {saved_paths.get('report')}")
    
    print("\n" + "=" * 60)
    print("✨ Done!")
    print("=" * 60)
    
    return 0


if __name__ == "__main__":
    exit(main())
