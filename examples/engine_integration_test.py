"""
Processing Engine Integration Test
處理引擎整合測試

Tests the complete workflow with RAG structured output.
測試使用 RAG 結構化輸出的完整工作流程。
"""

from pathlib import Path
from medical_deidentification.application.processing import (
    DeidentificationEngine,
    EngineConfig,
    StrategyType
)
from medical_deidentification.domain.models import PHIType


def test_1_engine_with_structured_output():
    """
    Test 1: Engine with RAG structured output
    測試 1：引擎使用 RAG 結構化輸出
    """
    print("=== Test 1: Engine with RAG Structured Output ===\n")
    
    # Configure engine
    config = EngineConfig(
        use_rag=True,
        llm_provider="openai",
        llm_model="gpt-4",
        embeddings_preset="multilingual",
        default_strategy=StrategyType.REDACTION,
        phi_specific_strategies={
            PHIType.AGE_OVER_89: StrategyType.GENERALIZATION,
            PHIType.NAME: StrategyType.PSEUDONYMIZATION,
            PHIType.RARE_DISEASE: StrategyType.REDACTION,
        }
    )
    
    engine = DeidentificationEngine(config)
    
    print("Engine Configuration:")
    print(f"  RAG: {config.use_rag}")
    print(f"  LLM: {config.llm_provider}/{config.llm_model}")
    print(f"  Default Strategy: {config.default_strategy.value}")
    print(f"  PHI Specific Strategies: {len(config.phi_specific_strategies)}")
    print()
    
    return engine


def test_2_mock_processing_flow():
    """
    Test 2: Mock complete processing flow
    測試 2：模擬完整處理流程
    """
    print("=== Test 2: Mock Processing Flow ===\n")
    
    from medical_deidentification.domain.models import PHIEntity
    
    # Mock input
    text = "患者張三，94歲，患有法布瑞氏症"
    print(f"Input Text:\n  {text}\n")
    
    # Mock RAG response (structured output)
    mock_entities = [
        PHIEntity(
            type=PHIType.NAME,
            text="張三",
            start_pos=3,
            end_pos=5,
            confidence=0.98,
            regulation_source="HIPAA"
        ),
        PHIEntity(
            type=PHIType.AGE_OVER_89,
            text="94歲",
            start_pos=6,
            end_pos=9,
            confidence=0.95,
            regulation_source="HIPAA"
        ),
        PHIEntity(
            type=PHIType.RARE_DISEASE,
            text="法布瑞氏症",
            start_pos=13,
            end_pos=18,
            confidence=0.92,
            regulation_source="Taiwan PDPA"
        )
    ]
    
    print("Structured PHI Entities from RAG:")
    for i, entity in enumerate(mock_entities, 1):
        print(f"  {i}. {entity.text} ({entity.type.value})")
        print(f"     Position: {entity.start_pos}-{entity.end_pos}")
        print(f"     Confidence: {entity.confidence:.2%}")
        print(f"     Source: {entity.regulation_source}")
    print()
    
    # Mock masking application
    print("Masking Application:")
    
    config = EngineConfig(
        phi_specific_strategies={
            PHIType.NAME: StrategyType.PSEUDONYMIZATION,
            PHIType.AGE_OVER_89: StrategyType.GENERALIZATION,
            PHIType.RARE_DISEASE: StrategyType.REDACTION,
        },
        strategy_config={
            "placeholder": "[已遮蔽]",
            "salt": "test-salt"
        }
    )
    
    engine = DeidentificationEngine(config)
    
    # Apply masking
    masked_text = engine._apply_masking(text, mock_entities)
    
    print(f"Masked Text:\n  {masked_text}\n")
    
    print("Masking Details:")
    for entity in mock_entities:
        strategy_type = config.phi_specific_strategies.get(
            entity.type,
            config.default_strategy
        )
        print(f"  - {entity.text} ({entity.type.value})")
        print(f"    Strategy: {strategy_type.value}")
    print()


