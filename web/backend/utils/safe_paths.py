"""Path / identifier validation helpers.

These helpers protect API endpoints from:
- Path traversal attacks via user-supplied identifiers (task_id / file_id)
- HTTP header injection via filenames in ``Content-Disposition``
"""

from __future__ import annotations

import re
from pathlib import Path

# Task / file identifiers are generated as UUID hex fragments
# (see ``services.file_service.FileService.upload`` and ``api.processing``).
# Restrict to a safe alphanumeric-with-dash character set so attackers cannot
# inject path separators or wildcards (e.g. ``../`` or ``*``).
_SAFE_ID_RE = re.compile(r"^[A-Za-z0-9_-]{1,128}$")

# Characters that are illegal/unsafe in a Content-Disposition filename or on
# common filesystems. Newlines are explicitly excluded to prevent header
# injection (CRLF) attacks.
_UNSAFE_FILENAME_CHARS = re.compile(r'[\x00-\x1f\x7f"\\/<>:|?*\r\n]')


def is_safe_identifier(identifier: str) -> bool:
    """Return ``True`` when *identifier* matches the safe identifier pattern.

    Used to reject path traversal payloads in user-supplied ``task_id`` or
    ``file_id`` query/path parameters before any filesystem access.
    """
    return bool(identifier) and bool(_SAFE_ID_RE.match(identifier))


def safe_join(base: Path, *parts: str) -> Path:
    """Resolve ``base / *parts`` and ensure it stays inside ``base``.

    Raises ``ValueError`` if the resolved path escapes the base directory.
    """
    base_resolved = base.resolve()
    candidate = base_resolved.joinpath(*parts).resolve()
    try:
        candidate.relative_to(base_resolved)
    except ValueError as exc:
        raise ValueError(
            f"Resolved path {candidate} escapes base directory {base_resolved}"
        ) from exc
    return candidate


def sanitize_filename(filename: str, fallback: str = "download") -> str:
    """Sanitize a filename for use in HTTP ``Content-Disposition`` headers.

    Replaces unsafe characters with ``_`` and strips leading dots/whitespace.
    Always returns a non-empty string (falls back to *fallback* when empty).
    """
    if not filename:
        return fallback
    cleaned = _UNSAFE_FILENAME_CHARS.sub("_", filename)
    cleaned = cleaned.strip(" .")
    return cleaned or fallback


__all__ = [
    "is_safe_identifier",
    "safe_join",
    "sanitize_filename",
]
