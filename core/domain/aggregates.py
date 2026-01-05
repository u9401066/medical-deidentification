"""
Domain Aggregates | 領域聚合

Aggregate roots for medical document de-identification domain.
醫療文件去識別化領域的聚合根。
"""

from datetime import datetime
from uuid import UUID, uuid4

from .entities import PHIEntity
from .value_objects import DocumentMetadata, RegulationContext, ValidationResult


class MedicalDocument:
    """
    Medical Document Aggregate Root | 醫療文件聚合根
    
    Main aggregate for the de-identification domain.
    去識別化領域的主要聚合。
    """

    def __init__(
        self,
        original_text: str,
        metadata: DocumentMetadata | None = None,
        document_id: UUID | None = None,
    ):
        self.id: UUID = document_id or uuid4()
        self.original_text: str = original_text
        self.detected_entities: list[PHIEntity] = []
        self.deidentified_text: str | None = None
        self.metadata: DocumentMetadata = metadata or DocumentMetadata(document_type="unknown")
        self.regulation_context: RegulationContext | None = None
        self.validation_result: ValidationResult | None = None
        self._created_at: datetime = datetime.now()

    def add_detected_entity(self, entity: PHIEntity) -> None:
        """
        Add a detected PHI entity | 添加檢測到的 PHI 實體
        
        Args:
            entity: The PHI entity to add
        """
        self.detected_entities.append(entity)

    def set_regulation_context(self, context: RegulationContext) -> None:
        """
        Set the regulation context from RAG | 設置來自 RAG 的法規上下文
        
        Args:
            context: Regulation context with retrieved rules
        """
        self.regulation_context = context

    def apply_deidentification(self, deidentified_text: str) -> None:
        """
        Apply de-identified text | 應用去識別化文本
        
        Args:
            deidentified_text: The de-identified version of the text
        """
        if not deidentified_text:
            raise ValueError("De-identified text cannot be empty")
        self.deidentified_text = deidentified_text

    def set_validation_result(self, result: ValidationResult) -> None:
        """
        Set validation result | 設置驗證結果
        
        Args:
            result: Validation result with quality metrics
        """
        self.validation_result = result

    def is_deidentified(self) -> bool:
        """Check if document has been de-identified | 檢查文件是否已去識別化"""
        return self.deidentified_text is not None

    def is_validated(self) -> bool:
        """Check if document has been validated | 檢查文件是否已驗證"""
        return self.validation_result is not None and self.validation_result.is_valid

    def get_phi_count(self) -> int:
        """Get count of detected PHI entities | 獲取檢測到的 PHI 實體數量"""
        return len(self.detected_entities)

    def __repr__(self) -> str:
        return (
            f"MedicalDocument(id={self.id}, "
            f"phi_count={self.get_phi_count()}, "
            f"deidentified={self.is_deidentified()})"
        )
