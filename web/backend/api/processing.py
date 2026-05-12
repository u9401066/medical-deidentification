"""
Processing API Router
PHI 處理 API
"""

import sys
import time
import uuid
import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from loguru import logger

# 處理相對 import
_backend_dir = Path(__file__).parent.parent
if str(_backend_dir) not in sys.path:
    sys.path.insert(0, str(_backend_dir))

from config import (
    DELETE_UPLOAD_AFTER_PROCESS,
    PROCESSING_WORKERS,
    PROGRESS_ESTIMATE_SECONDS,
    RESULT_TTL_HOURS,
    UPLOAD_TTL_HOURS,
)
from models.auth import AuthUser
from models.task import ProcessRequest, TaskStatus
from security import get_current_user
from services.file_service import get_file_service
from services.error_safety import safe_exception_message
from services.processing_service import get_processing_service
from services.task_service import get_task_service

router = APIRouter()
PROCESSING_EXECUTOR = ThreadPoolExecutor(
    max_workers=PROCESSING_WORKERS,
    thread_name_prefix="medical-deid-worker",
)
PHASE_LABELS = {
    "queued": "任務已排入佇列",
    "validating": "驗證檔案與設定",
    "reading": "讀取檔案內容",
    "model_scanning": "模型掃描 PHI 中",
    "finalizing": "整理去識別化輸出",
    "saving": "儲存結果與報告",
}
PHASE_PROGRESS = {
    "queued": 0.02,
    "validating": 0.06,
    "reading": 0.10,
    "finalizing": 0.92,
    "saving": 0.97,
}


