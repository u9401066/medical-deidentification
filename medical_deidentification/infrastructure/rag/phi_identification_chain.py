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
from dataclasses import replace
from pydantic import BaseModel, Field, field_validator
from loguru import logger

from ..llm.config import LLMConfig
from ..llm.factory import create_llm
from ..prompts import (
    get_phi_identification_prompt,
    get_phi_validation_prompt,
    DEFAULT_HIPAA_SAFE_HARBOR_RULES,
)
from ...domain import PHIType, PHIEntity, get_default_mapper
from .regulation_retrieval_chain import RegulationRetrievalChain
from .medical_retriever import MedicalTextRetriever, MedicalRetrieverConfig
from .embeddings import EmbeddingsManager

# Import PHI identification models from domain layer
from ...domain.phi_identification_models import (
    PHIIdentificationResult,
    PHIDetectionResponse,
    PHIIdentificationConfig,
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
        regulation_chain: Optional[RegulationRetrievalChain] = None,
        config: Optional[PHIIdentificationConfig] = None,
        embeddings_manager: Optional[EmbeddingsManager] = None,
        max_text_length: int = 2000,  # 超過此長度則分段處理
    ):
        """
        Initialize PHI identification chain
        
        Args:
            regulation_chain: RegulationRetrievalChain for retrieving regulation context
                             (Optional when retrieve_regulation_context=False)
            config: Chain configuration
            embeddings_manager: For MedicalTextRetriever (optional, created if None)
            max_text_length: Maximum text length before chunking (default: 2000)
        """
        self.regulation_chain = regulation_chain
        self.config = config or PHIIdentificationConfig()
        self.max_text_length = max_text_length
        
        # Validate: if retrieve_regulation_context=True, regulation_chain must be provided
        if self.config.retrieve_regulation_context and regulation_chain is None:
            raise ValueError(
                "regulation_chain is required when retrieve_regulation_context=True"
            )
        
        # Initialize LLM
        self.llm = create_llm(self.config.llm_config)
        
        # Initialize MedicalTextRetriever for long text handling
        if embeddings_manager is None:
            embeddings_manager = EmbeddingsManager()
        
        medical_config = MedicalRetrieverConfig(
            chunk_size=500,
            chunk_overlap=50,
            k=5  # Retrieve top 5 relevant chunks
        )
        self.medical_retriever = MedicalTextRetriever(embeddings_manager, medical_config)
        
        logger.info(
            f"PHIIdentificationChain initialized with "
            f"LLM: {self.config.llm_config.provider}/{self.config.llm_config.model_name}, "
            f"max_text_length: {max_text_length}"
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
        
        Uses chunking strategy for long texts to avoid LLM context limits:
        - Text <= max_text_length: Process directly
        - Text > max_text_length: Use MedicalTextRetriever to chunk and process
        
        使用分段策略處理長文本以避免 LLM 上下文限制：
        - 文本 <= max_text_length：直接處理
        - 文本 > max_text_length：使用 MedicalTextRetriever 分段處理
        
        Args:
            text: Medical text to analyze
            language: Language code (e.g., "zh-TW", "en")
            return_source: Whether to return source regulation documents
            return_entities: Whether to return identified entities
            
        Returns:
            Dictionary with:
            - text: Original text
            - language: Detected/provided language
            - total_entities: Count of entities
            - has_phi: Whether PHI was found
            - entities: List[PHIEntity] (if return_entities=True)
            - raw_results: List[PHIIdentificationResult] (if return_entities=True)
            - source_documents: Regulation docs used (if return_source=True)
        """
        logger.info(f"Identifying PHI in text ({len(text)} chars)")
        
        # Check if text needs chunking
        if len(text) > self.max_text_length:
            logger.warning(
                f"Text length ({len(text)}) exceeds max_text_length ({self.max_text_length}), "
                f"using chunked processing"
            )
            return self._identify_phi_chunked(text, language, return_source, return_entities)
        else:
            return self._identify_phi_direct(text, language, return_source, return_entities)
    
    def _identify_phi_direct(
        self,
        text: str,
        language: Optional[str],
        return_source: bool,
        return_entities: bool
    ) -> Dict[str, Any]:
        """
        Direct PHI identification for short texts (original implementation)
        短文本的直接 PHI 識別（原始實現）
        """
        # Step 1: Retrieve regulation context
        regulation_docs = []
        context = ""
        
        if self.config.retrieve_regulation_context and self.regulation_chain:
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
        else:
            # Use centralized default regulations from prompts module
            context = DEFAULT_HIPAA_SAFE_HARBOR_RULES
        
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
    
    def _identify_phi_chunked(
        self,
        text: str,
        language: Optional[str],
        return_source: bool,
        return_entities: bool
    ) -> Dict[str, Any]:
        """
        Chunked PHI identification for long texts using MedicalTextRetriever
        使用 MedicalTextRetriever 對長文本進行分段 PHI 識別
        
        Strategy:
        1. Split text into chunks using MedicalTextRetriever
        2. Process each chunk independently
        3. Merge results and adjust positions
        
        策略：
        1. 使用 MedicalTextRetriever 將文本分段
        2. 獨立處理每個分段
        3. 合併結果並調整位置
        """
        logger.info(f"Processing long text ({len(text)} chars) with chunking")
        
        # Get regulation context once (shared across all chunks)
        regulation_docs = []
        context = ""
        
        if self.config.retrieve_regulation_context and self.regulation_chain:
            query_context = text[:500]
            if language:
                query_context = f"[Language: {language}]\n\n{query_context}"
            
            regulation_docs = self.regulation_chain.retrieve_by_context(
                medical_context=query_context,
                k=self.config.regulation_context_k
            )
            
            context = "\n\n".join([
                f"[{doc.metadata.get('source', 'Unknown')}]\n{doc.page_content}"
                for doc in regulation_docs
            ])
        else:
            context = DEFAULT_HIPAA_SAFE_HARBOR_RULES
        
        # Split text into chunks
        chunks = self.medical_retriever._split_text(text)
        logger.info(f"Split into {len(chunks)} chunks")
        
        # Process each chunk
        all_entities = []
        all_raw_results = []
        current_position = 0
        
        for i, chunk in enumerate(chunks):
            logger.debug(f"Processing chunk {i+1}/{len(chunks)} (pos: {current_position})")
            
            # Identify PHI in this chunk
            if self.config.use_structured_output:
                chunk_entities, chunk_raw = self._identify_phi_structured(
                    text=chunk,
                    context=context,
                    language=language
                )
            else:
                chunk_entities, chunk_raw = self._identify_phi_json_fallback(
                    text=chunk,
                    context=context,
                    language=language
                )
            
            # Adjust positions to match original text
            for entity in chunk_entities:
                # Find entity text in original document starting from current_position
                entity_start = text.find(entity.text, current_position)
                if entity_start != -1:
                    # Create adjusted entity
                    adjusted_entity = replace(
                        entity,
                        start_pos=entity_start,
                        end_pos=entity_start + len(entity.text)
                    )
                    all_entities.append(adjusted_entity)
                else:
                    # Fallback: use relative position + current_position
                    adjusted_entity = replace(
                        entity,
                        start_pos=current_position + entity.start_pos,
                        end_pos=current_position + entity.end_pos
                    )
                    all_entities.append(adjusted_entity)
            
            all_raw_results.extend(chunk_raw)
            current_position += len(chunk)
        
        # Remove duplicates (entities found in overlapping chunks)
        unique_entities = self._deduplicate_entities(all_entities)
        
        logger.success(
            f"Chunked PHI identification complete: "
            f"{len(unique_entities)} unique entities found from {len(all_entities)} total"
        )
        
        # Build response
        response = {
            "text": text,
            "language": language,
            "total_entities": len(unique_entities),
            "has_phi": len(unique_entities) > 0,
            "chunked": True,
            "chunk_count": len(chunks),
        }
        
        if return_entities:
            response["entities"] = unique_entities
            response["raw_results"] = [r.model_dump() for r in all_raw_results]
        
        if return_source:
            response["source_documents"] = [
                {
                    "content": doc.page_content,
                    "metadata": doc.metadata
                }
                for doc in regulation_docs
            ]
        
        return response
    
    def _deduplicate_entities(self, entities: List[PHIEntity]) -> List[PHIEntity]:
        """
        Remove duplicate entities based on text and position overlap
        根據文本和位置重疊移除重複實體
        """
        if not entities:
            return []
        
        # Sort by start position
        sorted_entities = sorted(entities, key=lambda e: e.start_pos)
        
        unique = []
        for entity in sorted_entities:
            # Check if this entity overlaps with any existing unique entity
            is_duplicate = False
            for existing in unique:
                # Check for overlap
                if (entity.start_pos < existing.end_pos and 
                    entity.end_pos > existing.start_pos):
                    # Overlapping entities
                    if entity.text == existing.text:
                        is_duplicate = True
                        break
                    # If text similar (>80% overlap), consider duplicate
                    overlap_len = min(entity.end_pos, existing.end_pos) - max(entity.start_pos, existing.start_pos)
                    min_len = min(len(entity.text), len(existing.text))
                    if overlap_len / min_len > 0.8:
                        is_duplicate = True
                        break
            
            if not is_duplicate:
                unique.append(entity)
        
        return unique
    
    def _identify_phi_structured(
        self,
        text: str,
        context: str,
        language: Optional[str]
    ) -> Tuple[List[PHIEntity], List[PHIIdentificationResult]]:
        """
        Identify PHI using Ollama native structured output
        
        Uses Ollama's native format parameter with Pydantic schema
        for better performance and reliability.
        
        Returns:
            Tuple of (PHIEntity list, PHIIdentificationResult list)
        """
        # Get prompt template
        prompt_template = get_phi_identification_prompt(
            language=language or "en",
            structured=True
        )
        prompt = prompt_template.format(context=context, text=text)
        
        try:
            # Check if using Ollama (check model name or endpoint)
            # Attempt to use Ollama native structured output
            if hasattr(self.llm, 'model') and 'llama' in str(self.llm.model).lower():
                try:
                    import ollama
                    
                    # Extract model name from LLM config
                    model_name = self.llm.model if hasattr(self.llm, 'model') else 'llama3.1:8b'
                    
                    logger.debug(f"Using Ollama native structured output with model: {model_name}")
                    
                    # Use Ollama native structured output with timeout
                    # Note: ollama.chat() doesn't have built-in timeout, use httpx timeout from config
                    client = ollama.Client(host='http://localhost:11434', timeout=120.0)
                    response = client.chat(
                        model=model_name,
                        messages=[{
                            'role': 'user',
                            'content': prompt
                        }],
                        format=PHIDetectionResponse.model_json_schema(),
                    )
                    
                    # Parse response
                    detection_response = PHIDetectionResponse.model_validate_json(
                        response['message']['content']
                    )
                    
                    # Convert to domain entities
                    entities = [result.to_phi_entity() for result in detection_response.entities]
                    
                    logger.debug(f"Ollama structured output successful: {len(entities)} entities")
                    return entities, detection_response.entities
                    
                except ImportError:
                    logger.warning("ollama package not available, falling back to LangChain wrapper")
                except Exception as e:
                    logger.warning(f"Ollama native structured output failed: {e}, falling back to LangChain")
            
            # Fallback to LangChain with_structured_output
            logger.debug("Using LangChain with_structured_output")
            llm_structured = self.llm.with_structured_output(PHIDetectionResponse)
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
        
        response_text = ""  # Initialize for error logging
        try:
            # Use invoke() for compatibility with all LangChain chat models
            response = self.llm.invoke(prompt)
            # Get content from response (handles both old and new LangChain versions)
            response_text = response.content if hasattr(response, 'content') else str(response)
            
            # Clean markdown code blocks (```json ... ``` or ``` ... ```)
            import re
            response_text = re.sub(r'^```(?:json)?\s*', '', response_text.strip())
            response_text = re.sub(r'\s*```$', '', response_text.strip())
            
            # Try to extract JSON from response text if it contains extra text
            # Look for JSON array pattern [...]
            json_match = re.search(r'\[[\s\S]*\]', response_text)
            if json_match:
                json_str = json_match.group(0)
                logger.debug(f"Extracted JSON from response: {json_str[:200]}...")
            else:
                json_str = response_text
                logger.debug(f"Using full response as JSON: {response_text[:200]}...")
            
            json_data = json.loads(json_str)
            
            raw_results = [PHIIdentificationResult(**item) for item in json_data]
            entities = [result.to_phi_entity() for result in raw_results]
            
            return entities, raw_results
            
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"JSON parsing failed: {e}")
            logger.error(f"Response text (first 500 chars): {response_text[:500]}")
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
        
        if retrieve_evidence and self.regulation_chain:
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
            "regulation_chain_stats": self.regulation_chain.get_chain_stats() if self.regulation_chain else {}
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