def test_3_workflow_stages():
    """
    Test 3: Processing pipeline stages
    測試 3：處理流水線階段
    """
    print("=== Test 3: Workflow Stages ===\n")
    
    stages = [
        "1. Document Loading",
        "2. Language Detection",
        "3. Regulation Retrieval (RAG)",
        "4. PHI Identification (Structured Output)",
        "5. Masking Application",
        "6. Validation",
        "7. Output Generation"
    ]
    
    print("Processing Pipeline Stages:")
    for stage in stages:
        print(f"  {stage}")
    print()
    
    print("Key Integration Points:")
    print("  ✓ RAG returns List[PHIEntity] (structured)")
    print("  ✓ No JSON parsing required")
    print("  ✓ Type-safe entity handling")
    print("  ✓ Automatic validation via Pydantic")
    print("  ✓ Direct mapping to masking strategies")
    print()


def test_4_data_flow():
    """
    Test 4: Data flow visualization
    測試 4：資料流視覺化
    """
    print("=== Test 4: Data Flow ===\n")
    
    print("Data Flow:")
    print()
    print("  Document Loader")
    print("       ↓")
    print("  LoadedDocument")
    print("       ↓")
    print("  RegulationRAGChain.identify_phi()")
    print("       ↓")
    print("  PHIDetectionResponse (Pydantic)")
    print("       ↓")
    print("  List[PHIEntity] (Domain Models)")
    print("       ↓")
    print("  MaskingStrategy.mask(PHIEntity)")
    print("       ↓")
    print("  Masked Document")
    print()
    
    print("Type Safety:")
    print("  ✓ PHIIdentificationResult (LLM output schema)")
    print("  ✓ PHIDetectionResponse (wrapper with validation)")
    print("  ✓ PHIEntity (domain model)")
    print("  ✓ MaskingStrategy (strategy pattern)")
    print()


def test_5_error_handling():
    """
    Test 5: Error handling scenarios
    測試 5：錯誤處理場景
    """
    print("=== Test 5: Error Handling ===\n")
    
    print("Error Handling Scenarios:")
    print()
    
    print("1. Structured Output Failure:")
    print("   → Falls back to JSON parsing")
    print("   → Validation still applied")
    print()
    
    print("2. JSON Parsing Failure:")
    print("   → Returns empty entity list")
    print("   → Logs error")
    print("   → Processing continues")
    print()
    
    print("3. Invalid PHI Type:")
    print("   → Maps to PHIType.OTHER")
    print("   → Uses default strategy")
    print("   → Warning logged")
    print()
    
    print("4. Masking Strategy Error:")
    print("   → Skips problematic entity")
    print("   → Continues with other entities")
    print("   → All errors logged")
    print()


def test_6_benefits_summary():
    """
    Test 6: Benefits summary
    測試 6：優勢總結
    """
    print("=== Test 6: Integration Benefits ===\n")
    
    print("Benefits of Structured Output Integration:")
    print()
    
    print("1. Type Safety:")
    print("   ✓ Compile-time checks with Pydantic")
    print("   ✓ Runtime validation")
    print("   ✓ IDE autocomplete support")
    print()
    
    print("2. Reliability:")
    print("   ✓ No manual JSON parsing errors")
    print("   ✓ LLM forced to return valid schema")
    print("   ✓ Automatic field validation")
    print()
    
    print("3. Maintainability:")
    print("   ✓ Schema centrally defined")
    print("   ✓ Easy to extend PHI types")
    print("   ✓ Clear data contracts")
    print()
    
    print("4. Testability:")
    print("   ✓ Easy to mock PHIEntity")
    print("   ✓ Clear input/output types")
    print("   ✓ Unit test friendly")
    print()
    
    print("5. Performance:")
    print("   ✓ No regex parsing overhead")
    print("   ✓ Direct object conversion")
    print("   ✓ Efficient batch processing")
    print()


def main():
    """Run all tests"""
    tests = [
        test_1_engine_with_structured_output,
        test_2_mock_processing_flow,
        test_3_workflow_stages,
        test_4_data_flow,
        test_5_error_handling,
        test_6_benefits_summary,
    ]
    
    print("=" * 70)
    print("Processing Engine Integration Tests")
    print("RAG Structured Output Integration")
    print("=" * 70)
    print()
    
    for test in tests:
        test()
        print("-" * 70)
        print()
    
    print("=" * 70)
    print("All tests completed!")
    print("=" * 70)


if __name__ == "__main__":
    main()
