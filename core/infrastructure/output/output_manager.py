"""
Output Manager Module | 輸出管理模組 (Infrastructure Layer)
=========================================================

Manages output paths, folder structure, and file naming for processing results.
管理處理結果的輸出路徑、資料夾結構和檔案命名。

DDD Layer: Infrastructure
DDD 層級：基礎設施層

This module centralizes all output-related configuration and operations:
- Output folder structure (data/output/results/, data/output/reports/)
- Timestamped filename generation
- Automatic folder creation
- Path resolution

此模組集中所有輸出相關的配置和操作：
- 輸出資料夾結構 (data/output/results/, data/output/reports/)
- 時間戳檔名生成
- 自動建立資料夾
- 路徑解析
"""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from loguru import logger


@dataclass
class OutputConfig:
    """
    Output configuration | 輸出配置
    
    Centralized configuration for all output paths and naming conventions.
    集中管理所有輸出路徑和命名規範。
    """

    # Base output directory | 基礎輸出目錄
    base_dir: Path = field(default_factory=lambda: Path("data/output"))

    # Subdirectories | 子目錄
    results_subdir: str = "results"
    reports_subdir: str = "reports"

    # Filename patterns | 檔名模式
    use_timestamp: bool = True
    timestamp_format: str = "%Y%m%d_%H%M%S"

    # Auto-create folders | 自動建立資料夾
    auto_create_folders: bool = True

    def __post_init__(self):
        """Initialize and validate configuration"""
        # Ensure Path objects
        self.base_dir = Path(self.base_dir)

        # Auto-create folders if enabled
        if self.auto_create_folders:
            self.ensure_folders_exist()

    @property
    def results_dir(self) -> Path:
        """Get results directory path | 取得結果目錄路徑"""
        return self.base_dir / self.results_subdir

    @property
    def reports_dir(self) -> Path:
        """Get reports directory path | 取得報告目錄路徑"""
        return self.base_dir / self.reports_subdir

    def ensure_folders_exist(self) -> None:
        """
        Ensure all output folders exist | 確保所有輸出資料夾存在
        
        Creates base_dir, results_dir, and reports_dir if they don't exist.
        若不存在則建立 base_dir、results_dir 和 reports_dir。
        """
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.results_dir.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Output folders ensured: {self.base_dir}")

    def get_timestamp(self) -> str:
        """
        Get formatted timestamp | 取得格式化的時間戳
        
        Returns:
            Timestamp string in configured format (e.g., "20251123_143022")
        """
        return datetime.now().strftime(self.timestamp_format)


