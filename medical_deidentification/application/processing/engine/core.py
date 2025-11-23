"""
De-identification Engine Core
去識別化引擎核心模組

Main orchestration engine that integrates all components.
主要編排引擎，整合所有組件。
"""

from typing import Dict, List, Optional, Union
from pathlib import Path
import uuid
from loguru import logger

from .config import EngineConfig, ProcessingStatus
from .result import ProcessingResult
from .handlers import PipelineHandlers
from .masking import MaskingProcessor

from ..context import ProcessingContext, DocumentContext
from ..pipeline import DeidentificationPipeline, PipelineStage, StageResult, create_language_detection_handler, create_validation_handler
from ..strategies import create_masking_strategy, get_default_strategy_for_phi_type, MaskingStrategy
from ..output_manager import OutputManager, OutputConfig
from ..report_generator import ReportGenerator

from ....domain import PHIType
from ....infrastructure.loader import DocumentLoaderFactory
from ....infrastructure.rag import (
    EmbeddingsManager,
    RegulationVectorStore,
    RegulationRetrievalChain,
    PHIIdentificationChain,
    create_embeddings_manager,
    create_regulation_retrieval_chain
)
from ....infrastructure.llm import LLMConfig
from ....domain.phi_identification_models import PHIIdentificationConfig


