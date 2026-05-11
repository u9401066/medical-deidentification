"""
File Service
檔案管理服務
"""

import json
import re
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

from services.task_service import get_task_service


class FileService:
    """檔案管理服務 - 處理檔案上傳、列表、刪除"""

    def __init__(self, upload_dir: Path = UPLOAD_DIR):
        self.upload_dir = upload_dir
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def sanitize_path(file_id: str) -> bool:
        """驗證 file_id 格式，防止路徑穿越攻擊"""
        return bool(re.fullmatch(r"[a-zA-Z0-9-]{1,64}", file_id))

    @staticmethod
    def _can_access(meta: dict[str, Any], user_id: str, is_admin: bool) -> bool:
        owner_user_id = meta.get("owner_user_id")
        if is_admin:
            return True
        return bool(owner_user_id) and owner_user_id == user_id

    def _user_upload_dir(self, owner_user_id: str) -> Path:
        """Return the physical upload directory for a user."""
        user_dir = self.upload_dir / "users" / owner_user_id
        user_dir.mkdir(parents=True, exist_ok=True)
        return user_dir

    def _find_meta_file(self, file_id: str) -> Path | None:
        """Find metadata in either legacy root storage or user-scoped storage."""
        legacy_meta = self.upload_dir / f"{file_id}.meta.json"
        if legacy_meta.exists():
            return legacy_meta
        for meta_file in self.upload_dir.rglob(f"{file_id}.meta.json"):
            if meta_file.is_file():
                return meta_file
        return None

    def _load_metadata_file(self, meta_file: Path) -> dict[str, Any]:
        with open(meta_file, encoding="utf-8") as f:
            return json.load(f)

    def _write_metadata_file(self, meta_file: Path, metadata: dict[str, Any]) -> None:
        with open(meta_file, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

    def _validated_content_path(self, meta: dict[str, Any], file_id: str) -> Path:
        target_path = Path(meta["path"]).resolve()
        allowed_dir = self.upload_dir.resolve()
        if not target_path.is_relative_to(allowed_dir):
            logger.warning("Blocked file path outside upload directory", file_id=file_id)
            raise PermissionError("禁止的操作")
        return target_path

    def _prune_empty_dirs(self, start_dir: Path) -> None:
        users_root = (self.upload_dir / "users").resolve()
        current = start_dir.resolve()
        while current != self.upload_dir.resolve() and current != users_root.parent:
            if current == users_root:
                break
            try:
                current.rmdir()
            except OSError:
                break
            current = current.parent

    async def upload(
        self,
        filename: str,
        content: bytes,
        owner_user_id: str,
        owner_username: str | None = None,
    ) -> UploadedFile:
        """上傳檔案"""
        # 檢查檔案大小
        if len(content) > MAX_FILE_SIZE:
            raise ValueError(f"檔案過大，最大允許 {MAX_FILE_SIZE // (1024 * 1024)}MB")

        safe_filename = Path(filename).name
        file_id = str(uuid.uuid4())[:12]
        file_ext = Path(safe_filename).suffix.lower()
        user_dir = self._user_upload_dir(owner_user_id)
        save_path = user_dir / f"{file_id}{file_ext}"

        # 儲存檔案
        with open(save_path, "wb") as f:
            f.write(content)

        # 儲存元數據
        metadata = {
            "file_id": file_id,
            "filename": safe_filename,
            "size": len(content),
            "upload_time": datetime.now().isoformat(),
            "file_type": file_ext.lstrip("."),
            "path": str(save_path.resolve()),
            "owner_user_id": owner_user_id,
            "owner_username": owner_username,
            "content_deleted": False,
            "content_deleted_at": None,
        }

        self._write_metadata_file(user_dir / f"{file_id}.meta.json", metadata)

        # 日誌脫敏 - 只記錄 file_id，不記錄可能含 PHI 的原始檔名
        logger.info(f"📁 Uploaded file: [REDACTED] -> {file_id} ({file_ext}, {len(content)} bytes)")

        return UploadedFile(
            file_id=file_id,
            filename=safe_filename,
            size=len(content),
            upload_time=datetime.now(),
            file_type=file_ext.lstrip("."),
            owner_user_id=owner_user_id,
            owner_username=owner_username,
        )

    def list_files(self, user_id: str, is_admin: bool = False) -> list[UploadedFile]:
        """列出所有上傳的檔案（含處理狀態）"""
        files = []
        task_service = get_task_service()
        file_task_map = task_service.get_file_task_map(user_id=user_id, is_admin=is_admin)

        for meta_file in self.upload_dir.rglob("*.meta.json"):
            with open(meta_file, encoding="utf-8") as f:
                meta = json.load(f)
                file_id = meta["file_id"]
                if not self._can_access(meta, user_id=user_id, is_admin=is_admin):
                    continue

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

                raw_content_deleted = bool(meta.get("content_deleted"))
                raw_content_exists = Path(meta.get("path", "")).exists()
                files.append(
                    UploadedFile(
                        file_id=file_id,
                        filename=meta["filename"],
                        size=meta["size"],
                        upload_time=datetime.fromisoformat(meta["upload_time"]),
                        file_type=meta["file_type"],
                        preview_available=not raw_content_deleted and raw_content_exists,
                        content_deleted=raw_content_deleted or not raw_content_exists,
                        status=status,
                        task_id=task_id,
                        owner_user_id=meta.get("owner_user_id"),
                        owner_username=meta.get("owner_username"),
                    )
                )

        return sorted(files, key=lambda x: x.upload_time, reverse=True)

    def get_file_path(
        self,
        file_id: str,
        user_id: str | None = None,
        is_admin: bool = False,
    ) -> Path | None:
        """取得檔案路徑"""
        if not self.sanitize_path(file_id):
            raise ValueError("無效的檔案 ID")

        meta_file = self._find_meta_file(file_id)
        if meta_file is None:
            return None

        with open(meta_file, encoding="utf-8") as f:
            meta = json.load(f)
        if user_id is not None and not self._can_access(meta, user_id=user_id, is_admin=is_admin):
            raise PermissionError("禁止的操作")

        target_path = self._validated_content_path(meta, file_id)
        if bool(meta.get("content_deleted")) or not target_path.exists():
            return None

        return target_path

    def get_file_metadata(
        self,
        file_id: str,
        user_id: str | None = None,
        is_admin: bool = False,
    ) -> dict[str, Any] | None:
        """取得檔案元數據"""
        if not self.sanitize_path(file_id):
            raise ValueError("無效的檔案 ID")

        meta_file = self._find_meta_file(file_id)
        if meta_file is None:
            return None

        with open(meta_file, encoding="utf-8") as f:
            meta = json.load(f)
        if user_id is not None and not self._can_access(meta, user_id=user_id, is_admin=is_admin):
            raise PermissionError("禁止的操作")
        return meta

    def purge_file_content(
        self,
        file_id: str,
        user_id: str,
        is_admin: bool = False,
        keep_metadata: bool = True,
    ) -> bool:
        """Delete the raw upload while optionally preserving non-PHI metadata."""
        if not self.sanitize_path(file_id):
            raise ValueError("無效的檔案 ID")

        meta_file = self._find_meta_file(file_id)
        if meta_file is None:
            return False

        meta = self._load_metadata_file(meta_file)
        if not self._can_access(meta, user_id=user_id, is_admin=is_admin):
            raise PermissionError("禁止的操作")

        target_path = self._validated_content_path(meta, file_id)
        target_path.unlink(missing_ok=True)
        if keep_metadata:
            meta["content_deleted"] = True
            meta["content_deleted_at"] = datetime.now().isoformat()
            meta["preview_available"] = False
            self._write_metadata_file(meta_file, meta)
        else:
            meta_file.unlink(missing_ok=True)
        self._prune_empty_dirs(meta_file.parent)
        logger.info(f"🧹 Purged raw upload content: {file_id}")
        return True

    def cleanup_stale_uploads(self, max_age_hours: float) -> dict[str, int]:
        """Purge raw uploads older than the configured TTL, preserving metadata."""
        cutoff = datetime.now().timestamp() - (max_age_hours * 3600)
        files_purged = 0
        bytes_freed = 0

        for meta_file in self.upload_dir.rglob("*.meta.json"):
            try:
                meta = self._load_metadata_file(meta_file)
                if bool(meta.get("content_deleted")):
                    continue
                uploaded_at = datetime.fromisoformat(meta["upload_time"]).timestamp()
                if uploaded_at > cutoff:
                    continue
                target_path = self._validated_content_path(meta, meta.get("file_id", "unknown"))
                if target_path.exists():
                    bytes_freed += target_path.stat().st_size
                    target_path.unlink()
                meta["content_deleted"] = True
                meta["content_deleted_at"] = datetime.now().isoformat()
                meta["preview_available"] = False
                self._write_metadata_file(meta_file, meta)
                files_purged += 1
                self._prune_empty_dirs(meta_file.parent)
            except Exception as exc:
                logger.warning(f"Failed to purge stale upload {meta_file}: {exc}")

        if files_purged:
            logger.info(
                f"Cleaned stale uploads: {files_purged} files, {bytes_freed} bytes freed"
            )
        return {"files_purged": files_purged, "bytes_freed": bytes_freed}

    def delete(self, file_id: str, user_id: str, is_admin: bool = False) -> bool:
        """刪除檔案"""
        if not self.sanitize_path(file_id):
            raise ValueError("無效的檔案 ID")

        meta_file = self._find_meta_file(file_id)
        if meta_file is None:
            return False

        with open(meta_file, encoding="utf-8") as f:
            meta = json.load(f)
        if not self._can_access(meta, user_id=user_id, is_admin=is_admin):
            raise PermissionError("禁止的操作")

        # 路徑穿越防護
        target_path = self._validated_content_path(meta, file_id)

        # 刪除檔案和元數據
        target_path.unlink(missing_ok=True)
        meta_file.unlink()
        self._prune_empty_dirs(meta_file.parent)

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
