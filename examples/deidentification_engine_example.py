"""
De-identification Engine Example | 去識別化引擎範例
=================================================

DeidentificationEngine 是什麼？
--------------------------------
高階 API，整合完整的去識別化工作流程：
1. 文件載入 (DocumentLoader)
2. 語言檢測
3. PHI 識別 (使用 LLM)
4. 遮蔽策略應用
5. 結果驗證
6. 輸出生成

適用場景：
---------
✅ 生產環境的完整工作流程
✅ 需要自動化pipeline的場景
✅ 需要統一配置和管理的場景
✅ 需要完整錯誤處理的場景

與 BatchPHIProcessor 的區別：
---------------------------
- BatchPHIProcessor: 低階API，直接PHI識別，適合研究/測試
- DeidentificationEngine: 高階API，完整工作流程，適合生產環境

當前狀態：
---------
⚠️  PHI identification handler 需要配置才能正常工作
✅  Pipeline 架構完整
✅  文件載入功能正常
⚠️  建議用於簡化配置和workflow管理，實際PHI識別使用BatchPHIProcessor
"""

from pathlib import Path
from medical_deidentification.infrastructure.utils import configure_logging
from medical_deidentification.domain import StrategyType, PHIType
from medical_deidentification.application.processing import (
    DeidentificationEngine,
    EngineConfig,
)
from loguru import logger

# Configure logging
log_file = configure_logging(console_level="INFO", file_level="DEBUG")


def example_1_basic_usage():
    """
    範例 1：基本使用 - 簡化配置
    
    Engine 的主要優勢：用簡單的配置啟動完整的workflow
    """
    logger.info("="*80)
    logger.info("Example 1: Basic Usage - Simplified Configuration")
    logger.info("="*80)
    
    # 創建配置 - 只需幾行代碼
    config = EngineConfig(
        use_rag=False,                          # 不使用RAG（使用預設HIPAA規則）
        llm_provider="ollama",                  # LLM提供者
        llm_model="llama3.1:8b",               # 模型
        default_strategy=StrategyType.REDACTION # 預設遮蔽策略
    )
    
    logger.info("Configuration:")
    logger.info(f"  - RAG: {config.use_rag}")
    logger.info(f"  - LLM: {config.llm_provider}/{config.llm_model}")
    logger.info(f"  - Strategy: {config.default_strategy.value}")
    
    # 創建引擎 - 一行代碼
    engine = DeidentificationEngine(config)
    logger.success("✓ Engine initialized with default workflow")
    
    # Engine 自動設定了所有pipeline stages
    logger.info(f"\nPipeline: {engine.pipeline}")
    logger.info("  ✓ Language Detection")
    logger.info("  ✓ Regulation Retrieval")
    logger.info("  ✓ PHI Identification")
    logger.info("  ✓ Masking Application")
    logger.info("  ✓ Validation")
    logger.info("  ✓ Output Generation")
    
    return engine


def example_2_process_single_file(engine):
    """
    範例 2：處理單一文件
    
    Engine 的優勢：自動處理文件載入、錯誤處理、結果追蹤
    """
    logger.info("\n" + "="*80)
    logger.info("Example 2: Process Single File")
    logger.info("="*80)
    
    test_file = Path("data/test/test_complex_phi_cases.xlsx")
    
    if not test_file.exists():
        logger.error(f"Test file not found: {test_file}")
        return None
    
    logger.info(f"Processing: {test_file}")
    logger.info("Engine will automatically:")
    logger.info("  1. Load Excel file")
    logger.info("  2. Detect language")
    logger.info("  3. Identify PHI")
    logger.info("  4. Apply masking")
    logger.info("  5. Validate results")
    logger.info("  6. Generate output")
    
    # 處理文件 - 一行代碼完成所有步驟
    result = engine.process_file(
        str(test_file),
        job_name="single-file-example"
    )
    
    # 檢查結果
    logger.success(f"\n✓ Processing completed!")
    logger.info(f"\nJob Information:")
    logger.info(f"  Job ID: {result.job_id}")
    logger.info(f"  Status: {result.status.value}")
    logger.info(f"  Duration: {result.duration_seconds:.2f}s")
    
    logger.info(f"\nStatistics:")
    logger.info(f"  Documents processed: {result.processed_documents}/{result.total_documents}")
    logger.info(f"  Documents failed: {result.failed_documents}")
    logger.info(f"  PHI entities found: {result.total_phi_entities}")
    
    # 查看每個stage的結果
    logger.info(f"\nPipeline Stages:")
    for stage in result.stage_results:
        status = "✓" if stage.get("success") else "✗"
        duration = stage.get("duration_seconds", 0)
        logger.info(f"  {status} {stage['stage']}: {duration:.3f}s")
        if not stage.get("success"):
            logger.warning(f"    ⚠ Stage failed or had issues")
    
    # 錯誤報告
    if result.errors:
        logger.warning(f"\nErrors encountered: {len(result.errors)}")
        for i, error in enumerate(result.errors[:3], 1):
            logger.error(f"  {i}. {error.get('type')}: {error.get('message', '')[:100]}")
    
    return result


