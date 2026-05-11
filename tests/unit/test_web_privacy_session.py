"""Regression tests for web session isolation and raw-upload retention."""

import json
import sys
from pathlib import Path

import pytest
from fastapi import HTTPException
from starlette.requests import Request

BACKEND_DIR = Path(__file__).resolve().parents[2] / "web" / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from services.auth_service import AuthService
from services.file_service import FileService
from services import task_service as task_module
from services import result_sanitizer
from services.processing_service import ProcessingService
from security import validate_browser_origin


def _request(
    method: str,
    headers: dict[str, str] | None = None,
) -> Request:
    return Request(
        {
            "type": "http",
            "method": method,
            "path": "/api/files",
            "headers": [
                (key.lower().encode("latin-1"), value.encode("latin-1"))
                for key, value in (headers or {}).items()
            ],
            "client": ("203.0.113.10", 12345),
        }
    )


def test_anonymous_session_lifecycle(tmp_path: Path) -> None:
    service = AuthService(tmp_path / "auth.db")

    user, token, expires_at = service.create_anonymous_session()
    loaded = service.get_user_by_session(token)

    assert user.user_id.startswith("anon-")
    assert user.role == "user"
    assert expires_at > service._now()
    assert loaded is not None
    assert loaded.user_id == user.user_id
    assert loaded.username == user.username

    service.delete_session(token)
    assert service.get_user_by_session(token) is None


def test_browser_origin_guard_blocks_cross_site_fetch() -> None:
    request = _request("POST", {"sec-fetch-site": "cross-site"})

    with pytest.raises(HTTPException) as exc:
        validate_browser_origin(request)

    assert exc.value.status_code == 403


def test_browser_origin_guard_blocks_cookie_post_without_origin() -> None:
    request = _request("POST", {"cookie": "medical_deid_session=abc"})

    with pytest.raises(HTTPException) as exc:
        validate_browser_origin(request)

    assert exc.value.status_code == 403


def test_browser_origin_guard_allows_local_frontend_proxy() -> None:
    request = Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/api/files",
            "headers": [(b"x-medical-deid-frontend-proxy", b"1")],
            "client": ("127.0.0.1", 43123),
        }
    )

    validate_browser_origin(request)


def test_result_sanitizer_hides_raw_phi_by_default() -> None:
    payload = {
        "task_id": "task-1",
        "results": [
            {
                "original_content": "Patient 王小明",
                "phi_entities": [
                    {
                        "type": "NAME",
                        "value": "王小明",
                        "masked_value": "[REDACTED]",
                        "reason": "name",
                    }
                ],
            }
        ],
    }

    sanitized = result_sanitizer.sanitize_payload(payload)

    assert sanitized["results"][0]["original_content"] == ""
    assert sanitized["results"][0]["phi_entities"][0]["value"] == "[REDACTED]"
    assert sanitized["results"][0]["phi_entities"][0]["reason"] == ""
    assert sanitized["raw_phi_available"] is True
    assert sanitized["raw_phi_revealed"] is False
    assert payload["results"][0]["phi_entities"][0]["value"] == "王小明"


def test_result_sanitizer_reveals_raw_phi_only_when_allowed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(result_sanitizer, "ALLOW_PHI_REVEAL", True)
    payload = {
        "task_id": "task-1",
        "results": [
            {
                "original_content": "Patient 王小明",
                "phi_entities": [
                    {
                        "type": "NAME",
                        "value": "王小明",
                        "masked_value": "[REDACTED]",
                        "reason": "name",
                    }
                ],
            }
        ],
    }

    sanitized = result_sanitizer.sanitize_payload(payload, reveal_phi=True)

    assert sanitized["results"][0]["original_content"] == "Patient 王小明"
    assert sanitized["results"][0]["phi_entities"][0]["value"] == "王小明"
    assert sanitized["results"][0]["phi_entities"][0]["reason"] == "name"
    assert sanitized["raw_phi_revealed"] is True


