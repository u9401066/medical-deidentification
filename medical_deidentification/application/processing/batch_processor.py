"""
Batch PHI Identification Processor
批次 PHI 識別處理器

Processes multiple documents/rows from Excel files for PHI identification.
處理來自 Excel 文件的多個文檔/行以進行 PHI 識別。
"""

import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime

import pandas as pd
from loguru import logger

from ...domain.models import PHIEntity
from ...infrastructure.rag.phi_identification_chain import PHIIdentificationChain


@dataclass
class BatchProcessingConfig:
    """批次處理配置"""
    max_rows: Optional[int] = None  # 限制處理行數（None=全部）
    language: str = "zh-TW"  # 預設語言
    skip_empty_rows: bool = True  # 跳過空行
    combine_columns: bool = True  # 合併所有欄位為單一文本
    log_progress_interval: int = 10  # 每N行記錄一次進度


@dataclass
class RowProcessingResult:
    """單行處理結果"""
    row_number: int
    case_id: str
    text_length: int
    entities: List[PHIEntity] = field(default_factory=list)
    processing_time: float = 0.0
    success: bool = True
    error_message: Optional[str] = None


@dataclass
class BatchProcessingResult:
    """批次處理結果"""
    file_name: str
    total_rows: int
    processed_rows: int
    total_entities: int
    total_time: float
    average_time_per_row: float
    row_results: List[RowProcessingResult] = field(default_factory=list)
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    
    def mark_completed(self) -> None:
        """標記為完成"""
        self.completed_at = datetime.now()
    
    def get_phi_type_distribution(self) -> Dict[str, int]:
        """獲取PHI類型分布"""
        distribution: Dict[str, int] = {}
        for row_result in self.row_results:
            for entity in row_result.entities:
                phi_type = entity.type.value
                distribution[phi_type] = distribution.get(phi_type, 0) + 1
        return distribution
    
    def get_confidence_statistics(self) -> Dict[str, float]:
        """獲取信心度統計"""
        all_confidences = [
            entity.confidence
            for row_result in self.row_results
            for entity in row_result.entities
        ]
        
        if not all_confidences:
            return {"mean": 0.0, "min": 0.0, "max": 0.0}
        
        return {
            "mean": sum(all_confidences) / len(all_confidences),
            "min": min(all_confidences),
            "max": max(all_confidences)
        }
    
    def to_dataframe(self) -> pd.DataFrame:
        """轉換為DataFrame以便輸出"""
        records = []
        for row_result in self.row_results:
            for entity in row_result.entities:
                records.append({
                    "file": self.file_name,
                    "row": row_result.row_number,
                    "case_id": row_result.case_id,
                    "phi_type": entity.type.value,
                    "phi_text": entity.text,
                    "start_pos": entity.start_pos,
                    "end_pos": entity.end_pos,
                    "confidence": entity.confidence,
                    "reason": entity.reason,
                    "regulation_source": entity.regulation_source or ""
                })
        return pd.DataFrame(records)


