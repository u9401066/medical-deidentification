"""
Processing Context
處理上下文

Manages context and state during de-identification processing.
管理去識別化處理期間的上下文和狀態。
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from ...domain import LoadedDocument, PHIEntity, SupportedLanguage


class DocumentContext(BaseModel):
    """
    Context for a single document being processed
    單一文件的處理上下文
    
    Tracks document metadata, content, and processing state.
    """

    # Document information
    document: LoadedDocument = Field(description="Loaded document")
    document_id: str = Field(description="Unique document identifier")

    # Language detection
    detected_language: SupportedLanguage | None = Field(
        default=None,
        description="Detected document language"
    )

    # Processing state
    processing_started_at: datetime = Field(
        default_factory=datetime.now,
        description="When processing started"
    )
    processing_completed_at: datetime | None = Field(
        default=None,
        description="When processing completed"
    )

    # PHI entities found
    phi_entities: list[PHIEntity] = Field(
        default_factory=list,
        description="Identified PHI entities"
    )

    # Masked content
    masked_content: str | None = Field(
        default=None,
        description="Content after masking"
    )

    # Processing metadata
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional processing metadata"
    )

    class Config:
        arbitrary_types_allowed = True

    def add_phi_entity(self, entity: PHIEntity) -> None:
        """Add identified PHI entity"""
        self.phi_entities.append(entity)

    def get_processing_time(self) -> float | None:
        """Get processing time in seconds"""
        if self.processing_completed_at:
            delta = self.processing_completed_at - self.processing_started_at
            return delta.total_seconds()
        return None

    def mark_completed(self) -> None:
        """Mark processing as completed"""
        self.processing_completed_at = datetime.now()


class RegulationContext(BaseModel):
    """
    Context for regulation retrieval
    法規檢索上下文
    
    Stores retrieved regulations and relevance scores.
    """

    # Regulation source
    regulation_source: str = Field(
        default="general",
        description="Regulation source (HIPAA, GDPR, Taiwan, etc.)"
    )

    # Retrieved regulations
    retrieved_regulations: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Retrieved regulation documents"
    )

    # Relevance scores
    relevance_scores: dict[str, float] = Field(
        default_factory=dict,
        description="Relevance scores for regulations"
    )

    # Retrieval metadata
    retrieval_metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="RAG retrieval metadata"
    )

    def add_regulation(
        self,
        regulation_id: str,
        content: str,
        score: float,
        metadata: dict[str, Any] | None = None
    ) -> None:
        """Add retrieved regulation"""
        self.retrieved_regulations.append({
            "id": regulation_id,
            "content": content,
            "metadata": metadata or {}
        })
        self.relevance_scores[regulation_id] = score

    def get_top_regulations(self, k: int = 5) -> list[dict[str, Any]]:
        """Get top k most relevant regulations"""
        sorted_regs = sorted(
            self.retrieved_regulations,
            key=lambda x: self.relevance_scores.get(x["id"], 0.0),
            reverse=True
        )
        return sorted_regs[:k]


class ProcessingContext(BaseModel):
    """
    Main processing context
    主要處理上下文
    
    Manages context for entire de-identification job.
    Tracks documents, regulations, and overall state.
    
    管理整個去識別化作業的上下文。
    追蹤文件、法規和整體狀態。
    
    Examples:
        >>> context = ProcessingContext(job_id="job-001")
        >>> doc_context = DocumentContext(
        ...     document=loaded_doc,
        ...     document_id="doc-001"
        ... )
        >>> context.add_document(doc_context)
        >>> 
        >>> # Track regulations
        >>> reg_context = RegulationContext(regulation_source="HIPAA")
        >>> context.regulation_context = reg_context
    """

    # Job information
    job_id: str = Field(description="Unique job identifier")
    job_name: str | None = Field(default=None, description="Human-readable job name")

    # Timing
    started_at: datetime = Field(default_factory=datetime.now, description="Job start time")
    completed_at: datetime | None = Field(default=None, description="Job completion time")

    # Documents
    documents: list[DocumentContext] = Field(
        default_factory=list,
        description="Document contexts"
    )

    # Regulations
    regulation_context: RegulationContext | None = Field(
        default=None,
        description="Regulation retrieval context"
    )

    # Overall statistics
    total_documents: int = Field(default=0, description="Total documents to process")
    processed_documents: int = Field(default=0, description="Documents processed")
    failed_documents: int = Field(default=0, description="Documents failed")

    # Configuration
    config: dict[str, Any] = Field(
        default_factory=dict,
        description="Processing configuration"
    )

    # Errors
    errors: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Processing errors"
    )

    class Config:
        arbitrary_types_allowed = True

    def add_document(self, doc_context: DocumentContext) -> None:
        """Add document context"""
        self.documents.append(doc_context)
        self.total_documents += 1

    def mark_document_processed(self, success: bool = True) -> None:
        """Mark document as processed"""
        self.processed_documents += 1
        if not success:
            self.failed_documents += 1

    def add_error(
        self,
        error_type: str,
        message: str,
        document_id: str | None = None,
        details: dict[str, Any] | None = None
    ) -> None:
        """Add processing error"""
        self.errors.append({
            "timestamp": datetime.now().isoformat(),
            "type": error_type,
            "message": message,
            "document_id": document_id,
            "details": details or {}
        })

    def mark_completed(self) -> None:
        """Mark job as completed"""
        self.completed_at = datetime.now()

    def get_processing_time(self) -> float | None:
        """Get total processing time in seconds"""
        if self.completed_at:
            delta = self.completed_at - self.started_at
            return delta.total_seconds()
        return None

    def get_success_rate(self) -> float:
        """Get success rate (0.0 to 1.0)"""
        if self.processed_documents == 0:
            return 0.0
        success_count = self.processed_documents - self.failed_documents
        return success_count / self.processed_documents

    def get_summary(self) -> dict[str, Any]:
        """Get processing summary"""
        return {
            "job_id": self.job_id,
            "job_name": self.job_name,
            "status": "completed" if self.completed_at else "in_progress",
            "total_documents": self.total_documents,
            "processed_documents": self.processed_documents,
            "failed_documents": self.failed_documents,
            "success_rate": self.get_success_rate(),
            "processing_time_seconds": self.get_processing_time(),
            "errors_count": len(self.errors),
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None
        }

    def get_document_by_id(self, document_id: str) -> DocumentContext | None:
        """Get document context by ID"""
        for doc in self.documents:
            if doc.document_id == document_id:
                return doc
        return None

    def __repr__(self) -> str:
        """String representation"""
        return (
            f"ProcessingContext(job_id={self.job_id}, "
            f"documents={len(self.documents)}, "
            f"processed={self.processed_documents}/{self.total_documents})"
        )
