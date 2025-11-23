"""
簡單批次處理測試範例
Simple Batch Processing Test Example

測試多語言醫療記錄的 PHI 識別
Test PHI identification on multilingual medical records
"""

import sys
from pathlib import Path
from loguru import logger

# 配置日誌
logger.remove()
logger.add(sys.stderr, level="INFO")
logger.add("logs/simple_batch_test_{time}.log", level="DEBUG", rotation="10 MB")

logger.info("="*80)
logger.info("簡單批次處理測試 - Simple Batch Processing Test")
logger.info("="*80)

# 導入必要模組
from medical_deidentification.infrastructure.rag import (
    PHIIdentificationConfig,
    PHIIdentificationChain
)
from medical_deidentification.application.processing import (
    BatchPHIProcessor,
    BatchProcessingConfig,
    save_batch_results
)

def main():
    """主函數"""
    
    # ============= 配置 =============
    
    # 測試文件（使用之前成功的測試檔案）
    test_file = Path("data/test/test_complex_phi_cases.xlsx")
    output_file = Path("test_output/simple_batch_result.xlsx")
    
    if not test_file.exists():
        logger.error(f"❌ 測試文件不存在: {test_file}")
        return 1
    
    logger.info(f"✓ 測試文件: {test_file}")
    
    # PHI 識別配置（使用 Ollama）
    phi_config = PHIIdentificationConfig(
        retrieve_regulation_context=False,  # 不使用 RAG（避免載入 embeddings）
        use_structured_output=True,  # 使用 Ollama native structured output（之前成功的配置）
        llm_config={
            "provider": "ollama",
            "model_name": "llama3.1:8b",
            "temperature": 0.0,
            "timeout": 180,  # 增加超時到 180 秒
        }
    )
    
    # 批次處理配置（處理前 3 行測試）
    batch_config = BatchProcessingConfig(
        max_rows=3,  # 處理前 3 行
        language="zh-TW",
        skip_empty_rows=True,
        combine_columns=True,
        log_progress_interval=1
    )
    
    # ============= 初始化 =============
    
    logger.info("\n初始化 PHI Identification Chain...")
    try:
        phi_chain = PHIIdentificationChain(
            config=phi_config,
            max_text_length=8000  # 增加到 8000（默認 2000）以減少 chunks
        )
        logger.success("✓ PHI Chain 創建成功 (max_text_length=8000)")
    except Exception as e:
        logger.error(f"❌ 創建 PHI Chain 失敗: {e}")
        logger.exception("詳細錯誤:")
        return 1
    
    logger.info("\n初始化 Batch Processor...")
    try:
        processor = BatchPHIProcessor(
            phi_chain=phi_chain,
            config=batch_config
        )
        logger.success("✓ Batch Processor 創建成功")
    except Exception as e:
        logger.error(f"❌ 創建 Batch Processor 失敗: {e}")
        logger.exception("詳細錯誤:")
        return 1
    
    # ============= 處理 =============
    
    logger.info("\n" + "="*80)
    logger.info(f"開始處理（前 {batch_config.max_rows} 行測試）...")
    logger.info("="*80)
    
    try:
        result = processor.process_excel_file(
            str(test_file),
            case_id_column="case_id"  # test_complex_phi_cases.xlsx 的 ID 欄位
        )
        
        # ============= 顯示結果 =============
        
        logger.success("\n" + "="*80)
        logger.success("✅ 處理完成！")
        logger.success("="*80)
        
        # 處理統計
        logger.info(f"\n處理統計:")
        logger.info(f"  總行數: {result.total_rows}")
        logger.info(f"  成功處理: {result.processed_rows}")
        logger.info(f"  總 PHI 實體: {result.total_entities}")
        logger.info(f"  處理時間: {result.total_time:.2f} 秒")
        logger.info(f"  平均每行: {result.average_time_per_row:.2f} 秒")
        
        # PHI 類型分布
        logger.info(f"\nPHI 類型分布:")
        phi_distribution = result.get_phi_type_distribution()
        for phi_type, count in sorted(phi_distribution.items(), key=lambda x: -x[1]):
            logger.info(f"  {phi_type:30s}: {count:3d}")
        
        # 信心度統計
        logger.info(f"\n信心度統計:")
        confidence_stats = result.get_confidence_statistics()
        logger.info(f"  平均: {confidence_stats['mean']:.1%}")
        logger.info(f"  最小: {confidence_stats['min']:.1%}")
        logger.info(f"  最大: {confidence_stats['max']:.1%}")
        
        # 顯示前 3 行的結果詳情
        logger.info(f"\n前 3 行詳細結果:")
        for row_result in result.row_results[:3]:
            if row_result.success:
                logger.info(
                    f"  Row {row_result.row_number} ({row_result.case_id}): "
                    f"{len(row_result.entities)} PHI entities, "
                    f"{row_result.processing_time:.2f}s"
                )
                # 顯示找到的 PHI
                for entity in row_result.entities[:5]:  # 只顯示前 5 個
                    phi_type_str = entity.get_type_name()
                    logger.info(
                        f"    - {phi_type_str:20s}: {entity.text[:30]:30s} "
                        f"(confidence: {entity.confidence:.1%})"
                    )
            else:
                logger.error(f"  Row {row_result.row_number}: ❌ {row_result.error_message}")
        
        # 保存結果
        if result.processed_rows > 0:
            output_file.parent.mkdir(parents=True, exist_ok=True)
            save_batch_results([result], str(output_file))
            logger.info(f"\n✓ 結果已保存: {output_file}")
        
        return 0
        
    except Exception as e:
        logger.error("\n" + "="*80)
        logger.error("❌ 處理失敗！")
        logger.error("="*80)
        logger.error(f"錯誤類型: {type(e).__name__}")
        logger.error(f"錯誤訊息: {str(e)}")
        logger.exception("詳細錯誤堆疊:")
        return 1


if __name__ == "__main__":
    sys.exit(main())
