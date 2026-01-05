"""
Streaming Chain Unit Tests | 串流 Chain 單元測試

Tests for StreamingChunkProcessor and StreamingPHIChain
"""

import pytest
import tempfile
import os
import json
from pathlib import Path

from core.infrastructure.rag.chains.streaming_processor import (
    StreamingChunkProcessor,
    ChunkInfo,
    ChunkResult,
    ProcessingCheckpoint,
)
from core.infrastructure.rag.chains.streaming_phi_chain import (
    StreamingPHIChain,
    StreamingPHIConfig,
    PHIChunkResult,
)


class TestChunkInfo:
    """Test ChunkInfo dataclass"""
    
    def test_create_chunk_info(self):
        """Test creating ChunkInfo"""
        info = ChunkInfo(
            chunk_id=0,
            start_pos=0,
            end_pos=100,
            size=100,
            content_hash="abc123",
        )
        assert info.chunk_id == 0
        assert info.start_pos == 0
        assert info.end_pos == 100
        assert info.size == 100
        assert info.content_hash == "abc123"
    
    def test_to_dict(self):
        """Test ChunkInfo to_dict"""
        info = ChunkInfo(
            chunk_id=1,
            start_pos=100,
            end_pos=200,
            size=100,
            content_hash="def456",
        )
        d = info.to_dict()
        assert d["chunk_id"] == 1
        assert d["content_hash"] == "def456"
    
    def test_from_dict(self):
        """Test ChunkInfo from_dict"""
        d = {
            "chunk_id": 2,
            "start_pos": 200,
            "end_pos": 300,
            "size": 100,
            "content_hash": "ghi789",
        }
        info = ChunkInfo.from_dict(d)
        assert info.chunk_id == 2
        assert info.content_hash == "ghi789"


class TestProcessingCheckpoint:
    """Test ProcessingCheckpoint functionality"""
    
    def test_create_checkpoint(self):
        """Test creating checkpoint"""
        checkpoint = ProcessingCheckpoint(
            file_path="test.txt",
            file_hash="abc123",
            total_size=1000,
            total_chunks=10,
        )
        assert checkpoint.file_path == "test.txt"
        assert checkpoint.total_chunks == 10
        assert checkpoint.total_size == 1000
        assert len(checkpoint.processed_chunks) == 0
        assert checkpoint.is_complete is False
    
    def test_progress_percent(self):
        """Test progress calculation"""
        checkpoint = ProcessingCheckpoint(
            file_path="test.txt",
            file_hash="abc123",
            total_size=1000,
            total_chunks=4,
            processed_chunks=[0, 1],
        )
        assert checkpoint.progress_percent == pytest.approx(50.0, rel=0.1)
        
        checkpoint.processed_chunks.append(2)
        checkpoint.processed_chunks.append(3)
        assert checkpoint.is_complete is True
        assert checkpoint.progress_percent == 100.0
    
    def test_save_and_load_checkpoint(self):
        """Test checkpoint persistence"""
        with tempfile.TemporaryDirectory() as tmpdir:
            checkpoint_path = os.path.join(tmpdir, "test.checkpoint.json")
            
            # Create and save
            checkpoint = ProcessingCheckpoint(
                file_path="test.txt",
                file_hash="abc123",
                total_size=1000,
                total_chunks=5,
                processed_chunks=[0, 1],
                last_completed_chunk=1,
            )
            checkpoint.save(checkpoint_path)
            
            # Load
            loaded = ProcessingCheckpoint.load(checkpoint_path)
            assert loaded is not None
            assert loaded.file_path == "test.txt"
            assert loaded.file_hash == "abc123"
            assert 0 in loaded.processed_chunks
            assert 1 in loaded.processed_chunks
            assert loaded.last_completed_chunk == 1


