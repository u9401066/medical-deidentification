"""
Logging Configuration
日誌配置模組

配置 loguru 進行結構化日誌記錄，支援：
- Console 輸出（開發時使用）
- JSON 格式檔案輸出（用於問題追蹤）
- 分層日誌級別
"""

import sys
import os
from pathlib import Path

from typing import Any

from loguru import logger

# 日誌目錄
LOG_DIR = Path(os.getenv("MEDICAL_DEID_LOG_DIR", Path(__file__).parent / "logs")).expanduser()
LOG_DIR.mkdir(parents=True, exist_ok=True)


def configure_logging(
    log_level: str = "DEBUG",
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
    # 移除預設 handler
    logger.remove()

    # Console 輸出 (開發時使用)
    if console_output:
        logger.add(
            sys.stderr,
            level=log_level,
            format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
            colorize=True,
        )

    # JSON 格式檔案輸出 (用於問題追蹤)
    if json_output:
        logger.add(
            LOG_DIR / "processing_{time:YYYY-MM-DD}.log",
            level="DEBUG",
            format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} | {message}",
            rotation="10 MB",
            retention="7 days",
            compression="gz",
            serialize=False,  # 不使用 JSON 序列化以便人類閱讀
        )

        # 另外一個純 JSON 格式用於機器解析
        logger.add(
            LOG_DIR / "processing_{time:YYYY-MM-DD}.jsonl",
            level="DEBUG",
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
