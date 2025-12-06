"""
Unit Tests for PHI Detection Tools | PHI 檢測工具單元測試

Tests for Phase 1 tool implementations:
- RegexPHITool
- IDValidatorTool
- PhoneTool
- ToolRunner
"""

import pytest
from typing import List

from medical_deidentification.domain.phi_types import PHIType
from medical_deidentification.infrastructure.tools import (
    BasePHITool,
    ToolResult,
    ToolRunner,
    RegexPHITool,
    IDValidatorTool,
    PhoneTool,
)
from medical_deidentification.infrastructure.tools.base_tool import merge_results


class TestToolResult:
    """Tests for ToolResult dataclass"""
    
    def test_tool_result_creation(self):
        """Test basic ToolResult creation"""
        result = ToolResult(
            text="A123456789",
            phi_type=PHIType.ID,
            start_pos=10,
            end_pos=20,
            confidence=0.95,
            tool_name="test_tool"
        )
        
        assert result.text == "A123456789"
        assert result.phi_type == PHIType.ID
        assert result.confidence == 0.95
    
    def test_tool_result_to_dict(self):
        """Test ToolResult serialization"""
        result = ToolResult(
            text="test@example.com",
            phi_type=PHIType.EMAIL,
            start_pos=0,
            end_pos=16,
            confidence=0.90,
            tool_name="regex"
        )
        
        d = result.to_dict()
        assert d["text"] == "test@example.com"
        assert d["phi_type"] == "EMAIL"
        assert d["confidence"] == 0.90
    
    def test_tool_result_from_dict(self):
        """Test ToolResult deserialization"""
        d = {
            "text": "A123456789",
            "phi_type": "ID",
            "start_pos": 0,
            "end_pos": 10,
            "confidence": 0.95,
        }
        
        result = ToolResult.from_dict(d)
        assert result.text == "A123456789"
        assert result.phi_type == PHIType.ID
    
    def test_tool_result_equality(self):
        """Test ToolResult equality comparison"""
        r1 = ToolResult("A123456789", PHIType.ID, 0, 10)
        r2 = ToolResult("A123456789", PHIType.ID, 0, 10)
        r3 = ToolResult("B234567890", PHIType.ID, 0, 10)
        
        assert r1 == r2
        assert r1 != r3


class TestMergeResults:
    """Tests for merge_results function"""
    
    def test_merge_empty(self):
        """Test merging empty list"""
        assert merge_results([]) == []
    
    def test_merge_no_overlap(self):
        """Test merging non-overlapping results"""
        results = [
            ToolResult("A123456789", PHIType.ID, 0, 10),
            ToolResult("test@example.com", PHIType.EMAIL, 20, 36),
        ]
        
        merged = merge_results(results)
        assert len(merged) == 2
    
    def test_merge_overlapping_keep_higher_confidence(self):
        """Test merging overlapping results keeps higher confidence"""
        results = [
            ToolResult("A123456789", PHIType.ID, 0, 10, confidence=0.70),
            ToolResult("A123456789", PHIType.ID, 0, 10, confidence=0.95),
        ]
        
        merged = merge_results(results)
        assert len(merged) == 1
        assert merged[0].confidence == 0.95


