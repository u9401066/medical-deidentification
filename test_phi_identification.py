"""
PHI Identification Test Script
使用 PHIIdentificationChain 識別 Excel 檔案中的 PHI 資料

測試檔案: data/test/test_complex_phi_cases.xlsx
"""

import sys
import pandas as pd
from pathlib import Path
from loguru import logger
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logger
logger.remove()
logger.add(sys.stdout, level="INFO")

# Import PHI identification components
from medical_deidentification.infrastructure.rag import (
    RegulationVectorStore,
    RegulationRetrievalChain,
    PHIIdentificationChain,
    EmbeddingsManager,
    create_regulation_retrieval_chain,
    create_phi_identification_chain
)
from medical_deidentification.domain.models import PHIType


def load_excel_data(file_path: str) -> pd.DataFrame:
    """載入 Excel 測試資料"""
    logger.info(f"Loading Excel file: {file_path}")
    df = pd.read_excel(file_path)
    logger.info(f"Loaded {len(df)} rows, columns: {list(df.columns)}")
    return df


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
        logger.info("Please run: python scripts/setup_regulation_store.py")
        return None
    
    # Create regulation retrieval chain
    regulation_chain = create_regulation_retrieval_chain(
        vector_store=vector_store
    )
    
    # Create LLM config with timeout
    from medical_deidentification.infrastructure.llm.config import LLMConfig
    llm_config = LLMConfig(
        provider="openai",
        model_name="gpt-4o-mini",
        temperature=0.0,
        timeout=30.0  # 30 second timeout
    )
    
    # Create PHI identification config
    from medical_deidentification.infrastructure.rag.phi_identification_chain import PHIIdentificationConfig
    phi_config = PHIIdentificationConfig(
        llm_config=llm_config,
        retrieve_regulation_context=False,  # Disable to avoid vector store issues
        use_structured_output=True
    )
    
    # Create PHI identification chain
    from medical_deidentification.infrastructure.rag.phi_identification_chain import PHIIdentificationChain
    phi_chain = PHIIdentificationChain(regulation_chain, phi_config)
    
    logger.success("PHI identification chain initialized")
    return phi_chain


def analyze_text(phi_chain, text: str, row_index: int, column_name: str):
    """分析單一文本，識別 PHI"""
    logger.info(f"Analyzing Row {row_index + 1}, Column '{column_name}'")
    
    try:
        # Identify PHI using the chain
        result = phi_chain.identify_phi(
            text=text,
            language="zh-TW",  # Assume Traditional Chinese
            return_entities=True
        )
        
        entities = result.get("entities", [])
        
        if entities:
            logger.success(f"Found {len(entities)} PHI entities")
            return entities
        else:
            logger.debug(f"No PHI found in text: {text[:50]}...")
            return []
    
    except Exception as e:
        logger.error(f"Error analyzing text: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return []


def main():
    """主程式"""
    # File path
    excel_file = "data/test/test_complex_phi_cases.xlsx"
    
    if not Path(excel_file).exists():
        logger.error(f"File not found: {excel_file}")
        return
    
    # Load Excel data
    df = load_excel_data(excel_file)
    
    # Display data structure (removed print to avoid Unicode errors)
    logger.info(f"Loaded {len(df)} rows with {len(df.columns)} columns")
    
    # Initialize PHI chain
    phi_chain = initialize_phi_chain()
    if phi_chain is None:
        return
    
    # Results storage
    all_results = []
    
    # Analyze each row and relevant columns
    logger.info("\n=== PHI Identification Results ===\n")
    
    # Test first 3 rows, all columns
    test_rows = 3
    
    for idx, row in df.head(test_rows).iterrows():
        row_num = int(idx) + 1
        logger.info("=" * 80)
        logger.info(f"Row {row_num}:")
        logger.info("=" * 80)
        
        # Analyze each column that might contain PHI
        for col in df.columns:
            value = row[col]
            
            # Skip empty values
            if pd.isna(value) or str(value).strip() == "":
                continue
            
            text = str(value)
            
            # Print original text
            logger.info(f"Column: {col}")
            logger.debug(f"Text: {text[:100]}..." if len(text) > 100 else f"Text: {text}")
            
            # Identify PHI
            entities = analyze_text(phi_chain, text, idx, col)
            
            # Display results
            if entities:
                for entity in entities:
                    logger.info(f"PHI Detected: {entity.text}")
                    logger.info(f"Type: {entity.type.value}, Confidence: {entity.confidence:.2%}")
                    if entity.regulation_source:
                        logger.debug(f"Regulation: {entity.regulation_source}")
                    
                    # Store result
                    all_results.append({
                        "row": idx + 1,
                        "column": col,
                        "phi_type": entity.type.value,
                        "phi_text": entity.text,
                        "confidence": entity.confidence,
                        "regulation_source": entity.regulation_source,
                        "original_text": text
                    })
            else:
                print("   ✓ No PHI detected")
    
    # Summary
    print(f"\n\n{'='*80}")
    print("=== SUMMARY ===")
    print(f"{'='*80}")
    print(f"Total rows analyzed: {len(df)}")
    print(f"Total PHI entities found: {len(all_results)}")
    
    if all_results:
        # Group by PHI type
        phi_types = {}
        for result in all_results:
            phi_type = result["phi_type"]
            if phi_type not in phi_types:
                phi_types[phi_type] = []
            phi_types[phi_type].append(result)
        
        print(f"\nPHI Types Found:")
        for phi_type, items in phi_types.items():
            print(f"  - {phi_type}: {len(items)} occurrences")
        
        # Create summary DataFrame
        summary_df = pd.DataFrame(all_results)
        output_file = "phi_identification_results.xlsx"
        summary_df.to_excel(output_file, index=False)
        logger.success(f"\nResults saved to: {output_file}")
        
        # Display summary table
        print("\n=== Detailed Results ===")
        print(summary_df.to_string())
    else:
        logger.info("No PHI entities were identified in the document")


if __name__ == "__main__":
    main()
