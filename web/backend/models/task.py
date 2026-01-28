"""
Task Models
任務相關資料模型
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from .config import PHIConfig


class ProcessRequest(BaseModel):
    """處理請求"""

    file_ids: list[str] = Field(..., description="要處理的檔案 ID 列表")
    config: PHIConfig = Field(default_factory=PHIConfig)
    job_name: str | None = Field(default=None, description="任務名稱")


class FileResult(BaseModel):
    """單一檔案處理結果"""

    file_id: str
    filename: str | None = None  # 檔案名稱
    status: str  # pending, processing, completed, error
    phi_found: int = 0
    error: str | None = None
    processing_time: float | None = None  # 秒


class TaskStatus(BaseModel):
    """任務狀態"""

    task_id: str
    status: str  # pending, processing, completed, failed
    progress: float = 0.0
    message: str = ""
    file_ids: list[str] = []
    created_at: datetime
    updated_at: datetime
    result: dict[str, Any] | None = None
    error: str | None = None

    # 單檔處理狀態
    file_results: dict[str, FileResult] = Field(default_factory=dict)

    # 進度相關
    current_file: str | None = None
    files_completed: int = 0
    total_files: int = 0

    # 時間估計
    elapsed_time: float | None = None
    estimated_remaining: float | None = None
    elapsed_time_formatted: str | None = None
    estimated_remaining_formatted: str | None = None


__all__ = ["FileResult", "ProcessRequest", "TaskStatus"]
