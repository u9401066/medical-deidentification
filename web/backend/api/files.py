"""
Files API Router
檔案上傳/下載 API
"""

import json
import sys
from io import BytesIO
from pathlib import Path
from urllib.parse import quote

import pandas as pd
from fastapi import APIRouter, File, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from starlette.responses import StreamingResponse

# 處理相對 import
_backend_dir = Path(__file__).parent.parent
if str(_backend_dir) not in sys.path:
    sys.path.insert(0, str(_backend_dir))

from config import REPORTS_DIR, RESULTS_DIR


def make_content_disposition(filename: str) -> str:
    """產生 Content-Disposition header，支援中文檔名 (RFC 5987)"""
    # ASCII fallback
    ascii_name = filename.encode("ascii", "ignore").decode("ascii") or "download"
    # UTF-8 encoded (RFC 5987)
    encoded_name = quote(filename, safe="")
    return f"attachment; filename=\"{ascii_name}\"; filename*=UTF-8''{encoded_name}"
from models.file import UploadedFile
from services.file_service import get_file_service

router = APIRouter()


@router.post("/upload", response_model=UploadedFile)
async def upload_file(file: UploadFile = File(...)):
    """上傳檔案"""
    file_service = get_file_service()

    # 支援的檔案類型
    allowed_extensions = {
        # 表格
        ".xlsx", ".xls", ".csv",
        # 結構化
        ".json",
        # 文字
        ".txt", ".md", ".markdown",
        # 文件
        ".docx", ".doc", ".pdf",
    }
    file_ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if f".{file_ext}" not in allowed_extensions:
        supported = ", ".join(ext.lstrip(".") for ext in sorted(allowed_extensions))
        raise HTTPException(400, f"不支援的檔案類型: {file_ext}。支援: {supported}")

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


@router.get("/download/{file_id}")
async def download_result(
    file_id: str,
    file_type: str = Query("result", enum=["result", "report"]),
    format: str = Query("xlsx", enum=["xlsx", "csv", "json"]),
):
    """下載處理結果或報告 (整個任務)

    Args:
        file_id: 任務 ID
        file_type: result (處理結果) 或 report (報告)
        format: xlsx, csv, json
    """
    if file_type == "result":
        search_dir = RESULTS_DIR
    else:
        search_dir = REPORTS_DIR

    # 找到對應的 JSON 檔案
    matching_files = list(search_dir.glob(f"{file_id}*"))
    if not matching_files:
        raise HTTPException(404, "檔案不存在")

    json_path = matching_files[0]

    # 如果要求 JSON 格式，直接返回
    if format == "json":
        return FileResponse(
            json_path, filename=f"{file_id}_{file_type}.json", media_type="application/json"
        )

    # 讀取 JSON
    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)

    # 輸出 mask 後的完整資料
    output = BytesIO()

    if file_type == "result":
        # 優先使用 masked_data (表格資料)
        all_masked_data = []
        for file_result in data.get("results", []):
            masked_data = file_result.get("masked_data")
            if masked_data and isinstance(masked_data, list):
                all_masked_data.extend(masked_data)
            elif file_result.get("masked_content"):
                # 純文字內容，包裝成表格
                all_masked_data.append(
                    {
                        "檔案": file_result.get("filename", ""),
                        "內容": file_result.get("masked_content", ""),
                    }
                )

        if all_masked_data:
            df = pd.DataFrame(all_masked_data)
        else:
            # fallback: 輸出 PHI 摘要
            df = pd.DataFrame(
                [
                    {
                        "訊息": "沒有可輸出的資料",
                        "任務 ID": file_id,
                    }
                ]
            )
    else:
        # 報告格式：輸出 PHI 列表
        phi_records = []
        for file_detail in data.get("file_details", []):
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
            df = pd.DataFrame(phi_records)
        else:
            df = pd.DataFrame(
                [
                    {
                        "訊息": "沒有發現 PHI",
                        "任務 ID": file_id,
                    }
                ]
            )

    # 產生檔案
    if format == "xlsx":
        df.to_excel(output, index=False, engine="openpyxl")
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        filename = f"{file_id}_{file_type}.xlsx"
    else:  # csv
        df.to_csv(output, index=False, encoding="utf-8-sig")  # BOM for Excel
        media_type = "text/csv"
        filename = f"{file_id}_{file_type}.csv"

    output.seek(0)

    return StreamingResponse(
        output,
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/download/{task_id}/file/{target_file_id}")
async def download_single_file_result(
    task_id: str,
    target_file_id: str,
    format: str = Query("xlsx", enum=["xlsx", "csv", "json"]),
):
    """下載單一檔案的處理結果

    Args:
        task_id: 任務 ID
        target_file_id: 要下載的檔案 ID
        format: xlsx, csv, json
    """
    result_file = RESULTS_DIR / f"{task_id}_result.json"

    if not result_file.exists():
        raise HTTPException(404, "任務結果不存在")

    with open(result_file, encoding="utf-8") as f:
        data = json.load(f)

    # 找到指定的檔案結果
    file_result = None
    for r in data.get("results", []):
        if r.get("file_id") == target_file_id:
            file_result = r
            break

    if not file_result:
        raise HTTPException(404, f"找不到檔案 {target_file_id} 的結果")

    original_filename = file_result.get("filename", target_file_id)
    # 移除副檔名以便加上新的
    base_name = original_filename.rsplit(".", 1)[0] if "." in original_filename else original_filename

    # 如果要求 JSON 格式
    if format == "json":
        json_filename = f"{base_name}_deid.json"
        return StreamingResponse(
            BytesIO(json.dumps(file_result, ensure_ascii=False, indent=2).encode("utf-8")),
            media_type="application/json",
            headers={"Content-Disposition": make_content_disposition(json_filename)},
        )

    output = BytesIO()

    # 優先使用 masked_data (表格資料)
    masked_data = file_result.get("masked_data")
    if masked_data and isinstance(masked_data, list):
        df = pd.DataFrame(masked_data)
    elif file_result.get("masked_content"):
        # 純文字內容
        df = pd.DataFrame([{"內容": file_result.get("masked_content", "")}])
    else:
        df = pd.DataFrame([{"訊息": "沒有可輸出的資料", "檔案 ID": target_file_id}])

    # 產生檔案
    if format == "xlsx":
        df.to_excel(output, index=False, engine="openpyxl")
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        filename = f"{base_name}_deid.xlsx"
    else:  # csv
        df.to_csv(output, index=False, encoding="utf-8-sig")
        media_type = "text/csv"
        filename = f"{base_name}_deid.csv"

    output.seek(0)

    return StreamingResponse(
        output,
        media_type=media_type,
        headers={"Content-Disposition": make_content_disposition(filename)},
    )
