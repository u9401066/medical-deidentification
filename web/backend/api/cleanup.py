"""
Cleanup API Router
系統清理 API
"""

import sys
from pathlib import Path

from fastapi import APIRouter
from loguru import logger
from pydantic import BaseModel

# 處理相對 import
_backend_dir = Path(__file__).parent.parent
if str(_backend_dir) not in sys.path:
    sys.path.insert(0, str(_backend_dir))

from config import REPORTS_DIR, RESULTS_DIR, UPLOAD_DIR
from services.task_service import get_task_service

router = APIRouter()


class CleanupResult(BaseModel):
    """清理結果"""

    success: bool
    message: str
    files_deleted: int
    bytes_freed: int


class CleanupAllResult(BaseModel):
    """全部清理結果"""

    success: bool
    message: str
    uploads: CleanupResult
    results: CleanupResult
    reports: CleanupResult
    tasks_cleared: int


def _cleanup_directory(directory: Path, pattern: str = "*") -> CleanupResult:
    """清理目錄中的檔案

    Args:
        directory: 目標目錄
        pattern: 檔案模式 (glob pattern)

    Returns:
        清理結果
    """
    if not directory.exists():
        return CleanupResult(
            success=True,
            message=f"目錄不存在: {directory.name}",
            files_deleted=0,
            bytes_freed=0,
        )

    files_deleted = 0
    bytes_freed = 0

    try:
        for file_path in directory.glob(pattern):
            if file_path.is_file():
                bytes_freed += file_path.stat().st_size
                file_path.unlink()
                files_deleted += 1
                logger.debug(f"Deleted: {file_path.name}")

        logger.info(f"Cleaned {directory.name}: {files_deleted} files, {bytes_freed} bytes")

        return CleanupResult(
            success=True,
            message=f"已清理 {files_deleted} 個檔案",
            files_deleted=files_deleted,
            bytes_freed=bytes_freed,
        )
    except Exception as e:
        logger.error(f"Cleanup error in {directory}: {e}")
        return CleanupResult(
            success=False,
            message=f"清理失敗: {e!s}",
            files_deleted=files_deleted,
            bytes_freed=bytes_freed,
        )


@router.delete("/cleanup/uploads", response_model=CleanupResult)
async def cleanup_uploads():
    """清空所有上傳的檔案"""
    logger.warning("🗑️ Cleanup: Deleting all uploaded files")
    return _cleanup_directory(UPLOAD_DIR)


@router.delete("/cleanup/results", response_model=CleanupResult)
async def cleanup_results():
    """清空所有處理結果"""
    logger.warning("🗑️ Cleanup: Deleting all results")
    return _cleanup_directory(RESULTS_DIR)


@router.delete("/cleanup/reports", response_model=CleanupResult)
async def cleanup_reports():
    """清空所有報告"""
    logger.warning("🗑️ Cleanup: Deleting all reports")
    return _cleanup_directory(REPORTS_DIR)


@router.delete("/cleanup/all", response_model=CleanupAllResult)
async def cleanup_all():
    """清空所有資料（上傳、結果、報告、任務）"""
    logger.warning("🗑️🗑️🗑️ Cleanup: Deleting ALL data")

    # 清理各目錄
    uploads_result = _cleanup_directory(UPLOAD_DIR)
    results_result = _cleanup_directory(RESULTS_DIR)
    reports_result = _cleanup_directory(REPORTS_DIR)

    # 清理任務記錄
    task_service = get_task_service()
    tasks_cleared = task_service.clear_all_tasks()

    total_files = (
        uploads_result.files_deleted
        + results_result.files_deleted
        + reports_result.files_deleted
    )
    total_bytes = (
        uploads_result.bytes_freed
        + results_result.bytes_freed
        + reports_result.bytes_freed
    )

    return CleanupAllResult(
        success=uploads_result.success and results_result.success and reports_result.success,
        message=f"已清理 {total_files} 個檔案，釋放 {total_bytes / 1024:.1f} KB",
        uploads=uploads_result,
        results=results_result,
        reports=reports_result,
        tasks_cleared=tasks_cleared,
    )


@router.get("/cleanup/stats")
async def get_cleanup_stats():
    """取得各目錄的檔案統計"""

    def get_dir_stats(directory: Path) -> dict:
        if not directory.exists():
            return {"files": 0, "size": 0, "size_formatted": "0 B"}

        files = list(directory.glob("*"))
        file_count = sum(1 for f in files if f.is_file())
        total_size = sum(f.stat().st_size for f in files if f.is_file())

        # 格式化大小
        if total_size < 1024:
            size_str = f"{total_size} B"
        elif total_size < 1024 * 1024:
            size_str = f"{total_size / 1024:.1f} KB"
        else:
            size_str = f"{total_size / (1024 * 1024):.1f} MB"

        return {
            "files": file_count,
            "size": total_size,
            "size_formatted": size_str,
        }

    # 取得任務數量
    task_service = get_task_service()
    tasks = task_service.list_tasks()

    return {
        "uploads": get_dir_stats(UPLOAD_DIR),
        "results": get_dir_stats(RESULTS_DIR),
        "reports": get_dir_stats(REPORTS_DIR),
        "tasks": {
            "count": len(tasks),
            "processing": sum(1 for t in tasks if t.get("status") == "processing"),
            "completed": sum(1 for t in tasks if t.get("status") == "completed"),
            "failed": sum(1 for t in tasks if t.get("status") == "failed"),
        },
    }
