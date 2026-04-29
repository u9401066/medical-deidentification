"""Tests for backend.utils.safe_paths."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Make web/backend importable
_BACKEND_DIR = Path(__file__).resolve().parent.parent.parent / "web" / "backend"
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

from utils.safe_paths import (  # noqa: E402
    is_safe_identifier,
    safe_join,
    sanitize_filename,
)


@pytest.mark.parametrize(
    "value",
    ["abc", "abc-123", "ABC_def", "a" * 128, "12345678", "task-uuid-abc"],
)
def test_is_safe_identifier_accepts_valid(value: str) -> None:
    assert is_safe_identifier(value)


@pytest.mark.parametrize(
    "value",
    [
        "",
        "..",
        "../etc/passwd",
        "abc/def",
        "abc\\def",
        "abc def",
        "abc;rm",
        "abc\nfoo",
        "a" * 129,  # too long
        "*",
        "?",
    ],
)
def test_is_safe_identifier_rejects_invalid(value: str) -> None:
    assert not is_safe_identifier(value)


def test_safe_join_resolves_inside_base(tmp_path: Path) -> None:
    target = safe_join(tmp_path, "foo.json")
    assert target == (tmp_path / "foo.json").resolve()


def test_safe_join_blocks_traversal(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        safe_join(tmp_path, "../escape.json")


def test_safe_join_blocks_absolute_outside(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        safe_join(tmp_path, "/etc/passwd")


def test_sanitize_filename_strips_unsafe_chars() -> None:
    # CRLF + quote injection attempt for Content-Disposition
    raw = 'evil"\r\nSet-Cookie: x=1.txt'
    cleaned = sanitize_filename(raw)
    assert "\r" not in cleaned
    assert "\n" not in cleaned
    assert '"' not in cleaned
    assert cleaned.endswith(".txt")


def test_sanitize_filename_falls_back_when_empty() -> None:
    assert sanitize_filename("", fallback="x.bin") == "x.bin"
    assert sanitize_filename("...", fallback="x.bin") == "x.bin"


def test_sanitize_filename_preserves_alphanumeric() -> None:
    assert sanitize_filename("report_abc-123.csv") == "report_abc-123.csv"