def test_result_sanitizer_reports_when_raw_phi_was_not_persisted(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(result_sanitizer, "ALLOW_PHI_REVEAL", True)
    payload = {
        "task_id": "task-1",
        "results": [
            {
                "phi_entities": [
                    {
                        "type": "NAME",
                        "value": "[REDACTED]",
                        "masked_value": "[REDACTED]",
                    }
                ],
            }
        ],
    }

    sanitized = result_sanitizer.sanitize_payload(payload, reveal_phi=True)

    assert sanitized["raw_phi_available"] is False
    assert sanitized["raw_phi_revealed"] is False
    assert "沒有保留原始 PHI" in sanitized["raw_phi_notice"]


def test_processing_result_preserves_masked_table_and_true_char_count(tmp_path: Path) -> None:
    source = tmp_path / "sample.csv"
    source.write_text(
        "name,note\n王小明,Patient 王小明 visited on 2024-01-01\n",
        encoding="utf-8",
    )
    long_original = source.read_text(encoding="utf-8") + ("x" * 6000)
    result = type(
        "Result",
        (),
        {
            "documents": [
                {
                    "phi_entities": [
                        {
                            "type": "NAME",
                            "text": "王小明",
                            "confidence": 0.95,
                            "start_pos": 5,
                            "end_pos": 8,
                            "reason": "name",
                        }
                    ],
                    "original_content": long_original,
                    "masked_content": long_original.replace("王小明", "[REDACTED]"),
                }
            ],
            "summary": {},
        },
    )()

    converted = ProcessingService()._convert_engine_result(
        result,
        source,
        original_filename="sample.csv",
    )

    assert converted["total_chars"] == len(long_original)
    assert len(converted["masked_content"]) > 5000
    assert converted["masked_data"] == [
        {
            "__row": 1,
            "name": "[REDACTED]",
            "note": "Patient [REDACTED] visited on 2024-01-01",
        }
    ]


@pytest.mark.asyncio
async def test_purge_file_content_keeps_metadata_but_removes_raw_file(tmp_path: Path) -> None:
    file_service = FileService(tmp_path / "uploads")
    uploaded = await file_service.upload(
        "synthetic_phi.csv",
        "姓名,電話\n王小明,0912-345-678\n".encode("utf-8"),
        owner_user_id="user-a",
        owner_username="guest-a",
    )

    raw_path = file_service.get_file_path(uploaded.file_id, user_id="user-a")
    assert raw_path is not None
    assert raw_path.exists()

    assert file_service.purge_file_content(uploaded.file_id, user_id="user-a")

    meta_path = next((tmp_path / "uploads").rglob(f"{uploaded.file_id}.meta.json"))
    metadata = json.loads(meta_path.read_text(encoding="utf-8"))
    assert metadata["content_deleted"] is True
    assert metadata["preview_available"] is False
    assert not raw_path.exists()
    assert file_service.get_file_path(uploaded.file_id, user_id="user-a") is None


@pytest.mark.asyncio
async def test_purge_file_content_enforces_owner(tmp_path: Path) -> None:
    file_service = FileService(tmp_path / "uploads")
    uploaded = await file_service.upload(
        "owner_only.csv",
        b"name\nAlice\n",
        owner_user_id="owner",
    )

    with pytest.raises(PermissionError):
        file_service.purge_file_content(uploaded.file_id, user_id="other-user")


def test_interrupted_processing_tasks_are_recovered_as_failed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(task_module, "DATA_DIR", tmp_path)
    monkeypatch.setattr(task_module, "TASKS_DB_FILE", tmp_path / "tasks.json")
    service = task_module.TaskService()
    task = service.create_task(
        task_id="task-interrupted",
        file_ids=["file-1"],
        config={},
        owner_user_id="user-a",
        owner_username="guest-a",
        file_names={"file-1": "sample.csv"},
    )

    assert task["status"] == "processing"
    assert service.mark_interrupted_tasks_failed() == 1

    recovered = service.get_task("task-interrupted")
    assert recovered is not None
    assert recovered["status"] == "failed"
    assert recovered["file_results"]["file-1"]["status"] == "error"
    assert "重新處理" in recovered["message"]
