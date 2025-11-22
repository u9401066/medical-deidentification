"""
Processing Engine Usage Examples
處理引擎使用範例

Demonstrates how to use the de-identification engine for complete workflows.
示範如何使用去識別化引擎進行完整工作流程。
"""

from pathlib import Path
from medical_deidentification.application.processing import (
    DeidentificationEngine,
    EngineConfig,
    ProcessingStatus,
    StrategyType,
    create_masking_strategy
)
from medical_deidentification.domain.models import PHIType


def example_1_basic_processing():
    """
    Example 1: Basic file processing
    範例 1：基本檔案處理
    """
    print("=== Example 1: Basic File Processing ===\n")
    
    # Create engine with default config
    engine = DeidentificationEngine()
    
    # Process single file
    result = engine.process_file(
        "data/test/test_medical_records_multilang.xlsx",
        job_name="basic-processing-test"
    )
    
    print(f"Job ID: {result.job_id}")
    print(f"Status: {result.status.value}")
    print(f"Documents: {result.processed_documents}/{result.total_documents}")
    print(f"PHI entities: {result.total_phi_entities}")
    print(f"Duration: {result.duration_seconds:.2f}s")
    print()


def example_2_custom_configuration():
    """
    Example 2: Custom engine configuration
    範例 2：自訂引擎配置
    """
    print("=== Example 2: Custom Configuration ===\n")
    
    # Configure engine
    config = EngineConfig(
        use_rag=True,
        llm_provider="openai",
        llm_model="gpt-4",
        embeddings_preset="multilingual",
        default_strategy=StrategyType.GENERALIZATION,
        validate_output=True
    )
    
    engine = DeidentificationEngine(config)
    
    print(f"Engine: {engine}")
    print(f"RAG enabled: {config.use_rag}")
    print(f"LLM: {config.llm_provider}/{config.llm_model}")
    print(f"Default strategy: {config.default_strategy.value}")
    print()


def example_3_phi_specific_strategies():
    """
    Example 3: PHI-type specific masking strategies
    範例 3：PHI 類型特定遮蔽策略
    """
    print("=== Example 3: PHI-Specific Strategies ===\n")
    
    # Configure different strategies for different PHI types
    config = EngineConfig(
        phi_specific_strategies={
            PHIType.AGE_OVER_89: StrategyType.GENERALIZATION,
            PHIType.NAME: StrategyType.PSEUDONYMIZATION,
            PHIType.DATE: StrategyType.DATE_SHIFTING,
            PHIType.PHONE: StrategyType.PARTIAL_MASKING,
            PHIType.SSN: StrategyType.REDACTION,
        },
        strategy_config={
            "placeholder": "[已遮蔽]",
            "salt": "my-secure-salt",
            "offset_days": 60,
            "keep_prefix": 3,
            "keep_suffix": 2
        }
    )
    
    engine = DeidentificationEngine(config)
    
    print("PHI-specific strategies configured:")
    for phi_type, strategy_type in config.phi_specific_strategies.items():
        print(f"  - {phi_type.value}: {strategy_type.value}")
    print()


def example_4_batch_processing():
    """
    Example 4: Batch process multiple files
    範例 4：批次處理多個檔案
    """
    print("=== Example 4: Batch Processing ===\n")
    
    engine = DeidentificationEngine()
    
    # Process multiple files
    file_paths = [
        "data/test/test_medical_records_multilang.xlsx",
        "data/test/test_complex_phi_cases.xlsx",
    ]
    
    result = engine.process_files(
        file_paths,
        job_name="batch-processing-test"
    )
    
    print(f"Job: {result.job_name}")
    print(f"Total files: {result.total_documents}")
    print(f"Processed: {result.processed_documents}")
    print(f"Failed: {result.failed_documents}")
    print(f"Success rate: {result.summary['success_rate']:.1%}")
    
    print("\nDocument details:")
    for doc_result in result.documents:
        print(f"  - {doc_result['filename']}: {doc_result['phi_entities_count']} PHI entities")
    print()


def example_5_directory_processing():
    """
    Example 5: Process all files in directory
    範例 5：處理目錄中的所有檔案
    """
    print("=== Example 5: Directory Processing ===\n")
    
    engine = DeidentificationEngine()
    
    # Process all Excel files in directory
    result = engine.process_directory(
        directory="data/test",
        pattern="*.xlsx",
        recursive=False,
        job_name="directory-scan"
    )
    
    print(f"Scanned directory: data/test")
    print(f"Files found: {result.total_documents}")
    print(f"Processed: {result.processed_documents}")
    print(f"Total PHI: {result.total_phi_entities}")
    print(f"Duration: {result.duration_seconds:.2f}s")
    print()


