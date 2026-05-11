"""Results API Router."""

import json
import sys
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from loguru import logger

# 處理相對 import
_backend_dir = Path(__file__).parent.parent
if str(_backend_dir) not in sys.path:
    sys.path.insert(0, str(_backend_dir))

from config import REPORTS_DIR, RESULTS_DIR
from models.auth import AuthUser
from security import get_current_user
from services.result_sanitizer import sanitize_payload
from services.task_service import get_task_service

router = APIRouter()


def _find_artifact(base_dir: Path, filename: str) -> Path | None:
    """Find an artifact in legacy root storage or per-user storage."""
    legacy_path = base_dir / filename
    if legacy_path.exists():
        return legacy_path
    for artifact in base_dir.rglob(filename):
        if artifact.is_file():
            return artifact
    return None


@router.get("/results")
async def list_results(current_user: AuthUser = Depends(get_current_user)):
    """列出所有處理結果"""
    results = []
    task_service = get_task_service()

    for result_file in RESULTS_DIR.rglob("*_result.json"):
        try:
            with open(result_file, encoding="utf-8") as f:
                data = json.load(f)
            task = task_service.get_task(data.get("task_id", ""))
            if not task_service.can_access_task(
                task,
                user_id=current_user.user_id,
                is_admin=current_user.role == "admin",
            ):
                continue

            # 聚合 PHI 類型
            phi_by_type: dict[str, int] = {}
            file_results = data.get("results", [])
            filenames = []
            for file_result in file_results:
                filenames.append(file_result.get("filename", "unknown"))
                for entity in file_result.get("phi_entities", []):
                    phi_type = entity.get("type", "UNKNOWN")
                    phi_by_type[phi_type] = phi_by_type.get(phi_type, 0) + 1

            results.append(
                {
                    "task_id": data["task_id"],
                    "job_name": data.get("job_name", ""),
                    "files_count": len(file_results),
                    "filenames": filenames,  # 處理的檔案名稱列表
                    "owner_user_id": task.get("owner_user_id") if task else None,
                    "owner_username": task.get("owner_username") if task else None,
                    "total_phi_found": sum(r.get("phi_found", 0) for r in file_results),
                    "phi_by_type": phi_by_type,
                    "processed_at": data.get("processed_at", ""),
                }
            )
        except Exception as e:
            logger.warning(f"Error reading result file {result_file}: {e}")

    return sorted(results, key=lambda x: x["processed_at"], reverse=True)


@router.get("/results/{task_id}")
async def get_result(
    task_id: str,
    reveal_phi: bool = Query(False),
    current_user: AuthUser = Depends(get_current_user),
):
    """取得處理結果詳情"""
    task_service = get_task_service()
    task = task_service.get_task(task_id)
    if not task_service.can_access_task(
        task,
        user_id=current_user.user_id,
        is_admin=current_user.role == "admin",
    ):
        raise HTTPException(404, "結果不存在")

    result_file = _find_artifact(RESULTS_DIR, f"{task_id}_result.json")
    if result_file is None:
        raise HTTPException(404, "結果不存在")

    with open(result_file, encoding="utf-8") as f:
        return sanitize_payload(json.load(f), reveal_phi=reveal_phi)


@router.get("/reports")
async def list_reports(current_user: AuthUser = Depends(get_current_user)):
    """列出所有報告"""
    reports = []
    task_service = get_task_service()

    for report_file in REPORTS_DIR.rglob("*_report.json"):
        try:
            with open(report_file, encoding="utf-8") as f:
                report = json.load(f)

            task_id = report["task_id"]
            task = task_service.get_task(task_id)
            if not task_service.can_access_task(
                task,
                user_id=current_user.user_id,
                is_admin=current_user.role == "admin",
            ):
                continue

            # 更直觀的顯示名稱：檔案名稱 > job_name > task_id
            files_display = report.get("files_display", "")
            job_name = report.get("job_name", "")

            # 優先顯示檔案名稱，其次是 job_name
            if files_display:
                display_name = files_display
            elif job_name and not job_name.startswith("job-"):
                display_name = job_name
            else:
                # 從 file_details 取得檔名
                filenames = [f.get("filename", "") for f in report.get("file_details", [])]
                filenames = [f for f in filenames if f]  # 過濾空值
                if filenames:
                    display_name = ", ".join(filenames[:2])
                    if len(filenames) > 2:
                        display_name += f" 等 {len(filenames)} 個"
                else:
                    display_name = f"報告-{task_id[:8]}"

            reports.append(
                {
                    "id": task_id,  # 前端需要 id 欄位
                    "task_id": task_id,
                    "filename": display_name,  # 顯示更直觀的名稱
                    "job_name": job_name,
                    "owner_user_id": task.get("owner_user_id") if task else None,
                    "owner_username": task.get("owner_username") if task else None,
                    "files_processed": report["summary"]["files_processed"],
                    "total_phi_found": report["summary"]["total_phi_found"],
                    "created_at": report["generated_at"],  # 前端需要 created_at
                    "generated_at": report["generated_at"],
                }
            )
        except Exception as e:
            logger.warning(f"Error reading report file {report_file}: {e}")

    return sorted(reports, key=lambda x: x["generated_at"], reverse=True)