def example_3_multiple_files(engine):
    """
    範例 3：批次處理多個文件
    
    Engine 的優勢：統一管理多文件處理，自動錯誤處理
    """
    logger.info("\n" + "="*80)
    logger.info("Example 3: Batch Process Multiple Files")
    logger.info("="*80)
    
    # 準備文件列表
    files = [
        "data/test/test_complex_phi_cases.xlsx",
        # 可以加入更多文件
    ]
    
    existing_files = [f for f in files if Path(f).exists()]
    
    if not existing_files:
        logger.error("No test files found")
        return None
    
    logger.info(f"Processing {len(existing_files)} files:")
    for f in existing_files:
        logger.info(f"  - {Path(f).name}")
    
    # 批次處理 - 一行代碼處理多個文件
    result = engine.process_files(
        existing_files,
        job_name="batch-example"
    )
    
    logger.success(f"\n✓ Batch processing completed!")
    logger.info(f"\nBatch Statistics:")
    logger.info(f"  Total files: {result.total_documents}")
    logger.info(f"  Successful: {result.processed_documents}")
    logger.info(f"  Failed: {result.failed_documents}")
    logger.info(f"  Success rate: {result.processed_documents/result.total_documents*100:.1f}%")
    logger.info(f"  Total PHI: {result.total_phi_entities}")
    logger.info(f"  Total time: {result.duration_seconds:.2f}s")
    logger.info(f"  Avg per file: {result.duration_seconds/result.total_documents:.2f}s")
    
    return result


def example_4_custom_strategies():
    """
    範例 4：自訂遮蔽策略
    
    Engine 的優勢：為不同PHI類型配置不同策略
    """
    logger.info("\n" + "="*80)
    logger.info("Example 4: Custom Masking Strategies")
    logger.info("="*80)
    
    # 為不同PHI類型配置不同策略
    config = EngineConfig(
        use_rag=False,
        llm_provider="ollama",
        llm_model="llama3.1:8b",
        default_strategy=StrategyType.REDACTION,  # 預設：刪除
        phi_specific_strategies={
            PHIType.NAME: StrategyType.PSEUDONYMIZATION,  # 姓名：假名化
            PHIType.AGE_OVER_89: StrategyType.GENERALIZATION,  # 高齡：泛化
            PHIType.DATE: StrategyType.DATE_SHIFTING,  # 日期：位移
            PHIType.PHONE: StrategyType.PARTIAL_MASKING,  # 電話：部分遮蔽
        },
        strategy_config={
            "placeholder": "[已移除]",
            "salt": "my-secret-salt-123",
            "offset_days": 60,
            "keep_prefix": 3,
            "keep_suffix": 2
        }
    )
    
    logger.info("Custom Strategy Configuration:")
    logger.info(f"  Default: {config.default_strategy.value}")
    logger.info(f"  Custom strategies for {len(config.phi_specific_strategies)} PHI types:")
    for phi_type, strategy in config.phi_specific_strategies.items():
        logger.info(f"    - {phi_type.value}: {strategy.value}")
    
    engine = DeidentificationEngine(config)
    logger.success("✓ Engine with custom strategies initialized")
    
    return engine


def example_5_understanding_engine():
    """
    範例 5：理解 Engine 的真正用途
    
    Engine 不是為了替代 BatchPHIProcessor，而是為了：
    """
    logger.info("\n" + "="*80)
    logger.info("Example 5: Understanding DeidentificationEngine")
    logger.info("="*80)
    
    logger.info("\n✅ Engine 的優勢 (What it's GOOD for):")
    logger.info("  1. 簡化配置 - 一個 EngineConfig 搞定所有設定")
    logger.info("  2. 完整workflow - 自動處理 6 個 pipeline stages")
    logger.info("  3. 錯誤處理 - 自動捕捉和報告各階段錯誤")
    logger.info("  4. 結果追蹤 - 統一的 ProcessingResult 格式")
    logger.info("  5. 文件管理 - 自動處理多種文件格式")
    logger.info("  6. 策略管理 - 為不同 PHI 類型配置不同策略")
    
    logger.info("\n⚠️  目前的限制 (Current Limitations):")
    logger.info("  1. PHI identification handler 需要正確配置")
    logger.info("  2. 某些 pipeline stages 可能有驗證錯誤")
    logger.info("  3. 實際 PHI 識別效果未完全驗證")
    
    logger.info("\n💡 推薦使用方式:")
    logger.info("  • 生產環境: 用 Engine 管理 workflow 和配置")
    logger.info("  • 實際識別: 內部使用 BatchPHIProcessor (已驗證)")
    logger.info("  • 研究測試: 直接使用 BatchPHIProcessor")
    
    logger.info("\n📊 對比:")
    logger.info("  Engine (高階):        簡化配置 + 完整workflow + 自動管理")
    logger.info("  BatchProcessor (低階): 直接控制 + 詳細統計 + 靈活調整")


def main():
    """主程式 - 依序執行所有範例"""
    logger.info("\n" + "="*80)
    logger.info("De-identification Engine Examples")
    logger.info("去識別化引擎範例")
    logger.info("="*80)
    
    try:
        # 範例 1: 基本使用
        engine = example_1_basic_usage()
        
        # 範例 2: 處理單一文件
        result = example_2_process_single_file(engine)
        
        # 範例 3: 批次處理
        batch_result = example_3_multiple_files(engine)
        
        # 範例 4: 自訂策略
        custom_engine = example_4_custom_strategies()
        
        # 範例 5: 理解 Engine
        example_5_understanding_engine()
        
        logger.success("\n" + "="*80)
        logger.success("All examples completed!")
        logger.success("="*80)
        logger.info(f"\nLog file: {log_file}")
        logger.info("\n下一步建議:")
        logger.info("  1. 查看完整日誌了解 pipeline 執行細節")
        logger.info("  2. 使用 BatchPHIProcessor 進行實際 PHI 識別")
        logger.info("  3. Engine 適合用於配置管理和 workflow 編排")
        
    except Exception as e:
        logger.exception(f"Example failed: {e}")


if __name__ == "__main__":
    main()
