"""
File Service
檔案管理服務
"""

import json
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from loguru import logger

# 處理相對 import
_backend_dir = Path(__file__).parent.parent
if str(_backend_dir) not in sys.path:
    sys.path.insert(0, str(_backend_dir))

from config import MAX_FILE_SIZE, UPLOAD_DIR
from models.file import UploadedFile
from utils.safe_paths import is_safe_identifier, safe_join

from services.task_service import get_task_service


class FileService:
    """檔案管理服務 - 處理檔案上傳、列表、刪除"""

    def __init__(self, upload_dir: Path = UPLOAD_DIR):
        self.upload_dir = upload_dir
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def sanitize_path(file_id: str) -> bool:
        """驗證 file_id 格式，防止路徑穿越攻擊"""
        return is_safe_identifier(file_id)

    async def upload(self, filename: str, content: bytes) -> UploadedFile:
        """上傳檔案"""
        # 檢查檔案大小
        if len(content) > MAX_FILE_SIZE:
            raise ValueError(f"檔案過大，最大允許 {MAX_FILE_SIZE // (1024 * 1024)}MB")

        file_id = str(uuid.uuid4())[:8]
        file_ext = Path(filename).suffix.lower()
        save_path = self.upload_dir / f"{file_id}{file_ext}"

        # 儲存檔案
        with open(save_path, "wb") as f:
            f.write(content)

        # 儲存元數據
        metadata = {
            "file_id": file_id,
            "filename": filename,
            "size": len(content),
            "upload_time": datetime.now().isoformat(),
            "file_type": file_ext.lstrip("."),
            "path": str(save_path),
        }

        with open(self.upload_dir / f"{file_id}.meta.json", "w") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

        # 日誌脫敏 - 只記錄 file_id，不記錄可能含 PHI 的原始檔名
        logger.info(f"📁 Uploaded file: [REDACTED] -> {file_id} ({file_ext}, {len(content)} bytes)")

        return UploadedFile(
            file_id=file_id,
            filename=filename,
            size=len(content),
            upload_time=datetime.now(),
            file_type=file_ext.lstrip("."),
        )

    def list_files(self) -> list[UploadedFile]:
        """列出所有上傳的檔案（含處理狀態）"""
        files = []
        task_service = get_task_service()
        file_task_map = task_service.get_file_task_map()

        for meta_file in self.upload_dir.glob("*.meta.json"):
            with open(meta_file) as f:
                meta = json.load(f)
                file_id = meta["file_id"]

                # 使用單檔狀態（而非整體任務狀態）
                status = "pending"
                task_id = None
                if file_id in file_task_map:
                    file_info = file_task_map[file_id]
                    task_id = file_info["task_id"]
                    file_status = file_info.get("file_status", "pending")

                    # 映射狀態
                    status_map = {
                        "completed": "completed",
                        "processing": "processing",
                        "error": "error",
                        "pending": "pending",
                    }
                    status = status_map.get(file_status, "pending")

                files.append(
                    UploadedFile(
                        file_id=file_id,
                        filename=meta["filename"],
                        size=meta["size"],
                        upload_time=datetime.fromisoformat(meta["upload_time"]),
                        file_type=meta["file_type"],
                        status=status,
                        task_id=task_id,
                    )
                )

        return sorted(files, key=lambda x: x.upload_time, reverse=True)

    def get_file_path(self, file_id: str) -> Path | None:
        """取得檔案路徑"""
        if not self.sanitize_path(file_id):
            return None
        try:
            meta_file = safe_join(self.upload_dir, f"{file_id}.meta.json")
        except ValueError:
            return None
        if not meta_file.exists():
            return None

        with open(meta_file) as f:
            meta = json.load(f)

        try:
            return safe_join(self.upload_dir, Path(meta["path"]).name)
        except ValueError:
            logger.warning(f"⚠️ Invalid stored upload path blocked: {file_id}")
            return None

    def get_file_metadata(self, file_id: str) -> dict[str, Any] | None:
        """取得檔案元數據"""
        if not self.sanitize_path(file_id):
            return None
        try:
            meta_file = safe_join(self.upload_dir, f"{file_id}.meta.json")
        except ValueError:
            return None
        if not meta_file.exists():
            return None

        with open(meta_file) as f:
            return json.load(f)

    def delete(self, file_id: str) -> bool:
        """刪除檔案"""
        if not self.sanitize_path(file_id):
            raise ValueError("無效的檔案 ID")

        meta_file = self.upload_dir / f"{file_id}.meta.json"
        if not meta_file.exists():
            return False

        with open(meta_file) as f:
            meta = json.load(f)

        # 路徑穿越防護
        target_path = Path(meta["path"]).resolve()
        allowed_dir = self.upload_dir.resolve()
        if not str(target_path).startswith(str(allowed_dir)):
            logger.warning(f"⚠️ Path traversal attempt blocked: {file_id}")
            raise PermissionError("禁止的操作")

        # 刪除檔案和元數據
        target_path.unlink(missing_ok=True)
        meta_file.unlink()

        logger.info(f"🗑️ Deleted file: {file_id}")
        return True


# 單例模式
_file_service: FileService | None = None


def get_file_service() -> FileService:
    """取得 FileService 單例"""
    global _file_service
    if _file_service is None:
        _file_service = FileService()
    return _file_service


__all__ = ["FileService", "get_file_service"]
