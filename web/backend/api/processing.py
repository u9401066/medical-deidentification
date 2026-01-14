"""
Processing API Router
PHI 處理 API
"""
import sys
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, BackgroundTasks, HTTPException
from loguru import logger

# 處理相對 import
_backend_dir = Path(__file__).parent.parent
if str(_backend_dir) not in sys.path:
    sys.path.insert(0, str(_backend_dir))

from models.task import ProcessRequest, TaskStatus
from services.file_service import get_file_service
from services.task_service import get_task_service
from services.processing_service import get_processing_service

router = APIRouter()


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
    
    # 驗證檔案存在
    for file_id in request.file_ids:
        if not file_service.get_file_path(file_id):
            raise HTTPException(404, f"檔案不存在: {file_id}")
    
    # 建立任務
    task_id = str(uuid.uuid4())[:8]
    task = task_service.create_task(
        task_id=task_id,
        file_ids=request.file_ids,
        config=request.config.model_dump(),
        job_name=request.job_name,
    )
    
    # 啟動背景處理
    background_tasks.add_task(process_phi_task, task_id)
    
    now = datetime.now()
    return TaskStatus(
        task_id=task_id,
        status="pending",
        progress=0.0,
        message="任務已建立，等待處理...",
        file_ids=request.file_ids,
        created_at=now,
        updated_at=now,
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
                continue
            
            # 更新進度
            progress = idx / len(file_ids)
            elapsed = time.time() - start_time
            
            task_service.update_task(
                task_id,
                progress=progress,
                message=f"處理中: {file_path.name}",
                current_file=file_path.name,
                files_completed=idx,
                elapsed_time=elapsed,
                elapsed_time_formatted=format_time(elapsed),
            )
            
            # 處理檔案
            try:
                result = processing_service.process_file(file_path, config)
                result["file_id"] = file_id
                results.append(result)
                
                # 更新字數統計
                content_len = len(result.get("original_content", ""))
                total_chars += content_len
                processed_chars += content_len
                
            except Exception as e:
                logger.error(f"Error processing {file_id}: {e}")
                results.append({
                    "file_id": file_id,
                    "filename": file_path.name,
                    "status": "error",
                    "error": str(e),
                })
        
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
        
        # 完成任務
        total_phi = sum(r.get("phi_found", 0) for r in results)
        task_service.update_task(
            task_id,
            status="completed",
            progress=1.0,
            message=f"處理完成！發現 {total_phi} 個 PHI",
            files_completed=len(file_ids),
            elapsed_time=processing_time,
            elapsed_time_formatted=format_time(processing_time),
            result=full_result,
        )
        
        logger.info(f"✅ Task {task_id} completed: {len(results)} files, {total_phi} PHI found")
        
    except Exception as e:
        logger.error(f"❌ Task {task_id} failed: {e}")
        task_service.update_task(
            task_id,
            status="failed",
            message=f"處理失敗: {str(e)}",
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
