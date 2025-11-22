"""
測試 Ollama 本地 LLM 整合
Test Ollama Local LLM Integration
"""

from loguru import logger
from medical_deidentification.infrastructure.llm.config import LLMConfig, LLMPresets
from medical_deidentification.infrastructure.llm.factory import create_llm


def test_ollama_connection():
    """測試基本 Ollama 連接"""
    logger.info("="*80)
    logger.info("Test 1: 基本 Ollama 連接測試")
    logger.info("="*80 + "\n")
    
    # 使用預設配置
    config = LLMPresets.local_qwen()
    logger.info(f"Using config: {config}")
    
    try:
        llm = create_llm(config)
        logger.success("✓ LLM created successfully")
        
        # 簡單測試
        logger.info("\nSending test message...")
        response = llm.invoke("Say 'Hello from Ollama!' in one sentence.")
        logger.success(f"✓ Response: {response.content}\n")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Error: {e}")
        import traceback
        logger.debug(traceback.format_exc())
        return False


def test_phi_identification():
    """測試 PHI 識別（無 structured output）"""
    logger.info("="*80)
    logger.info("Test 2: PHI 識別測試（簡單 prompt）")
    logger.info("="*80 + "\n")
    
    test_text = """
    Patient 陳大明, 45歲男性。
    聯絡電話: 02-2345-6789
    地址: 台北市信義區忠孝東路123號
    """
    
    logger.info(f"Test text:\n{test_text}\n")
    
    config = LLMPresets.local_qwen()
    
    try:
        llm = create_llm(config)
        
        prompt = f"""Identify all PHI (Protected Health Information) in the following medical text.
PHI includes: names, ages, phone numbers, addresses, dates, IDs.

Text:
{test_text}

List each PHI found with its type."""
        
        logger.info("Sending PHI identification request...")
        response = llm.invoke(prompt)
        
        logger.success("✓ Response received:")
        logger.info(response.content)
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Error: {e}")
        import traceback
        logger.debug(traceback.format_exc())
        return False


def test_model_comparison():
    """比較不同本地模型"""
    logger.info("="*80)
    logger.info("Test 3: 模型比較測試")
    logger.info("="*80 + "\n")
    
    models = [
        ("qwen2.5:7b", "Qwen 2.5 7B"),
        ("llama3.1:8b", "Llama 3.1 8B"),
    ]
    
    test_prompt = "What is PHI in medical context? Answer in one sentence."
    
    for model_name, display_name in models:
        logger.info(f"\n--- Testing {display_name} ---")
        
        config = LLMConfig(
            provider="ollama",
            model_name=model_name,
            temperature=0.0,
        )
        
        try:
            llm = create_llm(config)
            response = llm.invoke(test_prompt)
            logger.success(f"✓ {display_name}:")
            logger.info(f"  {response.content[:150]}...\n")
            
        except Exception as e:
            logger.warning(f"✗ {display_name} failed: {e}\n")


def main():
    """主測試流程"""
    logger.info("\n" + "="*80)
    logger.info("Ollama 本地 LLM 整合測試")
    logger.info("="*80 + "\n")
    
    logger.info("⚠️ 請確保 Ollama 已安裝並運行:")
    logger.info("   1. 安裝: https://ollama.ai/download")
    logger.info("   2. 啟動: ollama serve")
    logger.info("   3. 下載模型: ollama pull qwen2.5:7b")
    logger.info("")
    
    input("按 Enter 繼續測試...")
    print()
    
    # Test 1: 基本連接
    test1_passed = test_ollama_connection()
    
    if not test1_passed:
        logger.error("基本連接失敗，停止後續測試")
        return
    
    # Test 2: PHI 識別
    test2_passed = test_phi_identification()
    
    # Test 3: 模型比較
    test_model_comparison()
    
    # Summary
    logger.info("\n" + "="*80)
    logger.info("測試總結")
    logger.info("="*80)
    logger.info(f"Test 1 (基本連接): {'✓ PASS' if test1_passed else '✗ FAIL'}")
    logger.info(f"Test 2 (PHI識別):  {'✓ PASS' if test2_passed else '✗ FAIL'}")
    logger.info(f"Test 3 (模型比較): 查看上方輸出")
    logger.info("\n")


if __name__ == "__main__":
    main()
