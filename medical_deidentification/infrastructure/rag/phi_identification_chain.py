"""
PHI Identification Chain | PHI 識別鏈

Chain for identifying PHI entities in medical text using regulation context.
使用法規上下文在醫療文本中識別 PHI 實體的鏈。

職責 Responsibilities:
- Identify PHI entities in medical text
- Use regulation context for accurate identification
- Support structured output (Pydantic models)
- Validate identified entities against regulations
- 在醫療文本中識別 PHI 實體
- 使用法規上下文進行精確識別
- 支援結構化輸出（Pydantic 模型）
- 根據法規驗證識別的實體

NOT responsible for:
- Storing or managing regulation documents (use RegulationRetrievalChain)
- Persisting medical text (uses MedicalTextRetriever for ephemeral processing)
"""

from typing import List, Dict, Any, Optional, Tuple
import json
from pydantic import BaseModel, Field, field_validator
from loguru import logger

from ..llm.config import LLMConfig
from ..llm.factory import create_llm
from ..prompts import (
    get_phi_identification_prompt,
    get_phi_validation_prompt,
)
from ...domain.models import PHIType, PHIEntity
from .regulation_retrieval_chain import RegulationRetrievalChain


class PHIIdentificationResult(BaseModel):
    """
    單個 PHI 實體的結構化識別結果
    
    Structured Output Model for LLM PHI identification results
    """
    
    entity_text: str = Field(
        description="The exact text from the document that was identified as PHI"
    )
    phi_type: PHIType = Field(
        description="PHI type enum (e.g., PHIType.NAME, PHIType.AGE_OVER_89)"
    )
    custom_type_name: Optional[str] = Field(
        default=None,
        description="Custom PHI type name if phi_type is CUSTOM"
    )
    custom_type_description: Optional[str] = Field(
        default=None,
        description="Description of custom PHI type"
    )
    start_position: int = Field(
        ge=0,
        description="Character position where entity starts (0-indexed)"
    )
    end_position: int = Field(
        ge=0,
        description="Character position where entity ends (exclusive)"
    )
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence level (0.0-1.0)"
    )
    reason: str = Field(
        description="Explanation of why this is PHI according to regulations"
    )
    regulation_source: Optional[str] = Field(
        default=None,
        description="Source regulation"
    )
    masking_action: Optional[str] = Field(
        default=None,
        description="Recommended masking action"
    )
    is_custom_from_regulation: bool = Field(
        default=False,
        description="Whether this PHI type was discovered from regulations"
    )
    
    @field_validator('end_position')
    @classmethod
    def validate_position_range(cls, v: int, info) -> int:
        """Ensure end_position >= start_position"""
        if 'start_position' in info.data and v < info.data['start_position']:
            raise ValueError('end_position must be >= start_position')
        return v
    
    @field_validator('custom_type_name')
    @classmethod
    def validate_custom_type(cls, v: Optional[str], info) -> Optional[str]:
        """Ensure CUSTOM type has custom_type_name"""
        if 'phi_type' in info.data and info.data['phi_type'] == PHIType.CUSTOM:
            if not v:
                raise ValueError('custom_type_name required when phi_type is CUSTOM')
        return v
    
    @field_validator('phi_type', mode='before')
    @classmethod
    def normalize_phi_type(cls, v) -> PHIType:
        """Convert string to PHIType enum"""
        if isinstance(v, PHIType):
            return v
        
        if isinstance(v, str):
            # Try direct enum match
            try:
                return PHIType(v.upper())
            except ValueError:
                pass
            
            # Default to CUSTOM for unknown types
            logger.warning(f"Unknown PHI type: {v}, treating as CUSTOM")
            return PHIType.CUSTOM
        
        raise ValueError(f"Invalid phi_type: {v}")
    
    def to_phi_entity(self) -> PHIEntity:
        """Convert to PHIEntity domain model"""
        from ...domain.models import CustomPHIType
        
        custom_type = None
        if self.phi_type == PHIType.CUSTOM and self.custom_type_name:
            custom_type = CustomPHIType(
                name=self.custom_type_name,
                description=self.custom_type_description or self.reason,
                regulation_source=self.regulation_source,
                masking_strategy=self.masking_action,
            )
        
        return PHIEntity(
            type=self.phi_type,
            text=self.entity_text,
            start_pos=self.start_position,
            end_pos=self.end_position,
            confidence=self.confidence,
            regulation_source=self.regulation_source,
            custom_type=custom_type,
        )


