"""Tests for strengthened PHI detection heuristics."""

from core.domain.phi_types import PHIType
from core.infrastructure.tools.id_validator_tool import IDValidatorTool
from core.infrastructure.tools.phone_tool import PhoneTool
from core.infrastructure.tools.regex_phi_tool import RegexPHITool


def test_regex_email_rejects_consecutive_dots() -> None:
    tool = RegexPHITool()
    results = tool.scan_type("bad test@..com good a.b@example.com", PHIType.EMAIL)
    assert [r.text for r in results] == ["a.b@example.com"]


def test_regex_date_rejects_invalid_month_day() -> None:
    tool = RegexPHITool()
    text = "invalid 2024-13-32 valid 2024-12-31 invalid 民國112年13月5日"
    results = tool.scan_type(text, PHIType.DATE)
    assert [r.text for r in results] == ["2024-12-31"]


def test_regex_scan_uses_full_match_when_capture_group_absent() -> None:
    tool = RegexPHITool()
    results = tool.scan_type("傳真: 02-1234-5678", PHIType.FAX)
    assert results
    assert results[0].text == "傳真: 02-1234-5678"


def test_phone_tool_deduplicates_normalized_numbers() -> None:
    tool = PhoneTool()
    results = tool.scan("手機 0912-345-678，備註 0912345678")
    normalized = [r.metadata["normalized"] for r in results]
    assert normalized.count("0912345678") == 1


def test_taiwan_arc_requires_two_valid_letters() -> None:
    tool = IDValidatorTool()
    assert not tool._validate_taiwan_arc("AZ12345678")