@router.get("/reports/{task_id}")
async def get_report(
    task_id: str,
    reveal_phi: bool = Query(False),
    current_user: AuthUser = Depends(get_current_user),
):
    """取得報告詳情"""
    task_service = get_task_service()
    task = task_service.get_task(task_id)
    if not task_service.can_access_task(
        task,
        user_id=current_user.user_id,
        is_admin=current_user.role == "admin",
    ):
        raise HTTPException(404, "報告不存在")

    report_file = _find_artifact(REPORTS_DIR, f"{task_id}_report.json")
    if report_file is None:
        raise HTTPException(404, "報告不存在")

    with open(report_file, encoding="utf-8") as f:
        return sanitize_payload(json.load(f), reveal_phi=reveal_phi)


@router.get("/reports/{task_id}/export")
async def export_report(
    task_id: str,
    format: str = "json",
    reveal_phi: bool = Query(False),
    current_user: AuthUser = Depends(get_current_user),
):
    """導出報告 (支援 json, csv, markdown 格式)"""
    from fastapi.responses import Response
    task_service = get_task_service()
    task = task_service.get_task(task_id)
    if not task_service.can_access_task(
        task,
        user_id=current_user.user_id,
        is_admin=current_user.role == "admin",
    ):
        raise HTTPException(404, "報告不存在")

    report_file = _find_artifact(REPORTS_DIR, f"{task_id}_report.json")
    if report_file is None:
        raise HTTPException(404, "報告不存在")

    with open(report_file, encoding="utf-8") as f:
        report = sanitize_payload(json.load(f), reveal_phi=reveal_phi)

    if format == "json":
        # 直接返回 JSON 供下載
        content = json.dumps(report, ensure_ascii=False, indent=2)
        return Response(
            content=content,
            media_type="application/json",
            headers={"Content-Disposition": f'attachment; filename="report_{task_id}.json"'},
        )
    elif format == "csv":
        # 導出為 CSV
        import csv
        import io

        output = io.StringIO()
        writer = csv.writer(output)

        # 寫入概要
        writer.writerow(["去識別化處理報告"])
        writer.writerow([])
        writer.writerow(["任務 ID", task_id])
        writer.writerow(["產生時間", report.get("generated_at", "")])
        writer.writerow(["處理檔案數", report.get("summary", {}).get("files_processed", 0)])
        writer.writerow(["發現 PHI 數量", report.get("summary", {}).get("total_phi_found", 0)])
        writer.writerow([])

        # 寫入檔案詳情
        writer.writerow(["檔案詳情"])
        writer.writerow(["檔案名稱", "PHI 數量", "狀態"])
        for file_detail in report.get("file_details", []):
            writer.writerow([
                file_detail.get("filename", ""),
                file_detail.get("phi_found", 0),
                file_detail.get("status", ""),
            ])

        content = output.getvalue()
        return Response(
            content=content,
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="report_{task_id}.csv"'},
        )
    elif format == "markdown" or format == "md":
        # 導出為 Markdown
        summary = report.get("summary", {})
        lines = [
            "# 去識別化處理報告",
            "",
            f"**任務 ID:** `{task_id}`",
            f"**產生時間:** {report.get('generated_at', '')}",
            "",
            "## 概要",
            "",
            "| 項目 | 數值 |",
            "|------|------|",
            f"| 處理檔案數 | {summary.get('files_processed', 0)} |",
            f"| 發現 PHI 數量 | {summary.get('total_phi_found', 0)} |",
            f"| 總字元數 | {summary.get('total_chars', 0):,} |",
            f"| 處理時間 | {summary.get('processing_time_seconds', 0):.2f} 秒 |",
            "",
            "## 檔案詳情",
            "",
        ]

        for file_detail in report.get("file_details", []):
            lines.append(f"### {file_detail.get('filename', '未知檔案')}")
            lines.append("")
            lines.append(f"- **狀態:** {file_detail.get('status', 'unknown')}")
            lines.append(f"- **發現 PHI:** {file_detail.get('phi_found', 0)}")

            phi_by_type = file_detail.get("phi_by_type", {})
            if phi_by_type:
                lines.append("- **PHI 類型分佈:**")
                for phi_type, count in phi_by_type.items():
                    lines.append(f"  - {phi_type}: {count}")

            lines.append("")

        content = "\n".join(lines)
        return Response(
            content=content,
            media_type="text/markdown",
            headers={"Content-Disposition": f'attachment; filename="report_{task_id}.md"'},
        )