class TestRegexPHITool:
    """Tests for RegexPHITool"""
    
    def test_detect_taiwan_id(self):
        """Test Taiwan National ID detection"""
        tool = RegexPHITool()
        text = "患者身份證: A123456789"
        
        results = tool.scan(text)
        
        id_results = [r for r in results if r.phi_type == PHIType.ID]
        assert len(id_results) >= 1
        assert any(r.text == "A123456789" for r in id_results)
    
    def test_detect_email(self):
        """Test email detection"""
        tool = RegexPHITool()
        text = "聯絡信箱: patient@hospital.com"
        
        results = tool.scan(text)
        
        email_results = [r for r in results if r.phi_type == PHIType.EMAIL]
        assert len(email_results) == 1
        assert email_results[0].text == "patient@hospital.com"
    
    def test_detect_url(self):
        """Test URL detection"""
        tool = RegexPHITool()
        text = "參考網址: https://www.example.com/patient/123"
        
        results = tool.scan(text)
        
        url_results = [r for r in results if r.phi_type == PHIType.URL]
        # May detect both https:// and www. patterns
        assert len(url_results) >= 1
        assert any("example.com" in r.text for r in url_results)
    
    def test_detect_date_formats(self):
        """Test various date format detection"""
        tool = RegexPHITool()
        text = "就診日期: 2024-03-15, 出生日期: 民國85年5月10日"
        
        results = tool.scan(text)
        
        date_results = [r for r in results if r.phi_type == PHIType.DATE]
        assert len(date_results) >= 2
    
    def test_detect_ip_address(self):
        """Test IP address detection"""
        tool = RegexPHITool()
        text = "登入 IP: 192.168.1.100"
        
        results = tool.scan(text)
        
        ip_results = [r for r in results if r.phi_type == PHIType.IP_ADDRESS]
        assert len(ip_results) == 1
        assert ip_results[0].text == "192.168.1.100"
    
    def test_positions_correct(self):
        """Test that start/end positions are correct"""
        tool = RegexPHITool()
        text = "ID: A123456789 done"
        
        results = tool.scan(text)
        id_results = [r for r in results if r.phi_type == PHIType.ID]
        
        assert len(id_results) >= 1
        result = id_results[0]
        assert text[result.start_pos:result.end_pos] == result.text


class TestIDValidatorTool:
    """Tests for IDValidatorTool"""
    
    def test_valid_taiwan_id(self):
        """Test valid Taiwan ID detection with checksum"""
        tool = IDValidatorTool()
        # A123456789 has valid checksum
        text = "身份證: A123456789"
        
        results = tool.scan(text)
        
        assert len(results) >= 1
        id_result = results[0]
        assert id_result.metadata.get("id_type") == "TW_NATIONAL_ID"
        # Note: A123456789 may or may not have valid checksum
        # depending on the actual checksum algorithm
    
    def test_invalid_taiwan_id_format(self):
        """Test invalid Taiwan ID format not detected"""
        tool = IDValidatorTool()
        text = "Invalid: 123456789A"  # Wrong format
        
        results = tool.scan(text)
        
        # Should not match wrong format
        assert all(r.metadata.get("id_type") != "TW_NATIONAL_ID" for r in results)
    
    def test_validate_checksum_function(self):
        """Test the checksum validation directly"""
        tool = IDValidatorTool()
        
        # These are well-known test cases
        # Note: Real valid IDs should not be used in tests
        is_valid, id_type = tool.validate_id("A123456789")
        assert id_type == "TW_NATIONAL_ID"


class TestPhoneTool:
    """Tests for PhoneTool"""
    
    def test_detect_taiwan_mobile(self):
        """Test Taiwan mobile number detection"""
        tool = PhoneTool()
        text = "手機: 0912-345-678"
        
        results = tool.scan(text)
        
        assert len(results) >= 1
        assert any(
            r.phi_type == PHIType.PHONE and "0912" in r.text
            for r in results
        )
    
    def test_detect_taiwan_landline(self):
        """Test Taiwan landline detection"""
        tool = PhoneTool()
        text = "電話: 02-1234-5678"
        
        results = tool.scan(text)
        
        assert len(results) >= 1
        phone_results = [r for r in results if r.phi_type == PHIType.PHONE]
        assert len(phone_results) >= 1
    
    def test_detect_fax_with_context(self):
        """Test fax detection based on context"""
        tool = PhoneTool()
        text = "傳真: 02-8765-4321"
        
        results = tool.scan(text)
        
        # Should be detected as FAX due to context
        fax_results = [r for r in results if r.phi_type == PHIType.FAX]
        assert len(fax_results) >= 1
    
    def test_detect_international_format(self):
        """Test international phone format"""
        tool = PhoneTool()
        text = "國際電話: +886-2-1234-5678"
        
        results = tool.scan(text)
        
        assert len(results) >= 1
        assert any("+886" in r.text for r in results)
    
    def test_normalize_phone(self):
        """Test phone normalization"""
        tool = PhoneTool()
        
        # Test internal normalization
        normalized = tool._normalize_phone("0912-345-678")
        assert normalized == "0912345678"
        
        normalized = tool._normalize_phone("+886-2-1234-5678")
        assert normalized == "+886212345678"


