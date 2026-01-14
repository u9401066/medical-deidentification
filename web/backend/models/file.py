"""
File Models
檔案相關資料模型
"""
from datetime import datetime

from pydantic import BaseModel


class UploadedFile(BaseModel):
    """已上傳的檔案資訊"""
    file_id: str
    filename: str
    size: int
    upload_time: datetime
    file_type: str
    preview_available: bool = True
    status: str = "pending"  # pending, processing, completed, error
    task_id: str | None = None  # 關聯的處理任務 ID


__all__ = ["UploadedFile"]
