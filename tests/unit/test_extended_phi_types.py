"""
Test Extended PHI Types | 測試擴充的 PHI 類型

Unit tests for extended PHI type system including custom types.
擴充 PHI 類型系統的單元測試,包含自定義類型。
"""

import pytest

from core.domain import (
    CustomPHIType,
    PHIEntity,
    PHIType,
    RegulationContext,
)


class TestPHIType:
    """Test PHI Type enumeration | 測試 PHI 類型枚舉"""

    def test_standard_phi_types_count(self):
        """Test standard PHI types | 測試標準 PHI 類型"""
        standard_types = PHIType.get_standard_types()
        assert len(standard_types) >= 7  # At least 7 standard types

    def test_strict_phi_types_includes_additional(self):
        """Test strict mode includes additional types | 測試嚴格模式包含額外類型"""
        standard = PHIType.get_standard_types()
        strict = PHIType.get_strict_types()

        assert len(strict) > len(standard)
        assert PHIType.AGE_OVER_90 in strict
        assert PHIType.HOSPITAL_NAME in strict
        assert PHIType.RARE_DISEASE in strict

    def test_age_related_types(self):
        """Test age-related PHI types | 測試年齡相關 PHI 類型"""
        assert PHIType.is_age_related(PHIType.AGE_OVER_89)
        assert PHIType.is_age_related(PHIType.AGE_OVER_90)
        assert not PHIType.is_age_related(PHIType.NAME)

    def test_facility_related_types(self):
        """Test facility-related PHI types | 測試醫療機構相關 PHI 類型"""
        assert PHIType.is_facility_related(PHIType.HOSPITAL_NAME)
        assert PHIType.is_facility_related(PHIType.WARD_NUMBER)
        assert PHIType.is_facility_related(PHIType.BED_NUMBER)
        assert not PHIType.is_facility_related(PHIType.NAME)

    def test_extended_phi_types_exist(self):
        """Test that extended PHI types exist | 測試擴充的 PHI 類型存在"""
        # Healthcare facility types
        assert hasattr(PHIType, 'HOSPITAL_NAME')
        assert hasattr(PHIType, 'WARD_NUMBER')
        assert hasattr(PHIType, 'BED_NUMBER')

        # Strict age requirement
        assert hasattr(PHIType, 'AGE_OVER_90')

        # Medical conditions
        assert hasattr(PHIType, 'RARE_DISEASE')
        assert hasattr(PHIType, 'GENETIC_INFO')

        # Extended contact
        assert hasattr(PHIType, 'PHONE')
        assert hasattr(PHIType, 'EMAIL')


class TestCustomPHIType:
    """Test Custom PHI Type | 測試自定義 PHI 類型"""

    def test_create_valid_custom_type(self):
        """Test creating a valid custom PHI type | 測試建立有效的自定義 PHI 類型"""
        custom = CustomPHIType(
            name="RARE_DISEASE_CODE",
            description="ICD-10 codes for rare diseases",
            pattern=r"[A-Z]\d{2}\.\d{1,2}",
            examples=["G60.0", "E70.3"],
            regulation_source="Hospital Policy",
            is_high_risk=True
        )

        assert custom.name == "RARE_DISEASE_CODE"
        assert custom.is_high_risk
        assert len(custom.examples) == 2

    def test_empty_name_raises_error(self):
        """Test that empty name raises error | 測試空名稱會引發錯誤"""
        with pytest.raises(ValueError, match="name cannot be empty"):
            CustomPHIType(name="", description="test")

    def test_missing_description_raises_error(self):
        """Test that missing description raises error | 測試缺少描述會引發錯誤"""
        with pytest.raises(ValueError, match="description is required"):
            CustomPHIType(name="TEST", description="")


