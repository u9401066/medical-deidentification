"""
測試多語言醫療記錄文件
Test multilingual medical records file

目的：找出代碼錯誤並修正
"""

from pathlib import Path
import time

# 先配置日誌，避免載入 embeddings
from loguru import logger
import sys

# 配置簡單的日誌
logger.remove()  # 移除預設
logger.add(sys.stderr, level="INFO")
logger.add("logs/test_multilang_{time}.log", level="DEBUG", rotation="10 MB")

logger.info("="*80)
logger.info("測試多語言醫療記錄 - Test Multilingual Medical Records")
logger.info("="*80)

# 延遲導入，避免載入 embeddings
from medical_deidentification.infrastructure.rag import (
    PHIIdentificationConfig
)

# 測試文件
test_file = Path("data/test/test_medical_records_multilang.xlsx")

if not test_file.exists():
    logger.error(f"❌ 測試文件不存在: {test_file}")
    exit(1)

logger.info(f"✓ 測試文件: {test_file}")

# 延遲導入以避免載入 embeddings
logger.info("\n配置 PHI Identification Chain...")
from medical_deidentification.infrastructure.rag import PHIIdentificationChain
from medical_deidentification.application.processing import (
    BatchPHIProcessor,
    BatchProcessingConfig,
    save_batch_results
)

# 配置 PHI 識別（使用 Ollama）
phi_config = PHIIdentificationConfig(
    retrieve_regulation_context=False,  # 不使用 RAG
    llm_config={
        "provider": "ollama",
        "model_name": "llama3.1:8b",
        "temperature": 0.0,
    }
)

# 批次處理配置
batch_config = BatchProcessingConfig(
    max_rows=3,  # 只處理前 3 行
    language="zh-TW",
    skip_empty_rows=True,
    combine_columns=True,
    log_progress_interval=1
)

try:
    logger.info("  ✓ 創建 PHIIdentificationChain...")
    phi_chain = PHIIdentificationChain(config=phi_config)
    logger.success("  ✓ PHI Chain 創建成功")
except Exception as e:
    logger.error(f"❌ 創建 PHI Chain 失敗: {e}")
    logger.exception("詳細錯誤:")
    exit(1)

# 創建批次處理器
logger.info("\n創建 Batch Processor...")
try:
    processor = BatchPHIProcessor(
        phi_chain=phi_chain,
        config=batch_config
    )
    logger.success("  ✓ Batch Processor 創建成功")
except Exception as e:
    logger.error(f"❌ 創建 Batch Processor 失敗: {e}")
    logger.exception("詳細錯誤:")
    exit(1)

# 執行處理（只處理前 3 行測試）
logger.info("\n" + "="*80)
logger.info("開始處理（前 3 行測試）...")
logger.info("="*80)

start_time = time.time()

try:
    result = processor.process_excel_file(
        str(test_file),
        case_id_column="Patient ID\n病患編號\n患者ID"  # 多語言列名
    )
    
    duration = time.time() - start_time
    
    logger.success("\n" + "="*80)
    logger.success("✅ 處理完成！")
    logger.success("="*80)
    
    # 顯示結果
    logger.info(f"\n處理統計:")
    logger.info(f"  總行數: {result.total_rows}")
    logger.info(f"  成功處理: {result.processed_rows}")
    logger.info(f"  總 PHI 實體: {result.total_entities}")
    logger.info(f"  處理時間: {duration:.2f} 秒")
    logger.info(f"  平均每行: {result.average_time_per_row:.2f} 秒")
    
    # Token 統計（移除，因為 BatchProcessingResult 沒有 token_stats）
    
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
    
    # 顯示每行的結果
    logger.info(f"\n每行詳細結果:")
    for row_result in result.row_results[:3]:  # 只顯示前 3 行
        if row_result.success:
            logger.info(
                f"  Row {row_result.row_number} ({row_result.case_id}): "
                f"{len(row_result.entities)} PHI entities, "
                f"{row_result.processing_time:.2f}s"
            )
        else:
            logger.error(f"  Row {row_result.row_number}: ❌ {row_result.error_message}")
    
    # 保存結果
    if result.processed_rows > 0:
        output_file = "test_output/multilang_result.xlsx"
        save_batch_results([result], output_file)
        logger.info(f"\n✓ 結果已保存: {output_file}")
    
    logger.info(f"\n完整日誌: {log_file}")
    
except Exception as e:
    duration = time.time() - start_time
    logger.error("\n" + "="*80)
    logger.error("❌ 處理失敗！")
    logger.error("="*80)
    logger.error(f"錯誤類型: {type(e).__name__}")
    logger.error(f"錯誤訊息: {str(e)}")
    logger.exception("詳細錯誤堆疊:")
    logger.info(f"\n執行時間: {duration:.2f} 秒")
    logger.info(f"日誌文件: {log_file}")
    exit(1)