def example_6_stage_results():
    """
    Example 6: Inspect pipeline stage results
    範例 6：檢查流水線階段結果
    """
    print("=== Example 6: Stage Results ===\n")
    
    engine = DeidentificationEngine()
    
    result = engine.process_file(
        "data/test/test_medical_records_multilang.xlsx"
    )
    
    print("Pipeline stages:")
    for stage_result in result.stage_results:
        status = "✓" if stage_result["success"] else "✗"
        duration = stage_result.get("duration_seconds", 0)
        print(f"  {status} {stage_result['stage']}: {duration:.2f}s")
    print()


def example_7_error_handling():
    """
    Example 7: Error handling
    範例 7：錯誤處理
    """
    print("=== Example 7: Error Handling ===\n")
    
    engine = DeidentificationEngine()
    
    # Try to process non-existent file
    result = engine.process_files([
        "data/test/test_medical_records_multilang.xlsx",
        "nonexistent_file.txt",
        "data/test/test_complex_phi_cases.xlsx"
    ])
    
    print(f"Total files: {result.total_documents}")
    print(f"Failed: {result.failed_documents}")
    
    if result.errors:
        print(f"\nErrors ({len(result.errors)}):")
        for error in result.errors:
            print(f"  - {error['type']}: {error['message']}")
    print()


def example_8_without_rag():
    """
    Example 8: Processing without RAG
    範例 8：不使用 RAG 處理
    """
    print("=== Example 8: Without RAG ===\n")
    
    # Disable RAG
    config = EngineConfig(
        use_rag=False,
        default_strategy=StrategyType.REDACTION
    )
    
    engine = DeidentificationEngine(config)
    
    print("RAG disabled - using pattern matching only")
    
    result = engine.process_file(
        "data/test/test_medical_records_multilang.xlsx"
    )
    
    print(f"Status: {result.status.value}")
    print(f"Note: PHI identification may be limited without RAG")
    print()


def example_9_masking_strategies():
    """
    Example 9: Test different masking strategies
    範例 9：測試不同遮蔽策略
    """
    print("=== Example 9: Masking Strategies ===\n")
    
    from medical_deidentification.domain.models import PHIEntity, PHIType
    
    # Create mock PHI entity
    entity = PHIEntity(
        text="94歲",
        phi_type=PHIType.AGE_OVER_89,
        start_position=10,
        end_position=13,
        confidence=0.95
    )
    
    # Test different strategies
    strategies = [
        ("Redaction", StrategyType.REDACTION, {"placeholder": "[已刪除]"}),
        ("Generalization", StrategyType.GENERALIZATION, {}),
        ("Pseudonymization", StrategyType.PSEUDONYMIZATION, {"salt": "test"}),
        ("Partial Masking", StrategyType.PARTIAL_MASKING, {"keep_prefix": 1, "keep_suffix": 1}),
        ("Suppression", StrategyType.SUPPRESSION, {}),
    ]
    
    print(f"Original: {entity.text}")
    print("\nMasked results:")
    
    for name, strategy_type, config in strategies:
        strategy = create_masking_strategy(strategy_type, config)
        masked = strategy.mask(entity)
        print(f"  - {name}: {masked}")
    print()


def example_10_result_summary():
    """
    Example 10: Detailed result summary
    範例 10：詳細結果摘要
    """
    print("=== Example 10: Result Summary ===\n")
    
    engine = DeidentificationEngine()
    
    result = engine.process_file(
        "data/test/test_medical_records_multilang.xlsx",
        job_name="summary-test"
    )
    
    print("Processing Summary:")
    print(f"  Job ID: {result.job_id}")
    print(f"  Job Name: {result.summary['job_name']}")
    print(f"  Status: {result.summary['status']}")
    print(f"  Started: {result.summary['started_at']}")
    print(f"  Completed: {result.summary['completed_at']}")
    print(f"  Duration: {result.summary['processing_time_seconds']:.2f}s")
    print(f"  Success Rate: {result.summary['success_rate']:.1%}")
    
    print("\nStatistics:")
    print(f"  Total Documents: {result.total_documents}")
    print(f"  Processed: {result.processed_documents}")
    print(f"  Failed: {result.failed_documents}")
    print(f"  PHI Entities: {result.total_phi_entities}")
    
    print("\nDocuments:")
    for doc in result.documents:
        print(f"  - {doc['filename']}")
        print(f"    PHI: {doc['phi_entities_count']}")
        print(f"    Masked: {doc['masked']}")
        print(f"    Time: {doc['processing_time_seconds']:.2f}s")
    print()