class DeidentificationEngine:
    """
    Main de-identification engine
    主要去識別化引擎
    
    Orchestrates the complete de-identification workflow:
    1. Load documents using Document Loader
    2. Detect document language
    3. Retrieve regulations via RAG
    4. Identify PHI using LLM + regulations
    5. Apply masking strategies
    6. Validate results
    7. Return masked documents
    
    Examples:
        >>> # Initialize engine
        >>> from medical_deidentification.application.processing.engine import (
        ...     DeidentificationEngine,
        ...     EngineConfig
        ... )
        >>> from medical_deidentification.domain import StrategyType
        >>> 
        >>> config = EngineConfig(
        ...     use_rag=True,
        ...     llm_provider="openai",
        ...     llm_model="gpt-4o-mini",
        ...     default_strategy=StrategyType.GENERALIZATION
        ... )
        >>> engine = DeidentificationEngine(config)
        >>> 
        >>> # Process single file
        >>> result = engine.process_file("patient_record.xlsx")
        >>> print(f"Processed {result.processed_documents} documents")
        >>> print(f"Found {result.total_phi_entities} PHI entities")
        >>> 
        >>> # Process multiple files
        >>> result = engine.process_files([
        ...     "record1.xlsx",
        ...     "record2.docx",
        ...     "record3.txt"
        ... ])
        >>> 
        >>> # Process directory
        >>> result = engine.process_directory(
        ...     "data/medical_records/",
        ...     pattern="*.xlsx",
        ...     recursive=True
        ... )
    """
    
    def __init__(self, config: Optional[EngineConfig] = None):
        """
        Initialize engine
        
        Args:
            config: Engine configuration. Uses defaults if None.
        """
        self.config = config or EngineConfig()
        
        # Initialize output manager and report generator
        output_config = OutputConfig(
            base_dir=Path(self.config.output_base_dir) if hasattr(self.config, 'output_base_dir') 
                     else Path("data/output")
        )
        self.output_manager = OutputManager(config=output_config)
        self.report_generator = ReportGenerator(output_manager=self.output_manager)
        
        # Initialize document loader
        self.loader_factory = DocumentLoaderFactory(
            default_config=self.config.loader_config
        )
        
        # Initialize RAG components (lazy loading)
        self._embeddings_manager: Optional[EmbeddingsManager] = None
        self._vector_store: Optional[RegulationVectorStore] = None
        self._regulation_chain: Optional[RegulationRetrievalChain] = None
        self._phi_chain: Optional[PHIIdentificationChain] = None
        
        # Initialize masking processor
        self._masking_processor = MaskingProcessor(
            default_strategy=self.config.default_strategy,
            phi_specific_strategies=self.config.phi_specific_strategies,
            strategy_config=self.config.strategy_config
        )
        
        # Initialize pipeline handlers
        self._pipeline_handlers: Optional[PipelineHandlers] = None
        
        # Initialize pipeline
        self.pipeline = DeidentificationPipeline()
        self._setup_pipeline()
        
        # Initialize strategies cache
        self.strategies: Dict[PHIType, MaskingStrategy] = {}
        self._setup_strategies()
        
        logger.info(f"DeidentificationEngine initialized with output: {self.output_manager.base_dir}")
    
    def _setup_pipeline(self) -> None:
        """Setup pipeline stages"""
        # Create pipeline handlers (will be fully initialized after RAG setup)
        self._pipeline_handlers = PipelineHandlers(
            regulation_chain=self._regulation_chain,
            phi_chain=self._phi_chain,
            masking_processor=self._masking_processor,
            use_rag=self.config.use_rag,
            output_manager=self.output_manager
        )
        
        # Add stage handlers
        self.pipeline.add_stage_handler(
            PipelineStage.LANGUAGE_DETECTION,
            create_language_detection_handler()
        )
        
        self.pipeline.add_stage_handler(
            PipelineStage.REGULATION_RETRIEVAL,
            self._pipeline_handlers.create_regulation_retrieval_handler()
        )
        
        self.pipeline.add_stage_handler(
            PipelineStage.PHI_IDENTIFICATION,
            self._pipeline_handlers.create_phi_identification_handler()
        )
        
        self.pipeline.add_stage_handler(
            PipelineStage.MASKING_APPLICATION,
            self._pipeline_handlers.create_masking_handler()
        )
        
        self.pipeline.add_stage_handler(
            PipelineStage.VALIDATION,
            create_validation_handler()
        )
        
        self.pipeline.add_stage_handler(
            PipelineStage.OUTPUT_GENERATION,
            self._pipeline_handlers.create_output_handler()
        )
        
        logger.debug("Pipeline stages configured")
    
    def _setup_strategies(self) -> None:
        """Setup masking strategies cache"""
        # Pre-create PHI-specific strategies
        for phi_type, strategy_type in self.config.phi_specific_strategies.items():
            self.strategies[phi_type] = create_masking_strategy(
                strategy_type,
                self.config.strategy_config
            )
        
        logger.info(f"Configured {len(self.strategies)} PHI-specific strategies")
    
    def _get_strategy_for_phi(self, phi_type: PHIType) -> MaskingStrategy:
        """
        Get masking strategy for PHI type
        
        Args:
            phi_type: PHI type
            
        Returns:
            MaskingStrategy
        """
        # Check if specific strategy exists in cache
        if phi_type in self.strategies:
            return self.strategies[phi_type]
        
        # Get default strategy for PHI type
        strategy_type = get_default_strategy_for_phi_type(phi_type)
        
        # Create and cache strategy
        strategy = create_masking_strategy(
            strategy_type,
            self.config.strategy_config
        )
        self.strategies[phi_type] = strategy
        
        return strategy
    
    def _initialize_rag(self) -> None:
        """Initialize RAG components (lazy loading)"""
        if not self.config.use_rag:
            logger.info("RAG disabled")
            return
        
        if self._regulation_chain is not None and self._phi_chain is not None:
            logger.debug("RAG already initialized")
            return  # Already initialized
        
        logger.info("Initializing RAG components...")
        
        # Create embeddings manager
        self._embeddings_manager = create_embeddings_manager()
        
        # Load vector store
        try:
            self._vector_store = RegulationVectorStore.load(
                embeddings_manager=self._embeddings_manager
            )
            logger.info("Loaded existing regulation vector store")
        except FileNotFoundError:
            logger.warning(
                "Regulation vector store not found. "
                "RAG will not be available until regulations are loaded."
            )
            return
        
        # Create regulation retrieval chain
        self._regulation_chain = create_regulation_retrieval_chain(
            vector_store=self._vector_store
        )
        
        # Create PHI identification chain
        llm_config = LLMConfig(
            provider=self.config.llm_provider,
            model_name=self.config.llm_model,
            temperature=0.0
        )
        phi_config = PHIIdentificationConfig(
            llm_config=llm_config,
            retrieve_regulation_context=self.config.use_rag
        )
        self._phi_chain = PHIIdentificationChain(
            regulation_chain=self._regulation_chain,
            config=phi_config,
            chunk_size=500,
            chunk_overlap=50
        )
        
        # Update pipeline handlers with initialized chains
        if self._pipeline_handlers:
            self._pipeline_handlers.regulation_chain = self._regulation_chain
            self._pipeline_handlers.phi_chain = self._phi_chain
        
        logger.success("RAG components initialized")
    
    def process_file(
        self,
        file_path: Union[str, Path],
        job_name: Optional[str] = None
    ) -> ProcessingResult:
        """
        Process single file
        
        Args:
            file_path: Path to file
            job_name: Optional job name
            
        Returns:
            ProcessingResult
        """
        return self.process_files([file_path], job_name)
    
    def process_files(
        self,
        file_paths: List[Union[str, Path]],
        job_name: Optional[str] = None
    ) -> ProcessingResult:
        """
        Process multiple files
        
        Args:
            file_paths: List of file paths
            job_name: Optional job name
            
        Returns:
            ProcessingResult
        """
        # Create processing context
        job_id = str(uuid.uuid4())
        context = ProcessingContext(
            job_id=job_id,
            job_name=job_name or f"batch-{len(file_paths)}-files",
            config=self.config.model_dump()
        )
        
        logger.info(
            f"Starting job {job_id}: processing {len(file_paths)} files"
        )
        
        # Load documents
        for file_path in file_paths:
            try:
                loaded_doc = self.loader_factory.load(file_path)
                doc_context = DocumentContext(
                    document=loaded_doc,
                    document_id=str(uuid.uuid4())
                )
                context.add_document(doc_context)
                logger.info(f"Loaded document: {loaded_doc.metadata.filename}")
            
            except Exception as e:
                logger.error(f"Failed to load {file_path}: {e}")
                context.add_error(
                    error_type="document_loading_error",
                    message=str(e),
                    details={"file_path": str(file_path)}
                )
                context.mark_document_processed(success=False)
        
        # Initialize RAG if needed
        if self.config.use_rag:
            self._initialize_rag()
        
        # Execute pipeline
        stage_results = self.pipeline.execute(context)
        
        # Mark job as completed
        context.mark_completed()
        
        # Build result
        result = self._build_result(context, stage_results)
        
        logger.success(
            f"Job {job_id} completed: "
            f"{result.processed_documents}/{result.total_documents} "
            f"documents processed in {result.duration_seconds:.2f}s"
        )
        
        return result
    
    def process_directory(
        self,
        directory: Union[str, Path],
        pattern: str = "*",
        recursive: bool = False,
        job_name: Optional[str] = None
    ) -> ProcessingResult:
        """
        Process all files in directory
        
        Args:
            directory: Directory path
            pattern: File pattern (e.g., "*.xlsx")
            recursive: Search subdirectories
            job_name: Optional job name
            
        Returns:
            ProcessingResult
        """
        directory = Path(directory)
        
        # Find files
        if recursive:
            file_paths = list(directory.rglob(pattern))
        else:
            file_paths = list(directory.glob(pattern))
        
        logger.info(
            f"Found {len(file_paths)} files in {directory} "
            f"(pattern: {pattern}, recursive: {recursive})"
        )
        
        # Process files
        return self.process_files(
            file_paths,
            job_name or f"directory-{directory.name}"
        )
    
    def _build_result(
        self,
        context: ProcessingContext,
        stage_results: List[StageResult]
    ) -> ProcessingResult:
        """
        Build processing result from context and stage results
        
        Args:
            context: Processing context
            stage_results: Results from each pipeline stage
            
        Returns:
            ProcessingResult
        """
        # Calculate statistics
        total_phi = sum(len(doc.phi_entities) for doc in context.documents)
        
        # Build document results
        doc_results = []
        for doc_context in context.documents:
            doc_results.append({
                "document_id": doc_context.document_id,
                "filename": doc_context.document.metadata.filename,
                "language": (
                    doc_context.detected_language.value
                    if doc_context.detected_language else None
                ),
                "phi_entities_count": len(doc_context.phi_entities),
                "masked": doc_context.masked_content is not None,
                "processing_time_seconds": doc_context.get_processing_time()
            })
        
        # Build stage results summary
        stage_summary = [
            {
                "stage": r.stage.value,
                "success": r.success,
                "duration_seconds": r.duration_seconds,
                "output": r.output
            }
            for r in stage_results
        ]
        
        # Determine overall status
        if context.failed_documents == 0:
            status = ProcessingStatus.COMPLETED
        elif context.processed_documents > 0:
            status = ProcessingStatus.COMPLETED  # Partial success
        else:
            status = ProcessingStatus.FAILED
        
        # Create result
        result = ProcessingResult(
            job_id=context.job_id,
            status=status,
            started_at=context.started_at,
            completed_at=context.completed_at,
            duration_seconds=context.get_processing_time(),
            total_documents=context.total_documents,
            processed_documents=context.processed_documents,
            failed_documents=context.failed_documents,
            total_phi_entities=total_phi,
            documents=doc_results,
            stage_results=stage_summary,
            errors=context.errors,
            summary=context.get_summary()
        )
        
        return result
    
    def __repr__(self) -> str:
        return (
            f"DeidentificationEngine("
            f"use_rag={self.config.use_rag}, "
            f"llm={self.config.llm_provider}/{self.config.llm_model})"
        )


__all__ = [
    "DeidentificationEngine",
]
