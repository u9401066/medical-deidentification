"""
RAG System Usage Examples
RAG 系統使用範例

Demonstrates how to use the regulation RAG system for medical de-identification.
示範如何使用法規 RAG 系統進行醫療去識別化。
"""

from pathlib import Path
from medical_deidentification.infrastructure.rag import (
    EmbeddingsManager,
    RegulationVectorStore,
    RegulationRetriever,
    RegulationRAGChain,
    create_embeddings_manager,
    create_regulation_rag_chain
)


def example_1_basic_setup():
    """
    Example 1: Basic setup and vector store creation
    範例 1：基本設置與向量庫建立
    """
    print("=== Example 1: Basic Setup ===\n")
    
    # Step 1: Create embeddings manager
    print("Step 1: Creating embeddings manager...")
    embeddings = create_embeddings_manager(
        preset="multilingual",  # Recommended for medical documents
        device="cpu"  # Use "cuda" if GPU available
    )
    print(f"✓ {embeddings}\n")
    
    # Step 2: Create regulation vector store
    print("Step 2: Creating regulation vector store...")
    store = RegulationVectorStore(embeddings_manager=embeddings)
    
    # Note: Before building, add regulation documents to:
    # regulations/source_documents/
    # Example files:
    #   - hipaa_safe_harbor.md
    #   - gdpr_article_4.md
    #   - taiwan_pdpa.md
    
    print("✓ Vector store created (not built yet)\n")
    print("Next: Add regulation documents to regulations/source_documents/")
    print("Then run: store.build_from_source()\n")


def example_2_build_vector_store():
    """
    Example 2: Build vector store from regulation documents
    範例 2：從法規文件建立向量庫
    """
    print("=== Example 2: Build Vector Store ===\n")
    
    # Setup
    embeddings = create_embeddings_manager(preset="multilingual")
    store = RegulationVectorStore(embeddings_manager=embeddings)
    
    # Build from source documents
    print("Building vector store from source documents...")
    try:
        store.build_from_source()
        print(f"✓ Vector store built successfully")
        print(f"Stats: {store.get_stats()}\n")
    except ValueError as e:
        print(f"✗ Error: {e}")
        print("Please add regulation documents first\n")


def example_3_search_regulations():
    """
    Example 3: Search for relevant regulations
    範例 3：搜索相關法規
    """
    print("=== Example 3: Search Regulations ===\n")
    
    # Load existing vector store
    embeddings = create_embeddings_manager(preset="multilingual")
    
    try:
        store = RegulationVectorStore.load(embeddings_manager=embeddings)
        
        # Search for age-related regulations
        print("Query: 'age over 89 years old'")
        docs = store.similarity_search("age over 89 years old", k=3)
        
        print(f"Found {len(docs)} relevant documents:\n")
        for i, doc in enumerate(docs, 1):
            print(f"Document {i}:")
            print(f"  Content: {doc.page_content[:200]}...")
            print(f"  Source: {doc.metadata.get('source', 'unknown')}\n")
    
    except FileNotFoundError as e:
        print(f"✗ Error: {e}")
        print("Please build vector store first\n")


def example_4_advanced_retrieval():
    """
    Example 4: Advanced retrieval with MMR
    範例 4：使用 MMR 的高級檢索
    """
    print("=== Example 4: Advanced Retrieval ===\n")
    
    embeddings = create_embeddings_manager(preset="multilingual")
    
    try:
        store = RegulationVectorStore.load(embeddings_manager=embeddings)
        
        # Create retriever with MMR
        from medical_deidentification.infrastructure.rag import RetrieverConfig
        
        config = RetrieverConfig(
            search_type="mmr",  # Maximal Marginal Relevance
            k=5,  # Return 5 documents
            fetch_k=20,  # Fetch 20 candidates
            lambda_mult=0.7  # Balance relevance (high) vs diversity (low)
        )
        
        retriever = RegulationRetriever(vector_store=store, config=config)
        
        # Retrieve for rare diseases
        print("Query: 'rare disease genetic information'")
        docs = retriever.retrieve("rare disease genetic information")
        
        print(f"Retrieved {len(docs)} diverse documents with MMR\n")
        for i, doc in enumerate(docs, 1):
            print(f"Document {i}: {doc.page_content[:150]}...\n")
    
    except FileNotFoundError as e:
        print(f"✗ Error: {e}")


def example_5_rag_chain_phi_identification():
    """
    Example 5: Full RAG chain for PHI identification
    範例 5：完整 RAG 鏈進行 PHI 識別
    """
    print("=== Example 5: RAG Chain PHI Identification ===\n")
    
    # Medical text with PHI
    medical_text = """
    患者張三，94歲男性，於2024年1月15日入院。
    主訴：患者主訴呼吸困難，診斷為法布瑞氏症（Fabry Disease）。
    聯絡電話：02-2345-6789
    住址：台北市信義區忠孝東路五段123號
    身分證號：A123456789
    """
    
    embeddings = create_embeddings_manager(preset="multilingual")
    
    try:
        store = RegulationVectorStore.load(embeddings_manager=embeddings)
        
        # Create RAG chain
        # Note: Requires OpenAI API key in environment
        chain = create_regulation_rag_chain(
            vector_store=store,
            llm_provider="openai",
            model_name="gpt-4",
            search_type="mmr"
        )
        
        print("Identifying PHI in medical text...\n")
        result = chain.identify_phi(
            text=medical_text,
            language="zh-TW",
            return_source=True
        )
        
        print("PHI Identification Result:")
        print(result["result"])
        
        if "source_documents" in result:
            print(f"\nUsed {len(result['source_documents'])} regulation documents")
    
    except FileNotFoundError as e:
        print(f"✗ Error: {e}")
    except Exception as e:
        print(f"✗ Error: {e}")
        print("Note: Make sure OPENAI_API_KEY is set in environment\n")