class BatchPHIProcessor:
    """
    批次 PHI 識別處理器
    
    用於處理 Excel 文件中的多行數據，識別每行中的 PHI 實體。
    
    Examples:
        >>> processor = BatchPHIProcessor(phi_chain)
        >>> result = processor.process_excel_file("data.xlsx")
        >>> result.to_dataframe().to_excel("results.xlsx")
    """
    
    def __init__(
        self,
        phi_chain: PHIIdentificationChain,
        config: Optional[BatchProcessingConfig] = None
    ):
        """
        初始化批次處理器
        
        Args:
            phi_chain: PHI identification chain
            config: 批次處理配置
        """
        self.phi_chain = phi_chain
        self.config = config or BatchProcessingConfig()
    
    def process_excel_file(
        self,
        file_path: str,
        case_id_column: Optional[str] = None
    ) -> BatchProcessingResult:
        """
        處理 Excel 文件
        
        Args:
            file_path: Excel 文件路徑
            case_id_column: Case ID 欄位名稱（None=使用第一欄）
            
        Returns:
            批次處理結果
        """
        logger.info(f"{'='*80}")
        logger.info(f"Processing Excel file: {file_path}")
        logger.info(f"{'='*80}")
        
        # 載入數據
        df = self._load_excel(file_path)
        
        # 限制行數
        if self.config.max_rows:
            df = df.head(self.config.max_rows)
            logger.info(f"Limited to first {self.config.max_rows} rows")
        
        # 初始化結果
        result = BatchProcessingResult(
            file_name=Path(file_path).name,
            total_rows=len(df),
            processed_rows=0,
            total_entities=0,
            total_time=0.0,
            average_time_per_row=0.0
        )
        
        start_time = time.time()
        
        # 處理每一行
        for idx, row in df.iterrows():
            row_number = idx + 1 if isinstance(idx, int) else int(str(idx)) + 1
            
            # 獲取 Case ID
            if case_id_column and case_id_column in df.columns:
                case_id = str(row[case_id_column])
            else:
                case_id = str(row.iloc[0]) if len(row) > 0 else f"Row-{row_number}"
            
            # 處理行
            row_result = self._process_row(row, df, row_number, case_id)
            result.row_results.append(row_result)
            
            if row_result.success:
                result.processed_rows += 1
                result.total_entities += len(row_result.entities)
            
            # 記錄進度
            if row_number % self.config.log_progress_interval == 0:
                logger.info(
                    f"Progress: {row_number}/{len(df)} rows processed, "
                    f"{result.total_entities} PHI entities found"
                )
        
        # 完成統計
        result.total_time = time.time() - start_time
        result.average_time_per_row = (
            result.total_time / result.processed_rows 
            if result.processed_rows > 0 else 0.0
        )
        result.mark_completed()
        
        self._log_summary(result)
        return result
    
    def process_multiple_files(
        self,
        file_paths: List[str],
        case_id_column: Optional[str] = None
    ) -> List[BatchProcessingResult]:
        """
        處理多個 Excel 文件
        
        Args:
            file_paths: Excel 文件路徑列表
            case_id_column: Case ID 欄位名稱
            
        Returns:
            批次處理結果列表
        """
        results = []
        
        for file_path in file_paths:
            if not Path(file_path).exists():
                logger.warning(f"File not found: {file_path}")
                continue
            
            result = self.process_excel_file(file_path, case_id_column)
            results.append(result)
        
        self._log_overall_summary(results)
        return results
    
    def _load_excel(self, file_path: str) -> pd.DataFrame:
        """載入 Excel 文件"""
        logger.info(f"Loading Excel file: {file_path}")
        df = pd.read_excel(file_path)
        logger.info(f"Loaded {len(df)} rows, {len(df.columns)} columns")
        return df
    
    def _process_row(
        self,
        row: pd.Series,
        df: pd.DataFrame,
        row_number: int,
        case_id: str
    ) -> RowProcessingResult:
        """處理單一行"""
        start_time = time.time()
        
        try:
            # 合併欄位文本
            if self.config.combine_columns:
                row_text = self._combine_row_text(row, df)
            else:
                row_text = " ".join(str(v) for v in row if pd.notna(v))
            
            # 跳過空行
            if self.config.skip_empty_rows and not row_text.strip():
                logger.debug(f"Row {row_number} is empty, skipping")
                return RowProcessingResult(
                    row_number=row_number,
                    case_id=case_id,
                    text_length=0,
                    processing_time=time.time() - start_time
                )
            
            # 識別 PHI
            result = self.phi_chain.identify_phi(
                text=row_text,
                language=self.config.language,
                return_entities=True
            )
            
            entities = result.get("entities", [])
            processing_time = time.time() - start_time
            
            if entities:
                logger.debug(
                    f"Row {row_number} ({case_id}): Found {len(entities)} PHI entities "
                    f"in {processing_time:.2f}s"
                )
            
            return RowProcessingResult(
                row_number=row_number,
                case_id=case_id,
                text_length=len(row_text),
                entities=entities,
                processing_time=processing_time,
                success=True
            )
        
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"Error processing row {row_number}: {e}")
            
            return RowProcessingResult(
                row_number=row_number,
                case_id=case_id,
                text_length=0,
                processing_time=processing_time,
                success=False,
                error_message=str(e)
            )
    
    def _combine_row_text(self, row: pd.Series, df: pd.DataFrame) -> str:
        """合併行的所有欄位為單一文本，保留欄位名稱"""
        parts = []
        for col in df.columns:
            value = row[col]
            if pd.notna(value) and str(value).strip():
                parts.append(f"[{col}] {str(value)}")
        return "\n\n".join(parts)
    
    def _log_summary(self, result: BatchProcessingResult) -> None:
        """記錄處理摘要"""
        logger.info(f"\n{'='*80}")
        logger.info("Batch Processing Complete")
        logger.info(f"{'='*80}")
        logger.info(f"File: {result.file_name}")
        logger.info(f"Total rows: {result.total_rows}")
        logger.info(f"Processed rows: {result.processed_rows}")
        logger.info(f"Total PHI entities: {result.total_entities}")
        logger.info(f"Total time: {result.total_time:.2f}s")
        logger.info(f"Average time per row: {result.average_time_per_row:.2f}s")
        
        # PHI 類型分布
        distribution = result.get_phi_type_distribution()
        if distribution:
            logger.info("\nPHI Type Distribution:")
            for phi_type, count in sorted(distribution.items(), key=lambda x: -x[1]):
                logger.info(f"  - {phi_type}: {count}")
        
        # 信心度統計
        confidence_stats = result.get_confidence_statistics()
        if confidence_stats["mean"] > 0:
            logger.info("\nConfidence Statistics:")
            logger.info(f"  - Mean: {confidence_stats['mean']:.2%}")
            logger.info(f"  - Min: {confidence_stats['min']:.2%}")
            logger.info(f"  - Max: {confidence_stats['max']:.2%}")
        
        logger.info(f"{'='*80}\n")
    
    def _log_overall_summary(self, results: List[BatchProcessingResult]) -> None:
        """記錄多文件處理總摘要"""
        total_rows = sum(r.total_rows for r in results)
        total_entities = sum(r.total_entities for r in results)
        total_time = sum(r.total_time for r in results)
        
        logger.info(f"\n{'='*80}")
        logger.info("Overall Summary")
        logger.info(f"{'='*80}")
        logger.info(f"Total files: {len(results)}")
        logger.info(f"Total rows: {total_rows}")
        logger.info(f"Total PHI entities: {total_entities}")
        logger.info(f"Total time: {total_time:.2f}s ({total_time/60:.1f} minutes)")
        logger.info(f"Average time per row: {total_time/total_rows:.2f}s")
        logger.info(f"{'='*80}\n")


def save_batch_results(
    results: List[BatchProcessingResult],
    output_file: str
) -> None:
    """
    儲存批次處理結果到 Excel
    
    Args:
        results: 批次處理結果列表
        output_file: 輸出文件路徑
    """
    # 合併所有結果
    all_dfs = [result.to_dataframe() for result in results]
    combined_df = pd.concat(all_dfs, ignore_index=True)
    
    # 儲存
    combined_df.to_excel(output_file, index=False)
    logger.success(f"Batch results saved to: {output_file}")
    
    # 顯示預覽
    logger.info("\nSample results (first 10 rows):")
    print(combined_df.head(10).to_string())