class OutputManager:
    """
    Output Manager | 輸出管理器 (Infrastructure)
    
    Manages output paths and filenames for processing results.
    管理處理結果的輸出路徑和檔名。
    
    Features:
    - Centralized output path management
    - Automatic timestamp generation
    - Folder creation
    - Path resolution
    
    功能：
    - 集中化輸出路徑管理
    - 自動時間戳生成
    - 資料夾建立
    - 路徑解析
    
    Example:
        >>> manager = OutputManager()
        >>> result_path = manager.get_result_path("batch_result", "xlsx")
        >>> # Returns: data/output/results/batch_result_20251123_143022.xlsx
    """

    def __init__(self, config: OutputConfig | None = None):
        """
        Initialize OutputManager | 初始化輸出管理器
        
        Args:
            config: Output configuration (uses default if None)
        """
        self.config = config or OutputConfig()
        logger.info(f"OutputManager initialized: base_dir={self.config.base_dir}")

    def get_result_path(
        self,
        filename_prefix: str,
        extension: str,
        use_timestamp: bool | None = None
    ) -> Path:
        """
        Get path for result file | 取得結果檔案路徑
        
        Args:
            filename_prefix: File name prefix (e.g., "batch_result", "deidentified")
            extension: File extension without dot (e.g., "xlsx", "csv")
            use_timestamp: Override config's use_timestamp setting
        
        Returns:
            Full path to result file
            
        Example:
            >>> manager.get_result_path("batch_result", "xlsx")
            Path("data/output/results/batch_result_20251123_143022.xlsx")
        """
        use_ts = use_timestamp if use_timestamp is not None else self.config.use_timestamp

        if use_ts:
            timestamp = self.config.get_timestamp()
            filename = f"{filename_prefix}_{timestamp}.{extension}"
        else:
            filename = f"{filename_prefix}.{extension}"

        return self.config.results_dir / filename

    def get_report_path(
        self,
        filename_prefix: str,
        extension: str = "json",
        use_timestamp: bool | None = None
    ) -> Path:
        """
        Get path for report file | 取得報告檔案路徑
        
        Args:
            filename_prefix: File name prefix (e.g., "report", "statistics")
            extension: File extension without dot (default: "json")
            use_timestamp: Override config's use_timestamp setting
        
        Returns:
            Full path to report file
            
        Example:
            >>> manager.get_report_path("report_batch")
            Path("data/output/reports/report_batch_20251123_143022.json")
        """
        use_ts = use_timestamp if use_timestamp is not None else self.config.use_timestamp

        if use_ts:
            timestamp = self.config.get_timestamp()
            filename = f"{filename_prefix}_{timestamp}.{extension}"
        else:
            filename = f"{filename_prefix}.{extension}"

        return self.config.reports_dir / filename

    def get_custom_path(
        self,
        subdirectory: str,
        filename: str,
        use_timestamp: bool | None = None
    ) -> Path:
        """
        Get custom path under base directory | 取得基礎目錄下的自訂路徑
        
        Args:
            subdirectory: Subdirectory name (relative to base_dir)
            filename: Filename with extension
            use_timestamp: Whether to add timestamp to filename
        
        Returns:
            Full path to custom file
        """
        use_ts = use_timestamp if use_timestamp is not None else self.config.use_timestamp

        custom_dir = self.config.base_dir / subdirectory
        custom_dir.mkdir(parents=True, exist_ok=True)

        if use_ts:
            # Insert timestamp before extension
            stem = Path(filename).stem
            suffix = Path(filename).suffix
            timestamp = self.config.get_timestamp()
            filename = f"{stem}_{timestamp}{suffix}"

        return custom_dir / filename

    def resolve_path(self, path: str | Path) -> Path:
        """
        Resolve path (convert string to Path, handle relative paths)
        解析路徑（將字串轉為 Path，處理相對路徑）
        
        Args:
            path: Path as string or Path object
        
        Returns:
            Resolved Path object
        """
        path = Path(path)

        # If relative path without parent, assume it's under results/
        if not path.is_absolute() and path.parent == Path():
            return self.config.results_dir / path

        return path

    def ensure_parent_exists(self, path: str | Path) -> Path:
        """
        Ensure parent directory of path exists | 確保路徑的父目錄存在
        
        Args:
            path: File path
        
        Returns:
            Path object with guaranteed existing parent directory
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def results_dir(self) -> Path:
        """Get results directory | 取得結果目錄"""
        return self.config.results_dir

    @property
    def reports_dir(self) -> Path:
        """Get reports directory | 取得報告目錄"""
        return self.config.reports_dir

    @property
    def base_dir(self) -> Path:
        """Get base directory | 取得基礎目錄"""
        return self.config.base_dir


# Global default instance | 全域預設實例
_default_manager: OutputManager | None = None


def get_default_output_manager() -> OutputManager:
    """
    Get or create default OutputManager instance | 取得或建立預設的 OutputManager 實例
    
    Returns:
        Default OutputManager with standard configuration
    """
    global _default_manager
    if _default_manager is None:
        _default_manager = OutputManager()
    return _default_manager


def set_default_output_manager(manager: OutputManager) -> None:
    """
    Set default OutputManager instance | 設定預設的 OutputManager 實例
    
    Args:
        manager: OutputManager instance to use as default
    """
    global _default_manager
    _default_manager = manager


# Convenience functions | 便利函數
def get_result_path(filename_prefix: str, extension: str) -> Path:
    """Convenience function to get result path using default manager"""
    return get_default_output_manager().get_result_path(filename_prefix, extension)


def get_report_path(filename_prefix: str, extension: str = "json") -> Path:
    """Convenience function to get report path using default manager"""
    return get_default_output_manager().get_report_path(filename_prefix, extension)
