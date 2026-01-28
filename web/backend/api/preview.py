"""
Preview API Router
資料預覽 API

支援格式：
- 表格: xlsx, xls, csv
- 文字: txt, md
- 文件: docx, doc, pdf
- 結構: json
"""

import json
import sys
from pathlib import Path
from typing import Any

import pandas as pd
from fastapi import APIRouter, HTTPException, Query
from loguru import logger

# 處理相對 import
_backend_dir = Path(__file__).parent.parent
if str(_backend_dir) not in sys.path:
    sys.path.insert(0, str(_backend_dir))

# 確保可以 import 主專案模組
_project_root = Path(__file__).parent.parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from services.file_service import get_file_service

router = APIRouter()

# 支援的檔案類型分類
TABULAR_TYPES = {"xlsx", "xls", "csv"}
TEXT_TYPES = {"txt", "md", "markdown"}
DOCUMENT_TYPES = {"docx", "doc", "pdf"}
STRUCTURED_TYPES = {"json"}


@router.get("/preview/{file_id}")
async def preview_file(
    file_id: str, page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100)
):
    """預覽檔案內容

    Args:
        file_id: 檔案 ID
        page: 頁碼
        page_size: 每頁筆數
    
    支援格式:
        - 表格: xlsx, xls, csv
        - 文字: txt, md
        - 文件: docx, doc, pdf
        - 結構: json
    """
    file_service = get_file_service()
    file_path = file_service.get_file_path(file_id)

    if not file_path or not file_path.exists():
        raise HTTPException(404, "檔案不存在")

    file_type = file_path.suffix.lower().lstrip(".")

    try:
        if file_type in TABULAR_TYPES:
            return await _preview_tabular(file_path, file_type, page, page_size)
        elif file_type in TEXT_TYPES:
            return await _preview_text(file_path, page, page_size, is_markdown=(file_type in {"md", "markdown"}))
        elif file_type in DOCUMENT_TYPES:
            return await _preview_document(file_path, file_type, page, page_size)
        elif file_type in STRUCTURED_TYPES:
            return await _preview_json(file_path, page, page_size)
        else:
            supported = TABULAR_TYPES | TEXT_TYPES | DOCUMENT_TYPES | STRUCTURED_TYPES
            raise HTTPException(400, f"不支援預覽的檔案類型: {file_type}，支援: {', '.join(sorted(supported))}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Preview error for {file_path}: {e}")
        raise HTTPException(500, f"預覽失敗: {e!s}")


async def _preview_tabular(
    file_path: Path, file_type: str, page: int, page_size: int
) -> dict[str, Any]:
    """預覽表格資料"""
    if file_type == "csv":
        df = pd.read_csv(file_path)
    else:
        df = pd.read_excel(file_path)

    total_rows = len(df)
    total_pages = (total_rows + page_size - 1) // page_size

    start_idx = (page - 1) * page_size
    end_idx = min(start_idx + page_size, total_rows)

    page_data = df.iloc[start_idx:end_idx]

    return {
        "type": "tabular",
        "columns": list(df.columns),
        "data": page_data.fillna("").to_dict(orient="records"),
        "total_rows": total_rows,
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total_rows": total_rows,
            "total_pages": total_pages,
        },
    }


async def _preview_text(file_path: Path, page: int, page_size: int, is_markdown: bool = False) -> dict[str, Any]:
    """預覽純文字/Markdown 檔案"""
    with open(file_path, encoding="utf-8", errors="replace") as f:
        content = f.read()

    lines = content.split("\n")
    total_lines = len(lines)
    total_pages = (total_lines + page_size - 1) // page_size

    start_idx = (page - 1) * page_size
    end_idx = min(start_idx + page_size, total_lines)

    return {
        "type": "markdown" if is_markdown else "text",
        "content": "\n".join(lines[start_idx:end_idx]),
        "total_rows": total_lines,
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total_rows": total_lines,
            "total_pages": total_pages,
        },
    }


async def _preview_document(file_path: Path, file_type: str, page: int, page_size: int) -> dict[str, Any]:
    """預覽文件檔案 (DOCX, DOC, PDF)
    
    使用 core 模組的 loader 提取文字內容
    """
    content = ""
    
    try:
        if file_type in {"docx", "doc"}:
            content = _load_word_content(file_path)
        elif file_type == "pdf":
            content = _load_pdf_content(file_path)
    except ImportError as e:
        logger.warning(f"Missing dependency for {file_type}: {e}")
        return {
            "type": "text",
            "content": f"[無法預覽：缺少必要的套件]\n\n請安裝相關依賴：\n- DOCX: pip install python-docx\n- PDF: pip install pymupdf 或 pdfplumber",
            "total_rows": 1,
            "error": str(e),
            "pagination": {"page": 1, "page_size": 1, "total_rows": 1, "total_pages": 1},
        }
    except Exception as e:
        logger.error(f"Error loading {file_type} file: {e}")
        raise

    # 分頁處理
    lines = content.split("\n")
    total_lines = len(lines)
    total_pages = (total_lines + page_size - 1) // page_size

    start_idx = (page - 1) * page_size
    end_idx = min(start_idx + page_size, total_lines)

    return {
        "type": "text",
        "content": "\n".join(lines[start_idx:end_idx]),
        "total_rows": total_lines,
        "source_format": file_type.upper(),
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total_rows": total_lines,
            "total_pages": total_pages,
        },
    }


def _load_word_content(file_path: Path) -> str:
    """載入 Word 文件內容"""
    try:
        from docx import Document
    except ImportError:
        raise ImportError("python-docx is required. Install with: pip install python-docx")
    
    doc = Document(file_path)
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    return "\n\n".join(paragraphs)


def _load_pdf_content(file_path: Path) -> str:
    """載入 PDF 文件內容"""
    # 嘗試 pymupdf (fitz)
    try:
        import fitz  # pymupdf
        doc = fitz.open(file_path)
        text_parts = []
        for page in doc:
            text_parts.append(page.get_text())
        doc.close()
        return "\n".join(text_parts)
    except ImportError:
        pass
    
    # 嘗試 pdfplumber
    try:
        import pdfplumber
        with pdfplumber.open(file_path) as pdf:
            text_parts = []
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    text_parts.append(text)
            return "\n".join(text_parts)
    except ImportError:
        pass
    
    raise ImportError("PDF reader required. Install with: pip install pymupdf or pip install pdfplumber")


async def _preview_json(file_path: Path, page: int, page_size: int) -> dict[str, Any]:
    """預覽 JSON 檔案"""
    with open(file_path, encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, list):
        total_rows = len(data)
        total_pages = (total_rows + page_size - 1) // page_size

        start_idx = (page - 1) * page_size
        end_idx = min(start_idx + page_size, total_rows)

        return {
            "type": "json",
            "data": data[start_idx:end_idx],
            "total_rows": total_rows,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total_rows": total_rows,
                "total_pages": total_pages,
            },
        }
    else:
        # 單一物件，直接返回
        return {
            "type": "json",
            "data": data,
            "total_rows": 1,
            "pagination": {
                "page": 1,
                "page_size": 1,
                "total_rows": 1,
                "total_pages": 1,
            },
        }
