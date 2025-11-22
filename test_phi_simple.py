"""
簡單的 PHI 識別測試
測試單一文本的 PHI 識別功能
"""

import os
from dotenv import load_dotenv
from loguru import logger

# Load environment variables
load_dotenv()

# Import necessary components
from medical_deidentification.infrastructure.rag.phi_identification_chain import (
    create_phi_identification_chain
)
from medical_deidentification.infrastructure.rag.regulation_retrieval_chain import (
    create_regulation_retrieval_chain
)
from medical_deidentification.infrastructure.rag.regulation_store import (
    RegulationVectorStore
)
from medical_deidentification.infrastructure.embeddings.manager import (
    EmbeddingsManager
)


def main():
    logger.info("=== Simple PHI Identification Test ===\n")
    
    # Test text with obvious PHI
    test_text = """
    Patient 陳大明 (Mr. Chen Ta-Ming), 45-year-old male.
    Date of Birth: January 15, 1979.
    Contact phone: 02-2345-6789.
    Address: 台北市信義區忠孝東路123號.
    Treated by Dr. 王小華 at 台大醫院.
    """
    
    logger.info(f"Test text:\n{test_text}\n")
    
    # Initialize embeddings manager
    embeddings_manager = EmbeddingsManager()
    
    # Load regulation vector store (or skip it)
    logger.info("Loading regulation vector store...")
    try:
        vector_store = RegulationVectorStore.load(
            embeddings_manager=embeddings_manager
        )
        logger.success("Loaded regulation vector store")
        
        # Create regulation retrieval chain
        regulation_chain = create_regulation_retrieval_chain(
            vector_store=vector_store
        )
    except Exception as e:
        logger.warning(f"Could not load vector store: {e}")
        logger.info("Creating dummy regulation chain...")
        regulation_chain = None
    
    if regulation_chain is None:
        logger.error("Cannot proceed without regulation chain")
        return
    
    # Create PHI identification chain (without regulation context)
    logger.info("Creating PHI identification chain...")
    phi_chain = create_phi_identification_chain(
        regulation_chain=regulation_chain,
        llm_provider="openai",
        model_name="gpt-4o-mini",
        retrieve_regulation_context=False  # Disable to avoid issues
    )
    logger.success("PHI chain created\n")
    
    # Identify PHI
    logger.info("Identifying PHI...")
    try:
        result = phi_chain.identify_phi(
            text=test_text,
            language="zh-TW",
            return_entities=True
        )
        
        entities = result.get("entities", [])
        logger.success(f"Found {len(entities)} PHI entities:\n")
        
        for i, entity in enumerate(entities, 1):
            logger.info(f"{i}. {entity.entity_text}")
            logger.info(f"   Type: {entity.phi_type}")
            logger.info(f"   Reason: {entity.reason}")
            logger.info(f"   Confidence: {entity.confidence:.2f}\n")
        
        if len(entities) == 0:
            logger.warning("No PHI detected!")
            
    except Exception as e:
        logger.error(f"Error identifying PHI: {e}")
        import traceback
        logger.error(traceback.format_exc())


if __name__ == "__main__":
    main()
