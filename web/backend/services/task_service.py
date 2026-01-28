"""
Task Service
任務管理服務
"""

from datetime import datetime
from typing import Any

from loguru import logger


class TaskService:
    """任務管理服務 - 管理 PHI 處理任務的生命週期"""

    def __init__(self):
        self._tasks_db: dict[str, dict[str, Any]] = {}

        # 處理速度統計
        self._processing_stats = {
            "total_chars_processed": 0,
            "total_time_seconds": 0.0,
            "task_count": 0,
            "avg_chars_per_second": 50.0,
        }

    @property
    def tasks_db(self) -> dict[str, dict[str, Any]]:
        """取得任務資料庫"""
        return self._tasks_db

    def create_task(
        self, task_id: str, file_ids: list[str], config: dict[str, Any], job_name: str | None = None
    ) -> dict[str, Any]:
        """建立新任務"""
        now = datetime.now()
        
        # 初始化每個檔案的狀態
        file_results = {
            file_id: {
                "file_id": file_id,
                "status": "pending",
                "phi_found": 0,
                "error": None,
                "processing_time": None,
            }
            for file_id in file_ids
        }
        
        task = {
            "task_id": task_id,
            "status": "pending",
            "progress": 0.0,
            "message": "等待處理...",
            "file_ids": file_ids,
            "config": config,
            "job_name": job_name or f"job-{task_id}",
            "created_at": now,
            "updated_at": now,
            "result": None,
            "error": None,
            "current_file": None,
            "files_completed": 0,
            "total_files": len(file_ids),
            "elapsed_time": None,
            "estimated_remaining": None,
            "file_results": file_results,  # 新增：單檔狀態追蹤
        }
        self._tasks_db[task_id] = task
        logger.info(f"📋 Created task: {task_id} with {len(file_ids)} files")
        return task

    def get_task(self, task_id: str) -> dict[str, Any] | None:
        """取得任務資訊"""
        return self._tasks_db.get(task_id)

    def update_task(self, task_id: str, **updates) -> dict[str, Any] | None:
        """更新任務狀態"""
        task = self._tasks_db.get(task_id)
        if task:
            task.update(updates)
            task["updated_at"] = datetime.now()
            return task
        return None

    def update_file_result(
        self,
        task_id: str,
        file_id: str,
        status: str,
        phi_found: int = 0,
        error: str | None = None,
        processing_time: float | None = None,
    ) -> dict[str, Any] | None:
        """更新單一檔案的處理結果"""
        task = self._tasks_db.get(task_id)
        if not task:
            return None

        file_results = task.get("file_results", {})
        file_results[file_id] = {
            "file_id": file_id,
            "status": status,
            "phi_found": phi_found,
            "error": error,
            "processing_time": processing_time,
        }
        task["file_results"] = file_results
        task["updated_at"] = datetime.now()

        logger.debug(f"Updated file result: {task_id}/{file_id} -> {status}")
        return file_results[file_id]

    def get_file_result(self, task_id: str, file_id: str) -> dict[str, Any] | None:
        """取得單一檔案的處理結果"""
        task = self._tasks_db.get(task_id)
        if not task:
            return None
        return task.get("file_results", {}).get(file_id)

    def list_tasks(self) -> list[dict[str, Any]]:
        """列出所有任務 (按建立時間倒序)"""
        return sorted(self._tasks_db.values(), key=lambda x: x["created_at"], reverse=True)

    def get_file_task_map(self) -> dict[str, dict[str, Any]]:
        """取得檔案 ID -> 任務+檔案狀態的映射
        
        返回每個檔案最新任務中的單檔狀態
        """
        file_task_map: dict[str, dict[str, Any]] = {}
        for task in self._tasks_db.values():
            for file_id in task.get("file_ids", []):
                # 取最新的任務
                if (
                    file_id not in file_task_map
                    or task["created_at"] > file_task_map[file_id]["task"]["created_at"]
                ):
                    # 取得該檔案的單獨結果
                    file_result = task.get("file_results", {}).get(file_id, {})
                    file_task_map[file_id] = {
                        "task": task,
                        "task_id": task["task_id"],
                        "file_status": file_result.get("status", "pending"),
                        "phi_found": file_result.get("phi_found", 0),
                        "error": file_result.get("error"),
                        "processing_time": file_result.get("processing_time"),
                    }
        return file_task_map

    def estimate_remaining_time(
        self, total_chars: int, processed_chars: int, elapsed: float
    ) -> float | None:
        """估計剩餘處理時間"""
        if processed_chars <= 0 or elapsed <= 0:
            return None

        chars_per_second = processed_chars / elapsed
        remaining_chars = total_chars - processed_chars
        return remaining_chars / chars_per_second

    def update_processing_stats(self, chars_processed: int, time_seconds: float):
        """更新處理統計資料"""
        if chars_processed > 0 and time_seconds > 0:
            self._processing_stats["total_chars_processed"] += chars_processed
            self._processing_stats["total_time_seconds"] += time_seconds
            self._processing_stats["task_count"] += 1
            self._processing_stats["avg_chars_per_second"] = (
                self._processing_stats["total_chars_processed"]
                / self._processing_stats["total_time_seconds"]
            )

    def get_processing_stats(self) -> dict[str, Any]:
        """取得處理統計資料"""
        return {
            **self._processing_stats,
            "active_tasks": sum(1 for t in self._tasks_db.values() if t["status"] == "processing"),
            "total_tasks": len(self._tasks_db),
        }

    def clear_all_tasks(self) -> int:
        """清空所有任務記錄
        
        Returns:
            刪除的任務數量
        """
        count = len(self._tasks_db)
        self._tasks_db.clear()
        
        # 重置統計
        self._processing_stats = {
            "total_chars_processed": 0,
            "total_time_seconds": 0.0,
            "task_count": 0,
            "avg_chars_per_second": 50.0,
        }
        
        logger.warning(f"🗑️ Cleared {count} tasks")
        return count


# 單例模式
_task_service: TaskService | None = None


def get_task_service() -> TaskService:
    """取得 TaskService 單例"""
    global _task_service
    if _task_service is None:
        _task_service = TaskService()
    return _task_service


__all__ = ["TaskService", "get_task_service"]
