"""
Files API Router
檔案上傳/下載 API
"""

import json
import sys
from io import BytesIO
from pathlib import Path

import pandas as pd
from fastapi import APIRouter, File, HTTPException, Query, UploadFile
from fastapi.responses import Response
from starlette.responses import StreamingResponse

# 處理相對 import
_backend_dir = Path(__file__).parent.parent
if str(_backend_dir) not in sys.path:
    sys.path.insert(0, str(_backend_dir))

from config import REPORTS_DIR, RESULTS_DIR
from models.file import UploadedFile
from services.file_service import get_file_service
from utils.safe_paths import content_disposition_header, is_safe_identifier, safe_join

router = APIRouter()


def _load_download_json(directory: Path, task_id: str, suffix: str) -> dict:
    """Load a task-scoped JSON artifact after identifier and path validation."""
    if not is_safe_identifier(task_id):
        raise HTTPException(400, "無效的 task_id")

    try:
        json_path = safe_join(directory, f"{task_id}{suffix}")
    except ValueError:
        raise HTTPException(400, "無效的路徑")

    if not json_path.exists() or not json_path.is_file():
        raise HTTPException(404, "檔案不存在")

    with open(json_path, encoding="utf-8") as f:
        data: dict = json.load(f)
    return data


def _result_dataframe(file_results: list[dict], task_id: str) -> pd.DataFrame:
    """Convert one or more file processing results into downloadable tabular data."""
    all_masked_data = []
    for file_result in file_results:
        masked_data = file_result.get("masked_data")
        if masked_data and isinstance(masked_data, list):
            all_masked_data.extend(masked_data)
        elif file_result.get("masked_content"):
            all_masked_data.append(
                {
                    "檔案": file_result.get("filename", ""),
                    "內容": file_result.get("masked_content", ""),
                }
            )

    if all_masked_data:
        return pd.DataFrame(all_masked_data)

    return pd.DataFrame(
        [
            {
                "訊息": "沒有可輸出的資料",
                "任務 ID": task_id,
            }
        ]
    )


def _report_dataframe(report: dict, task_id: str) -> pd.DataFrame:
    """Convert report JSON into downloadable tabular PHI records."""
    phi_records = []
    for file_detail in report.get("file_details", []):
        filename = file_detail.get("filename", "unknown")
        for phi in file_detail.get("phi_entities", []):
            phi_records.append(
                {
                    "檔案": filename,
                    "PHI 類型": phi.get("type", ""),
                    "原始值": phi.get("value", ""),
                    "遮罩值": phi.get("masked_value", "[MASKED]"),
                    "信心度": phi.get("confidence", ""),
                }
            )

    if phi_records:
        return pd.DataFrame(phi_records)

    return pd.DataFrame(
        [
            {
                "訊息": "沒有發現 PHI",
                "任務 ID": task_id,
            }
        ]
    )


def _stream_dataframe(df: pd.DataFrame, filename: str, format: str) -> StreamingResponse:
    """Serialize dataframe as XLSX or CSV and return a download response."""
    output = BytesIO()
    if format == "xlsx":
        df.to_excel(output, index=False, engine="openpyxl")
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    elif format == "csv":
        df.to_csv(output, index=False, encoding="utf-8-sig")  # BOM for Excel
        media_type = "text/csv"
    else:
        raise HTTPException(400, "不支援的輸出格式")

    output.seek(0)
    return StreamingResponse(
        output,
        media_type=media_type,
        headers={"Content-Disposition": content_disposition_header(filename)},
    )


@router.post("/upload", response_model=UploadedFile)
async def upload_file(file: UploadFile = File(...)):
    """上傳檔案"""
    file_service = get_file_service()

    if not file.filename:
        raise HTTPException(400, "未提供檔案名稱")

    allowed_extensions = {".xlsx", ".xls", ".csv", ".json", ".txt"}
    file_ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if f".{file_ext}" not in allowed_extensions:
        raise HTTPException(400, f"不支援的檔案類型: {file_ext}。支援: xlsx, xls, csv, json, txt")

    content = await file.read()

    try:
        result = await file_service.upload(file.filename, content)
        return result
    except ValueError as e:
        raise HTTPException(413, str(e))


@router.get("/files", response_model=list[UploadedFile])
async def list_files():
    """列出所有上傳的檔案（含處理狀態）"""
    file_service = get_file_service()
    return file_service.list_files()


@router.delete("/files/{file_id}")
async def delete_file(file_id: str):
    """刪除檔案"""
    file_service = get_file_service()

    try:
        if file_service.delete(file_id):
            return {"message": "檔案已刪除"}
        raise HTTPException(404, "檔案不存在")
    except ValueError as e:
        raise HTTPException(400, str(e))
    except PermissionError as e:
        raise HTTPException(403, str(e))


@router.get("/download/{task_id}")
async def download_result(
    task_id: str,
    file_type: str = Query("result", enum=["result", "report"]),
    format: str = Query("xlsx", enum=["xlsx", "csv", "json"]),
):
    """下載處理結果或報告

    Args:
        task_id: 任務 ID
        file_type: result (處理結果) 或 report (報告)
        format: xlsx, csv, json
    """
    artifacts = {
        "result": (RESULTS_DIR, "_result.json"),
        "report": (REPORTS_DIR, "_report.json"),
    }
    if file_type not in artifacts:
        raise HTTPException(400, "不支援的檔案類型")

    search_dir, expected_suffix = artifacts[file_type]
    data = _load_download_json(search_dir, task_id, expected_suffix)

    # 如果要求 JSON 格式，直接返回
    if format == "json":
        filename = f"{task_id}_{file_type}.json"
        content = json.dumps(data, ensure_ascii=False, indent=2, default=str)
        return Response(
            content=content,
            media_type="application/json",
            headers={"Content-Disposition": content_disposition_header(filename)},
        )

    if file_type == "result":
        df = _result_dataframe(data.get("results", []), task_id)
    else:
        df = _report_dataframe(data, task_id)

    return _stream_dataframe(df, f"{task_id}_{file_type}.{format}", format)


@router.get("/download/{task_id}/file/{file_id}")
async def download_single_file_result(
    task_id: str,
    file_id: str,
    format: str = Query("xlsx", enum=["xlsx", "csv", "json"]),
):
    """下載單一檔案的處理結果。"""
    if not is_safe_identifier(file_id):
        raise HTTPException(400, "無效的 file_id")

    data = _load_download_json(RESULTS_DIR, task_id, "_result.json")
    file_result = next(
        (item for item in data.get("results", []) if item.get("file_id") == file_id),
        None,
    )
    if not file_result:
        raise HTTPException(404, "單一檔案結果不存在")

    original_name = file_result.get("filename") or file_id
    stem = Path(original_name).stem or file_id

    if format == "json":
        filename = f"{stem}_deid.json"
        content = json.dumps(file_result, ensure_ascii=False, indent=2, default=str)
        return Response(
            content=content,
            media_type="application/json",
            headers={"Content-Disposition": content_disposition_header(filename)},
        )

    df = _result_dataframe([file_result], task_id)
    return _stream_dataframe(df, f"{stem}_deid.{format}", format)
