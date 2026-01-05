"""
Streaming PHI Chain Example | 串流 PHI Chain 範例

Demonstrates how to process large medical files with:
- Unlimited file size support
- Checkpoint/resume capability
- RAG on/off configuration
- Tool calling configuration

展示如何處理大型醫療檔案：
- 無限檔案大小支援
- 斷點續處理能力
- RAG 開關配置
- 工具呼叫配置

Usage:
    python examples/streaming_phi_example.py --file data/large_medical.txt
    python examples/streaming_phi_example.py --file data/large_medical.txt --resume
    python examples/streaming_phi_example.py --file data/large_medical.txt --no-rag --no-tools
"""

import argparse
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from loguru import logger

from core.infrastructure.rag.chains import (
    StreamingPHIChain,
    StreamingPHIConfig,
)
from core.infrastructure.tools import (
    RegexPHITool,
    IDValidatorTool,
    PhoneTool,
)


def main():
    parser = argparse.ArgumentParser(description="Streaming PHI Detection")
    parser.add_argument("--file", type=str, help="Input file path")
    parser.add_argument("--text", type=str, help="Input text string")
    parser.add_argument("--resume", action="store_true", help="Resume from checkpoint")
    parser.add_argument("--reset", action="store_true", help="Reset checkpoint")
    parser.add_argument("--no-rag", action="store_true", help="Disable RAG")
    parser.add_argument("--no-tools", action="store_true", help="Disable tools")
    parser.add_argument("--chunk-size", type=int, default=2000, help="Chunk size")
    parser.add_argument("--checkpoint-dir", type=str, default="./checkpoints")
    parser.add_argument("--output-dir", type=str, default="./data/output/streaming")
    parser.add_argument("--language", type=str, default="zh-TW", help="Language hint")
    args = parser.parse_args()
    
    # Configure logging
    logger.info("=" * 60)
    logger.info("Streaming PHI Chain Example")
    logger.info("=" * 60)
    
    # Create config
    config = StreamingPHIConfig(
        chunk_size=args.chunk_size,
        chunk_overlap=100,
        enable_rag=not args.no_rag,
        enable_tools=not args.no_tools,
        checkpoint_dir=args.checkpoint_dir,
        checkpoint_interval=1,
        output_dir=args.output_dir,
    )
    
    logger.info(f"Config: chunk_size={config.chunk_size}, rag={config.enable_rag}, tools={config.enable_tools}")
    
    # Create tools
    tools = [
        RegexPHITool(),
        IDValidatorTool(),
        PhoneTool(),
    ]
    
    # Create LLM (using environment variable or default)
    llm = None
    try:
        from core.infrastructure.llm.factory import create_llm
        from core.infrastructure.llm.config import LLMConfig
        llm_config = LLMConfig(provider="ollama", model_name="llama3.1:8b")
        llm = create_llm(llm_config)
        logger.info("LLM initialized: ollama/llama3.1:8b")
    except Exception as e:
        logger.warning(f"LLM not available: {e}")
        logger.info("Running in tool-only mode")
    
    # Create chain
    chain = StreamingPHIChain(
        llm=llm,
        config=config,
        tools=tools,
    )
    
    if args.file:
        # Reset checkpoint if requested
        if args.reset:
            chain.reset_checkpoint(args.file)
            logger.info("Checkpoint reset")
        
        # Check progress
        progress = chain.get_progress(args.file)
        if progress:
            logger.info(f"Previous progress: {progress['progress_percent']:.1f}%")
        
        # Process file
        logger.info(f"Processing file: {args.file}")
        total_entities = 0
        
        for result in chain.process_file(
            args.file, 
            resume=args.resume,
            language=args.language,
        ):
            if result.success:
                logger.info(
                    f"Chunk {result.chunk_id}: "
                    f"{len(result.entities)} entities found, "
                    f"tools={result.tool_calls_made}, "
                    f"rag={result.rag_used}, "
                    f"{result.processing_time_ms:.0f}ms"
                )
                total_entities += len(result.entities)
                
                # Print entities for debugging
                for entity in result.entities:
                    logger.debug(f"  - {entity.type.value}: {entity.text}")
            else:
                logger.error(f"Chunk {result.chunk_id} failed: {result.error}")
        
        logger.info(f"Total entities found: {total_entities}")
        
        # Final progress
        final_progress = chain.get_progress(args.file)
        if final_progress:
            logger.info(f"Final: {final_progress['chunks_processed']}/{final_progress['total_chunks']} chunks")
    
    elif args.text:
        # Process text string
        logger.info(f"Processing text: {args.text[:50]}...")
        
        for result in chain.process_text(
            args.text,
            text_id="cli_input",
            resume=args.resume,
            language=args.language,
        ):
            if result.success:
                logger.info(f"Chunk {result.chunk_id}: {len(result.entities)} entities")
                for entity in result.entities:
                    print(f"  {entity.type.value}: {entity.text}")
            else:
                logger.error(f"Failed: {result.error}")
    
    else:
        # Demo with sample text
        demo_text = """
        病患姓名：王小明
        身分證字號：A123456789
        聯絡電話：0912-345-678
        電子郵件：wang.xiaoming@email.com
        地址：台北市信義區信義路五段7號
        出生日期：1985年3月15日
        就診日期：2024年1月20日
        
        主訴：患者因持續頭痛三天前來就診。
        
        診斷：偏頭痛 (Migraine)
        
        處方：
        - Acetaminophen 500mg TID
        - 建議多休息，避免熬夜
        
        醫師：李醫師
        """
        
        logger.info("Running demo with sample text...")
        
        for result in chain.process_text(demo_text, "demo", language="zh-TW"):
            if result.success:
                logger.info(f"Found {len(result.entities)} PHI entities:")
                for entity in result.entities:
                    print(f"  [{entity.type.value}] {entity.text}")
    
    logger.info("=" * 60)
    logger.info("Done!")


if __name__ == "__main__":
    main()