class TestPHIEntityExtended:
    """Test extended PHI Entity | 測試擴充的 PHI 實體"""

    def test_create_entity_with_strict_age(self):
        """Test creating entity with strict age requirement | 測試建立嚴格年齡要求的實體"""
        entity = PHIEntity(
            type=PHIType.AGE_OVER_90,
            text="95 years old",
            start_pos=0,
            end_pos=12,
            confidence=0.98
        )

        assert entity.type == PHIType.AGE_OVER_90
        assert entity.is_high_risk()  # Age over 90 is high risk

    def test_create_entity_with_hospital_name(self):
        """Test creating entity with hospital name | 測試建立醫院名稱實體"""
        entity = PHIEntity(
            type=PHIType.HOSPITAL_NAME,
            text="National Taiwan University Hospital",
            start_pos=0,
            end_pos=37,
            confidence=0.95
        )

        assert entity.type == PHIType.HOSPITAL_NAME

    def test_create_entity_with_rare_disease(self):
        """Test creating entity with rare disease | 測試建立罕見疾病實體"""
        entity = PHIEntity(
            type=PHIType.RARE_DISEASE,
            text="Fabry disease",
            start_pos=0,
            end_pos=13,
            confidence=0.90,
            regulation_source="High identification risk"
        )

        assert entity.type == PHIType.RARE_DISEASE
        assert entity.is_high_risk()

    def test_create_entity_with_custom_type(self):
        """Test creating entity with custom PHI type | 測試建立自定義 PHI 類型實體"""
        custom_type = CustomPHIType(
            name="RESEARCH_PROTOCOL_ID",
            description="Research protocol identifier",
            is_high_risk=True
        )

        entity = PHIEntity(
            type=PHIType.CUSTOM,
            text="PROTO-2024-001",
            start_pos=0,
            end_pos=15,
            confidence=0.92,
            custom_type=custom_type
        )

        assert entity.type == PHIType.CUSTOM
        assert entity.custom_type is not None
        assert entity.is_high_risk()  # Custom type is high risk

    def test_custom_type_without_custom_phi_raises_error(self):
        """Test that CUSTOM type without custom_type raises error | 測試 CUSTOM 類型沒有 custom_type 會引發錯誤"""
        with pytest.raises(ValueError, match="custom_type must be provided"):
            PHIEntity(
                type=PHIType.CUSTOM,
                text="test",
                start_pos=0,
                end_pos=4,
                confidence=0.9,
                custom_type=None  # Missing custom_type
            )

    def test_high_risk_detection(self):
        """Test high-risk PHI detection | 測試高風險 PHI 檢測"""
        # High-risk types
        assert PHIEntity(
            type=PHIType.RARE_DISEASE, text="test", start_pos=0, end_pos=4, confidence=0.9
        ).is_high_risk()

        assert PHIEntity(
            type=PHIType.AGE_OVER_90, text="test", start_pos=0, end_pos=4, confidence=0.9
        ).is_high_risk()

        assert PHIEntity(
            type=PHIType.GENETIC_INFO, text="test", start_pos=0, end_pos=4, confidence=0.9
        ).is_high_risk()

        # Non-high-risk types
        assert not PHIEntity(
            type=PHIType.DATE, text="test", start_pos=0, end_pos=4, confidence=0.9
        ).is_high_risk()


class TestRegulationContextExtended:
    """Test extended Regulation Context | 測試擴充的法規上下文"""

    def test_standard_strictness_level(self):
        """Test standard strictness level | 測試標準嚴格程度"""
        context = RegulationContext(
            applicable_regulations=["HIPAA"],
            retrieved_rules=["Standard rules"],
            masking_instructions=["Mask standard PHI"],
            strictness_level="standard"
        )

        phi_types = context.get_all_phi_types()
        assert PHIType.NAME in phi_types
        assert len(phi_types) == len(PHIType.get_standard_types())

    def test_strict_strictness_level(self):
        """Test strict strictness level | 測試嚴格程度"""
        context = RegulationContext(
            applicable_regulations=["HIPAA", "Hospital Policy"],
            retrieved_rules=["Strict rules"],
            masking_instructions=["Mask all sensitive PHI"],
            strictness_level="strict"
        )

        phi_types = context.get_all_phi_types()
        assert PHIType.AGE_OVER_90 in phi_types
        assert PHIType.HOSPITAL_NAME in phi_types
        assert PHIType.RARE_DISEASE in phi_types

    def test_custom_phi_types_in_context(self):
        """Test custom PHI types in regulation context | 測試法規上下文中的自定義 PHI 類型"""
        custom_type = CustomPHIType(
            name="INSTITUTIONAL_ID",
            description="Institution-specific identifier",
            regulation_source="Internal Policy"
        )

        context = RegulationContext(
            applicable_regulations=["Internal Policy"],
            retrieved_rules=["Custom rule"],
            masking_instructions=["Mask institutional IDs"],
            custom_phi_types=[custom_type]
        )

        assert context.requires_custom_types()
        assert len(context.custom_phi_types) == 1

    def test_required_phi_types_override(self):
        """Test required PHI types override default | 測試必需 PHI 類型覆蓋預設"""
        specific_types = [PHIType.NAME, PHIType.WARD_NUMBER, PHIType.RARE_DISEASE]

        context = RegulationContext(
            applicable_regulations=["Custom"],
            retrieved_rules=["Specific requirements"],
            masking_instructions=["Mask specific types"],
            required_phi_types=specific_types
        )

        result = context.get_all_phi_types()
        assert result == specific_types
        assert len(result) == 3
