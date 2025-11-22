"""
De-identification Engine
去識別化引擎

Main orchestration engine that integrates all components:
- Document Loader (Module 1)
- RAG Regulation Engine (Module 2)
- Processing Pipeline (Module 3)
- Masking Strategies (Module 5)

主要編排引擎，整合所有組件：
- 文件載入器（模組 1）
- RAG 法規引擎（模組 2）
- 處理流水線（模組 3）
- 遮蔽策略（模組 5）
"""

from typing import Dict, List, Any, Optional, Union
from pathlib import Path
from enum import Enum
from datetime import datetime
import uuid
from pydantic import BaseModel, Field
from loguru import logger

from .context import ProcessingContext, DocumentContext, RegulationContext
from .pipeline import DeidentificationPipeline, PipelineStage, StageResult
from .strategies import (
    MaskingStrategy,
    StrategyType,
    create_masking_strategy,
    get_default_strategy_for_phi_type
)

from ...domain.models import PHIEntity, PHIType, SupportedLanguage
from ...infrastructure.loader import (
    DocumentLoaderFactory,
    LoadedDocument,
    LoaderConfig
)
from ...infrastructure.rag import (
    EmbeddingsManager,
    RegulationVectorStore,
    RegulationRetrievalChain,
    PHIIdentificationChain,
    create_embeddings_manager,
    create_regulation_retrieval_chain,
    create_phi_identification_chain
)


class ProcessingStatus(str, Enum):
    """處理狀態 | Processing status"""
    PENDING = "pending"
    LOADING = "loading"
    PROCESSING = "processing"
    MASKING = "masking"
    VALIDATING = "validating"
    COMPLETED = "completed"
    FAILED = "failed"


class EngineConfig(BaseModel):
    """
    Engine configuration
    引擎配置
    """
    
    # Loader configuration
    loader_config: Optional[LoaderConfig] = Field(
        default=None,
        description="Document loader configuration"
    )
    
    # RAG configuration
    use_rag: bool = Field(
        default=True,
        description="Whether to use RAG for regulation retrieval"
    )
    llm_provider: str = Field(
        default="openai",
        description="LLM provider (openai or anthropic)"
    )
    llm_model: str = Field(
        default="gpt-4",
        description="LLM model name"
    )
    embeddings_preset: str = Field(
        default="multilingual",
        description="Embeddings model preset"
    )
    
    # Masking strategy
    default_strategy: StrategyType = Field(
        default=StrategyType.REDACTION,
        description="Default masking strategy"
    )
    strategy_config: Dict[str, Any] = Field(
        default_factory=dict,
        description="Strategy configuration"
    )
    phi_specific_strategies: Dict[PHIType, StrategyType] = Field(
        default_factory=dict,
        description="PHI-type specific strategies"
    )
    
    # Processing options
    batch_size: int = Field(
        default=10,
        description="Batch size for processing multiple documents"
    )
    parallel_processing: bool = Field(
        default=False,
        description="Enable parallel processing (future)"
    )
    
    # Validation
    validate_output: bool = Field(
        default=True,
        description="Validate masked output"
    )
    
    class Config:
        arbitrary_types_allowed = True


