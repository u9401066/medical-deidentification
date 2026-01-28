"""
Processing API Router
PHI 處理 API
"""

import sys
import time
import uuid
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, HTTPException
from loguru import logger

# 處理相對 import
_backend_dir = Path(__file__).parent.parent
if str(_backend_dir) not in sys.path:
    sys.path.insert(0, str(_backend_dir))

from models.task import FileResult, ProcessRequest, TaskStatus
from services.file_service import get_file_service
from services.processing_service import get_processing_service
from services.task_service import get_task_service

router = APIRouter()


def _convert_file_results(file_results_dict: dict) -> dict[str, FileResult]:
    """轉換 file_results 字典為 FileResult 模型"""
    return {
        file_id: FileResult(**data)
        for file_id, data in file_results_dict.items()
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


@router.post("/process", response_model=TaskStatus)
async def start_processing(request: ProcessRequest, background_tasks: BackgroundTasks):
    """開始 PHI 處理任務"""
    file_service = get_file_service()
    task_service = get_task_service()

    # 驗證檔案存在並收集原始檔名
    file_names: dict[str, str] = {}
    for file_id in request.file_ids:
        file_path = file_service.get_file_path(file_id)
        if not file_path:
            raise HTTPException(404, f"檔案不存在: {file_id}")
        # 取得原始檔名 (metadata 中儲存的 filename)
        meta = file_service.get_file_metadata(file_id)
        file_names[file_id] = meta["filename"] if meta else file_path.name

    # 建立任務
    task_id = str(uuid.uuid4())[:8]
    task = task_service.create_task(
        task_id=task_id,
        file_ids=request.file_ids,
        config=request.config.model_dump(),
        job_name=request.job_name,
        file_names=file_names,
    )

    # 啟動背景處理
    background_tasks.add_task(process_phi_task, task_id)

    # 返回實際的任務狀態（已經是 processing）
    return TaskStatus(
        task_id=task_id,
        status=task["status"],
        progress=task.get("progress", 0.0),
        message=task.get("message", "準備處理中..."),
        file_ids=request.file_ids,
        created_at=task["created_at"],
        updated_at=task["updated_at"],
        file_results=_convert_file_results(task.get("file_results", {})),
        current_file=task.get("current_file"),
        files_completed=task.get("files_completed", 0),
        total_files=task.get("total_files", 0),
    )


async def process_phi_task(task_id: str):
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
    config = task["config"]
    job_name = task.get("job_name", f"job-{task_id}")

    # 更新為處理中
    task_service.update_task(
        task_id,
        status="processing",
        message="開始處理...",
    )

    results = []
    total_chars = 0
    processed_chars = 0

    try:
        for idx, file_id in enumerate(file_ids):
            file_path = file_service.get_file_path(file_id)
            if not file_path:
                logger.warning(f"File not found: {file_id}")
                task_service.update_file_result(
                    task_id, file_id, status="error", error="檔案不存在"
                )
                continue

            # 更新進度
            progress = idx / len(file_ids)
            elapsed = time.time() - start_time

            # 標記該檔案為處理中
            task_service.update_file_result(task_id, file_id, status="processing")

            task_service.update_task(
                task_id,
                progress=progress,
                message=f"處理中: {file_path.name}",
                current_file=file_path.name,
                files_completed=idx,
                elapsed_time=elapsed,
                elapsed_time_formatted=format_time(elapsed),
            )

            # 取得原始檔名
            file_metadata = file_service.get_file_metadata(file_id)
            original_filename = file_metadata.get("filename") if file_metadata else file_path.name

            # 處理檔案
            file_start_time = time.time()
            try:
                result = processing_service.process_file(
                    file_path, config, original_filename=original_filename
                )
                result["file_id"] = file_id
                results.append(result)

                # 更新字數統計
                content_len = len(result.get("original_content") or "")
                total_chars += content_len
                processed_chars += content_len

                # 記錄單檔成功
                phi_found = result.get("phi_found", 0)
                file_time = time.time() - file_start_time
                task_service.update_file_result(
                    task_id, file_id,
                    status="completed",
                    phi_found=phi_found,
                    processing_time=file_time,
                )

            except Exception as e:
                logger.error(f"Error processing {file_id}: {e}")

                # 記錄單檔失敗
                task_service.update_file_result(
                    task_id, file_id,
                    status="error",
                    error=str(e),
                    processing_time=time.time() - file_start_time,
                )

                results.append(
                    {
                        "file_id": file_id,
                        "filename": file_path.name,
                        "status": "error",
                        "error": str(e),
                    }
                )

        # 計算處理時間
        processing_time = time.time() - start_time

        # 儲存結果
        full_result = {
            "task_id": task_id,
            "job_name": job_name,
            "config": config,
            "results": results,
            "processed_at": datetime.now().isoformat(),
        }

        processing_service.save_result(task_id, full_result)
        processing_service.save_report(task_id, job_name, results, processing_time)

        # 更新統計
        task_service.update_processing_stats(total_chars, processing_time)

        # 計算成功/失敗數量
        total_phi = sum(r.get("phi_found", 0) for r in results)
        success_count = sum(1 for r in results if r.get("status") == "completed")
        error_count = sum(1 for r in results if r.get("status") == "error")

        # 決定任務整體狀態
        if error_count == len(file_ids):
            final_status = "failed"
            final_message = f"所有檔案處理失敗 ({error_count} 個錯誤)"
        elif error_count > 0:
            final_status = "completed"  # 部分成功也算完成
            final_message = f"處理完成：{success_count} 成功 / {error_count} 失敗，共發現 {total_phi} 個 PHI"
        else:
            final_status = "completed"
            final_message = f"處理完成！發現 {total_phi} 個 PHI"

        task_service.update_task(
            task_id,
            status=final_status,
            progress=1.0,
            message=final_message,
            files_completed=len(file_ids),
            elapsed_time=processing_time,
            elapsed_time_formatted=format_time(processing_time),
            result=full_result,
        )

        logger.info(f"✅ Task {task_id} completed: {success_count}/{len(file_ids)} files, {total_phi} PHI found")

    except Exception as e:
        logger.error(f"❌ Task {task_id} failed: {e}")
        task_service.update_task(
            task_id,
            status="failed",
            message=f"處理失敗: {e!s}",
            error=str(e),
        )


@router.get("/tasks", response_model=list[TaskStatus])
async def list_tasks():
    """列出所有任務"""
    task_service = get_task_service()
    tasks = task_service.list_tasks()

    return [
        TaskStatus(
            task_id=t["task_id"],
            status=t["status"],
            progress=t.get("progress", 0),
            message=t.get("message", ""),
            file_ids=t.get("file_ids", []),
            created_at=t["created_at"],
            updated_at=t["updated_at"],
            file_results=_convert_file_results(t.get("file_results", {})),
            current_file=t.get("current_file"),
            files_completed=t.get("files_completed", 0),
            total_files=t.get("total_files", 0),
            elapsed_time=t.get("elapsed_time"),
            estimated_remaining=t.get("estimated_remaining"),
            elapsed_time_formatted=t.get("elapsed_time_formatted"),
            estimated_remaining_formatted=t.get("estimated_remaining_formatted"),
        )
        for t in tasks
    ]


@router.get("/tasks/{task_id}", response_model=TaskStatus)
async def get_task(task_id: str):
    """取得任務狀態"""
    task_service = get_task_service()
    task = task_service.get_task(task_id)

    if not task:
        raise HTTPException(404, "任務不存在")

    return TaskStatus(
        task_id=task["task_id"],
        status=task["status"],
        progress=task.get("progress", 0),
        message=task.get("message", ""),
        file_ids=task.get("file_ids", []),
        created_at=task["created_at"],
        updated_at=task["updated_at"],
        file_results=_convert_file_results(task.get("file_results", {})),
        current_file=task.get("current_file"),
        files_completed=task.get("files_completed", 0),
        total_files=task.get("total_files", 0),
        elapsed_time=task.get("elapsed_time"),
        estimated_remaining=task.get("estimated_remaining"),
        elapsed_time_formatted=task.get("elapsed_time_formatted"),
        estimated_remaining_formatted=task.get("estimated_remaining_formatted"),
    )


@router.get("/stats/processing")
async def get_processing_stats():
    """取得處理統計資料"""
    task_service = get_task_service()
    return task_service.get_processing_stats()
