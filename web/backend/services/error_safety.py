"""Backend-safe error summaries for logs and API/task state."""

from __future__ import annotations


def safe_exception_message(exc: BaseException, *, context: str = "Operation") -> str:
    """Summarize an exception without copying raw text into logs/state."""
    return f"{context} failed ({type(exc).__name__}); details redacted"


__all__ = ["safe_exception_message"]