def example_6_multi_phi_retrieval():
    """
    Example 6: Retrieve regulations for multiple PHI types
    範例 6：為多個 PHI 類型檢索法規
    """
    print("=== Example 6: Multi-PHI Retrieval ===\n")
    
    embeddings = create_embeddings_manager(preset="multilingual")
    
    try:
        store = RegulationVectorStore.load(embeddings_manager=embeddings)
        retriever = RegulationRetriever(vector_store=store)
        
        # Retrieve for multiple PHI types
        phi_types = ["AGE_OVER_89", "RARE_DISEASE", "GENETIC_INFO"]
        
        print(f"Retrieving regulations for: {phi_types}\n")
        docs = retriever.retrieve_multi_phi(
            phi_types=phi_types,
            combine_strategy="union"  # Get all relevant docs
        )
        
        print(f"Found {len(docs)} unique regulation documents\n")
    
    except FileNotFoundError as e:
        print(f"✗ Error: {e}")


def example_7_validate_with_regulations():
    """
    Example 7: Validate entity with regulations
    範例 7：根據法規驗證實體
    """
    print("=== Example 7: Validate Entity ===\n")
    
    embeddings = create_embeddings_manager(preset="multilingual")
    
    try:
        store = RegulationVectorStore.load(embeddings_manager=embeddings)
        chain = create_regulation_rag_chain(vector_store=store)
        
        # Validate if "94歲" should be masked
        result = chain.validate_with_regulations(
            entity_text="94歲",
            phi_type="AGE_OVER_89",
            retrieve_evidence=True
        )
        
        print(f"Entity: {result['entity_text']}")
        print(f"PHI Type: {result['phi_type']}")
        print(f"Should Mask: {result['should_mask']}")
        print(f"Confidence: {result['confidence']}")
        print(f"\nEvidence documents: {len(result['evidence'])}\n")
    
    except Exception as e:
        print(f"✗ Error: {e}")


def example_8_ephemeral_medical_processing():
    """
    Example 8: Ephemeral in-memory processing for medical documents
    範例 8：病歷文件的臨時記憶體處理（不持久化）
    """
    print("=== Example 8: Ephemeral Processing (No Persistence) ===\n")
    
    from medical_deidentification.infrastructure.rag import InMemoryDocumentProcessor
    
    embeddings = create_embeddings_manager(preset="multilingual")
    processor = InMemoryDocumentProcessor(embeddings_manager=embeddings)
    
    medical_text = """
    患者李四，92歲，患有罕見疾病龐貝氏症。
    於本院心臟科接受治療，主治醫師為王醫師。
    """
    
    print("Processing medical document in memory (ephemeral)...")
    print("Query: 'age and rare disease information'\n")
    
    results = processor.process_and_destroy(
        text=medical_text,
        query="age and rare disease information",
        k=3
    )
    
    print(f"Retrieved {len(results)} relevant chunks:")
    for i, doc in enumerate(results, 1):
        print(f"  Chunk {i}: {doc.page_content}\n")
    
    print("✓ Vector store destroyed (no persistence)\n")


def main():
    """Run all examples"""
    examples = [
        example_1_basic_setup,
        example_2_build_vector_store,
        example_3_search_regulations,
        example_4_advanced_retrieval,
        example_5_rag_chain_phi_identification,
        example_6_multi_phi_retrieval,
        example_7_validate_with_regulations,
        example_8_ephemeral_medical_processing,
    ]
    
    print("=" * 60)
    print("RAG System Usage Examples")
    print("=" * 60)
    print()
    
    for i, example in enumerate(examples, 1):
        print(f"\n{'=' * 60}")
        try:
            example()
        except Exception as e:
            print(f"✗ Example {i} failed: {e}\n")
        
        if i < len(examples):
            input("Press Enter to continue to next example...")
    
    print("\n" + "=" * 60)
    print("All examples completed!")
    print("=" * 60)


if __name__ == "__main__":
    # Run specific example
    import sys
    
    if len(sys.argv) > 1:
        example_num = int(sys.argv[1])
        examples = [
            example_1_basic_setup,
            example_2_build_vector_store,
            example_3_search_regulations,
            example_4_advanced_retrieval,
            example_5_rag_chain_phi_identification,
            example_6_multi_phi_retrieval,
            example_7_validate_with_regulations,
            example_8_ephemeral_medical_processing,
        ]
        
        if 1 <= example_num <= len(examples):
            examples[example_num - 1]()
        else:
            print(f"Invalid example number. Choose 1-{len(examples)}")
    else:
        main()