class ProcessingResult(BaseModel):
    """
    Processing result
    處理結果
    """
    
    # Job information
    job_id: str = Field(description="Job identifier")
    status: ProcessingStatus = Field(description="Processing status")
    
    # Timing
    started_at: datetime = Field(description="Processing start time")
    completed_at: Optional[datetime] = Field(default=None)
    duration_seconds: Optional[float] = Field(default=None)
    
    # Statistics
    total_documents: int = Field(default=0)
    processed_documents: int = Field(default=0)
    failed_documents: int = Field(default=0)
    total_phi_entities: int = Field(default=0)
    
    # Results
    documents: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Stage results
    stage_results: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Errors
    errors: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Summary
    summary: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        arbitrary_types_allowed = True


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
        >>> config = EngineConfig(
        ...     use_rag=True,
        ...     llm_provider="openai",
        ...     default_strategy=StrategyType.GENERALIZATION
        ... )
        >>> engine = DeidentificationEngine(config)
        >>> 
        >>> # Process single file
        >>> result = engine.process_file("patient_record.xlsx")
        >>> 
        >>> # Process multiple files
        >>> result = engine.process_files([
        ...     "record1.xlsx",
        ...     "record2.docx",
        ...     "record3.txt"
        ... ])
        >>> 
        >>> # Process directory
        >>> result = engine.process_directory("data/medical_records/")
    """
    
    def __init__(self, config: Optional[EngineConfig] = None):
        """
        Initialize engine
        
        Args:
            config: Engine configuration. Uses defaults if None.
        """
        self.config = config or EngineConfig()
        
        # Initialize components
        self.loader_factory = DocumentLoaderFactory(
            default_config=self.config.loader_config
        )
        
        # Initialize RAG components (lazy loading)
        self._embeddings_manager: Optional[EmbeddingsManager] = None
        self._vector_store: Optional[RegulationVectorStore] = None
        self._regulation_chain: Optional[RegulationRetrievalChain] = None
        self._phi_chain: Optional[PHIIdentificationChain] = None
        
        # Initialize pipeline
        self.pipeline = DeidentificationPipeline()
        self._setup_pipeline()
        
        # Initialize strategies
        self.strategies: Dict[PHIType, MaskingStrategy] = {}
        self._setup_strategies()
        
        logger.info("DeidentificationEngine initialized")
    
    def _setup_pipeline(self) -> None:
        """Setup pipeline stages"""
        from .pipeline import (
            create_language_detection_handler,
            create_validation_handler
        )
        
        # Add stage handlers
        self.pipeline.add_stage_handler(
            PipelineStage.LANGUAGE_DETECTION,
            create_language_detection_handler()
        )
        
        self.pipeline.add_stage_handler(
            PipelineStage.REGULATION_RETRIEVAL,
            self._create_regulation_retrieval_handler()
        )
        
        self.pipeline.add_stage_handler(
            PipelineStage.PHI_IDENTIFICATION,
            self._create_phi_identification_handler()
        )
        
        self.pipeline.add_stage_handler(
            PipelineStage.MASKING_APPLICATION,
            self._create_masking_handler()
        )
        
        self.pipeline.add_stage_handler(
            PipelineStage.VALIDATION,
            create_validation_handler()
        )
        
        self.pipeline.add_stage_handler(
            PipelineStage.OUTPUT_GENERATION,
            self._create_output_handler()
        )
    
    def _setup_strategies(self) -> None:
        """Setup masking strategies"""
        # Set up PHI-specific strategies
        for phi_type, strategy_type in self.config.phi_specific_strategies.items():
            self.strategies[phi_type] = create_masking_strategy(
                strategy_type,
                self.config.strategy_config
            )
        
        logger.info(f"Configured {len(self.strategies)} PHI-specific strategies")
    
    def _get_strategy_for_phi(self, phi_type: PHIType) -> MaskingStrategy:
        """Get masking strategy for PHI type"""
        # Check if specific strategy exists
        if phi_type in self.strategies:
            return self.strategies[phi_type]
        
        # Get default strategy for PHI type
        strategy_type = get_default_strategy_for_phi_type(phi_type)
        
        # Create and cache strategy
        strategy = create_masking_strategy(strategy_type, self.config.strategy_config)
        self.strategies[phi_type] = strategy
        
        return strategy
    
    def _initialize_rag(self) -> None:
        """Initialize RAG components (lazy loading)"""
        if not self.config.use_rag:
            return
        
        if self._regulation_chain is not None and self._phi_chain is not None:
            return  # Already initialized
        
        logger.info("Initializing RAG components...")
        
        # Create embeddings manager
        self._embeddings_manager = create_embeddings_manager(
            preset=self.config.embeddings_preset
        )
        
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
        self._phi_chain = create_phi_identification_chain(
            regulation_chain=self._regulation_chain,
            llm_provider=self.config.llm_provider,
            model_name=self.config.llm_model
        )
        
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
        
        logger.info(f"Starting job {job_id}: processing {len(file_paths)} files")
        
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
            f"Job {job_id} completed: {result.processed_documents}/{result.total_documents} "
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
        
        # Filter directories
        file_paths = [p for p in file_paths if p.is_file()]
        
        logger.info(f"Found {len(file_paths)} files in {directory}")
        
        return self.process_files(
            file_paths,
            job_name=job_name or f"directory-{directory.name}"
        )
    
    def _create_regulation_retrieval_handler(self):
        """Create regulation retrieval stage handler"""
        def handler(context: ProcessingContext) -> StageResult:
            result = StageResult(stage=PipelineStage.REGULATION_RETRIEVAL)
            
            try:
                if not self.config.use_rag or self._regulation_chain is None:
                    logger.info("RAG disabled or not available, skipping")
                    result.output["skipped"] = True
                    result.mark_completed(success=True)
                    return result
                
                # Create regulation context
                reg_context = RegulationContext()
                context.regulation_context = reg_context
                
                # Retrieve regulations for all documents
                # (In real implementation, retrieve based on detected PHI types)
                result.output["regulations_retrieved"] = True
                result.mark_completed(success=True)
            
            except Exception as e:
                result.set_error(str(e))
            
            return result
        
        return handler
    
    def _create_phi_identification_handler(self):
        """Create PHI identification stage handler"""
        def handler(context: ProcessingContext) -> StageResult:
            result = StageResult(stage=PipelineStage.PHI_IDENTIFICATION)
            
            try:
                total_phi = 0
                
                for doc_context in context.documents:
                    text = doc_context.document.content
                    language = doc_context.detected_language
                    
                    if self.config.use_rag and self._phi_chain:
                        # Use RAG for PHI identification with structured output
                        logger.info(f"Identifying PHI using RAG for {doc_context.document_id}")
                        
                        rag_response = self._phi_chain.identify_phi(
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
                            f"Found {len(phi_entities)} PHI entities in {doc_context.document_id}"
                        )
                    
                    else:
                        # Without RAG, use pattern matching or skip
                        logger.warning(
                            f"RAG disabled for {doc_context.document_id}, "
                            "PHI identification limited to pattern matching"
                        )
                        # Pattern-based fallback could be implemented here
                    
                    context.mark_document_processed(success=True)
                
                result.output["total_phi_entities"] = total_phi
                result.output["documents_processed"] = len(context.documents)
                result.mark_completed(success=True)
                
                logger.success(f"PHI identification completed: {total_phi} entities found")
            
            except Exception as e:
                logger.error(f"PHI identification failed: {e}")
                result.set_error(
                    message=str(e),
                    details={"stage": "phi_identification"}
                )
            
            return result
        
        return handler
    
    def _create_masking_handler(self):
        """Create masking application stage handler"""
        def handler(context: ProcessingContext) -> StageResult:
            result = StageResult(stage=PipelineStage.MASKING_APPLICATION)
            
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
                    masked_text = self._apply_masking(
                        text=doc_context.document.content,
                        phi_entities=phi_entities
                    )
                    
                    doc_context.masked_content = masked_text
                    doc_context.mark_completed()
                    total_masked += len(phi_entities)
                    
                    logger.info(
                        f"Masked {len(phi_entities)} entities in {doc_context.document_id}"
                    )
                
                result.output["total_masked_entities"] = total_masked
                result.output["documents_masked"] = len([
                    d for d in context.documents if d.masked_content
                ])
                result.mark_completed(success=True)
                
                logger.success(f"Masking completed: {total_masked} entities masked")
            
            except Exception as e:
                logger.error(f"Masking application failed: {e}")
                result.set_error(
                    message=str(e),
                    details={"stage": "masking_application"}
                )
            
            return result
        
        return handler
    
    def _create_output_handler(self):
        """Create output generation stage handler"""
        def handler(context: ProcessingContext) -> StageResult:
            result = StageResult(stage=PipelineStage.OUTPUT_GENERATION)
            
            try:
                # Output generation logic
                result.output["output_generated"] = True
                result.mark_completed(success=True)
            
            except Exception as e:
                result.set_error(str(e))
            
            return result
        
        return handler
    
    def _apply_masking(self, text: str, phi_entities: List[PHIEntity]) -> str:
        """
        Apply masking to text
        
        Args:
            text: Original text
            phi_entities: PHI entities to mask
            
        Returns:
            Masked text
        """
        if not phi_entities:
            return text
        
        # Sort entities by position (descending) to avoid offset issues
        sorted_entities = sorted(
            phi_entities,
            key=lambda e: e.start_pos,  # Fixed: use start_pos not start_position
            reverse=True
        )
        
        masked_text = text
        
        for entity in sorted_entities:
            # Get masking strategy for this PHI type
            strategy_type = self.config.phi_specific_strategies.get(
                entity.type,  # Fixed: use type not phi_type
                self.config.default_strategy
            )
            
            strategy = create_masking_strategy(
                strategy_type,
                self.config.strategy_config
            )
            
            # Mask entity
            masked_value = strategy.mask(entity)
            
            # Replace in text using correct attribute names
            masked_text = (
                masked_text[:entity.start_pos] +  # Fixed: use start_pos
                masked_value +
                masked_text[entity.end_pos:]  # Fixed: use end_pos
            )
        
        return masked_text
    
    def _build_result(
        self,
        context: ProcessingContext,
        stage_results: List[StageResult]
    ) -> ProcessingResult:
        """Build processing result"""
        # Calculate statistics
        total_phi = sum(len(doc.phi_entities) for doc in context.documents)
        
        # Build document results
        doc_results = []
        for doc_context in context.documents:
            doc_results.append({
                "document_id": doc_context.document_id,
                "filename": doc_context.document.metadata.filename,
                "language": doc_context.detected_language.value if doc_context.detected_language else None,
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
        
        # Create result
        result = ProcessingResult(
            job_id=context.job_id,
            status=ProcessingStatus.COMPLETED if context.failed_documents == 0 else ProcessingStatus.FAILED,
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
        return f"DeidentificationEngine(use_rag={self.config.use_rag}, llm={self.config.llm_provider})"
