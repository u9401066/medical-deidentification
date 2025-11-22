"""
Simple PHI Identification Test
測試簡單的 PHI 識別
"""

import sys
from pathlib import Path
from loguru import logger

# Setup logging
logger.remove()
logger.add(sys.stdout, level="INFO")
log_file = f"test_simple_{Path(__file__).stem}.log"
logger.add(log_file, level="DEBUG")
logger.info(f"Log file created: {log_file}")

from medical_deidentification.infrastructure.llm.config import LLMConfig
from medical_deidentification.infrastructure.rag.phi_identification_chain import (
    PHIIdentificationChain,
    PHIIdentificationConfig
)


def test_simple_text():
    """測試簡單文本"""
    
    logger.info("=== Test 1: Simple Patient Name ===")
    
    # Configure Ollama
    llm_config = LLMConfig(
        provider="ollama",
        model_name="llama3.1:8b",
        temperature=0.0,
        timeout=120,
    )
    
    config = PHIIdentificationConfig(
        llm_config=llm_config,
        use_structured_output=False,
        retrieve_regulation_context=False,
    )
    
    # Initialize chain
    logger.info("Initializing PHI chain...")
    chain = PHIIdentificationChain(config=config)
    
    # Test text
    text = "患者姓名：王小明，年齡：45歲，病歷號：A123456"
    
    logger.info(f"Testing text: {text}")
    
    try:
        result = chain.identify_phi(text)
        
        logger.success(f"✓ Detected {len(result)} PHI entities")
        for i, entity in enumerate(result, 1):
            logger.info(f"  {i}. {entity.type.value}: '{entity.text}' (confidence: {entity.confidence:.2f})")
            if entity.reason:
                logger.debug(f"     Reason: {entity.reason}")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


def test_multiple_texts():
    """測試多個短文本"""
    
    logger.info("\n=== Test 2: Multiple Short Texts ===")
    
    llm_config = LLMConfig(
        provider="ollama",
        model_name="llama3.1:8b",
        temperature=0.0,
        timeout=120,
    )
    
    config = PHIIdentificationConfig(
        llm_config=llm_config,
        use_structured_output=False,
        retrieve_regulation_context=False,
    )
    
    chain = PHIIdentificationChain(config=config)
    
    test_cases = [
        "電話：0912-345-678",
        "Email: patient@example.com",
        "住址：台北市信義區",
    ]
    
    success_count = 0
    for i, text in enumerate(test_cases, 1):
        logger.info(f"\nTest case {i}/{len(test_cases)}: {text}")
        try:
            result = chain.identify_phi(text)
            logger.success(f"✓ Found {len(result)} entities")
            for entity in result:
                logger.info(f"  - {entity.type.value}: {entity.text}")
            success_count += 1
        except Exception as e:
            logger.error(f"✗ Failed: {e}")
    
    logger.info(f"\nSuccess rate: {success_count}/{len(test_cases)}")
    return success_count == len(test_cases)


if __name__ == "__main__":
    logger.info("Starting Simple PHI Identification Tests")
    logger.info("=" * 60)
    
    # Test 1: Simple text
    test1_ok = test_simple_text()
    
    # Test 2: Multiple texts
    if test1_ok:
        test2_ok = test_multiple_texts()
    else:
        logger.warning("Skipping Test 2 due to Test 1 failure")
        test2_ok = False
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("Test Summary:")
    logger.info(f"  Test 1 (Simple Text): {'✓ PASS' if test1_ok else '✗ FAIL'}")
    logger.info(f"  Test 2 (Multiple Texts): {'✓ PASS' if test2_ok else '✗ FAIL'}")
    logger.info("=" * 60)
    
    sys.exit(0 if (test1_ok and test2_ok) else 1)
