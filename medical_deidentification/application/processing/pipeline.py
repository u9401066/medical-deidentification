"""
De-identification Pipeline
去識別化流水線

Defines processing stages and orchestrates the de-identification workflow.
定義處理階段並編排去識別化工作流程。
"""

from enum import Enum
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
from pydantic import BaseModel, Field
from loguru import logger

from .context import ProcessingContext, DocumentContext
from ...domain.models import PHIEntity


class PipelineStage(str, Enum):
    """處理階段 | Processing stages"""
    DOCUMENT_LOADING = "document_loading"
    LANGUAGE_DETECTION = "language_detection"
    REGULATION_RETRIEVAL = "regulation_retrieval"
    PHI_IDENTIFICATION = "phi_identification"
    MASKING_APPLICATION = "masking_application"
    VALIDATION = "validation"
    OUTPUT_GENERATION = "output_generation"


class StageResult(BaseModel):
    """
    Result of a pipeline stage
    流水線階段結果
    """
    
    stage: PipelineStage = Field(description="Stage name")
    success: bool = Field(description="Whether stage succeeded")
    started_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = Field(default=None)
    duration_seconds: Optional[float] = Field(default=None)
    
    # Stage output
    output: Dict[str, Any] = Field(default_factory=dict)
    
    # Errors
    error_message: Optional[str] = Field(default=None)
    error_details: Optional[Dict[str, Any]] = Field(default=None)
    
    def mark_completed(self, success: bool = True) -> None:
        """Mark stage as completed"""
        self.completed_at = datetime.now()
        self.success = success
        delta = self.completed_at - self.started_at
        self.duration_seconds = delta.total_seconds()
    
    def set_error(self, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        """Set error information"""
        self.error_message = message
        self.error_details = details or {}
        self.mark_completed(success=False)


class DeidentificationPipeline:
    """
    De-identification processing pipeline
    去識別化處理流水線
    
    Orchestrates the complete workflow:
    1. Load documents
    2. Detect language
    3. Retrieve regulations via RAG
    4. Identify PHI using LLM
    5. Apply masking strategies
    6. Validate results
    7. Generate output
    
    編排完整工作流程：
    1. 載入文件
    2. 偵測語言
    3. 透過 RAG 檢索法規
    4. 使用 LLM 識別 PHI
    5. 應用遮蔽策略
    6. 驗證結果
    7. 產生輸出
    
    Examples:
        >>> pipeline = DeidentificationPipeline()
        >>> pipeline.add_stage_handler(
        ...     PipelineStage.DOCUMENT_LOADING,
        ...     load_document_handler
        ... )
        >>> result = pipeline.execute(context)
    """
    
    def __init__(self):
        """Initialize pipeline"""
        self.stage_handlers: Dict[PipelineStage, Callable] = {}
        self.stage_order: List[PipelineStage] = [
            PipelineStage.DOCUMENT_LOADING,
            PipelineStage.LANGUAGE_DETECTION,
            PipelineStage.REGULATION_RETRIEVAL,
            PipelineStage.PHI_IDENTIFICATION,
            PipelineStage.MASKING_APPLICATION,
            PipelineStage.VALIDATION,
            PipelineStage.OUTPUT_GENERATION,
        ]
    
    def add_stage_handler(
        self,
        stage: PipelineStage,
        handler: Callable[[ProcessingContext], StageResult]
    ) -> None:
        """
        Add handler for stage
        
        Args:
            stage: Pipeline stage
            handler: Handler function that takes ProcessingContext and returns StageResult
        """
        self.stage_handlers[stage] = handler
        logger.info(f"Added handler for stage: {stage.value}")
    
    def remove_stage(self, stage: PipelineStage) -> None:
        """Remove stage from pipeline"""
        if stage in self.stage_order:
            self.stage_order.remove(stage)
            logger.info(f"Removed stage: {stage.value}")
    
    def execute(
        self,
        context: ProcessingContext,
        skip_stages: Optional[List[PipelineStage]] = None
    ) -> List[StageResult]:
        """
        Execute pipeline
        
        Args:
            context: Processing context
            skip_stages: Stages to skip (optional)
            
        Returns:
            List of stage results
        """
        skip_stages = skip_stages or []
        results: List[StageResult] = []
        
        logger.info(f"Starting pipeline execution for job: {context.job_id}")
        
        for stage in self.stage_order:
            # Skip if requested
            if stage in skip_stages:
                logger.info(f"Skipping stage: {stage.value}")
                continue
            
            # Check if handler exists
            if stage not in self.stage_handlers:
                logger.warning(f"No handler for stage: {stage.value}, skipping")
                continue
            
            # Execute stage
            logger.info(f"Executing stage: {stage.value}")
            
            try:
                handler = self.stage_handlers[stage]
                stage_result = handler(context)
                results.append(stage_result)
                
                # Check if stage failed
                if not stage_result.success:
                    logger.error(
                        f"Stage {stage.value} failed: {stage_result.error_message}"
                    )
                    
                    # Add error to context
                    context.add_error(
                        error_type=f"stage_failure_{stage.value}",
                        message=stage_result.error_message or "Unknown error",
                        details=stage_result.error_details
                    )
                    
                    # Stop pipeline on critical failure
                    if self._is_critical_stage(stage):
                        logger.error("Critical stage failed, stopping pipeline")
                        break
                
                else:
                    logger.info(
                        f"Stage {stage.value} completed in "
                        f"{stage_result.duration_seconds:.2f}s"
                    )
            
            except Exception as e:
                logger.exception(f"Unexpected error in stage {stage.value}: {e}")
                
                stage_result = StageResult(stage=stage, success=False)
                stage_result.set_error(str(e), {"exception_type": type(e).__name__})
                results.append(stage_result)
                
                context.add_error(
                    error_type=f"stage_exception_{stage.value}",
                    message=str(e),
                    details={"exception_type": type(e).__name__}
                )
                
                # Stop on critical failure
                if self._is_critical_stage(stage):
                    logger.error("Critical stage exception, stopping pipeline")
                    break
        
        logger.info(f"Pipeline execution completed for job: {context.job_id}")
        return results
    
    def _is_critical_stage(self, stage: PipelineStage) -> bool:
        """Check if stage is critical (failure should stop pipeline)"""
        critical_stages = [
            PipelineStage.DOCUMENT_LOADING,
            PipelineStage.PHI_IDENTIFICATION,
        ]
        return stage in critical_stages
    
    def get_stage_summary(self, results: List[StageResult]) -> Dict[str, Any]:
        """
        Get summary of stage results
        
        Args:
            results: List of stage results
            
        Returns:
            Summary dictionary
        """
        total_stages = len(results)
        successful_stages = sum(1 for r in results if r.success)
        failed_stages = total_stages - successful_stages
        
        total_duration = sum(
            r.duration_seconds for r in results 
            if r.duration_seconds is not None
        )
        
        return {
            "total_stages": total_stages,
            "successful_stages": successful_stages,
            "failed_stages": failed_stages,
            "success_rate": successful_stages / total_stages if total_stages > 0 else 0.0,
            "total_duration_seconds": total_duration,
            "stage_details": [
                {
                    "stage": r.stage.value,
                    "success": r.success,
                    "duration_seconds": r.duration_seconds,
                    "error": r.error_message
                }
                for r in results
            ]
        }
    
    def __repr__(self) -> str:
        return (
            f"DeidentificationPipeline("
            f"stages={len(self.stage_order)}, "
            f"handlers={len(self.stage_handlers)})"
        )


# Stage handler templates
# 階段處理器範本

def create_document_loading_handler(loader_factory):
    """Create document loading stage handler"""
    def handler(context: ProcessingContext) -> StageResult:
        result = StageResult(stage=PipelineStage.DOCUMENT_LOADING)
        
        try:
            # Document loading logic here
            # This is handled by the engine
            result.output["loaded"] = True
            result.mark_completed(success=True)
        except Exception as e:
            result.set_error(str(e))
        
        return result
    
    return handler


def create_language_detection_handler():
    """Create language detection stage handler"""
    def handler(context: ProcessingContext) -> StageResult:
        result = StageResult(stage=PipelineStage.LANGUAGE_DETECTION)
        
        try:
            # Language detection logic
            for doc_context in context.documents:
                # Simple heuristic: check for Chinese characters
                text = doc_context.document.content
                has_chinese = any('\u4e00' <= char <= '\u9fff' for char in text)
                
                if has_chinese:
                    from ...domain.models import SupportedLanguage
                    doc_context.detected_language = SupportedLanguage.ZH_TW
                else:
                    from ...domain.models import SupportedLanguage
                    doc_context.detected_language = SupportedLanguage.EN
            
            result.output["detected"] = True
            result.mark_completed(success=True)
        except Exception as e:
            result.set_error(str(e))
        
        return result
    
    return handler


def create_validation_handler():
    """Create validation stage handler"""
    def handler(context: ProcessingContext) -> StageResult:
        result = StageResult(stage=PipelineStage.VALIDATION)
        
        try:
            # Validation logic
            total_phi = 0
            total_masked = 0
            
            for doc_context in context.documents:
                total_phi += len(doc_context.phi_entities)
                if doc_context.masked_content:
                    total_masked += 1
            
            result.output["total_phi_entities"] = total_phi
            result.output["total_masked_documents"] = total_masked
            result.output["validation_passed"] = total_masked == len(context.documents)
            
            result.mark_completed(success=True)
        except Exception as e:
            result.set_error(str(e))
        
        return result
    
    return handler
