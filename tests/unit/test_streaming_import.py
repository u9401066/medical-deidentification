"""Test imports for streaming PHI chain"""
import sys

results = []

try:
    results.append("Testing streaming_processor...")
    from core.infrastructure.rag.chains.streaming_processor import (
        StreamingChunkProcessor,
        ChunkInfo,
        ChunkResult,
        ProcessingCheckpoint,
    )
    results.append("  OK")
    
    results.append("Testing streaming_phi_chain...")
    from core.infrastructure.rag.chains.streaming_phi_chain import (
        StreamingPHIChain,
        StreamingPHIConfig,
        PHIChunkResult,
    )
    results.append("  OK")
    
    results.append("Testing chains __init__...")
    from core.infrastructure.rag.chains import (
        StreamingPHIChain,
        StreamingPHIConfig,
    )
    results.append("  OK")
    
    results.append("\nAll imports successful!")
    
except Exception as e:
    results.append(f"ERROR: {e}")
    import traceback
    results.append(traceback.format_exc())

# Write results to file
with open("test_import_result.txt", "w") as f:
    f.write("\n".join(results))