class PHIDetectionResponse(BaseModel):
    """Complete PHI detection response (multiple entities)"""
    
    entities: List[PHIIdentificationResult] = Field(
        default_factory=list,
        description="List of detected PHI entities"
    )
    total_entities: int = Field(
        ge=0,
        description="Total number of entities detected"
    )
    has_phi: bool = Field(
        description="Whether any PHI was detected"
    )
    
    @field_validator('total_entities')
    @classmethod
    def validate_total(cls, v: int, info) -> int:
        """Ensure total_entities matches entities count"""
        if 'entities' in info.data and v != len(info.data['entities']):
            raise ValueError('total_entities must match entities list length')
        return v


class PHIIdentificationConfig(BaseModel):
    """Configuration for PHI identification chain"""
    
    llm_config: LLMConfig = Field(
        default_factory=LLMConfig,
        description="LLM configuration"
    )
    use_structured_output: bool = Field(
        default=True,
        description="Use LLM structured output (recommended)"
    )
    retrieve_regulation_context: bool = Field(
        default=True,
        description="Retrieve regulation context before identification"
    )
    regulation_context_k: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Number of regulation documents to retrieve for context"
    )


class PHIIdentificationChain:
    """
    Chain for identifying PHI in medical text
    
    職責：從醫療文本中識別需要 mask 的 PHI 實體
    
    Uses:
    - RegulationRetrievalChain for regulation context
    - LLM for structured PHI identification
    - Centralized prompts module
    
    Examples:
        >>> from medical_deidentification.infrastructure.rag import (
        ...     PHIIdentificationChain,
        ...     RegulationRetrievalChain,
        ...     RegulationVectorStore,
        ...     EmbeddingsManager
        ... )
        >>> 
        >>> # Setup
        >>> embeddings = EmbeddingsManager()
        >>> store = RegulationVectorStore.load(embeddings_manager=embeddings)
        >>> reg_chain = RegulationRetrievalChain(store)
        >>> phi_chain = PHIIdentificationChain(reg_chain)
        >>> 
        >>> # Identify PHI
        >>> medical_text = "患者張三，94歲，患有法布瑞氏症..."
        >>> result = phi_chain.identify_phi(medical_text, language="zh-TW")
        >>> 
        >>> # Get PHI entities
        >>> entities = result["entities"]  # List[PHIEntity]
    """
    
    def __init__(
        self,
        regulation_chain: RegulationRetrievalChain,
        config: Optional[PHIIdentificationConfig] = None
    ):
        """
        Initialize PHI identification chain
        
        Args:
            regulation_chain: RegulationRetrievalChain for retrieving regulation context
            config: Chain configuration
        """
        self.regulation_chain = regulation_chain
        self.config = config or PHIIdentificationConfig()
        
        # Initialize LLM
        self.llm = create_llm(self.config.llm_config)
        
        logger.info(
            f"PHIIdentificationChain initialized with "
            f"LLM: {self.config.llm_config.provider}/{self.config.llm_config.model_name}"
        )
    
    def identify_phi(
        self,
        text: str,
        language: Optional[str] = None,
        return_source: bool = False,
        return_entities: bool = True
    ) -> Dict[str, Any]:
        """
        Identify PHI in medical text
        
        Args:
            text: Medical text to analyze
            language: Language code (e.g., "zh-TW", "en")
            return_source: Whether to return source regulation documents
            return_entities: Whether to return PHIEntity domain objects
            
        Returns:
            Dictionary with:
            - entities: List[PHIEntity] (if return_entities=True)
            - raw_results: List[PHIIdentificationResult]
            - source_documents: List[Document] (if return_source=True)
            - metadata: Detection metadata
        """
        logger.info(f"Identifying PHI in text ({len(text)} chars)")
        
        # Step 1: Retrieve regulation context
        regulation_docs = []
        context = ""
        
        if self.config.retrieve_regulation_context:
            # Use first 500 chars for context query
            query_context = text[:500]
            if language:
                query_context = f"[Language: {language}]\n\n{query_context}"
            
            regulation_docs = self.regulation_chain.retrieve_by_context(
                medical_context=query_context,
                k=self.config.regulation_context_k
            )
            
            # Build context string
            context = "\n\n".join([
                f"[{doc.metadata.get('source', 'Unknown')}]\n{doc.page_content}"
                for doc in regulation_docs
            ])
        
        # Step 2: Identify PHI using LLM
        if self.config.use_structured_output:
            entities, raw_results = self._identify_phi_structured(
                text=text,
                context=context,
                language=language
            )
        else:
            entities, raw_results = self._identify_phi_json_fallback(
                text=text,
                context=context,
                language=language
            )
        
        # Step 3: Build response
        response = {
            "text": text,
            "language": language,
            "total_entities": len(entities),
            "has_phi": len(entities) > 0,
        }
        
        if return_entities:
            response["entities"] = entities
            response["raw_results"] = [r.model_dump() for r in raw_results]
        
        if return_source:
            response["source_documents"] = [
                {
                    "content": doc.page_content,
                    "metadata": doc.metadata
                }
                for doc in regulation_docs
            ]
        
        logger.success(f"PHI identification complete: {len(entities)} entities found")
        return response
    
    def _identify_phi_structured(
        self,
        text: str,
        context: str,
        language: Optional[str]
    ) -> Tuple[List[PHIEntity], List[PHIIdentificationResult]]:
        """
        Identify PHI using LLM structured output
        
        Returns:
            Tuple of (PHIEntity list, PHIIdentificationResult list)
        """
        # Create structured output LLM
        llm_structured = self.llm.with_structured_output(PHIDetectionResponse)
        
        # Get prompt template
        prompt_template = get_phi_identification_prompt(
            language=language or "en",
            structured=True
        )
        prompt = prompt_template.format(context=context, text=text)
        
        try:
            # Get structured response
            detection_response: PHIDetectionResponse = llm_structured.invoke(prompt)
            
            # Convert to domain entities
            entities = [result.to_phi_entity() for result in detection_response.entities]
            
            return entities, detection_response.entities
            
        except Exception as e:
            logger.error(f"Structured output failed: {e}, falling back to JSON parsing")
            return self._identify_phi_json_fallback(text, context, language)
    
    def _identify_phi_json_fallback(
        self,
        text: str,
        context: str,
        language: Optional[str]
    ) -> Tuple[List[PHIEntity], List[PHIIdentificationResult]]:
        """
        Fallback method using JSON parsing
        
        Returns:
            Tuple of (PHIEntity list, PHIIdentificationResult list)
        """
        prompt_template = get_phi_identification_prompt(language=language or "en")
        prompt = prompt_template.format(context=context, question=text)
        
        try:
            response = self.llm.predict(prompt)
            json_data = json.loads(response)
            
            raw_results = [PHIIdentificationResult(**item) for item in json_data]
            entities = [result.to_phi_entity() for result in raw_results]
            
            return entities, raw_results
            
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"JSON parsing failed: {e}")
            return [], []
    
    def validate_entity(
        self,
        entity_text: str,
        phi_type: str,
        retrieve_evidence: bool = True
    ) -> Dict[str, Any]:
        """
        Validate if entity should be masked according to regulations
        
        Args:
            entity_text: The entity text to validate
            phi_type: Claimed PHI type
            retrieve_evidence: Whether to retrieve regulation evidence
            
        Returns:
            Validation result with evidence
        """
        logger.info(f"Validating entity '{entity_text}' as {phi_type}")
        
        result = {
            "entity_text": entity_text,
            "phi_type": phi_type,
            "should_mask": False,
            "confidence": 0.0,
            "evidence": []
        }
        
        if retrieve_evidence:
            # Retrieve relevant regulations
            regulation_docs = self.regulation_chain.get_phi_definitions([phi_type])
            
            result["evidence"] = [
                {
                    "content": doc.page_content,
                    "source": doc.metadata.get("source", "unknown")
                }
                for doc in regulation_docs
            ]
            
            # Use LLM to validate
            validation_prompt_template = get_phi_validation_prompt()
            validation_prompt = validation_prompt_template.format(
                entity_text=entity_text,
                phi_type=phi_type,
                regulations="\n".join([doc.page_content for doc in regulation_docs])
            )
            
            llm_response = self.llm.predict(validation_prompt)
            
            # Parse validation result
            try:
                validation = json.loads(llm_response)
                result["should_mask"] = validation.get("should_mask", False)
                result["confidence"] = validation.get("confidence", 0.0)
                result["reason"] = validation.get("reason", "")
            except json.JSONDecodeError:
                logger.warning("Failed to parse LLM validation response")
        
        return result
    
    def batch_identify(
        self,
        texts: List[str],
        language: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Batch identify PHI in multiple texts
        
        Args:
            texts: List of medical texts
            language: Language code
            
        Returns:
            List of identification results
        """
        logger.info(f"Batch identifying PHI in {len(texts)} texts")
        
        results = []
        for i, text in enumerate(texts):
            logger.debug(f"Processing text {i+1}/{len(texts)}")
            result = self.identify_phi(text, language=language)
            results.append(result)
        
        logger.success("Batch identification complete")
        return results
    
    def get_chain_stats(self) -> Dict[str, Any]:
        """Get chain statistics"""
        return {
            "llm_config": self.config.llm_config.model_dump(),
            "use_structured_output": self.config.use_structured_output,
            "regulation_chain_stats": self.regulation_chain.get_chain_stats()
        }
    
    def __repr__(self) -> str:
        return (
            f"PHIIdentificationChain("
            f"llm={self.config.llm_config.provider}/{self.config.llm_config.model_name}, "
            f"structured_output={self.config.use_structured_output})"
        )


def create_phi_identification_chain(
    regulation_chain: RegulationRetrievalChain,
    llm_provider: str = "openai",
    model_name: str = "gpt-4",
    temperature: float = 0.0,
    use_structured_output: bool = True,
    **kwargs
) -> PHIIdentificationChain:
    """
    Factory function to create PHI identification chain
    
    Args:
        regulation_chain: RegulationRetrievalChain instance
        llm_provider: 'openai' or 'anthropic'
        model_name: Model name (e.g., 'gpt-4')
        temperature: LLM temperature (0.0=deterministic)
        use_structured_output: Whether to use structured output
        **kwargs: Additional config parameters
        
    Returns:
        Configured PHIIdentificationChain
    
    Examples:
        >>> chain = create_phi_identification_chain(
        ...     regulation_chain=reg_chain,
        ...     llm_provider="openai",
        ...     model_name="gpt-4"
        ... )
    """
    from ..llm.config import LLMProvider
    from typing import cast
    
    llm_config = LLMConfig(
        provider=cast(LLMProvider, llm_provider),
        model_name=model_name,
        temperature=temperature
    )
    
    config = PHIIdentificationConfig(
        llm_config=llm_config,
        use_structured_output=use_structured_output,
        **kwargs
    )
    
    return PHIIdentificationChain(regulation_chain, config)
