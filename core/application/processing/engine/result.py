"""
Processing Result
處理結果模組

Defines the result structure for de-identification processing.
定義去識別化處理的結果結構。
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from .config import ProcessingStatus


class ProcessingResult(BaseModel):
    """
    Processing result
    處理結果
    
    Contains comprehensive information about a de-identification job including:
    - Job metadata (ID, status, timing)
    - Statistics (documents processed, PHI entities found)
    - Detailed results per document
    - Stage-by-stage results
    - Errors and warnings
    - Summary information
    
    Examples:
        >>> result = ProcessingResult(
        ...     job_id="job_123",
        ...     status=ProcessingStatus.COMPLETED,
        ...     started_at=datetime.now(),
        ...     total_documents=5,
        ...     processed_documents=5,
        ...     total_phi_entities=42
        ... )
        >>> 
        >>> # Check if successful
        >>> if result.status == ProcessingStatus.COMPLETED:
        ...     print(f"Processed {result.processed_documents} documents")
        ...     print(f"Found {result.total_phi_entities} PHI entities")
    """

    # Job information
    job_id: str = Field(
        description="Unique job identifier"
    )
    status: ProcessingStatus = Field(
        description="Processing status"
    )

    # Timing
    started_at: datetime = Field(
        description="Processing start time"
    )
    completed_at: datetime | None = Field(
        default=None,
        description="Processing completion time"
    )
    duration_seconds: float | None = Field(
        default=None,
        description="Total duration in seconds"
    )

    # Statistics
    total_documents: int = Field(
        default=0,
        description="Total number of documents to process"
    )
    processed_documents: int = Field(
        default=0,
        description="Number of successfully processed documents"
    )
    failed_documents: int = Field(
        default=0,
        description="Number of failed documents"
    )
    total_phi_entities: int = Field(
        default=0,
        description="Total number of PHI entities identified"
    )

    # Results
    documents: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Per-document results"
    )

    # Stage results
    stage_results: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Results from each pipeline stage"
    )

    # Errors
    errors: list[dict[str, Any]] = Field(
        default_factory=list,
        description="List of errors encountered"
    )

    # Summary
    summary: dict[str, Any] = Field(
        default_factory=dict,
        description="Summary information"
    )

    class Config:
        arbitrary_types_allowed = True

    def is_successful(self) -> bool:
        """Check if processing was successful"""
        return self.status == ProcessingStatus.COMPLETED

    def has_errors(self) -> bool:
        """Check if any errors occurred"""
        return len(self.errors) > 0 or self.failed_documents > 0

    def get_success_rate(self) -> float:
        """Calculate success rate as percentage"""
        if self.total_documents == 0:
            return 0.0
        return (self.processed_documents / self.total_documents) * 100


__all__ = [
    "ProcessingResult",
]
