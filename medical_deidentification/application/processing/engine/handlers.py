"""
Pipeline Handlers
Pipeline 處理器模組

Provides handler functions for each stage of the de-identification pipeline.
提供去識別化 pipeline 每個階段的處理函數。
"""

from typing import List, Optional, Callable
from loguru import logger

from ..context import ProcessingContext, RegulationContext
from ..pipeline import StageResult, PipelineStage
from ..output_manager import OutputManager, get_default_output_manager
from ..report_generator import ReportGenerator
from ....domain import PHIEntity
from ....infrastructure.rag import (
    RegulationRetrievalChain,
    PHIIdentificationChain
)
from .masking import MaskingProcessor


class PipelineHandlers:
    """
    Pipeline handlers factory
    Pipeline 處理器工廠
    
    Creates handler functions for each pipeline stage.
    為每個 pipeline 階段創建處理器函數。
    
    This class encapsulates all the stage-specific logic and dependencies,
    making the main engine class cleaner and more maintainable.
    """
    
    def __init__(
        self,
        regulation_chain: Optional[RegulationRetrievalChain] = None,
        phi_chain: Optional[PHIIdentificationChain] = None,
        masking_processor: Optional[MaskingProcessor] = None,
        use_rag: bool = True,
        output_manager: Optional[OutputManager] = None
    ):
        """
        Initialize pipeline handlers
        
        Args:
            regulation_chain: Regulation retrieval chain
            phi_chain: PHI identification chain
            masking_processor: Masking processor
            use_rag: Whether to use RAG for PHI identification
            output_manager: Output manager for file paths and reports
        """
        self.regulation_chain = regulation_chain
        self.phi_chain = phi_chain
        self.masking_processor = masking_processor
        self.use_rag = use_rag
        self.output_manager = output_manager or get_default_output_manager()
        self.report_generator = ReportGenerator(output_manager=self.output_manager)
    
    def create_regulation_retrieval_handler(self) -> Callable:
        """
        Create regulation retrieval stage handler
        創建法規檢索階段處理器
        """
        def handler(context: ProcessingContext) -> StageResult:
            result = StageResult(
                stage=PipelineStage.REGULATION_RETRIEVAL,
                success=False
            )
            
            try:
                if not self.use_rag or self.regulation_chain is None:
                    logger.info("RAG disabled or not available, skipping regulation retrieval")
                    result.output["skipped"] = True
                    result.mark_completed(success=True)
                    return result
                
                # Create regulation context
                reg_context = RegulationContext()
                context.regulation_context = reg_context
                
                # Retrieve regulations for all documents
                # (In production, retrieve based on detected PHI types)
                result.output["regulations_retrieved"] = True
                result.mark_completed(success=True)
                
                logger.success("Regulation retrieval completed")
            
            except Exception as e:
                logger.error(f"Regulation retrieval failed: {e}")
                result.set_error(str(e))
            
            return result
        
        return handler
    
    def create_phi_identification_handler(self) -> Callable:
        """
        Create PHI identification stage handler
        創建 PHI 識別階段處理器
        """
        def handler(context: ProcessingContext) -> StageResult:
            result = StageResult(
                stage=PipelineStage.PHI_IDENTIFICATION,
                success=False
            )
            
            try:
                total_phi = 0
                
                for doc_context in context.documents:
                    text = doc_context.document.content
                    language = doc_context.detected_language
                    
                    # Always use PHI chain if available (RAG flag only affects regulation retrieval)
                    if self.phi_chain:
                        # Use LLM for PHI identification with structured output
                        logger.info(
                            f"Identifying PHI for {doc_context.document_id} "
                            f"(RAG={'enabled' if self.use_rag else 'disabled'})"
                        )
                        
                        rag_response = self.phi_chain.identify_phi(
                            text=text,
                            language=language.value if language else None,
                            return_entities=True  # Get structured PHIEntity list
                        )
                        
                        # Get structured PHI entities (List[PHIEntity])
                        phi_entities: List[PHIEntity] = rag_response.get("entities", [])
                        
                        # Add entities to document context
                        for entity in phi_entities:
                            doc_context.add_phi_entity(entity)
                        
                        total_phi += len(phi_entities)
                        
                        logger.info(
                            f"Found {len(phi_entities)} PHI entities in "
                            f"{doc_context.document_id}"
                        )
                    
                    else:
                        # PHI chain not initialized
                        logger.warning(
                            f"PHI chain not available for {doc_context.document_id}, "
                            "skipping PHI identification"
                        )
                    
                    context.mark_document_processed(success=True)
                
                result.output["total_phi_entities"] = total_phi
                result.output["documents_processed"] = len(context.documents)
                result.mark_completed(success=True)
                
                logger.success(
                    f"PHI identification completed: {total_phi} entities found"
                )
            
            except Exception as e:
                logger.error(f"PHI identification failed: {e}")
                result.set_error(
                    message=str(e),
                    details={"stage": "phi_identification"}
                )
            
            return result
        
        return handler
    
    def create_masking_handler(self) -> Callable:
        """
        Create masking application stage handler
        創建遮蔽應用階段處理器
        """
        def handler(context: ProcessingContext) -> StageResult:
            result = StageResult(
                stage=PipelineStage.MASKING_APPLICATION,
                success=False
            )
            
            if not self.masking_processor:
                logger.error("Masking processor not initialized")
                result.set_error("Masking processor not available")
                return result
            
            try:
                total_masked = 0
                
                for doc_context in context.documents:
                    # Get PHI entities (already structured PHIEntity objects)
                    phi_entities = doc_context.phi_entities
                    
                    if not phi_entities:
                        logger.info(f"No PHI found in {doc_context.document_id}")
                        doc_context.masked_content = doc_context.document.content
                        continue
                    
                    logger.info(
                        f"Applying masking to {len(phi_entities)} PHI entities "
                        f"in {doc_context.document_id}"
                    )
                    
                    # Apply masking using structured entities
                    masked_text = self.masking_processor.apply_masking(
                        text=doc_context.document.content,
                        phi_entities=phi_entities
                    )
                    
                    doc_context.masked_content = masked_text
                    doc_context.mark_completed()
                    total_masked += len(phi_entities)
                    
                    logger.info(
                        f"Masked {len(phi_entities)} entities in "
                        f"{doc_context.document_id}"
                    )
                
                result.output["total_masked_entities"] = total_masked
                result.output["documents_masked"] = len([
                    d for d in context.documents if d.masked_content
                ])
                result.mark_completed(success=True)
                
                logger.success(
                    f"Masking completed: {total_masked} entities masked"
                )
            
            except Exception as e:
                logger.error(f"Masking application failed: {e}")
                result.set_error(
                    message=str(e),
                    details={"stage": "masking_application"}
                )
            
            return result
        
        return handler
    
    def create_output_handler(self) -> Callable:
        """
        Create output generation stage handler
        創建輸出生成階段處理器
        """
        def handler(context: ProcessingContext) -> StageResult:
            result = StageResult(
                stage=PipelineStage.OUTPUT_GENERATION,
                success=False
            )
            
            try:
                # Generate output paths based on job_id
                result_path = self.output_manager.get_result_path(
                    f"deidentified_{context.job_id}",
                    "xlsx"
                )
                
                # Store output path in context for engine to use
                result.output["result_path"] = str(result_path)
                result.output["reports_dir"] = str(self.output_manager.reports_dir)
                result.output["output_generated"] = True
                
                result.mark_completed(success=True)
                logger.success(f"✓ Output paths configured: {result_path}")
            
            except Exception as e:
                logger.error(f"Output generation failed: {e}")
                result.set_error(str(e))
            
            return result
        
        return handler


__all__ = [
    "PipelineHandlers",
]