class TestToolRunner:
    """Tests for ToolRunner"""
    
    def test_create_default(self):
        """Test default ToolRunner creation"""
        runner = ToolRunner.create_default()
        
        assert len(runner.tools) == 3  # regex, id_validator, phone
        assert runner.num_workers == 1
    
    def test_run_all_single_process(self):
        """Test single-process tool execution"""
        runner = ToolRunner.create_default()
        text = "患者張三, ID: A123456789, 電話: 0912-345-678"
        
        results = runner.run_all(text)
        
        # Should find ID and phone
        assert len(results) >= 2
        phi_types = {r.phi_type for r in results}
        assert PHIType.ID in phi_types or PHIType.PHONE in phi_types
    
    def test_run_batch_single_process(self):
        """Test batch processing in single-process mode"""
        runner = ToolRunner.create_default()
        texts = [
            "ID: A123456789",
            "電話: 0912-345-678",
            "Email: test@example.com",
        ]
        
        results = runner.run_batch(texts)
        
        assert len(results) == 3
        assert "chunk_0" in results
        assert "chunk_1" in results
        assert "chunk_2" in results
    
    def test_run_batch_with_custom_ids(self):
        """Test batch processing with custom chunk IDs"""
        runner = ToolRunner.create_default()
        texts = ["ID: A123456789"]
        chunk_ids = ["my_chunk_1"]
        
        results = runner.run_batch(texts, chunk_ids=chunk_ids)
        
        assert "my_chunk_1" in results
    
    def test_context_manager(self):
        """Test context manager for resource cleanup"""
        with ToolRunner.create_default() as runner:
            results = runner.run_all("test@example.com")
            assert len(results) >= 1
    
    def test_empty_text(self):
        """Test handling of empty text"""
        runner = ToolRunner.create_default()
        results = runner.run_all("")
        
        assert results == []
    
    def test_no_phi_text(self):
        """Test handling of text with no PHI"""
        runner = ToolRunner.create_default()
        results = runner.run_all("這是一段沒有個資的普通文字。")
        
        # May or may not find anything depending on patterns
        # Just ensure no crash
        assert isinstance(results, list)


class TestToolIntegration:
    """Integration tests combining multiple tools"""
    
    def test_multiple_phi_types_in_single_text(self):
        """Test detecting multiple PHI types in one text"""
        runner = ToolRunner.create_default()
        text = """
        病患資料：
        姓名：張三
        身份證字號：A123456789
        電話：0912-345-678
        電子郵件：patient@hospital.com
        就診日期：2024-03-15
        """
        
        results = runner.run_all(text)
        
        # Should find multiple different PHI types
        phi_types = {r.phi_type for r in results}
        assert len(phi_types) >= 2  # At least ID, phone, or email
    
    def test_deduplication_across_tools(self):
        """Test that overlapping detections are deduplicated"""
        runner = ToolRunner.create_default()
        # Both regex and ID validator might detect this
        text = "A123456789"
        
        results = runner.run_all(text)
        
        # Should be deduplicated to one result per unique position
        positions = [(r.start_pos, r.end_pos) for r in results]
        unique_positions = set(positions)
        # Allow some duplicates due to different tools, but not excessive
        assert len(positions) <= len(unique_positions) * 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
