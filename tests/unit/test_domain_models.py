"""
Test Domain Models | 測試領域模型

Unit tests for domain layer models and value objects.
領域層模型與值物件的單元測試。
"""

import pytest
from datetime import datetime
from uuid import uuid4

from medical_deidentification.domain.models import (
    MedicalDocument,
    PHIEntity,
    PHIType,
    RegulationContext,
    DocumentMetadata,
    ValidationResult,
)


class TestPHIEntity:
    """Test PHI Entity value object | 測試 PHI 實體值物件"""
    
    def test_create_valid_phi_entity(self):
        """Test creating a valid PHI entity | 測試建立有效的 PHI 實體"""
        entity = PHIEntity(
            type=PHIType.NAME,
            text="John Doe",
            start_pos=0,
            end_pos=8,
            confidence=0.95,
            regulation_source="HIPAA Safe Harbor"
        )
        
        assert entity.type == PHIType.NAME
        assert entity.text == "John Doe"
        assert entity.confidence == 0.95
    
    def test_invalid_confidence_raises_error(self):
        """Test that invalid confidence raises error | 測試無效的信心度會引發錯誤"""
        with pytest.raises(ValueError, match="Confidence must be between"):
            PHIEntity(
                type=PHIType.NAME,
                text="John Doe",
                start_pos=0,
                end_pos=8,
                confidence=1.5  # Invalid
            )
    
    def test_invalid_position_raises_error(self):
        """Test that invalid position raises error | 測試無效的位置會引發錯誤"""
        with pytest.raises(ValueError, match="Invalid position range"):
            PHIEntity(
                type=PHIType.NAME,
                text="John Doe",
                start_pos=10,
                end_pos=5,  # End before start
                confidence=0.95
            )


class TestRegulationContext:
    """Test Regulation Context | 測試法規上下文"""
    
    def test_regulation_context_with_rules(self):
        """Test regulation context with retrieved rules | 測試有檢索規則的法規上下文"""
        context = RegulationContext(
            applicable_regulations=["HIPAA", "GDPR"],
            retrieved_rules=["Mask all names", "Redact dates"],
            masking_instructions=["Apply redaction to NAME entities"]
        )
        
        assert context.has_rules()
        assert len(context.retrieved_rules) == 2
    
    def test_regulation_context_without_rules(self):
        """Test regulation context without rules | 測試沒有規則的法規上下文"""
        context = RegulationContext(
            applicable_regulations=["HIPAA"],
            retrieved_rules=[],
            masking_instructions=[]
        )
        
        assert not context.has_rules()


class TestMedicalDocument:
    """Test Medical Document aggregate | 測試醫療文件聚合"""
    
    def test_create_medical_document(self):
        """Test creating a medical document | 測試建立醫療文件"""
        doc = MedicalDocument(
            original_text="Patient John Doe visited on 2024-01-15",
            metadata=DocumentMetadata(document_type="clinical_note")
        )
        
        assert doc.original_text == "Patient John Doe visited on 2024-01-15"
        assert doc.get_phi_count() == 0
        assert not doc.is_deidentified()
    
    def test_add_detected_entity(self):
        """Test adding detected PHI entity | 測試添加檢測到的 PHI 實體"""
        doc = MedicalDocument(original_text="Test text")
        
        entity = PHIEntity(
            type=PHIType.NAME,
            text="John Doe",
            start_pos=8,
            end_pos=16,
            confidence=0.95
        )
        
        doc.add_detected_entity(entity)
        assert doc.get_phi_count() == 1
        assert doc.detected_entities[0].text == "John Doe"
    
    def test_apply_deidentification(self):
        """Test applying de-identification | 測試應用去識別化"""
        doc = MedicalDocument(original_text="Patient John Doe")
        doc.apply_deidentification("Patient [NAME]")
        
        assert doc.is_deidentified()
        assert doc.deidentified_text == "Patient [NAME]"
    
    def test_apply_empty_deidentification_raises_error(self):
        """Test that empty de-identification raises error | 測試空的去識別化會引發錯誤"""
        doc = MedicalDocument(original_text="Test")
        
        with pytest.raises(ValueError, match="cannot be empty"):
            doc.apply_deidentification("")
    
    def test_set_regulation_context(self):
        """Test setting regulation context | 測試設置法規上下文"""
        doc = MedicalDocument(original_text="Test")
        context = RegulationContext(
            applicable_regulations=["HIPAA"],
            retrieved_rules=["Rule 1"],
            masking_instructions=["Mask names"]
        )
        
        doc.set_regulation_context(context)
        assert doc.regulation_context is not None
        assert doc.regulation_context.has_rules()
    
    def test_validation_workflow(self):
        """Test complete validation workflow | 測試完整的驗證工作流程"""
        doc = MedicalDocument(original_text="Patient data")
        doc.apply_deidentification("Patient [REDACTED]")
        
        validation_result = ValidationResult(
            is_valid=True,
            residual_phi_detected=[],
            precision=0.95,
            recall=0.92,
            f1_score=0.935
        )
        
        doc.set_validation_result(validation_result)
        assert doc.is_validated()
        assert doc.validation_result.f1_score == 0.935


class TestDocumentMetadata:
    """Test Document Metadata | 測試文件元數據"""
    
    def test_create_metadata_with_defaults(self):
        """Test creating metadata with default values | 測試使用預設值建立元數據"""
        metadata = DocumentMetadata(document_type="clinical_note")
        
        assert metadata.document_type == "clinical_note"
        assert metadata.language == "zh-TW"
        assert isinstance(metadata.created_at, datetime)
    
    def test_create_metadata_with_custom_fields(self):
        """Test creating metadata with custom fields | 測試使用自定義欄位建立元數據"""
        metadata = DocumentMetadata(
            document_type="discharge_summary",
            custom_fields={"hospital": "General Hospital", "department": "Cardiology"}
        )
        
        assert metadata.custom_fields["hospital"] == "General Hospital"


class TestValidationResult:
    """Test Validation Result | 測試驗證結果"""
    
    def test_successful_validation(self):
        """Test successful validation result | 測試成功的驗證結果"""
        result = ValidationResult(
            is_valid=True,
            residual_phi_detected=[],
            precision=1.0,
            recall=1.0,
            f1_score=1.0,
            compliance_status={"HIPAA": "compliant", "GDPR": "compliant"}
        )
        
        assert result.is_valid
        assert len(result.residual_phi_detected) == 0
        assert result.f1_score == 1.0
    
    def test_failed_validation_with_residual_phi(self):
        """Test failed validation with residual PHI | 測試有殘留 PHI 的失敗驗證"""
        residual = PHIEntity(
            type=PHIType.DATE,
            text="2024-01-15",
            start_pos=0,
            end_pos=10,
            confidence=0.8
        )
        
        result = ValidationResult(
            is_valid=False,
            residual_phi_detected=[residual],
            warnings=["Date not properly masked"]
        )
        
        assert not result.is_valid
        assert len(result.residual_phi_detected) == 1
        assert len(result.warnings) == 1