def format_time(seconds: float | None) -> str:
    """格式化時間為人類可讀格式"""
    if seconds is None or seconds < 0:
        return "計算中..."
    if seconds < 60:
        return f"{seconds:.0f} 秒"
    elif seconds < 3600:
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{mins} 分 {secs} 秒"
    else:
        hours = int(seconds // 3600)
        mins = int((seconds % 3600) // 60)
        return f"{hours} 小時 {mins} 分"


def normalized_file_results(task: dict) -> dict:
    """Return file_results, synthesizing legacy tasks so UI can show filenames."""
    file_results = dict(task.get("file_results") or {})
    file_names = task.get("file_names") or {}
    task_status = task.get("status", "pending")
    default_file_status = (
        "completed" if task_status == "completed" else "error" if task_status == "failed" else task_status
    )

    for file_id in task.get("file_ids", []):
        file_results.setdefault(
            file_id,
            {
                "file_id": file_id,
                "filename": file_names.get(file_id, file_id),
                "status": default_file_status,
                "phi_found": 0,
                "error": None,
                "processing_time": None,
            },
        )
    return file_results


def _overall_progress(file_index: int, total_files: int, current_file_progress: float) -> float:
    """Convert per-file progress into whole-task progress."""
    if total_files <= 0:
        return 0.0
    bounded = min(max(current_file_progress, 0.0), 1.0)
    return min((file_index + bounded) / total_files, 0.99)


def _format_estimated_remaining(elapsed: float, overall_progress: float) -> tuple[float | None, str | None]:
    if overall_progress <= 0.03:
        return None, None
    remaining = max((elapsed / overall_progress) - elapsed, 0.0)
    return remaining, format_time(remaining)


def _model_scan_progress(scan_elapsed: float) -> float:
    """Estimated in-file progress while the LLM call is blocking."""
    scan_window = max(float(PROGRESS_ESTIMATE_SECONDS), 1.0)
    linear = min(scan_elapsed / scan_window, 1.0)
    # Keep headroom for post-processing so the UI never claims completion while LLM is still running.
    return 0.12 + (0.76 * linear)


def _update_phase(
    task_service,
    task_id: str,
    *,
    phase: str,
    file_index: int,
    total_files: int,
    current_file: str,
    current_file_progress: float,
    started_at: float,
    detail_label: str | None = None,
) -> None:
    overall = _overall_progress(file_index, total_files, current_file_progress)
    elapsed = time.time() - started_at
    remaining, remaining_text = _format_estimated_remaining(elapsed, overall)
    label = detail_label or PHASE_LABELS.get(phase, phase)
    task_service.update_task(
        task_id,
        progress=overall,
        message=f"{label}: {current_file}",
        current_file=current_file,
        files_completed=file_index,
        total_files=total_files,
        phase=phase,
        phase_label=label,
        current_file_progress=current_file_progress,
        elapsed_time=elapsed,
        estimated_remaining=remaining,
        elapsed_time_formatted=format_time(elapsed),
        estimated_remaining_formatted=remaining_text,
    )


def _start_model_scan_heartbeat(
    task_service,
    task_id: str,
    *,
    file_index: int,
    total_files: int,
    current_file: str,
    task_started_at: float,
    progress_state: dict[str, Any] | None = None,
    state_lock: Any | None = None,
) -> tuple[threading.Event, threading.Thread]:
    stop_event = threading.Event()
    scan_started_at = time.time()

    def heartbeat() -> None:
        while not stop_event.wait(2.0):
            detail_label: str | None = None
            if progress_state is not None and state_lock is not None:
                with state_lock:
                    true_progress_mode = bool(progress_state.get("true_progress_mode"))
                    current_file_progress = float(
                        progress_state.get("current_file_progress", PHASE_PROGRESS["reading"])
                    )
                    detail_label = progress_state.get("detail_label")
                if not true_progress_mode:
                    current_file_progress = max(
                        current_file_progress,
                        _model_scan_progress(time.time() - scan_started_at),
                    )
            else:
                current_file_progress = _model_scan_progress(time.time() - scan_started_at)

            _update_phase(
                task_service,
                task_id,
                phase="model_scanning",
                file_index=file_index,
                total_files=total_files,
                current_file=current_file,
                current_file_progress=current_file_progress,
                started_at=task_started_at,
                detail_label=detail_label,
            )

    thread = threading.Thread(
        target=heartbeat,
        name=f"progress-heartbeat-{task_id[:8]}",
        daemon=True,
    )
    thread.start()
    return stop_event, thread


def _build_core_progress_callback(
    task_service,
    task_id: str,
    *,
    file_index: int,
    total_files: int,
    current_file: str,
    task_started_at: float,
    progress_state: dict[str, Any],
    state_lock: Any,
):
    """Translate core engine progress events into task progress for the UI."""

    def update_from_core(
        *,
        phase: str,
        current_file_progress: float,
        detail_label: str | None = None,
        true_progress_mode: bool = False,
    ) -> None:
        with state_lock:
            previous = float(progress_state.get("current_file_progress", 0.0))
            next_progress = max(previous, min(max(current_file_progress, 0.0), 0.99))
            progress_state["current_file_progress"] = next_progress
            progress_state["detail_label"] = detail_label
            progress_state["true_progress_mode"] = true_progress_mode

        _update_phase(
            task_service,
            task_id,
            phase=phase,
            file_index=file_index,
            total_files=total_files,
            current_file=current_file,
            current_file_progress=next_progress,
            started_at=task_started_at,
            detail_label=detail_label,
        )

    def callback(event: dict[str, Any]) -> None:
        event_name = event.get("event")

        if event_name == "file_load_completed":
            update_from_core(
                phase="reading",
                current_file_progress=PHASE_PROGRESS["reading"],
                detail_label="檔案讀取完成",
            )
            return

        if event_name == "engine_initializing":
            update_from_core(
                phase="model_scanning",
                current_file_progress=0.12,
                detail_label="初始化去識別化引擎",
            )
            return

        if event_name == "direct_llm_started":
            update_from_core(
                phase="model_scanning",
                current_file_progress=0.18,
                detail_label="模型掃描 PHI 中 (單一 batch)",
                true_progress_mode=False,
            )
            return

        if event_name == "direct_llm_completed":
            update_from_core(
                phase="model_scanning",
                current_file_progress=0.86,
                detail_label="模型掃描完成",
                true_progress_mode=False,
            )
            return

        if event_name == "chunks_prepared":
            total_chunks = int(event.get("total_chunks") or 0)
            update_from_core(
                phase="model_scanning",
                current_file_progress=0.18,
                detail_label=f"模型掃描 PHI 中 (0/{total_chunks} chunks)",
                true_progress_mode=total_chunks > 0,
            )
            return

        if event_name in {"chunk_started", "chunk_completed"}:
            total_chunks = max(int(event.get("total_chunks") or 1), 1)
            chunk_number = max(int(event.get("chunk_number") or 1), 1)
            completed_chunks = chunk_number if event_name == "chunk_completed" else chunk_number - 1
            completed_chunks = min(max(completed_chunks, 0), total_chunks)
            chunk_progress = 0.18 + (0.68 * (completed_chunks / total_chunks))
            update_from_core(
                phase="model_scanning",
                current_file_progress=chunk_progress,
                detail_label=f"模型掃描 PHI 中 ({completed_chunks}/{total_chunks} chunks)",
                true_progress_mode=True,
            )
            return

        if event_name == "reduce_started":
            update_from_core(
                phase="finalizing",
                current_file_progress=0.88,
                detail_label="合併 chunk 掃描結果",
                true_progress_mode=True,
            )
            return

        if event_name in {"reduce_completed", "phi_document_completed"}:
            update_from_core(
                phase="finalizing",
                current_file_progress=0.89,
                detail_label="PHI 掃描結果整理完成",
                true_progress_mode=True,
            )
            return

        if event_name == "masking_document_started":
            update_from_core(
                phase="finalizing",
                current_file_progress=0.90,
                detail_label="套用去識別化遮罩",
                true_progress_mode=True,
            )
            return

        if event_name == "masking_document_completed":
            update_from_core(
                phase="finalizing",
                current_file_progress=0.93,
                detail_label="去識別化遮罩完成",
                true_progress_mode=True,
            )
            return

        if event_name == "pipeline_stage_started":
            stage = event.get("stage")
            stage_progress = {
                "language_detection": (0.13, "偵測文件語言"),
                "regulation_retrieval": (0.15, "準備法規脈絡"),
                "phi_identification": (0.18, "模型掃描 PHI 中"),
                "validation": (0.94, "驗證去識別化結果"),
                "output_generation": (0.96, "產生輸出檔案"),
            }.get(stage)
            if stage_progress:
                if stage == "language_detection":
                    phase = "reading"
                elif stage in {"regulation_retrieval", "phi_identification"}:
                    phase = "model_scanning"
                else:
                    phase = "finalizing"
                update_from_core(
                    phase=phase,
                    current_file_progress=stage_progress[0],
                    detail_label=stage_progress[1],
                    true_progress_mode=stage != "phi_identification",
                )
            return

    return callback


@router.post("/process", response_model=TaskStatus)
async def start_processing(
    request: ProcessRequest,
    current_user: AuthUser = Depends(get_current_user),
):
    """開始 PHI 處理任務"""
    file_service = get_file_service()
    task_service = get_task_service()

    # 驗證檔案存在
    file_names = {}
    for file_id in request.file_ids:
        try:
            file_path = file_service.get_file_path(
                file_id,
                user_id=current_user.user_id,
                is_admin=current_user.role == "admin",
            )
        except (PermissionError, ValueError) as e:
            raise HTTPException(400, str(e)) from e
        if not file_path:
            raise HTTPException(404, f"檔案不存在: {file_id}")
        metadata = file_service.get_file_metadata(
            file_id,
            user_id=current_user.user_id,
            is_admin=current_user.role == "admin",
        ) or {}
        file_names[file_id] = metadata.get("filename", file_path.name)

    # 建立任務
    task_id = str(uuid.uuid4())
    task = task_service.create_task(
        task_id=task_id,
        file_ids=request.file_ids,
        config=request.config.model_dump(),
        owner_user_id=current_user.user_id,
        owner_role=current_user.role,
        owner_username=current_user.username,
        job_name=request.job_name,
        file_names=file_names,
    )

    # 啟動背景處理；固定 worker pool 避免多使用者時無上限建立 thread。
    loop = asyncio.get_running_loop()
    loop.run_in_executor(PROCESSING_EXECUTOR, process_phi_task, task_id)

    now = datetime.now()
    return TaskStatus(
        task_id=task_id,
        status="processing",
        progress=0.0,
        message="任務已建立，開始處理...",
        file_ids=request.file_ids,
        created_at=now,
        updated_at=now,
        owner_user_id=current_user.user_id,
        owner_username=current_user.username,
        file_results=task.get("file_results", {}),
        phase=task.get("phase"),
        phase_label=task.get("phase_label"),
        current_file_progress=task.get("current_file_progress"),
    )


def process_phi_task(task_id: str):
    """背景處理 PHI 任務"""
    task_service = get_task_service()
    file_service = get_file_service()
    processing_service = get_processing_service()

    task = task_service.get_task(task_id)
    if not task:
        logger.error(f"Task not found: {task_id}")
        return

    start_time = time.time()
    file_ids = task["file_ids"]
    file_names = task.get("file_names", {})
    owner_user_id = task.get("owner_user_id", "")
    owner_is_admin = task.get("owner_role") == "admin"
    config = task["config"]
    job_name = task.get("job_name", f"job-{task_id}")

    # 更新為處理中
    task_service.update_task(
        task_id,
        status="processing",
        message="驗證檔案與設定...",
        phase="validating",
        phase_label=PHASE_LABELS["validating"],
        progress=0.01,
    )

    results = []
    total_chars = 0
    processed_chars = 0

    try:
        for idx, file_id in enumerate(file_ids):
            file_path = file_service.get_file_path(
                file_id,
                user_id=owner_user_id,
                is_admin=owner_is_admin,
            )
            if not file_path:
                logger.warning(f"File not found: {file_id}")
                task_service.update_file_result(
                    task_id,
                    file_id,
                    status="error",
                    error="檔案不存在",
                )
                results.append(
                    {
                        "file_id": file_id,
                        "filename": file_names.get(file_id, file_id),
                        "status": "error",
                        "error": "檔案不存在",
                    }
                )
                continue

            # 更新進度
            display_filename = file_names.get(file_id, file_path.name)
            _update_phase(
                task_service,
                task_id,
                phase="reading",
                file_index=idx,
                total_files=len(file_ids),
                current_file=display_filename,
                current_file_progress=PHASE_PROGRESS["reading"],
                started_at=start_time,
            )

            # 處理檔案
            heartbeat_stop: threading.Event | None = None
            heartbeat_thread: threading.Thread | None = None
            try:
                file_started_at = time.time()
                task_service.update_file_result(task_id, file_id, status="processing")
                progress_state: dict[str, Any] = {
                    "true_progress_mode": False,
                    "current_file_progress": PHASE_PROGRESS["reading"],
                    "detail_label": PHASE_LABELS["reading"],
                }
                progress_state_lock = threading.Lock()
                core_progress_callback = _build_core_progress_callback(
                    task_service,
                    task_id,
                    file_index=idx,
                    total_files=len(file_ids),
                    current_file=display_filename,
                    task_started_at=start_time,
                    progress_state=progress_state,
                    state_lock=progress_state_lock,
                )
                heartbeat_stop, heartbeat_thread = _start_model_scan_heartbeat(
                    task_service,
                    task_id,
                    file_index=idx,
                    total_files=len(file_ids),
                    current_file=display_filename,
                    task_started_at=start_time,
                    progress_state=progress_state,
                    state_lock=progress_state_lock,
                )
                result = processing_service.process_file(
                    file_path,
                    config,
                    original_filename=display_filename,
                    artifact_dir=processing_service.get_task_artifact_dir(
                        task_id,
                        owner_user_id,
                    ),
                    progress_callback=core_progress_callback,
                )
                if heartbeat_stop:
                    heartbeat_stop.set()
                if heartbeat_thread:
                    heartbeat_thread.join(timeout=1.0)
                _update_phase(
                    task_service,
                    task_id,
                    phase="finalizing",
                    file_index=idx,
                    total_files=len(file_ids),
                    current_file=display_filename,
                    current_file_progress=PHASE_PROGRESS["finalizing"],
                    started_at=start_time,
                )
                result["file_id"] = file_id
                results.append(result)

                # 更新字數統計
                content_len = int(result.get("total_chars") or 0)
                total_chars += content_len
                processed_chars += content_len
                task_service.update_file_result(
                    task_id,
                    file_id,
                    status="completed",
                    phi_found=result.get("phi_found", 0),
                    processing_time=time.time() - file_started_at,
                )

            except Exception as e:
                safe_error = safe_exception_message(e, context="File processing")
                if heartbeat_stop:
                    heartbeat_stop.set()
                if heartbeat_thread:
                    heartbeat_thread.join(timeout=1.0)
                logger.error(
                    safe_error,
                    file_id=file_id,
                    error_type=type(e).__name__,
                )
                task_service.update_file_result(
                    task_id,
                    file_id,
                    status="error",
                    error=safe_error,
                )
                results.append(
                    {
                        "file_id": file_id,
                        "filename": display_filename,
                        "status": "error",
                        "error": safe_error,
                    }
                )
            finally:
                if heartbeat_stop:
                    heartbeat_stop.set()
                if heartbeat_thread:
                    heartbeat_thread.join(timeout=1.0)
                if DELETE_UPLOAD_AFTER_PROCESS:
                    try:
                        file_service.purge_file_content(
                            file_id,
                            user_id=owner_user_id,
                            is_admin=owner_is_admin,
                            keep_metadata=True,
                        )
                    except Exception as purge_error:
                        logger.warning(f"Could not purge raw upload {file_id}: {purge_error}")

        # 計算處理時間
        processing_time = time.time() - start_time
        last_filename = file_names.get(file_ids[-1], file_ids[-1]) if file_ids else job_name
        _update_phase(
            task_service,
            task_id,
            phase="saving",
            file_index=max(len(file_ids) - 1, 0),
            total_files=max(len(file_ids), 1),
            current_file=last_filename,
            current_file_progress=PHASE_PROGRESS["saving"],
            started_at=start_time,
        )

        # 儲存結果
        full_result = {
            "task_id": task_id,
            "job_name": job_name,
            "owner_user_id": owner_user_id,
            "config": config,
            "results": results,
            "processed_at": datetime.now().isoformat(),
        }

        processing_service.save_result(task_id, full_result, owner_user_id=owner_user_id)
        processing_service.save_report(
            task_id,
            job_name,
            results,
            processing_time,
            owner_user_id=owner_user_id,
        )
        processing_service.cleanup_expired_outputs(RESULT_TTL_HOURS)
        file_service.cleanup_stale_uploads(UPLOAD_TTL_HOURS)

        # 更新統計
        task_service.update_processing_stats(total_chars, processing_time)

        # 完成任務
        failed_count = sum(1 for r in results if r.get("status") == "error")
        success_count = max(len(results) - failed_count, 0)
        if failed_count == len(file_ids):
            final_status = "failed"
            final_message = f"處理失敗：{failed_count}/{len(file_ids)} 個檔案失敗"
        elif failed_count:
            final_status = "completed_with_errors"
            final_message = f"部分完成：{success_count}/{len(file_ids)} 個檔案成功，{failed_count} 個失敗"
        else:
            final_status = "completed"
            final_message = None

        total_phi = sum(r.get("phi_found", 0) for r in results)
        task_service.update_task(
            task_id,
            status=final_status,
            progress=1.0,
            message=final_message or f"處理完成！發現 {total_phi} 個 PHI",
            files_completed=success_count,
            phase=final_status,
            phase_label="處理完成" if final_status == "completed" else final_message,
            current_file_progress=1.0,
            elapsed_time=processing_time,
            elapsed_time_formatted=format_time(processing_time),
            estimated_remaining=0,
            estimated_remaining_formatted="0 秒",
            result={
                "task_id": task_id,
                "job_name": job_name,
                "files_count": len(results),
                "total_phi_found": total_phi,
                "processed_at": full_result["processed_at"],
            },
        )

        logger.info(
            f"✅ Task {task_id} finished with status={final_status}: "
            f"{success_count} succeeded, {failed_count} failed, {total_phi} PHI found"
        )

    except Exception as e:
        safe_error = safe_exception_message(e, context="Task processing")
        logger.error(
            safe_error,
            task_id=task_id,
            error_type=type(e).__name__,
        )
        task_service.update_task(
            task_id,
            status="failed",
            message=f"處理失敗: {safe_error}",
            error=safe_error,
            phase="failed",
            phase_label="處理失敗",
        )


@router.get("/tasks", response_model=list[TaskStatus])
async def list_tasks(current_user: AuthUser = Depends(get_current_user)):
    """列出所有任務"""
    task_service = get_task_service()
    tasks = task_service.list_tasks(
        user_id=current_user.user_id,
        is_admin=current_user.role == "admin",
    )

    return [
        TaskStatus(
            task_id=t["task_id"],
            status=t["status"],
            progress=t.get("progress", 0),
            message=t.get("message", ""),
            file_ids=t.get("file_ids", []),
            created_at=t["created_at"],
            updated_at=t["updated_at"],
            owner_user_id=t.get("owner_user_id"),
            owner_username=t.get("owner_username"),
            current_file=t.get("current_file"),
            files_completed=t.get("files_completed", 0),
            total_files=t.get("total_files", 0),
            elapsed_time=t.get("elapsed_time"),
            estimated_remaining=t.get("estimated_remaining"),
            elapsed_time_formatted=t.get("elapsed_time_formatted"),
            estimated_remaining_formatted=t.get("estimated_remaining_formatted"),
            phase=t.get("phase"),
            phase_label=t.get("phase_label"),
            current_file_progress=t.get("current_file_progress"),
            file_results=normalized_file_results(t),
        )
        for t in tasks
    ]


@router.get("/tasks/{task_id}", response_model=TaskStatus)
async def get_task(task_id: str, current_user: AuthUser = Depends(get_current_user)):
    """取得任務狀態"""
    task_service = get_task_service()
    task = task_service.get_task(task_id)

    if not task_service.can_access_task(
        task,
        user_id=current_user.user_id,
        is_admin=current_user.role == "admin",
    ):
        raise HTTPException(404, "任務不存在")

    return TaskStatus(
        task_id=task["task_id"],
        status=task["status"],
        progress=task.get("progress", 0),
        message=task.get("message", ""),
        file_ids=task.get("file_ids", []),
        created_at=task["created_at"],
        updated_at=task["updated_at"],
        owner_user_id=task.get("owner_user_id"),
        owner_username=task.get("owner_username"),
        current_file=task.get("current_file"),
        files_completed=task.get("files_completed", 0),
        total_files=task.get("total_files", 0),
        elapsed_time=task.get("elapsed_time"),
        estimated_remaining=task.get("estimated_remaining"),
        elapsed_time_formatted=task.get("elapsed_time_formatted"),
        estimated_remaining_formatted=task.get("estimated_remaining_formatted"),
        phase=task.get("phase"),
        phase_label=task.get("phase_label"),
        current_file_progress=task.get("current_file_progress"),
        file_results=normalized_file_results(task),
    )


@router.get("/stats/processing")
async def get_processing_stats(current_user: AuthUser = Depends(get_current_user)):
    """取得處理統計資料"""
    task_service = get_task_service()
    is_admin = current_user.role == "admin"
    user_tasks = task_service.list_tasks(
        user_id=current_user.user_id,
        is_admin=is_admin,
    )
    if is_admin:
        stats = task_service.get_processing_stats()
    else:
        completed_tasks = [task for task in user_tasks if task.get("status") == "completed"]
        total_time = sum(float(task.get("elapsed_time") or 0) for task in completed_tasks)
        stats = {
            "total_chars_processed": None,
            "total_time_seconds": total_time,
            "task_count": len(completed_tasks),
            "avg_chars_per_second": None,
            "active_tasks": sum(1 for task in user_tasks if task.get("status") == "processing"),
            "total_tasks": len(user_tasks),
        }
    stats["visible_tasks"] = len(user_tasks)
    return stats
