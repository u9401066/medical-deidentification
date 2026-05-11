"""Privacy-aware result/report response shaping."""

import json
from typing import Any

from config import ALLOW_PHI_REVEAL


REDACTED_VALUES = {"", "[REDACTED]", "[已隱藏]", None}


def _clone_payload(data: dict[str, Any]) -> dict[str, Any]:
    return json.loads(json.dumps(data, ensure_ascii=False, default=str))


def _iter_entity_containers(payload: dict[str, Any]):
    for result in payload.get("results", []) or []:
        yield result
    for detail in payload.get("file_details", []) or []:
        yield detail


def _has_raw_phi_values(payload: dict[str, Any]) -> bool:
    for container in _iter_entity_containers(payload):
        for entity in container.get("phi_entities", []) or []:
            if entity.get("value") not in REDACTED_VALUES:
                return True
    return False


def _set_review_metadata(
    payload: dict[str, Any],
    *,
    reveal_requested: bool,
    raw_available: bool,
    raw_revealed: bool,
) -> None:
    payload["raw_phi_available"] = raw_available
    payload["raw_phi_revealed"] = raw_revealed
    payload["raw_phi_reveal_requested"] = reveal_requested
    payload["raw_phi_reveal_allowed"] = ALLOW_PHI_REVEAL

    if raw_revealed:
        payload["raw_phi_notice"] = "校對模式已啟用：原始 PHI 僅提供給此結果的授權使用者檢視。"
    elif reveal_requested and not ALLOW_PHI_REVEAL:
        payload["raw_phi_notice"] = (
            "伺服器未啟用 PHI 校對揭露。請設定 MEDICAL_DEID_ALLOW_PHI_REVEAL=1。"
        )
    elif reveal_requested and not raw_available:
        payload["raw_phi_notice"] = (
            "這批結果沒有保留原始 PHI 值，無法事後揭露；請在校對模式設定下重新處理。"
        )
    else:
        payload["raw_phi_notice"] = "原始 PHI 預設隱藏；需要校對時可切換校對模式。"


def sanitize_payload(data: dict[str, Any], *, reveal_phi: bool = False) -> dict[str, Any]:
    """Return a copy safe for API responses.

    Raw PHI values are revealed only when the caller explicitly requests it and
    the server policy allows it. Generated files may contain legacy raw PHI, so
    the response layer must be conservative regardless of how the file was made.
    """
    sanitized = _clone_payload(data)
    raw_available = _has_raw_phi_values(sanitized)
    raw_revealed = bool(reveal_phi and ALLOW_PHI_REVEAL and raw_available)

    if not raw_revealed:
        for container in _iter_entity_containers(sanitized):
            container.pop("original_data", None)
            container["original_content"] = ""
            for entity in container.get("phi_entities", []) or []:
                entity["value"] = "[REDACTED]"
                entity["reason"] = ""

    _set_review_metadata(
        sanitized,
        reveal_requested=bool(reveal_phi),
        raw_available=raw_available,
        raw_revealed=raw_revealed,
    )
    return sanitized


__all__ = ["sanitize_payload"]