class TestStreamingChunkProcessor:
    """Test StreamingChunkProcessor"""
    
    def test_chunk_text_iterator(self):
        """Test text chunking"""
        text = "A" * 100  # 100 characters
        
        processor = StreamingChunkProcessor[str](
            chunk_size=30,
            chunk_overlap=10,
            process_func=lambda c, i: c,
        )
        
        chunks = list(processor.chunk_text_iterator(text, start_chunk=0))
        
        # Should have multiple chunks
        assert len(chunks) >= 3
        
        # First chunk should have chunk_id 0
        content, info = chunks[0]
        assert info.chunk_id == 0
        assert len(content) == 30
        
        # Check content hash is generated
        assert info.content_hash is not None
        assert len(info.content_hash) == 8
    
    def test_process_text(self):
        """Test processing text"""
        text = "Hello World! This is a test text for chunking."
        processed = []
        
        def process_func(content: str, info: ChunkInfo) -> str:
            return content.upper()
        
        def output_func(result: ChunkResult) -> None:
            if result.success:
                processed.append(result.output)
        
        processor = StreamingChunkProcessor[str](
            chunk_size=20,
            chunk_overlap=5,
            process_func=process_func,
            output_func=output_func,
        )
        
        results = list(processor.process_text(text, "test", resume=False))
        
        # Should have results
        assert len(results) > 0
        
        # All should be successful
        for result in results:
            assert result.success is True
            assert result.output is not None
    
    def test_process_file(self):
        """Test processing file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test file
            test_file = os.path.join(tmpdir, "test.txt")
            with open(test_file, "w", encoding="utf-8") as f:
                f.write("A" * 200)
            
            processed_chunks = []
            
            def process_func(content: str, info: ChunkInfo) -> dict:
                return {"length": len(content), "chunk_id": info.chunk_id}
            
            processor = StreamingChunkProcessor[dict](
                chunk_size=50,
                chunk_overlap=10,
                process_func=process_func,
                checkpoint_dir=tmpdir,
            )
            
            results = list(processor.process_file(test_file, resume=False))
            
            # Should have multiple chunks
            assert len(results) >= 3
            
            # All successful
            for result in results:
                assert result.success is True


class TestStreamingPHIConfig:
    """Test StreamingPHIConfig"""
    
    def test_default_config(self):
        """Test default configuration"""
        config = StreamingPHIConfig()
        
        assert config.chunk_size == 2000
        assert config.chunk_overlap == 100
        assert config.enable_rag is True
        assert config.enable_tools is True
        assert config.checkpoint_interval == 1
    
    def test_custom_config(self):
        """Test custom configuration"""
        config = StreamingPHIConfig(
            chunk_size=1000,
            enable_rag=False,
            enable_tools=False,
        )
        
        assert config.chunk_size == 1000
        assert config.enable_rag is False
        assert config.enable_tools is False


class TestStreamingPHIChain:
    """Test StreamingPHIChain"""
    
    def test_create_chain_without_llm(self):
        """Test creating chain without LLM"""
        config = StreamingPHIConfig(
            enable_rag=False,
            enable_tools=False,
        )
        
        chain = StreamingPHIChain(
            llm=None,
            config=config,
        )
        
        assert chain.config.enable_rag is False
        assert chain.config.enable_tools is False
    
    def test_rag_toggle(self):
        """Test RAG enable/disable"""
        config = StreamingPHIConfig(enable_rag=True)
        chain = StreamingPHIChain(config=config)
        
        assert chain.config.enable_rag is True
        
        chain.disable_rag()
        assert chain.config.enable_rag is False
        
        chain.enable_rag()
        assert chain.config.enable_rag is True
    
    def test_tools_toggle(self):
        """Test tools enable/disable"""
        config = StreamingPHIConfig(enable_tools=True)
        chain = StreamingPHIChain(config=config)
        
        assert chain.config.enable_tools is True
        
        chain.disable_tools()
        assert chain.config.enable_tools is False
        
        chain.enable_tools()
        assert chain.config.enable_tools is True


class TestPHIChunkResult:
    """Test PHIChunkResult"""
    
    def test_create_result(self):
        """Test creating PHI chunk result"""
        result = PHIChunkResult(
            chunk_id=0,
            start_pos=0,
            end_pos=100,
            entities=[],
            raw_text="test",
            success=True,
        )
        
        assert result.chunk_id == 0
        assert result.success is True
        assert len(result.entities) == 0
    
    def test_to_dict(self):
        """Test serialization to dict"""
        result = PHIChunkResult(
            chunk_id=1,
            start_pos=100,
            end_pos=200,
            entities=[],
            raw_text="test content",
            success=True,
            processing_time_ms=50.0,
            tool_calls_made=2,
            rag_used=True,
        )
        
        d = result.to_dict()
        
        assert d["chunk_id"] == 1
        assert d["start_pos"] == 100
        assert d["success"] is True
        assert d["processing_time_ms"] == 50.0
        assert d["tool_calls_made"] == 2
        assert d["rag_used"] is True
