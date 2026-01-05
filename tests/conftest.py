"""
Pytest Configuration | Pytest 配置

Shared fixtures and configuration for all tests.
所有測試的共享 fixtures 與配置。
"""

import pytest
from typing import Generator

from core.domain import (
    MedicalDocument,
    DocumentMetadata,
    PHIEntity,
    PHIType,
    SupportedLanguage,
    ValidationResult,
    RegulationContext,
)


@pytest.fixture
def sample_medical_text() -> str:
    """
    Sample medical text for testing (synthetic, not real PHI).
    測試用的範例醫療文本（合成的,非真實個資）。
    """
    return """
    Patient Name: John Doe
    Date of Birth: 1980-05-15
    Medical Record Number: MRN-123456
    Visit Date: 2024-01-15
    
    Chief Complaint: Patient presents with chest pain.
    
    History: 45-year-old male with history of hypertension.
    Lives in Taipei City, Taiwan.
    Contact: (02) 1234-5678
    
    Assessment: Stable angina.
    Plan: Schedule follow-up in 2 weeks.
    """


@pytest.fixture
def sample_document(sample_medical_text: str) -> MedicalDocument:
    """
    Sample medical document for testing.
    測試用的範例醫療文件。
    """
    metadata = DocumentMetadata(
        document_type="clinical_note",
        source="test_suite",
        language=SupportedLanguage.TRADITIONAL_CHINESE
    )
    return MedicalDocument(
        original_text=sample_medical_text,
        metadata=metadata
    )


@pytest.fixture
def sample_phi_entities() -> list[PHIEntity]:
    """
    Sample PHI entities for testing.
    測試用的範例 PHI 實體。
    """
    return [
        PHIEntity(
            type=PHIType.NAME,
            text="John Doe",
            start_pos=18,
            end_pos=26,
            confidence=0.95,
            regulation_source="HIPAA Safe Harbor"
        ),
        PHIEntity(
            type=PHIType.DATE,
            text="1980-05-15",
            start_pos=46,
            end_pos=56,
            confidence=0.98,
            regulation_source="HIPAA Safe Harbor"
        ),
        PHIEntity(
            type=PHIType.MEDICAL_RECORD_NUMBER,
            text="MRN-123456",
            start_pos=85,
            end_pos=95,
            confidence=0.99,
            regulation_source="HIPAA Safe Harbor"
        ),
    ]


@pytest.fixture
def deidentified_text() -> str:
    """
    De-identified version of sample text.
    範例文本的去識別化版本。
    """
    return """
    Patient Name: [NAME]
    Date of Birth: [DATE]
    Medical Record Number: [ID]
    Visit Date: [DATE]
    
    Chief Complaint: Patient presents with chest pain.
    
    History: [AGE]-year-old male with history of hypertension.
    Lives in [LOCATION].
    Contact: [CONTACT]
    
    Assessment: Stable angina.
    Plan: Schedule follow-up in 2 weeks.
    """
