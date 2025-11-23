"""
Batch Processing Example - Low Level API
批次處理範例 - 低階 API

Demonstrates using BatchPHIProcessor for detailed control and statistics.
示範使用 BatchPHIProcessor 進行詳細控制和統計。
"""

import sys
from pathlib import Path

# Import and configure logging from package
from medical_deidentification.infrastructure.utils import configure_logging
from loguru import logger

# Configure logging using package's built-in function
log_file = configure_logging(
    console_level="INFO",
    file_level="DEBUG",
    rotation="10 MB",
    retention="10 days"
)
logger.info(f"Logging configured: {log_file}")

from medical_deidentification.infrastructure.llm.config import LLMConfig
from medical_deidentification.infrastructure.rag.phi_identification_chain import (
    PHIIdentificationConfig,
    PHIIdentificationChain
)
from medical_deidentification.infrastructure.rag.regulation_retrieval_chain import (
    create_regulation_retrieval_chain
)
from medical_deidentification.infrastructure.rag.embeddings import EmbeddingsManager
from medical_deidentification.infrastructure.utils.token_counter import TokenCounter
from medical_deidentification.application.processing.batch_processor import (
    BatchPHIProcessor,
    BatchProcessingConfig,
    save_batch_results,
)


def main():
    """主函數 - 使用新的批次處理器"""
    
    # ============= 配置 =============
    
    # 測試文件路徑
    test_file = Path("data/test/test_complex_phi_cases.xlsx")
    
    # Ollama配置（使用本地llama3.1:8b模型，啟用GPU加速）
    llm_config = LLMConfig(
        provider="ollama",
        model_name="llama3.1:8b",
        temperature=0.0,
        max_tokens=8192,
        timeout=120,
        use_gpu=True,  # ✅ 啟用 GPU 加速（默認使用所有可用 GPU）
        # num_gpu=1,    # 可選：指定使用的 GPU 數量（None=自動檢測所有GPU）
        # gpu_layers=33, # 可選：指定卸載到 GPU 的層數（None=全部）
    )
    
    # PHI識別配置
    phi_config = PHIIdentificationConfig(
        llm_config=llm_config,
        retrieve_regulation_context=False,  # 不使用FAISS（避免維度問題）
        use_structured_output=True,  # ✅ 使用Ollama native structured output (已安裝ollama package)
    )
    
    # 批次處理配置
    batch_config = BatchProcessingConfig(
        max_rows=None,  # 處理所有行（可改為數字限制測試）
        language="zh-TW",
        skip_empty_rows=True,
        combine_columns=True,
        log_progress_interval=1,  # 每行都記錄
    )
    
    # ============= 初始化 =============
    
    logger.info("Initializing PHI Identification Chain with Ollama...")
    logger.info("Note: retrieve_regulation_context=False, will use default HIPAA rules")
    logger.info("Note: max_text_length=2000, texts longer than this will be chunked")
    
    # Since retrieve_regulation_context=False, regulation_chain won't be called
    # We pass None and PHIIdentificationChain will use default rules
    phi_chain = PHIIdentificationChain(
        regulation_chain=None,  # Not needed when retrieve_regulation_context=False
        config=phi_config,
        max_text_length=2000,  # Chunk texts longer than 2000 chars
    )
    
    logger.info("Initializing Batch PHI Processor...")
    processor = BatchPHIProcessor(phi_chain, batch_config)
    
    # Initialize token counter
    token_counter = TokenCounter(model_name=llm_config.model_name)
    logger.info(f"Token counter initialized for model: {llm_config.model_name}")
    
    # ============= 處理 =============
    
    if not test_file.exists():
        logger.error(f"Test file not found: {test_file}")
        logger.info("Please ensure data/case_details.xlsx exists")
        return
    
    logger.info(f"Processing file: {test_file}")
    
    # 使用批次處理器處理文件
    result = processor.process_excel_file(
        str(test_file),
        case_id_column="案例編號"  # 指定Case ID欄位
    )
    
    # ============= 輸出結果 =============
    
    # 儲存詳細結果到 Excel 和生成報告
    # save_batch_results 會自動使用 OutputManager 管理路徑
    saved_paths = save_batch_results([result], generate_report=True)
    
    # 計算 token 統計
    # 估算總輸入 tokens（所有處理的文本）
    total_input_tokens = 0
    total_output_tokens = 0
    
    # 從結果中計算
    for row_result in result.row_results:
        # 使用 text_length 來估算輸入 tokens
        # 假設平均 3 字符 = 1 token
        estimated_tokens = row_result.text_length / 3
        total_input_tokens += int(estimated_tokens)
        
        # 估算輸出 tokens（每個實體的識別結果約 50 tokens）
        total_output_tokens += len(row_result.entities) * 50
    
    total_tokens = total_input_tokens + total_output_tokens
    tokens_per_second = total_tokens / result.total_time if result.total_time > 0 else 0
    
    # 顯示摘要
    print(f"\n{'='*80}")
    print("Processing Complete!")
    print(f"{'='*80}")
    print(f"Total rows: {result.total_rows}")
    print(f"Processed rows: {result.processed_rows}")
    print(f"Total PHI entities: {result.total_entities}")
    print(f"Total time: {result.total_time:.2f}s ({result.total_time/60:.1f} minutes)")
    print(f"Average time per row: {result.average_time_per_row:.2f}s")
    
    # Token 處理速度
    print(f"\n{'='*80}")
    print("Token Processing Statistics:")
    print(f"{'='*80}")
    print(f"Total tokens (estimated):     {total_tokens:>10,}")
    print(f"  - Input tokens:             {total_input_tokens:>10,}")
    print(f"  - Output tokens:            {total_output_tokens:>10,}")
    print(f"Token processing rate:        {tokens_per_second:>10.1f} tokens/sec")
    print(f"Average tokens per row:       {total_tokens/result.processed_rows if result.processed_rows > 0 else 0:>10.1f}")
    
    # PHI類型分布
    print(f"\n{'='*80}")
    print("PHI Type Distribution:")
    print(f"{'='*80}")
    distribution = result.get_phi_type_distribution()
    for phi_type, count in sorted(distribution.items(), key=lambda x: -x[1]):
        print(f"{phi_type:30s}: {count:3d}")
    
    # 信心度統計
    print(f"\n{'='*80}")
    print("Confidence Statistics:")
    print(f"{'='*80}")
    confidence_stats = result.get_confidence_statistics()
    print(f"Mean: {confidence_stats['mean']:.2%}")
    print(f"Min:  {confidence_stats['min']:.2%}")
    print(f"Max:  {confidence_stats['max']:.2%}")
    
    print(f"\n✅ 結果已儲存:")
    print(f"  Excel: {saved_paths.get('result')}")
    if 'report' in saved_paths:
        print(f"  Report: {saved_paths.get('report')}")


if __name__ == "__main__":
    main()
