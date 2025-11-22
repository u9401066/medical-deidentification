"""
Structured Output Demo
結構化輸出示範

Demonstrates the new structured output from RAG system.
示範新的 RAG 系統結構化輸出。
"""

from medical_deidentification.infrastructure.rag import (
    RegulationRAGChain,
    RegulationVectorStore,
    EmbeddingsManager,
    PHIIdentificationResult,
    PHIDetectionResponse
)
from medical_deidentification.domain.models import PHIEntity, PHIType


def demo_1_structured_output_basics():
    """
    Demo 1: Basic structured output
    示範 1：基本結構化輸出
    """
    print("=== Demo 1: Structured Output Basics ===\n")
    
    # Mock structured result (in production, comes from LLM)
    result = PHIIdentificationResult(
        entity_text="94歲",
        phi_type="AGE_OVER_89",
        start_position=10,
        end_position=13,
        confidence=0.95,
        reason="Age over 89 is identifiable under HIPAA Safe Harbor",
        regulation_source="HIPAA"
    )
    
    print("Structured Result:")
    print(f"  Text: {result.entity_text}")
    print(f"  Type: {result.phi_type}")
    print(f"  Position: {result.start_position}-{result.end_position}")
    print(f"  Confidence: {result.confidence:.2%}")
    print(f"  Reason: {result.reason}")
    print(f"  Source: {result.regulation_source}")
    print()
    
    # Convert to domain entity
    phi_entity = RegulationRAGChain._to_phi_entity(result)
    
    print("Domain Entity (PHIEntity):")
    print(f"  Type: {phi_entity.type.value}")
    print(f"  Text: {phi_entity.text}")
    print(f"  Position: {phi_entity.start_pos}-{phi_entity.end_pos}")
    print(f"  Confidence: {phi_entity.confidence:.2%}")
    print(f"  High Risk: {phi_entity.is_high_risk()}")
    print()


def demo_2_multiple_entities():
    """
    Demo 2: Multiple PHI entities detection
    示範 2：多個 PHI 實體檢測
    """
    print("=== Demo 2: Multiple Entities Detection ===\n")
    
    # Mock detection response
    response = PHIDetectionResponse(
        entities=[
            PHIIdentificationResult(
                entity_text="張三",
                phi_type="NAME",
                start_position=3,
                end_position=5,
                confidence=0.98,
                reason="Patient name is direct identifier",
                regulation_source="HIPAA"
            ),
            PHIIdentificationResult(
                entity_text="94歲",
                phi_type="AGE_OVER_89",
                start_position=6,
                end_position=9,
                confidence=0.95,
                reason="Age over 89 under HIPAA Safe Harbor",
                regulation_source="HIPAA"
            ),
            PHIIdentificationResult(
                entity_text="法布瑞氏症",
                phi_type="RARE_DISEASE",
                start_position=13,
                end_position=18,
                confidence=0.92,
                reason="Rare disease with high identification risk",
                regulation_source="Taiwan PDPA"
            )
        ],
        total_entities=3,
        has_phi=True
    )
    
    print(f"Detection Response:")
    print(f"  Total Entities: {response.total_entities}")
    print(f"  Has PHI: {response.has_phi}")
    print()
    
    print("Entities:")
    for i, entity in enumerate(response.entities, 1):
        print(f"  {i}. {entity.entity_text} ({entity.phi_type})")
        print(f"     Confidence: {entity.confidence:.2%}")
        print(f"     Source: {entity.regulation_source}")
        print()


def demo_3_phi_type_mapping():
    """
    Demo 3: PHI type mapping
    示範 3：PHI 類型映射
    """
    print("=== Demo 3: PHI Type Mapping ===\n")
    
    test_cases = [
        "NAME",
        "AGE_OVER_89",
        "name",  # lowercase
        "age over 89",  # with spaces
        "姓名",  # Chinese
        "年齡",  # Chinese
        "rare disease",
        "UNKNOWN_TYPE"  # fallback case
    ]
    
    print("PHI Type Mapping:")
    for test_input in test_cases:
        phi_type = RegulationRAGChain._map_phi_type(test_input)
        print(f"  '{test_input}' -> {phi_type.value}")
    print()


