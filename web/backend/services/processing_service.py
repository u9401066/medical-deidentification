"""
Processing Service
PHI 處理服務
"""

import json
import os
import re
import sys
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import Any

from loguru import logger

# 處理相對 import
_backend_dir = Path(__file__).parent.parent
if str(_backend_dir) not in sys.path:
    sys.path.insert(0, str(_backend_dir))

from config import OLLAMA_BASE_URL, OLLAMA_MODEL, REPORTS_DIR, RESULTS_DIR, STORE_RAW_PHI
from services.error_safety import safe_exception_message
from services.llm_config_service import get_llm_config_service

# 建立專用 logger
log = logger.bind(component="processing_service")


class ProcessingService:
    """PHI 處理服務 - 封裝去識別化引擎"""

    def __init__(self) -> None:
        self.results_dir = RESULTS_DIR
        self.reports_dir = REPORTS_DIR
        self._engine_available = False
        self._check_engine()

    def _check_engine(self) -> None:
        """檢查引擎是否可用"""
        if os.getenv("MEDICAL_DEID_FORCE_SIMULATION", "0").lower() in {"1", "true", "yes"}:
            logger.warning("PHI Engine disabled by MEDICAL_DEID_FORCE_SIMULATION")
            self._engine_available = False
            return

        try:
            # 確保可以 import 主專案模組
            project_root = Path(__file__).parent.parent.parent.parent
            if str(project_root) not in sys.path:
                sys.path.insert(0, str(project_root))

            import importlib
            importlib.import_module('core.application.processing.engine')

            self._engine_available = True
        except ImportError as e:
            logger.warning(f"PHI Engine not available: {e}")
            self._engine_available = False

    @property
    def engine_available(self) -> bool:
        return self._engine_available

    def process_file(
        self,
        file_path: Path,
        config: dict[str, Any],
        original_filename: str | None = None,
        artifact_dir: Path | None = None,
        progress_callback: Callable[[dict[str, Any]], None] | None = None,
    ) -> dict[str, Any]:
        """處理單一檔案

        Args:
            file_path: 檔案路徑
            config: 處理配置
            original_filename: 原始檔名 (用於報告顯示)
            artifact_dir: Optional directory for format-preserving output artifacts
            progress_callback: Optional core engine progress event callback
        """
        if not self._engine_available:
            return self._simulate_processing(file_path, original_filename)

        try:
            from core.application.processing.engine import (
                DeidentificationEngine,
                EngineConfig,
            )

            llm_config = get_llm_config_service().get_config()
            engine_config = EngineConfig(
                llm_provider="ollama",
                llm_model=llm_config.model or OLLAMA_MODEL,
                llm_base_url=llm_config.base_url or OLLAMA_BASE_URL,
                use_rag=False,
            )
            engine = DeidentificationEngine(engine_config)
            result = engine.process_file(file_path, progress_callback=progress_callback)

            masking_type = config.get("masking_type", "redact")
            return self._convert_engine_result(
                result,
                file_path,
                original_filename,
                masking_type,
                artifact_dir=artifact_dir,
            )

        except Exception as e:
            logger.error(safe_exception_message(e, context="Processing"))
            raise

    def _convert_engine_result(
        self,
        result: Any,
        file_path: Path,
        original_filename: str | None = None,
        masking_type: str = "redact",
        artifact_dir: Path | None = None,
    ) -> dict[str, Any]:
        """轉換引擎結果為標準格式

        Args:
            result: 引擎處理結果
            file_path: 檔案路徑 (含 file_id)
            original_filename: 原始檔名 (用於報告顯示)
            masking_type: 遮罩類型 (redact/hash/generalize)
            artifact_dir: Optional directory for format-preserving output artifacts
        """
        # 從 ProcessingResult 提取資料
        phi_entities = []
        original_content = ""
        masked_content = ""

        # ProcessingResult 使用 documents 屬性 (不是 document_results)
        documents = getattr(result, "documents", [])
        log.debug(
            "Engine result received",
            documents_count=len(documents),
            has_summary=hasattr(result, "summary"),
        )

        if documents:
            for doc_idx, doc in enumerate(documents):
                # doc 是 dict，包含 phi_entities, masked_content, original_content
                if isinstance(doc, dict):
                    raw_entities = doc.get("phi_entities", [])
                    log.info(
                        "Document PHI entities from engine",
                        doc_idx=doc_idx,
                        entities_count=len(raw_entities),
                        entity_types=[e.get("type") for e in raw_entities[:10]],
                    )

                    for entity in raw_entities:
                        original_text = entity.get("text", "")
                        # 計算 masked_value 基於遮罩類型
                        masked_value = self._compute_masked_value(
                            original_text,
                            entity.get("type", "UNKNOWN"),
                            masking_type,
                        )
                        phi_entities.append(
                            {
                                "type": entity.get("type", "UNKNOWN"),
                                "value": original_text,
                                "masked_value": masked_value,
                                "confidence": entity.get("confidence", 0.0),
                                "start_pos": entity.get("start_pos"),
                                "end_pos": entity.get("end_pos"),
                                "reason": entity.get("reason", "Identified as PHI"),
                            }
                        )
                    original_content = doc.get("original_content", "") or ""
                    masked_content = doc.get("masked_content", "") or ""

                    # 檢查 masked_content 和 original_content 的差異
                    log.debug(
                        "Content comparison",
                        original_len=len(original_content),
                        masked_len=len(masked_content),
                    )

        # 若 documents 為空，嘗試從 summary.phi_entities 取得
        if not phi_entities and hasattr(result, "summary"):
            summary = result.summary
            if isinstance(summary, dict):
                for entity in summary.get("phi_entities", []):
                    original_text = entity.get("text", "")
                    masked_value = self._compute_masked_value(
                        original_text,
                        entity.get("type", "UNKNOWN"),
                        masking_type,
                    )
                    phi_entities.append(
                        {
                            "type": entity.get("type", "UNKNOWN"),
                            "value": original_text,
                            "masked_value": masked_value,
                            "confidence": entity.get("confidence", 0.0),
                            "start_pos": entity.get("start_pos"),
                            "end_pos": entity.get("end_pos"),
                            "reason": entity.get("reason", ""),
                        }
                    )

        # 使用原始檔名 (若提供) 或檔案路徑名稱
        display_filename = original_filename or file_path.name
        file_id = file_path.stem.split("_")[0] if "_" in file_path.stem else file_path.stem[:8]

        # 記錄 hard rules 前的 entities
        entities_before_rules = len(phi_entities)
        log.debug(
            "Before hard rules",
            entities_count=entities_before_rules,
            entities_types=[e.get("type") for e in phi_entities],
        )

        # 套用 hard rules 後處理 (修正 LLM 常見錯誤)
        phi_entities, corrections = self._apply_hard_rules(phi_entities)
        if corrections:
            log.warning(
                "Hard rules applied",
                corrections=corrections,
                removed_count=entities_before_rules - len(phi_entities),
            )

            # 如果有 entities 被移除，需要重新生成 masked_content
            # 因為 Engine 返回的 masked_content 是用所有 entities 生成的
            if entities_before_rules != len(phi_entities) and original_content:
                log.info("Regenerating masked_content after hard rules filtering")
                masked_content = self._regenerate_masked_content(
                    original_content, phi_entities, masking_type
                )

        log.info(
            "Final engine result",
            file_id=file_id,
            phi_found=len(phi_entities),
            phi_types=[e.get("type") for e in phi_entities],
        )

        total_chars = len(original_content)
        stored_entities = self._entities_for_storage(phi_entities)
        masked_data, masked_sheets = self._build_masked_tabular_data(
            file_path,
            phi_entities,
            masking_type,
        )
        artifact = self._build_deidentified_artifact(
            file_path,
            display_filename,
            phi_entities,
            masking_type,
            artifact_dir,
        )
        payload = {
            "file_id": file_id,
            "filename": display_filename,
            "source_extension": file_path.suffix.lower(),
            "phi_found": len(phi_entities),
            "phi_entities": stored_entities,
            "total_chars": total_chars,
            "masked_data": masked_data,
            "masked_sheets": masked_sheets,
            "original_content": original_content[:5000] if (STORE_RAW_PHI and original_content) else "",
            "original_content_truncated": bool(
                STORE_RAW_PHI and original_content and len(original_content) > 5000
            ),
            "masked_content": masked_content if masked_content else "",
            "status": "completed",
        }
        if artifact:
            payload.update(
                {
                    "artifact_path": str(artifact.path.resolve()),
                    "artifact_filename": artifact.filename,
                    "artifact_media_type": artifact.media_type,
                    "artifact_format_preserved": artifact.format_preserved,
                    "artifact_engine": artifact.engine,
                    "artifact_warnings": artifact.warnings,
                }
            )
        return payload

    def _entities_for_storage(self, phi_entities: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Return PHI entities safe for persistence/API responses by default."""
        if STORE_RAW_PHI:
            return phi_entities

        safe_entities = []
        for entity in phi_entities:
            safe_entities.append(
                {
                    **entity,
                    "value": "[REDACTED]",
                    "reason": "",
                }
            )
        return safe_entities

    def _compute_masked_value(self, original_text: str, phi_type: str, masking_type: str) -> str:
        """計算遮罩後的值"""
        if not original_text:
            return "[REDACTED]"

        if masking_type in {"hash", "pseudonymize"}:
            import hashlib
            import hmac
            import os

            secret = (
                os.getenv("MEDICAL_DEID_PSEUDONYM_SECRET")
                or os.getenv("MEDICAL_DEID_API_TOKEN")
                or "medical-deid-local-default"
            )
            hash_val = hmac.new(
                secret.encode("utf-8"),
                original_text.encode("utf-8"),
                hashlib.sha256,
            ).hexdigest()[:12]
            return f"[{phi_type}_{hash_val}]"
        elif masking_type == "generalize":
            # 泛化: 保留類型標籤
            return f"[{phi_type}]"
        else:  # redact (預設)
            return "[REDACTED]"

    def _apply_hard_rules(
        self, phi_entities: list[dict[str, Any]]
    ) -> tuple[list[dict[str, Any]], list[str]]:
        """
        套用 hard rules 後處理，修正 LLM 常見錯誤

        Returns:
            (filtered_entities, corrections): 過濾後的實體列表和修正記錄
        """
        corrections: list[str] = []
        filtered: list[dict[str, Any]] = []

        for entity in phi_entities:
            phi_type = entity.get("type", "")
            value = entity.get("value", "")

            # Rule 1: AGE_OVER_* 類型必須 >= 89 才保留。
            # Generic AGE is a separate benchmark/configurable PHI type and is kept.
            if phi_type in ("AGE_OVER_89", "AGE_OVER_90"):
                age = self._extract_age_number(value)
                if age is not None and age < 89:
                    corrections.append(f"Removed {phi_type} candidate (age={age} < 89)")
                    continue  # 跳過這條記錄
                elif age is not None and age >= 89:
                    # 年齡正確，保留
                    filtered.append(entity)
                else:
                    # 無法解析數字，移除（保守策略：不確定就不要遮罩）
                    corrections.append(f"Removed {phi_type} candidate (unable to parse age)")
                    continue
            else:
                # 其他類型直接保留
                filtered.append(entity)

        return filtered, corrections

    def _extract_age_number(self, text: str) -> int | None:
        """
        從文字中提取年齡數值

        支援格式: "72歲", "92 歲", "85", "age 72", "年齡: 90"
        """
        if not text:
            return None

        # 移除常見單位和標籤
        clean_text = text.strip()

        # 嘗試直接匹配數字
        # Pattern 1: 純數字或數字+歲
        match = re.search(r"(\d+)\s*歲?", clean_text)
        if match:
            return int(match.group(1))

        # Pattern 2: age/年齡 + 數字
        match = re.search(r"(?:age|年齡|歲數)[\s:：]*(\d+)", clean_text, re.IGNORECASE)
        if match:
            return int(match.group(1))

        return None

    def _regenerate_masked_content(
        self,
        original_content: str,
        phi_entities: list[dict[str, Any]],
        masking_type: str,
    ) -> str:
        """
        根據過濾後的 phi_entities 重新生成 masked_content

        這用於在 _apply_hard_rules 移除了某些 entities 後，
        確保 masked_content 和 phi_entities 保持同步。

        Args:
            original_content: 原始文本內容
            phi_entities: 過濾後的 PHI 實體列表
            masking_type: 遮罩類型 (redact/hash/generalize)

        Returns:
            重新生成的 masked_content
        """
        if not phi_entities:
            return original_content

        # 按位置排序（從後往前替換以避免位置偏移問題）
        sorted_entities = sorted(phi_entities, key=lambda e: e.get("start_pos", 0), reverse=True)

        masked_text = original_content

        for entity in sorted_entities:
            start_pos = entity.get("start_pos")
            end_pos = entity.get("end_pos")
            value = entity.get("value", "")
            phi_type = entity.get("type", "UNKNOWN")

            if start_pos is None or end_pos is None:
                # 沒有位置信息，嘗試搜索替換
                masked_value = self._compute_masked_value(value, phi_type, masking_type)
                masked_text = masked_text.replace(value, masked_value, 1)
                log.debug(
                    "Replaced entity by search",
                    phi_type=phi_type,
                )
            else:
                # 使用位置替換
                masked_value = self._compute_masked_value(value, phi_type, masking_type)

                # 驗證位置是否匹配
                if start_pos < len(masked_text) and masked_text[start_pos:end_pos] == value:
                    masked_text = masked_text[:start_pos] + masked_value + masked_text[end_pos:]
                    log.debug(
                        "Replaced entity by position",
                        phi_type=phi_type,
                        pos=f"{start_pos}-{end_pos}",
                    )
                # 位置不匹配，嘗試搜索替換
                elif value in masked_text:
                    masked_text = masked_text.replace(value, masked_value, 1)
                    log.warning(
                        "Position mismatch, replaced by search",
                        expected_pos=f"{start_pos}-{end_pos}",
                    )
                else:
                    log.error(
                        "Could not replace entity",
                        phi_type=phi_type,
                    )

        return masked_text

    def _build_masked_tabular_data(
        self,
        file_path: Path,
        phi_entities: list[dict[str, Any]],
        masking_type: str,
    ) -> tuple[list[dict[str, Any]] | None, list[dict[str, Any]] | None]:
        """Build structured masked rows for CSV/Excel downloads.

        The core engine works on flattened document text. For user downloads we
        reconstruct a safe tabular view from the original spreadsheet and apply
        detected entity replacements cell-by-cell, preserving row/column shape.
        """
        suffix = file_path.suffix.lower()
        if suffix not in {".csv", ".xlsx", ".xls"}:
            return None, None

        replacements = self._replacement_pairs(phi_entities, masking_type)
        if not replacements:
            replacements = []

        try:
            import pandas as pd

            if suffix == ".csv":
                dataframe = pd.read_csv(file_path, dtype=str, keep_default_na=False)
                return self._mask_dataframe(dataframe, replacements), None

            excel = pd.ExcelFile(file_path)
            rows: list[dict[str, Any]] = []
            sheets: list[dict[str, Any]] = []
            include_sheet = len(excel.sheet_names) > 1
            for sheet_name in excel.sheet_names:
                dataframe = pd.read_excel(
                    excel,
                    sheet_name=sheet_name,
                    dtype=str,
                    keep_default_na=False,
                )
                sheet_rows = self._mask_dataframe(dataframe, replacements)
                sheets.append({"name": sheet_name, "rows": sheet_rows})
                if include_sheet:
                    sheet_rows = [{"__sheet": sheet_name, **row} for row in sheet_rows]
                rows.extend(sheet_rows)
            return rows, sheets
        except Exception as exc:
            log.warning(
                "Could not build structured masked data",
                file_id=file_path.stem[:8],
                error_type=type(exc).__name__,
            )
            return None, None

    def _build_deidentified_artifact(
        self,
        file_path: Path,
        original_filename: str,
        phi_entities: list[dict[str, Any]],
        masking_type: str,
        artifact_dir: Path | None,
    ) -> Any | None:
        """Generate a format-preserving artifact before raw upload purge."""
        if artifact_dir is None:
            return None

        try:
            from core.infrastructure.format_preservation import build_deidentified_artifact

            replacements = self._replacement_pairs(phi_entities, masking_type)
            return build_deidentified_artifact(
                file_path,
                original_filename,
                replacements,
                artifact_dir,
            )
        except Exception as exc:
            log.warning(
                "Could not build deidentified artifact",
                file_id=file_path.stem[:8],
                error_type=type(exc).__name__,
            )
            return None

    def _replacement_pairs(
        self,
        phi_entities: list[dict[str, Any]],
        masking_type: str,
    ) -> list[tuple[str, str]]:
        pairs: dict[str, str] = {}
        for entity in phi_entities:
            value = str(entity.get("value") or "")
            if not value or value == "[REDACTED]":
                continue
            pairs[value] = self._compute_masked_value(
                value,
                str(entity.get("type") or "UNKNOWN"),
                masking_type,
            )
        return sorted(pairs.items(), key=lambda item: len(item[0]), reverse=True)

    def _mask_dataframe(
        self,
        dataframe: Any,
        replacements: list[tuple[str, str]],
    ) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for row_index, row in dataframe.fillna("").astype(str).iterrows():
            output_row: dict[str, Any] = {"__row": int(row_index) + 1}
            for column, value in row.items():
                output_row[str(column)] = self._mask_cell(str(value), replacements)
            rows.append(output_row)
        return rows

    def _mask_cell(self, value: str, replacements: list[tuple[str, str]]) -> str:
        masked = value
        for original, replacement in replacements:
            if original in masked:
                masked = masked.replace(original, replacement)
        return masked

    def _simulate_processing(
        self, file_path: Path, original_filename: str | None = None
    ) -> dict[str, Any]:
        """模擬處理（當引擎不可用時）"""
        import time

        time.sleep(1)  # 模擬處理時間

        display_filename = original_filename or file_path.name

        return {
            "file_id": file_path.stem[:8],
            "filename": display_filename,
            "phi_found": 0,
            "phi_entities": [],
            "total_chars": 0,
            "masked_data": None,
            "masked_sheets": None,
            "original_content": "[Simulated - Engine not available]",
            "masked_content": "[Simulated - Engine not available]",
            "status": "completed",
            "warning": "PHI 引擎未載入，使用模擬處理",
        }

    def _owned_output_dir(self, base_dir: Path, owner_user_id: str | None) -> Path:
        """Store new artifacts in per-user directories while keeping legacy reads compatible."""
        if not owner_user_id:
            return base_dir
        output_dir = base_dir / "users" / owner_user_id
        output_dir.mkdir(parents=True, exist_ok=True)
        return output_dir

    def get_task_artifact_dir(self, task_id: str, owner_user_id: str | None = None) -> Path:
        """Return the per-task directory used for generated de-identified files."""
        artifact_dir = self._owned_output_dir(self.results_dir, owner_user_id) / "artifacts" / task_id
        artifact_dir.mkdir(parents=True, exist_ok=True)
        return artifact_dir

    def cleanup_expired_outputs(self, max_age_hours: float) -> dict[str, int]:
        """Delete generated result/report artifacts older than the configured TTL."""
        cutoff = datetime.now().timestamp() - (max_age_hours * 3600)
        files_deleted = 0
        bytes_freed = 0

        for base_dir in (self.results_dir, self.reports_dir):
            if not base_dir.exists():
                continue
            for artifact in base_dir.rglob("*"):
                if not artifact.is_file():
                    continue
                try:
                    if artifact.stat().st_mtime > cutoff:
                        continue
                    bytes_freed += artifact.stat().st_size
                    artifact.unlink()
                    files_deleted += 1
                except Exception as exc:
                    logger.warning(f"Failed to delete expired artifact {artifact}: {exc}")

            for directory in sorted(
                [path for path in base_dir.rglob("*") if path.is_dir()],
                key=lambda path: len(path.parts),
                reverse=True,
            ):
                try:
                    directory.rmdir()
                except OSError:
                    pass

        if files_deleted:
            logger.info(
                f"Cleaned expired outputs: {files_deleted} files, {bytes_freed} bytes freed"
            )
        return {"files_deleted": files_deleted, "bytes_freed": bytes_freed}

    def save_result(
        self,
        task_id: str,
        result: dict[str, Any],
        owner_user_id: str | None = None,
    ) -> Path:
        """儲存處理結果"""
        result_path = self._owned_output_dir(self.results_dir, owner_user_id) / f"{task_id}_result.json"
        with open(result_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False, default=str)
        return result_path

    def save_report(
        self,
        task_id: str,
        job_name: str,
        file_results: list[dict[str, Any]],
        processing_time: float,
        owner_user_id: str | None = None,
    ) -> Path:
        """生成並儲存報告"""
        total_phi = sum(r.get("phi_found", 0) for r in file_results)
        total_chars = sum(int(r.get("total_chars") or 0) for r in file_results)

        # 建立檔案名稱清單 (用於顯示)
        filenames = [r.get("filename", "") for r in file_results if r.get("filename")]
        files_display = ", ".join(filenames[:3])  # 最多顯示 3 個
        if len(filenames) > 3:
            files_display += f" ... 等 {len(filenames)} 個檔案"

        # 聚合 PHI 類型統計
        phi_by_type: dict[str, int] = {}
        for result in file_results:
            for entity in result.get("phi_entities", []):
                phi_type = entity.get("type", "UNKNOWN")
                phi_by_type[phi_type] = phi_by_type.get(phi_type, 0) + 1

        report = {
            "task_id": task_id,
            "job_name": job_name,
            "owner_user_id": owner_user_id,
            "files_display": files_display,  # 新增：檔案名稱顯示
            "generated_at": datetime.now().isoformat(),
            "summary": {
                "files_processed": len(file_results),
                "total_phi_found": total_phi,
                "total_chars": total_chars,
                "processing_time_seconds": processing_time,
                "processing_speed_chars_per_sec": total_chars / processing_time
                if processing_time > 0
                else 0,
                "filenames": filenames,  # 新增：完整檔案名稱列表
            },
            "file_details": [
                {
                    "file_id": r.get("file_id"),
                    "filename": r.get("filename"),
                    "phi_found": r.get("phi_found", 0),
                    "total_chars": r.get("total_chars", 0),
                    "phi_by_type": self._count_phi_types(r.get("phi_entities", [])),
                    "status": r.get("status", "completed"),
                    "phi_entities": r.get("phi_entities", []),
                }
                for r in file_results
            ],
        }

        report_path = self._owned_output_dir(self.reports_dir, owner_user_id) / f"{task_id}_report.json"
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)

        return report_path

    def _count_phi_types(self, entities: list[dict]) -> dict[str, int]:
        """統計 PHI 類型數量"""
        counts: dict[str, int] = {}
        for entity in entities:
            phi_type = entity.get("type", "UNKNOWN")
            counts[phi_type] = counts.get(phi_type, 0) + 1
        return counts


# 單例模式
_processing_service: ProcessingService | None = None


def get_processing_service() -> ProcessingService:
    """取得 ProcessingService 單例"""
    global _processing_service
    if _processing_service is None:
        _processing_service = ProcessingService()
    return _processing_service


__all__ = ["ProcessingService", "get_processing_service"]
