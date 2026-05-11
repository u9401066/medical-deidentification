"""Helpers for avoiding sensitive text in logs and persisted error fields."""

from __future__ import annotations

from typing import Any


def safe_exception_message(exc: BaseException, *, context: str = "Operation") -> str:
    """Return an exception summary that never includes raw exception text.

    LLM/parser exceptions often embed raw model output. In this project raw model
    output can contain PHI, so callers should log/persist only type-level detail.
    """
    return f"{context} failed ({type(exc).__name__}); details redacted"


def safe_error_payload(exc: BaseException, *, context: str = "Operation") -> dict[str, Any]:
    """Structured safe error detail for task state or pipeline results."""
    return {
        "message": safe_exception_message(exc, context=context),
        "exception_type": type(exc).__name__,
    }


__all__ = ["safe_error_payload", "safe_exception_message"]
