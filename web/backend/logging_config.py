"""
Logging Configuration
日誌配置模組

配置 loguru 進行結構化日誌記錄，支援：
- Console 輸出（開發時使用）
- JSON 格式檔案輸出（用於問題追蹤）
- 分層日誌級別
"""

import os
import sys

from typing import Any

from loguru import logger

from config import LOG_DIR

LOG_DIR.mkdir(parents=True, exist_ok=True)


SENSITIVE_KEYS = {
    "text",
    "value",
    "filename",
    "file_name",
    "filepath",
    "file_path",
    "job_name",
    "original",
    "original_content",
    "original_preview",
    "masked_preview",
    "content",
    "api_key",
    "authorization",
}
SENSITIVE_MESSAGE_MARKERS = {
    "original",
    "original_content",
    "original preview",
    "masked_preview",
    "llm output",
    "model output",
    "raw text",
    "content preview",
}


def _redact(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: "[REDACTED]" if key.lower() in SENSITIVE_KEYS else _redact(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_redact(item) for item in value]
    return value


def _redaction_filter(record: dict[str, Any]) -> bool:
    record["extra"] = _redact(record.get("extra", {}))
    message = str(record.get("message", ""))
    lowered = message.lower()
    if any(marker in lowered for marker in SENSITIVE_MESSAGE_MARKERS):
        record["message"] = "[REDACTED potentially sensitive log message]"
    return True


def configure_logging(
    log_level: str | None = None,
    json_output: bool = True,
    console_output: bool = True,
) -> None:
    """
    配置 loguru 日誌系統

    Args:
        log_level: 日誌級別 (DEBUG, INFO, WARNING, ERROR)
        json_output: 是否輸出 JSON 格式到檔案
        console_output: 是否輸出到 console
    """
    log_level = log_level or os.getenv("MEDICAL_DEID_LOG_LEVEL", "INFO")

    # 移除預設 handler
    logger.remove()

    # Console 輸出 (開發時使用)
    if console_output:
        logger.add(
            sys.stderr,
            level=log_level,
            filter=_redaction_filter,
            format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
            colorize=True,
        )

    # JSON 格式檔案輸出 (用於問題追蹤)
    if json_output:
        logger.add(
            LOG_DIR / "processing_{time:YYYY-MM-DD}.log",
            level=log_level,
            filter=_redaction_filter,
            format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} | {message}",
            rotation="10 MB",
            retention="7 days",
            compression="gz",
            serialize=False,  # 不使用 JSON 序列化以便人類閱讀
        )

        # 另外一個純 JSON 格式用於機器解析
        logger.add(
            LOG_DIR / "processing_{time:YYYY-MM-DD}.jsonl",
            level=log_level,
            filter=_redaction_filter,
            serialize=True,  # JSON 序列化
            rotation="10 MB",
            retention="7 days",
            compression="gz",
        )

    logger.info("📋 Logging configured", log_level=log_level)


def get_processing_logger(name: str = "processing") -> Any:
    """
    取得處理專用的 logger

    用法:
        from logging_config import get_processing_logger
        log = get_processing_logger("phi_identification")
        log.info("Processing started", task_id="abc123", file_count=5)
    """
    return logger.bind(component=name)


__all__ = ["LOG_DIR", "configure_logging", "get_processing_logger"]
