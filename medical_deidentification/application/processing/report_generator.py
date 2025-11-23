"""
Report Generator Module | 報告生成模組
=====================================

Generates comprehensive reports for de-identification processing results.
為去識別化處理結果生成完整報告。

Features:
- JSON report generation
- Statistical summaries
- PHI distribution analysis
- Processing metrics
- Error reporting

功能：
- JSON 報告生成
- 統計摘要
- PHI 分布分析
- 處理指標
- 錯誤報告
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional, Union
from dataclasses import asdict

from loguru import logger

from .batch_processor import BatchProcessingResult, RowProcessingResult
from .output_manager import OutputManager, get_default_output_manager


class ReportGenerator:
    """
    Report Generator | 報告生成器
    
    Generates processing reports in various formats.
    以各種格式生成處理報告。
    
    Example:
        >>> generator = ReportGenerator()
        >>> report = generator.generate_batch_report(batch_result)
        >>> generator.save_report(report, "batch_report")
    """
    
    def __init__(self, output_manager: Optional[OutputManager] = None):
        """
        Initialize ReportGenerator | 初始化報告生成器
        
        Args:
            output_manager: OutputManager instance (uses default if None)
        """
        self.output_manager = output_manager or get_default_output_manager()
    
    def generate_batch_report(
        self,
        result: BatchProcessingResult,
        include_details: bool = True
    ) -> Dict[str, Any]:
        """
        Generate comprehensive report for batch processing result
        為批次處理結果生成完整報告
        
        Args:
            result: BatchProcessingResult instance
            include_details: Whether to include row-level details
        
        Returns:
            Report dictionary with all statistics and metadata
        """
        # Basic metadata
        report = {
            "report_type": "batch_processing",
            "generated_at": datetime.now().isoformat(),
            "file_name": result.file_name,
            
            # Processing summary
            "summary": {
                "total_rows": result.total_rows,
                "processed_rows": result.processed_rows,
                "failed_rows": result.total_rows - result.processed_rows,
                "success_rate": (result.processed_rows / result.total_rows * 100) 
                                if result.total_rows > 0 else 0,
                "total_phi_entities": result.total_entities,
            },
            
            # Timing statistics
            "timing": {
                "started_at": result.started_at.isoformat(),
                "completed_at": result.completed_at.isoformat() if result.completed_at else None,
                "total_time_seconds": result.total_time,
                "total_time_minutes": result.total_time / 60,
                "average_time_per_row": result.average_time_per_row,
            },
            
            # PHI statistics
            "phi_statistics": {
                "type_distribution": result.get_phi_type_distribution(),
                "confidence_statistics": result.get_confidence_statistics(),
                "average_entities_per_row": (result.total_entities / result.processed_rows)
                                           if result.processed_rows > 0 else 0,
            },
        }
        
        # Add row-level details if requested
        if include_details:
            report["row_details"] = [
                self._row_to_dict(row_result)
                for row_result in result.row_results
            ]
        
        return report
    
    def generate_engine_report(
        self,
        result: Any,  # ProcessingResult from engine
        include_stage_details: bool = True
    ) -> Dict[str, Any]:
        """
        Generate report for engine processing result
        為引擎處理結果生成報告
        
        Args:
            result: ProcessingResult from DeidentificationEngine
            include_stage_details: Whether to include stage-level details
        
        Returns:
            Report dictionary
        """
        report = {
            "report_type": "engine_processing",
            "generated_at": datetime.now().isoformat(),
            "job_id": result.job_id,
            
            # Processing summary
            "summary": {
                "status": result.status.value if hasattr(result.status, 'value') else str(result.status),
                "total_documents": result.total_documents,
                "processed_documents": result.processed_documents,
                "failed_documents": result.failed_documents,
                "success_rate": result.get_success_rate() if hasattr(result, 'get_success_rate') else 0,
                "total_phi_entities": result.total_phi_entities,
            },
            
            # Timing statistics
            "timing": {
                "started_at": result.started_at.isoformat() if result.started_at else None,
                "completed_at": result.completed_at.isoformat() if result.completed_at else None,
                "duration_seconds": result.duration_seconds,
                "duration_minutes": result.duration_seconds / 60 if result.duration_seconds else 0,
            },
            
            # Error summary
            "errors": {
                "has_errors": result.has_errors() if hasattr(result, 'has_errors') else False,
                "error_count": len(result.errors) if hasattr(result, 'errors') else 0,
                "errors": result.errors[:10] if hasattr(result, 'errors') else [],  # First 10 errors
            },
        }
        
        # Add stage details if requested
        if include_stage_details and hasattr(result, 'stage_results'):
            report["stage_results"] = result.stage_results
        
        return report
    
    def generate_summary_report(
        self,
        results: List[Union[BatchProcessingResult, Any]],
        report_title: str = "Processing Summary"
    ) -> Dict[str, Any]:
        """
        Generate summary report for multiple processing results
        為多個處理結果生成摘要報告
        
        Args:
            results: List of processing results
            report_title: Title for the report
        
        Returns:
            Summary report dictionary
        """
        total_rows = sum(r.total_rows for r in results if hasattr(r, 'total_rows'))
        processed_rows = sum(r.processed_rows for r in results if hasattr(r, 'processed_rows'))
        total_entities = sum(
            r.total_entities if hasattr(r, 'total_entities')
            else r.total_phi_entities if hasattr(r, 'total_phi_entities')
            else 0
            for r in results
        )
        
        report = {
            "report_type": "summary",
            "title": report_title,
            "generated_at": datetime.now().isoformat(),
            
            "summary": {
                "total_jobs": len(results),
                "total_rows": total_rows,
                "processed_rows": processed_rows,
                "success_rate": (processed_rows / total_rows * 100) if total_rows > 0 else 0,
                "total_phi_entities": total_entities,
            },
            
            "individual_results": [
                {
                    "job_id": getattr(r, 'job_id', getattr(r, 'file_name', f"job_{i}")),
                    "rows": getattr(r, 'total_rows', getattr(r, 'total_documents', 0)),
                    "phi_entities": getattr(r, 'total_entities', getattr(r, 'total_phi_entities', 0)),
                }
                for i, r in enumerate(results)
            ],
        }
        
        return report
    
    def save_report(
        self,
        report: Dict[str, Any],
        filename_prefix: str,
        format: str = "json"
    ) -> Path:
        """
        Save report to file | 儲存報告到檔案
        
        Args:
            report: Report dictionary
            filename_prefix: Filename prefix (e.g., "batch_report", "engine_report")
            format: Output format ("json" supported, future: "html", "pdf")
        
        Returns:
            Path to saved report file
        """
        if format == "json":
            report_path = self.output_manager.get_report_path(filename_prefix, "json")
            
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            logger.success(f"Report saved: {report_path}")
            return report_path
        
        else:
            raise ValueError(f"Unsupported report format: {format}")
    
    def save_batch_report(
        self,
        result: BatchProcessingResult,
        filename_prefix: Optional[str] = None,
        include_details: bool = True
    ) -> Path:
        """
        Generate and save batch processing report
        生成並儲存批次處理報告
        
        Args:
            result: BatchProcessingResult instance
            filename_prefix: Custom filename prefix (auto-generated if None)
            include_details: Whether to include row-level details
        
        Returns:
            Path to saved report file
        """
        # Generate report
        report = self.generate_batch_report(result, include_details=include_details)
        
        # Auto-generate filename if not provided
        if filename_prefix is None:
            file_stem = Path(result.file_name).stem
            filename_prefix = f"report_{file_stem}"
        
        # Save report
        return self.save_report(report, filename_prefix)
    
    def save_engine_report(
        self,
        result: Any,  # ProcessingResult
        filename_prefix: Optional[str] = None,
        include_stage_details: bool = True
    ) -> Path:
        """
        Generate and save engine processing report
        生成並儲存引擎處理報告
        
        Args:
            result: ProcessingResult from DeidentificationEngine
            filename_prefix: Custom filename prefix (auto-generated if None)
            include_stage_details: Whether to include stage-level details
        
        Returns:
            Path to saved report file
        """
        # Generate report
        report = self.generate_engine_report(result, include_stage_details=include_stage_details)
        
        # Auto-generate filename if not provided
        if filename_prefix is None:
            job_id = getattr(result, 'job_id', 'unknown')
            filename_prefix = f"report_engine_{job_id}"
        
        # Save report
        return self.save_report(report, filename_prefix)
    
    def _row_to_dict(self, row_result: RowProcessingResult) -> Dict[str, Any]:
        """Convert RowProcessingResult to dictionary"""
        return {
            "row_number": row_result.row_number,
            "case_id": row_result.case_id,
            "success": row_result.success,
            "entity_count": len(row_result.entities),
            "processing_time": row_result.processing_time,
            "text_length": row_result.text_length,
            "entities": [
                {
                    "type": e.phi_type.value if hasattr(e.phi_type, 'value') else str(e.phi_type),
                    "text": e.text,
                    "start": e.start_pos,
                    "end": e.end_pos,
                    "confidence": e.confidence,
                    "reason": e.reason,
                }
                for e in row_result.entities
            ] if row_result.success else [],
            "error": row_result.error_message if not row_result.success else None,
        }


# Convenience functions
def generate_batch_report(result: BatchProcessingResult) -> Dict[str, Any]:
    """Convenience function to generate batch report"""
    generator = ReportGenerator()
    return generator.generate_batch_report(result)


def save_batch_report(
    result: BatchProcessingResult,
    filename_prefix: Optional[str] = None
) -> Path:
    """Convenience function to save batch report"""
    generator = ReportGenerator()
    return generator.save_batch_report(result, filename_prefix)
