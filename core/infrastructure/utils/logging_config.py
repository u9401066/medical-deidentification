"""
Logging Configuration | 日誌配置

Centralized logging configuration for the entire package.
套件的集中式日誌配置。
"""

import sys
from datetime import datetime
from pathlib import Path

from loguru import logger

# Default log settings
DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_LOG_DIR = Path("logs")
DEFAULT_ROTATION = "10 MB"
DEFAULT_RETENTION = "10 days"
DEFAULT_COMPRESSION = "zip"


def configure_logging(
    log_dir: Path | None = None,
    console_level: str = "INFO",
    file_level: str = "DEBUG",
    rotation: str = DEFAULT_ROTATION,
    retention: str = DEFAULT_RETENTION,
    compression: str | None = DEFAULT_COMPRESSION,
    log_format: str | None = None,
    enable_console: bool = True,
    enable_file: bool = True,
) -> Path | None:
    """
    Configure logging for the application
    配置應用程式的日誌記錄
    
    Args:
        log_dir: Directory for log files (default: ./logs)
        console_level: Log level for console output (default: INFO)
        file_level: Log level for file output (default: DEBUG)
        rotation: When to rotate log files (default: "10 MB")
        retention: How long to keep log files (default: "10 days")
        compression: Compression format for rotated logs (default: "zip")
        log_format: Custom log format string
        enable_console: Enable console logging (default: True)
        enable_file: Enable file logging (default: True)
    
    Returns:
        Path to the log file (or None if file logging is disabled)
    
    Examples:
        >>> # Basic setup
        >>> from core.infrastructure.utils import configure_logging
        >>> log_file = configure_logging()
        >>> logger.info("Logging configured!")
        
        >>> # Custom configuration
        >>> log_file = configure_logging(
        ...     log_dir=Path("my_logs"),
        ...     console_level="WARNING",
        ...     file_level="DEBUG",
        ...     rotation="50 MB",
        ...     retention="30 days"
        ... )
        
        >>> # Disable console, only file
        >>> log_file = configure_logging(enable_console=False)
    """
    # Remove default handler
    logger.remove()

    # Default format
    if log_format is None:
        log_format = (
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>"
        )

    # Console handler
    if enable_console:
        logger.add(
            sys.stderr,
            level=console_level,
            format=log_format,
            colorize=True
        )

    # File handler
    log_file = None
    if enable_file:
        # Create log directory
        if log_dir is None:
            log_dir = DEFAULT_LOG_DIR
        log_dir.mkdir(parents=True, exist_ok=True)

        # Generate log filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = log_dir / f"core_{timestamp}.log"

        logger.add(
            str(log_file),
            level=file_level,
            format=log_format,
            rotation=rotation,
            retention=retention,
            compression=compression,
            encoding="utf-8"
        )

        logger.info(f"Log file configured: {log_file}")

    return log_file


def get_module_logger(module_name: str):
    """
    Get a logger for a specific module
    獲取特定模組的日誌記錄器
    
    This is mainly for future extension if we want module-specific logging.
    Currently, loguru uses a global logger, so this just returns logger.
    
    Args:
        module_name: Name of the module
    
    Returns:
        Logger instance
    
    Examples:
        >>> from core.infrastructure.utils import get_module_logger
        >>> logger = get_module_logger(__name__)
        >>> logger.info("Module initialized")
    """
    # For loguru, we use the global logger
    # Module name is automatically captured in the log format
    return logger


def disable_logging():
    """
    Disable all logging
    禁用所有日誌記錄
    
    Useful for testing or when logging is not needed.
    
    Examples:
        >>> from core.infrastructure.utils import disable_logging
        >>> disable_logging()
    """
    logger.remove()
    logger.disable("core")


def enable_logging():
    """
    Re-enable logging after it was disabled
    在禁用後重新啟用日誌記錄
    
    Examples:
        >>> from core.infrastructure.utils import enable_logging
        >>> enable_logging()
    """
    logger.enable("core")


def set_log_level(level: str = "INFO"):
    """
    Change log level at runtime
    在執行時更改日誌級別
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    
    Examples:
        >>> from core.infrastructure.utils import set_log_level
        >>> set_log_level("DEBUG")  # Show debug messages
        >>> set_log_level("WARNING")  # Only warnings and errors
    """
    logger.remove()
    logger.add(
        sys.stderr,
        level=level,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>"
        ),
        colorize=True
    )


# Initialize with default configuration on import
# Can be reconfigured by calling configure_logging()
_default_initialized = False

def _init_default_logging():
    """Initialize default logging if not already configured"""
    global _default_initialized
    if not _default_initialized:
        # Set up basic console logging
        logger.remove()
        logger.add(
            sys.stderr,
            level=DEFAULT_LOG_LEVEL,
            format=(
                "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
                "<level>{level: <8}</level> | "
                "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
                "<level>{message}</level>"
            ),
            colorize=True
        )
        _default_initialized = True


# Initialize on import
_init_default_logging()