def demo_4_rag_integration():
    """
    Demo 4: Full RAG integration with structured output
    示範 4：完整 RAG 整合與結構化輸出
    """
    print("=== Demo 4: RAG Integration (Mock) ===\n")
    
    # In production, this would call actual RAG system
    text = "患者張三，94歲，患有法布瑞氏症，住台北市"
    
    print(f"Input Text:\n  {text}\n")
    
    # Mock RAG response (in production, from identify_phi())
    mock_response = {
        "text": text,
        "language": "zh-TW",
        "total_entities": 4,
        "has_phi": True,
        "entities": [
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
            ),
            PHIEntity(
                type=PHIType.LOCATION,
                text="台北市",
                start_pos=20,
                end_pos=23,
                confidence=0.88,
                regulation_source="Taiwan PDPA"
            )
        ]
    }
    
    print("RAG Response:")
    print(f"  Language: {mock_response['language']}")
    print(f"  Total Entities: {mock_response['total_entities']}")
    print(f"  Has PHI: {mock_response['has_phi']}")
    print()
    
    print("Detected PHI Entities:")
    for entity in mock_response['entities']:
        print(f"  - {entity.text} ({entity.type.value})")
        print(f"    Position: {entity.start_pos}-{entity.end_pos}")
        print(f"    Confidence: {entity.confidence:.2%}")
        print(f"    Source: {entity.regulation_source}")
        print(f"    High Risk: {entity.is_high_risk()}")
        print()


def demo_5_masking_with_entities():
    """
    Demo 5: Apply masking based on structured entities
    示範 5：基於結構化實體應用遮蔽
    """
    print("=== Demo 5: Masking with Structured Entities ===\n")
    
    text = "患者張三，94歲，患有法布瑞氏症"
    
    entities = [
        PHIEntity(
            type=PHIType.NAME,
            text="張三",
            start_pos=3,
            end_pos=5,
            confidence=0.98
        ),
        PHIEntity(
            type=PHIType.AGE_OVER_89,
            text="94歲",
            start_pos=6,
            end_pos=9,
            confidence=0.95
        ),
        PHIEntity(
            type=PHIType.RARE_DISEASE,
            text="法布瑞氏症",
            start_pos=11,
            end_pos=16,
            confidence=0.92
        )
    ]
    
    print(f"Original Text:\n  {text}\n")
    
    # Simple masking (in production, use MaskingStrategy)
    masked_text = text
    for entity in sorted(entities, key=lambda e: e.start_pos, reverse=True):
        masked_text = (
            masked_text[:entity.start_pos] +
            "[已遮蔽]" +
            masked_text[entity.end_pos:]
        )
    
    print(f"Masked Text:\n  {masked_text}\n")
    
    print("Masking Details:")
    for entity in entities:
        print(f"  - {entity.text} -> [已遮蔽] ({entity.type.value})")
    print()


def demo_6_validation():
    """
    Demo 6: Validation with structured output
    示範 6：結構化輸出驗證
    """
    print("=== Demo 6: Validation ===\n")
    
    # Valid result
    try:
        valid_result = PHIIdentificationResult(
            entity_text="張三",
            phi_type="NAME",
            start_position=10,
            end_position=12,
            confidence=0.95,
            reason="Patient name"
        )
        print("✓ Valid result created successfully")
        print(f"  {valid_result.entity_text} ({valid_result.phi_type})")
    except Exception as e:
        print(f"✗ Validation failed: {e}")
    print()
    
    # Invalid confidence
    try:
        invalid_confidence = PHIIdentificationResult(
            entity_text="測試",
            phi_type="NAME",
            start_position=0,
            end_position=2,
            confidence=1.5,  # Invalid: > 1.0
            reason="Test"
        )
        print("✗ Should have failed validation!")
    except Exception as e:
        print(f"✓ Correctly rejected invalid confidence: {e}")
    print()
    
    # Invalid position
    try:
        invalid_position = PHIIdentificationResult(
            entity_text="測試",
            phi_type="NAME",
            start_position=10,
            end_position=5,  # Invalid: end < start
            confidence=0.9,
            reason="Test"
        )
        print("✗ Should have failed validation!")
    except Exception as e:
        print(f"✓ Correctly rejected invalid position: {e}")
    print()


def main():
    """Run all demos"""
    demos = [
        demo_1_structured_output_basics,
        demo_2_multiple_entities,
        demo_3_phi_type_mapping,
        demo_4_rag_integration,
        demo_5_masking_with_entities,
        demo_6_validation,
    ]
    
    print("=" * 60)
    print("Structured Output Demonstration")
    print("結構化輸出示範")
    print("=" * 60)
    print()
    
    for demo in demos:
        demo()
        print("-" * 60)
        print()
    
    print("=" * 60)
    print("All demos completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
