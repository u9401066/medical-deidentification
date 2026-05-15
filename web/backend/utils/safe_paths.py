"""Path / identifier validation helpers.

These helpers protect API endpoints from:
- Path traversal attacks via user-supplied identifiers (task_id / file_id)
- HTTP header injection via filenames in ``Content-Disposition``
"""

from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import quote

# Task / file / preset identifiers are generated from UUIDs (see e.g.
# ``services.file_service.FileService.upload``) but may also include
# user-supplied preset names. Restrict to a safe ASCII subset so attackers
# cannot inject path separators, wildcards, or shell metacharacters
# (e.g. ``../``, ``*``, NUL).
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


def content_disposition_header(filename: str, fallback: str = "download") -> str:
    """Return a safe attachment Content-Disposition value.

    Includes both a quoted ``filename`` and RFC 5987 ``filename*`` so browsers
    can correctly download non-ASCII filenames such as Chinese report names.
    """
    safe_name = sanitize_filename(filename, fallback=fallback)
    encoded_name = quote(safe_name)
    return f'attachment; filename="{safe_name}"; filename*=UTF-8\'\'{encoded_name}'


__all__ = [
    "is_safe_identifier",
    "safe_join",
    "sanitize_filename",
    "content_disposition_header",
]