def example_11_integration_workflow():
    """
    Example 11: Complete integration workflow
    範例 11：完整整合工作流程
    """
    print("=== Example 11: Integration Workflow ===\n")
    
    print("Step 1: Configure engine")
    config = EngineConfig(
        use_rag=True,
        llm_provider="openai",
        llm_model="gpt-4",
        phi_specific_strategies={
            PHIType.AGE_OVER_89: StrategyType.GENERALIZATION,
            PHIType.NAME: StrategyType.PSEUDONYMIZATION,
            PHIType.RARE_DISEASE: StrategyType.REDACTION,
        },
        validate_output=True
    )
    engine = DeidentificationEngine(config)
    print("✓ Engine configured\n")
    
    print("Step 2: Load documents")
    # Document loading handled by engine
    print("✓ Document loader ready\n")
    
    print("Step 3: Initialize RAG")
    # RAG initialized lazily on first use
    print("✓ RAG will be initialized on first use\n")
    
    print("Step 4: Process files")
    result = engine.process_file(
        "data/test/test_medical_records_multilang.xlsx",
        job_name="integration-test"
    )
    print(f"✓ Processed {result.processed_documents} documents\n")
    
    print("Step 5: Review results")
    print(f"  Status: {result.status.value}")
    print(f"  PHI found: {result.total_phi_entities}")
    print(f"  Errors: {len(result.errors)}")
    print()
    
    print("✓ Integration workflow complete!")
    print()


def example_12_export_results():
    """
    Example 12: Export masked results
    範例 12：匯出遮蔽結果
    """
    print("=== Example 12: Export Results ===\n")
    
    engine = DeidentificationEngine()
    
    result = engine.process_file(
        "data/test/test_medical_records_multilang.xlsx"
    )
    
    # Export to JSON
    import json
    
    output = {
        "job_id": result.job_id,
        "status": result.status.value,
        "documents": result.documents,
        "summary": result.summary
    }
    
    output_file = Path("output/processing_result.json")
    output_file.parent.mkdir(exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"Results exported to: {output_file}")
    print(f"File size: {output_file.stat().st_size} bytes")
    print()


def main():
    """Run all examples"""
    examples = [
        example_1_basic_processing,
        example_2_custom_configuration,
        example_3_phi_specific_strategies,
        example_4_batch_processing,
        example_5_directory_processing,
        example_6_stage_results,
        example_7_error_handling,
        example_8_without_rag,
        example_9_masking_strategies,
        example_10_result_summary,
        example_11_integration_workflow,
        example_12_export_results,
    ]
    
    print("=" * 60)
    print("Processing Engine Usage Examples")
    print("=" * 60)
    print()
    
    for i, example in enumerate(examples, 1):
        print(f"\n{'=' * 60}")
        try:
            example()
        except Exception as e:
            print(f"✗ Example {i} failed: {e}\n")
        
        if i < len(examples):
            input("Press Enter to continue to next example...")
    
    print("\n" + "=" * 60)
    print("All examples completed!")
    print("=" * 60)


if __name__ == "__main__":
    # Run specific example
    import sys
    
    if len(sys.argv) > 1:
        example_num = int(sys.argv[1])
        examples = [
            example_1_basic_processing,
            example_2_custom_configuration,
            example_3_phi_specific_strategies,
            example_4_batch_processing,
            example_5_directory_processing,
            example_6_stage_results,
            example_7_error_handling,
            example_8_without_rag,
            example_9_masking_strategies,
            example_10_result_summary,
            example_11_integration_workflow,
            example_12_export_results,
        ]
        
        if 1 <= example_num <= len(examples):
            examples[example_num - 1]()
        else:
            print(f"Invalid example number. Choose 1-{len(examples)}")
    else:
        # Run quick demo
        print("Running quick demo (first 3 examples)...\n")
        example_2_custom_configuration()
        example_3_phi_specific_strategies()
        example_9_masking_strategies()
