"""
Regulation RAG Chain
法規 RAG 鏈

LangChain-based RAG system for regulation retrieval and PHI identification.
基於 LangChain 的 RAG 系統，用於法規檢索和 PHI 識別。
"""

from typing import List, Dict, Any, Optional, Tuple
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain.schema import Document
from pydantic import BaseModel, Field
from loguru import logger

from .regulation_store import RegulationVectorStore
from .retriever import RegulationRetriever, RetrieverConfig
from ...domain.models import PHIType, SupportedLanguage


class RAGChainConfig(BaseModel):
    """RAG 鏈配置"""
    
    llm_provider: str = Field(
        default="openai",
        description="LLM provider: 'openai' or 'anthropic'"
    )
    model_name: str = Field(
        default="gpt-4",
        description="Model name"
    )
    temperature: float = Field(
        default=0.0,
        description="LLM temperature (0=deterministic)"
    )
    max_tokens: Optional[int] = Field(
        default=None,
        description="Max tokens in response"
    )
    retriever_config: RetrieverConfig = Field(
        default_factory=RetrieverConfig,
        description="Retriever configuration"
    )


class RegulationRAGChain:
    """
    RAG Chain for regulation-based de-identification
    
    Core innovation: Retrieves "what to mask" instead of "what to preserve"
    
    核心創新：檢索「需要遮蔽的內容」而非「需要保留的內容」
    
    Workflow:
    1. User provides medical text
    2. System retrieves relevant regulations (what constitutes PHI)
    3. LLM identifies PHI entities based on regulations
    4. System applies masking strategies
    
    Examples:
        >>> from medical_deidentification.infrastructure.rag import (
        ...     RegulationRAGChain, RegulationVectorStore, EmbeddingsManager
        ... )
        >>> 
        >>> # Setup
        >>> embeddings = EmbeddingsManager()
        >>> store = RegulationVectorStore.load(embeddings_manager=embeddings)
        >>> chain = RegulationRAGChain(store)
        >>> 
        >>> # Identify PHI
        >>> text = "患者張三，94歲，患有法布瑞氏症..."
        >>> phi_entities = chain.identify_phi(text, language="zh-TW")
        >>> 
        >>> # Get masking strategy
        >>> strategy = chain.get_masking_strategy("AGE_OVER_89")
    """
    
    # Prompt template for PHI identification
    PHI_IDENTIFICATION_PROMPT = """You are a medical de-identification expert. Based on the provided regulations, identify all PHI (Protected Health Information) in the given medical text.

Regulations (retrieved from vector store):
{context}

Medical Text:
{question}

Instructions:
1. Identify ALL PHI entities according to the regulations
2. For each entity, provide:
   - entity_text: The exact text from the document
   - phi_type: Type according to regulations (e.g., NAME, AGE_OVER_89, RARE_DISEASE)
   - start_position: Character position where entity starts
   - end_position: Character position where entity ends
   - confidence: Your confidence level (0.0-1.0)
   - reason: Why this is considered PHI according to regulations

3. Special attention to:
   - Ages over 89 (HIPAA Safe Harbor)
   - Ages over 90 (Taiwan regulations)
   - Rare diseases that could identify individuals
   - Genetic information
   - Small geographic areas
   
4. Return results as JSON array:
[
  {{
    "entity_text": "...",
    "phi_type": "...",
    "start_position": 123,
    "end_position": 456,
    "confidence": 0.95,
    "reason": "..."
  }},
  ...
]

If no PHI found, return empty array: []

Answer:"""
    
    def __init__(
        self,
        vector_store: RegulationVectorStore,
        config: Optional[RAGChainConfig] = None
    ):
        """
        Initialize RAG chain
        
        Args:
            vector_store: RegulationVectorStore instance
            config: Chain configuration. Uses defaults if None.
        """
        self.vector_store = vector_store
        self.config = config or RAGChainConfig()
        
        # Initialize LLM
        self.llm = self._create_llm()
        
        # Initialize retriever
        self.retriever = RegulationRetriever(
            vector_store=vector_store,
            config=self.config.retriever_config
        )
        
        # Create QA chain
        self.qa_chain = self._create_qa_chain()
    
    def _create_llm(self):
        """Create LLM based on configuration"""
        if self.config.llm_provider == "openai":
            return ChatOpenAI(
                model=self.config.model_name,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens
            )
        elif self.config.llm_provider == "anthropic":
            return ChatAnthropic(
                model=self.config.model_name,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens
            )
        else:
            raise ValueError(f"Unsupported LLM provider: {self.config.llm_provider}")
    
    def _create_qa_chain(self) -> RetrievalQA:
        """Create RetrievalQA chain"""
        prompt = PromptTemplate(
            template=self.PHI_IDENTIFICATION_PROMPT,
            input_variables=["context", "question"]
        )
        
        chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=self.retriever.base_retriever,
            return_source_documents=True,
            chain_type_kwargs={"prompt": prompt}
        )
        
        return chain
    
    def identify_phi(
        self,
        text: str,
        language: Optional[str] = None,
        return_source: bool = False
    ) -> Dict[str, Any]:
        """
        Identify PHI in medical text using RAG
        
        Args:
            text: Medical text to analyze
            language: Language code (e.g., "zh-TW", "en")
            return_source: Whether to return source regulation documents
            
        Returns:
            Dictionary with PHI entities and optional source documents
        """
        logger.info(f"Identifying PHI in text ({len(text)} chars)")
        
        # Add language context to query if provided
        query = text
        if language:
            query = f"[Language: {language}]\n\n{text}"
        
        # Run RAG chain
        result = self.qa_chain({"query": query})
        
        response = {
            "text": text,
            "language": language,
            "result": result["result"],
        }
        
        if return_source:
            response["source_documents"] = [
                {
                    "content": doc.page_content,
                    "metadata": doc.metadata
                }
                for doc in result.get("source_documents", [])
            ]
        
        logger.success(f"PHI identification complete")
        return response
    
    def get_masking_strategy(
        self,
        phi_type: str,
        k: int = 3
    ) -> List[Document]:
        """
        Retrieve masking strategies for specific PHI type
        
        Args:
            phi_type: PHI type (e.g., "AGE_OVER_89")
            k: Number of regulation documents to retrieve
            
        Returns:
            Relevant regulation documents with masking strategies
        """
        query = f"masking strategy for {phi_type.replace('_', ' ').lower()}"
        
        # Temporarily update retriever config for this query
        original_k = self.retriever.config.k
        self.retriever.update_config(k=k)
        
        docs = self.retriever.retrieve(query)
        
        # Restore original config
        self.retriever.update_config(k=original_k)
        
        return docs
    
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
        
        logger.success(f"Batch identification complete")
        return results
    
    def retrieve_regulations_for_context(
        self,
        phi_types: List[str],
        regulation_source: Optional[str] = None
    ) -> List[Document]:
        """
        Retrieve regulations for multiple PHI types
        
        Args:
            phi_types: List of PHI types
            regulation_source: Filter by source (e.g., "HIPAA", "GDPR")
            
        Returns:
            Relevant regulation documents
        """
        docs = self.retriever.retrieve_multi_phi(
            phi_types=phi_types,
            combine_strategy="union"
        )
        
        # Filter by source if specified
        if regulation_source:
            docs = [
                doc for doc in docs
                if regulation_source.upper() in doc.metadata.get("source", "").upper()
            ]
        
        return docs
    
    def validate_with_regulations(
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
            query = f"{phi_type.replace('_', ' ').lower()}: {entity_text}"
            docs = self.retriever.retrieve(query)
            
            result["evidence"] = [
                {
                    "content": doc.page_content,
                    "source": doc.metadata.get("source", "unknown")
                }
                for doc in docs
            ]
            
            # Use LLM to validate
            validation_prompt = f"""Based on the regulations below, should this entity be masked?

Entity: {entity_text}
Claimed PHI Type: {phi_type}

Regulations:
{chr(10).join([doc.page_content for doc in docs])}

Answer with JSON:
{{
  "should_mask": true/false,
  "confidence": 0.0-1.0,
  "reason": "explanation"
}}
"""
            
            llm_response = self.llm.predict(validation_prompt)
            
            # Parse LLM response (simplified, production needs robust parsing)
            import json
            try:
                validation = json.loads(llm_response)
                result["should_mask"] = validation.get("should_mask", False)
                result["confidence"] = validation.get("confidence", 0.0)
                result["reason"] = validation.get("reason", "")
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse LLM validation response")
        
        return result
    
    def get_chain_stats(self) -> Dict[str, Any]:
        """Get RAG chain statistics"""
        return {
            "llm_provider": self.config.llm_provider,
            "model_name": self.config.model_name,
            "retriever_config": self.retriever.get_config(),
            "vector_store_stats": self.vector_store.get_stats()
        }
    
    def __repr__(self) -> str:
        return (
            f"RegulationRAGChain("
            f"llm={self.config.llm_provider}/{self.config.model_name}, "
            f"retriever={self.retriever.config.search_type})"
        )


def create_regulation_rag_chain(
    vector_store: RegulationVectorStore,
    llm_provider: str = "openai",
    model_name: str = "gpt-4",
    search_type: str = "mmr",
    **kwargs
) -> RegulationRAGChain:
    """
    Factory function to create RAG chain
    
    Args:
        vector_store: RegulationVectorStore instance
        llm_provider: 'openai' or 'anthropic'
        model_name: Model name (e.g., 'gpt-4', 'claude-3-opus-20240229')
        search_type: Retriever search type ('similarity' or 'mmr')
        **kwargs: Additional config parameters
        
    Returns:
        Configured RegulationRAGChain
    
    Examples:
        >>> chain = create_regulation_rag_chain(
        ...     vector_store=store,
        ...     llm_provider="openai",
        ...     model_name="gpt-4",
        ...     search_type="mmr"
        ... )
    """
    retriever_config = RetrieverConfig(search_type=search_type)
    
    config = RAGChainConfig(
        llm_provider=llm_provider,
        model_name=model_name,
        retriever_config=retriever_config,
        **kwargs
    )
    
    return RegulationRAGChain(vector_store, config)
