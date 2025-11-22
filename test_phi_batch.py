"""
優化版 PHI 識別測試 - 批次處理整行
減少 LLM API 呼叫次數，提升效率
"""

import os
import pandas as pd
from dotenv import load_dotenv
from loguru import logger
from pathlib import Path
from typing import List, Dict, Any
import time

# Load environment variables
load_dotenv()

# Import necessary components
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
    PHIIdentificationChain
)


def load_excel_data(file_path: str) -> pd.DataFrame:
    """載入 Excel 測試資料"""
    logger.info(f"Loading Excel file: {file_path}")
    df = pd.read_excel(file_path)
    logger.info(f"Loaded {len(df)} rows, {len(df.columns)} columns")
    return df


def combine_row_text(row: pd.Series, df: pd.DataFrame) -> str:
    """
    將一行的所有欄位合併成單一文本
    保留欄位名稱作為標記，方便後續定位
    """
    parts = []
    for col in df.columns:
        value = row[col]
        if pd.notna(value) and str(value).strip():
            # 格式: [Column Name] content
            parts.append(f"[{col}] {str(value)}")
    
    return "\n\n".join(parts)


def initialize_phi_chain():
    """初始化 PHI identification chain"""
    logger.info("Initializing PHI identification chain...")
    
    # Initialize embeddings manager
    embeddings_manager = EmbeddingsManager()
    
    # Load regulation vector store
    try:
        vector_store = RegulationVectorStore.load(
            embeddings_manager=embeddings_manager
        )
        logger.info("Loaded regulation vector store")
    except FileNotFoundError:
        logger.error("Regulation vector store not found!")
        return None
    
    # Create regulation retrieval chain
    regulation_chain = create_regulation_retrieval_chain(
        vector_store=vector_store
    )
    
    # Create LLM config with timeout
    llm_config = LLMConfig(
        provider="openai",
        model_name="gpt-4o-mini",
        temperature=0.0,
        timeout=60.0  # 60 second timeout for longer texts
    )
    
    # Create PHI identification config
    phi_config = PHIIdentificationConfig(
        llm_config=llm_config,
        retrieve_regulation_context=False,  # Disable to avoid issues
        use_structured_output=True
    )
    
    # Create PHI identification chain
    phi_chain = PHIIdentificationChain(regulation_chain, phi_config)
    
    logger.success("PHI identification chain initialized")
    return phi_chain


def analyze_row(phi_chain, row_text: str, row_index: int, case_id: str):
    """分析單一行（已合併所有欄位）"""
    logger.info(f"Analyzing Row {row_index} (Case: {case_id})")
    logger.debug(f"Text length: {len(row_text)} chars")
    
    start_time = time.time()
    
    try:
        # Identify PHI using the chain
        result = phi_chain.identify_phi(
            text=row_text,
            language="zh-TW",
            return_entities=True
        )
        
        elapsed = time.time() - start_time
        entities = result.get("entities", [])
        
        if entities:
            logger.success(f"Found {len(entities)} PHI entities in {elapsed:.2f}s")
            return entities
        else:
            logger.info(f"No PHI found in {elapsed:.2f}s")
            return []
    
    except Exception as e:
        logger.error(f"Error analyzing row: {e}")
        import traceback
        logger.debug(traceback.format_exc())
        return []


def process_file(file_path: str, phi_chain, max_rows: int = None):
    """處理單一測試檔案"""
    logger.info(f"\n{'='*80}")
    logger.info(f"Processing file: {file_path}")
    logger.info(f"{'='*80}\n")
    
    # Load data
    df = load_excel_data(file_path)
    
    # Limit rows if specified
    if max_rows:
        df = df.head(max_rows)
        logger.info(f"Limited to first {max_rows} rows")
    
    # Results storage
    all_results = []
    total_start = time.time()
    
    # Process each row
    for idx, row in df.iterrows():
        row_num = int(idx) + 1
        
        # Get case ID for reference
        case_id = row.iloc[0] if len(row) > 0 else f"Row-{row_num}"
        
        # Combine all columns into one text
        row_text = combine_row_text(row, df)
        
        if not row_text.strip():
            logger.warning(f"Row {row_num} is empty, skipping")
            continue
        
        # Analyze the combined text (1 API call per row!)
        entities = analyze_row(phi_chain, row_text, row_num, case_id)
        
        # Store results
        for entity in entities:
            all_results.append({
                "file": Path(file_path).name,
                "row": row_num,
                "case_id": case_id,
                "phi_type": entity.type.value,
                "phi_text": entity.text,
                "start_pos": entity.start_pos,
                "end_pos": entity.end_pos,
                "confidence": entity.confidence,
                "reason": entity.reason,
                "regulation_source": entity.regulation_source
            })
    
    total_elapsed = time.time() - total_start
    
    logger.info(f"\n{'='*80}")
    logger.info(f"File processing complete in {total_elapsed:.2f}s")
    logger.info(f"Total rows processed: {len(df)}")
    logger.info(f"Total PHI entities found: {len(all_results)}")
    logger.info(f"Average time per row: {total_elapsed/len(df):.2f}s")
    logger.info(f"{'='*80}\n")
    
    return all_results, df


def main():
    """主程式"""
    logger.info("\n" + "="*80)
    logger.info("PHI Identification - Batch Processing Mode")
    logger.info("="*80 + "\n")
    
    # Test files
    test_files = [
        "data/test/test_complex_phi_cases.xlsx",
        "data/test/test_medical_records_multilang.xlsx"
    ]
    
    # Initialize PHI chain once
    phi_chain = initialize_phi_chain()
    if phi_chain is None:
        logger.error("Failed to initialize PHI chain")
        return
    
    # Process each file
    all_results = []
    file_stats = []
    
    for file_path in test_files:
        if not os.path.exists(file_path):
            logger.warning(f"File not found: {file_path}")
            continue
        
        # Process file (limit to 5 rows per file for initial test)
        results, df = process_file(file_path, phi_chain, max_rows=5)
        all_results.extend(results)
        
        file_stats.append({
            "file": Path(file_path).name,
            "rows_processed": len(df),
            "phi_found": len(results)
        })
    
    # Save combined results
    if all_results:
        results_df = pd.DataFrame(all_results)
        output_file = "phi_batch_results.xlsx"
        results_df.to_excel(output_file, index=False)
        logger.success(f"Results saved to: {output_file}")
        
        # Display summary
        logger.info(f"\n{'='*80}")
        logger.info("=== OVERALL SUMMARY ===")
        logger.info(f"{'='*80}\n")
        
        for stat in file_stats:
            logger.info(f"File: {stat['file']}")
            logger.info(f"  Rows processed: {stat['rows_processed']}")
            logger.info(f"  PHI entities found: {stat['phi_found']}")
            logger.info("")
        
        logger.info(f"Total PHI entities across all files: {len(all_results)}")
        
        # PHI type distribution
        phi_type_counts = results_df['phi_type'].value_counts()
        logger.info("\nPHI Types Distribution:")
        for phi_type, count in phi_type_counts.items():
            logger.info(f"  - {phi_type}: {count} occurrences")
        
        # Display sample results
        logger.info(f"\n{'='*80}")
        logger.info("=== SAMPLE RESULTS (First 10) ===")
        logger.info(f"{'='*80}\n")
        print(results_df.head(10).to_string())
    
    else:
        logger.warning("No PHI entities found in any file")


if __name__ == "__main__":
    main()
