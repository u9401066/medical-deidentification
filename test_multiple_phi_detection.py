"""
測試 RAG Structured Output 是否能正確識別多個 PHI
驗證 PHIDetectionResponse 的 List[PHIIdentificationResult] 功能
"""

import os
from dotenv import load_dotenv
from loguru import logger

load_dotenv()

from medical_deidentification.infrastructure.rag.regulation_retrieval_chain import (
    create_regulation_retrieval_chain
)
from medical_deidentification.infrastructure.rag.regulation_store import (
    RegulationVectorStore
)
from medical_deidentification.infrastructure.rag.embeddings import (
    EmbeddingsManager
)
from medical_deidentification.infrastructure.llm.config import LLMConfig
from medical_deidentification.infrastructure.rag.phi_identification_chain import (
    PHIIdentificationConfig,
    PHIIdentificationChain,
    PHIDetectionResponse
)


def test_multiple_phi_detection():
    """測試包含多個 PHI 的文本"""
    
    logger.info("="*80)
    logger.info("測試多個 PHI 識別能力")
    logger.info("="*80 + "\n")
    
    # 測試文本：包含多種 PHI 類型
    test_cases = [
        {
            "name": "Test 1: 簡單案例 (3個PHI)",
            "text": """
            Patient 陳大明 (Chen Ta-Ming), 45歲男性。
            聯絡電話: 02-2345-6789
            地址: 台北市信義區忠孝東路123號
            """,
            "expected_phi_types": ["NAME", "AGE", "PHONE", "ADDRESS"],
            "expected_min_count": 3
        },
        {
            "name": "Test 2: 複雜案例 (7+個PHI)",
            "text": """
            Patient 王小華, 94歲女性, 患有法布瑞氏症 (Fabry disease)。
            身分證: A123456789
            Medicare ID: H987654321
            就診日期: 2024年11月15日
            主治醫師: Dr. 李建國
            病患住在新北市板橋區中山路456號7樓
            緊急聯絡人: 女兒 王美麗, 電話 0912-345-678
            """,
            "expected_phi_types": ["NAME", "AGE_OVER_89", "DISEASE", "ID", "DATE", "DOCTOR", "ADDRESS", "PHONE"],
            "expected_min_count": 7
        },
        {
            "name": "Test 3: 邊界案例 (年齡、罕病)",
            "text": """
            案例編號: CASE-2024-001
            92歲男性患者，診斷為龐貝氏症 (Pompe disease)
            居住於台中市西屯區已35年
            """,
            "expected_phi_types": ["ID", "AGE_OVER_89", "DISEASE", "ADDRESS"],
            "expected_min_count": 3
        }
    ]
    
    # 初始化 PHI chain
    logger.info("初始化 PHI identification chain...")
    embeddings_manager = EmbeddingsManager()
    
    try:
        vector_store = RegulationVectorStore.load(embeddings_manager=embeddings_manager)
        logger.success("Loaded regulation vector store")
    except:
        logger.error("Failed to load vector store")
        return
    
    regulation_chain = create_regulation_retrieval_chain(vector_store=vector_store)
    
    llm_config = LLMConfig(
        provider="openai",
        model_name="gpt-4o-mini",
        temperature=0.0,
        timeout=30.0
    )
    
    phi_config = PHIIdentificationConfig(
        llm_config=llm_config,
        retrieve_regulation_context=False,  # 快速測試
        use_structured_output=True
    )
    
    phi_chain = PHIIdentificationChain(regulation_chain, phi_config)
    logger.success("PHI chain initialized\n")
    
    # 執行測試
    results_summary = []
    
    for i, test_case in enumerate(test_cases, 1):
        logger.info("="*80)
        logger.info(f"{test_case['name']}")
        logger.info("="*80)
        logger.info(f"測試文本: {test_case['text'].strip()[:100]}...")
        logger.info(f"期望最少識別: {test_case['expected_min_count']} 個 PHI\n")
        
        try:
            # 執行識別
            result = phi_chain.identify_phi(
                text=test_case['text'],
                language="zh-TW",
                return_entities=True
            )
            
            entities = result.get("entities", [])
            raw_results = result.get("raw_results", [])
            
            # 顯示結果
            logger.info(f"✓ 識別到 {len(entities)} 個 PHI entities:")
            
            for j, entity in enumerate(entities, 1):
                logger.info(f"\n  [{j}] PHI Entity:")
                logger.info(f"      Text: '{entity.text}'")
                logger.info(f"      Type: {entity.type.value}")
                logger.info(f"      Position: {entity.start_pos}-{entity.end_pos}")
                logger.info(f"      Confidence: {entity.confidence:.2%}")
                if entity.reason:
                    logger.info(f"      Reason: {entity.reason[:80]}...")
            
            # 驗證結果
            passed = len(entities) >= test_case['expected_min_count']
            
            if passed:
                logger.success(f"\n✓ PASS: 識別到 {len(entities)} 個 PHI (期望 ≥{test_case['expected_min_count']})")
            else:
                logger.warning(f"\n✗ FAIL: 只識別到 {len(entities)} 個 PHI (期望 ≥{test_case['expected_min_count']})")
            
            results_summary.append({
                "test": test_case['name'],
                "expected": test_case['expected_min_count'],
                "actual": len(entities),
                "passed": passed
            })
            
        except Exception as e:
            logger.error(f"✗ ERROR: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            results_summary.append({
                "test": test_case['name'],
                "expected": test_case['expected_min_count'],
                "actual": 0,
                "passed": False,
                "error": str(e)
            })
        
        logger.info("\n")
    
    # 總結
    logger.info("="*80)
    logger.info("測試總結")
    logger.info("="*80 + "\n")
    
    for result in results_summary:
        status = "✓ PASS" if result['passed'] else "✗ FAIL"
        logger.info(f"{status} | {result['test']}")
        logger.info(f"       Expected: ≥{result['expected']} PHI, Got: {result['actual']} PHI")
        if 'error' in result:
            logger.info(f"       Error: {result['error']}")
        logger.info("")
    
    total_tests = len(results_summary)
    passed_tests = sum(1 for r in results_summary if r['passed'])
    
    logger.info(f"總測試: {total_tests}")
    logger.info(f"通過: {passed_tests}")
    logger.info(f"失敗: {total_tests - passed_tests}")
    logger.info(f"成功率: {passed_tests/total_tests*100:.1f}%\n")
    
    if passed_tests == total_tests:
        logger.success("🎉 所有測試通過！RAG 可以正確識別多個 PHI。")
    else:
        logger.warning(f"⚠️ {total_tests - passed_tests} 個測試失敗，需要檢查。")


if __name__ == "__main__":
    test_multiple_phi_detection()
