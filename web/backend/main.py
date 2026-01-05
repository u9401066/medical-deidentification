"""
Medical De-identification Web API
FastAPI 後端服務
"""
import json

# 確保可以 import 主專案模組
import sys
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import BackgroundTasks, FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from loguru import logger

# Import PHIType for type handling
try:
    from core.domain import PHIType
except ImportError:
    PHIType = None  # Fallback if not available

# 設定資料目錄
DATA_DIR = Path(__file__).parent / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
RESULTS_DIR = DATA_DIR / "results"
REPORTS_DIR = DATA_DIR / "reports"
REGULATIONS_DIR = DATA_DIR / "regulations"

for d in [UPLOAD_DIR, RESULTS_DIR, REPORTS_DIR, REGULATIONS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# 任務狀態存儲
tasks_db: dict[str, dict[str, Any]] = {}


def format_time(seconds: float | None) -> str:
    """格式化時間為人類可讀格式"""
    if seconds is None or seconds < 0:
        return "計算中..."
    if seconds < 60:
        return f"{seconds:.0f} 秒"
    elif seconds < 3600:
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{mins} 分 {secs} 秒"
    else:
        hours = int(seconds // 3600)
        mins = int((seconds % 3600) // 60)
        return f"{hours} 小時 {mins} 分"


# ============================================================
# Pydantic Models
# ============================================================

class PHIConfig(BaseModel):
    """PHI 處理配置"""
    masking_type: str = Field(default="redact", description="redact, hash, pseudonymize")
    phi_types: list[str] = Field(default_factory=lambda: [
        "NAME", "DATE", "PHONE", "EMAIL", "ADDRESS", "ID_NUMBER", "MEDICAL_RECORD"
    ])
    preserve_format: bool = Field(default=True)
    custom_patterns: dict[str, str] | None = None


class ProcessRequest(BaseModel):
    """處理請求"""
    file_ids: list[str]
    config: PHIConfig | None = None
    job_name: str | None = None


class TaskStatus(BaseModel):
    """任務狀態"""
    task_id: str
    status: str  # pending, processing, completed, failed
    progress: float = 0.0
    message: str = ""
    created_at: datetime
    completed_at: datetime | None = None
    result_file: str | None = None
    report_file: str | None = None
    # 計時相關
    started_at: datetime | None = None
    elapsed_seconds: float | None = None
    estimated_remaining_seconds: float | None = None
    processing_speed: float | None = None  # chars per second
    total_chars: int | None = None
    processed_chars: int | None = None


class RegulationRule(BaseModel):
    """法規規則"""
    id: str
    name: str
    description: str
    phi_types: list[str]
    source: str  # hipaa, taiwan_pdpa, custom
    enabled: bool = True


class UploadedFile(BaseModel):
    """上傳的檔案資訊"""
    file_id: str
    filename: str
    size: int
    upload_time: datetime
    file_type: str
    preview_available: bool = True


# ============================================================
# Application Setup
# ============================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """應用程式生命週期管理"""
    logger.info("🚀 Medical De-identification Web API starting...")
    # 載入已有的任務狀態
    tasks_file = DATA_DIR / "tasks.json"
    if tasks_file.exists():
        try:
            with open(tasks_file) as f:
                saved_tasks = json.load(f)
                for task_id, task_data in saved_tasks.items():
                    task_data["created_at"] = datetime.fromisoformat(task_data["created_at"])
                    if task_data.get("completed_at"):
                        task_data["completed_at"] = datetime.fromisoformat(task_data["completed_at"])
                    tasks_db[task_id] = task_data
            logger.info(f"Loaded {len(tasks_db)} existing tasks")
        except Exception as e:
            logger.warning(f"Could not load tasks: {e}")

    yield

    # 保存任務狀態
    logger.info("💾 Saving tasks state...")
    try:
        serializable = {}
        for task_id, task in tasks_db.items():
            serializable[task_id] = {
                **task,
                "created_at": task["created_at"].isoformat(),
                "completed_at": task["completed_at"].isoformat() if task.get("completed_at") else None
            }
        with open(tasks_file, "w") as f:
            json.dump(serializable, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Could not save tasks: {e}")


app = FastAPI(
    title="Medical De-identification API",
    description="醫療文本去識別化 Web API",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS 設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# File Upload & Download APIs
# ============================================================

@app.post("/api/upload", response_model=UploadedFile)
async def upload_file(file: UploadFile = File(...)):
    """上傳檔案"""
    file_id = str(uuid.uuid4())[:8]
    file_ext = Path(file.filename).suffix.lower()

    # 支援的檔案類型
    supported_types = {".csv", ".xlsx", ".xls", ".txt", ".json", ".docx", ".pdf"}
    if file_ext not in supported_types:
        raise HTTPException(400, f"不支援的檔案類型: {file_ext}. 支援: {supported_types}")

    # 儲存檔案
    save_path = UPLOAD_DIR / f"{file_id}{file_ext}"
    content = await file.read()

    with open(save_path, "wb") as f:
        f.write(content)

    # 儲存元數據
    metadata = {
        "file_id": file_id,
        "filename": file.filename,
        "size": len(content),
        "upload_time": datetime.now().isoformat(),
        "file_type": file_ext[1:],
        "path": str(save_path),
    }

    with open(UPLOAD_DIR / f"{file_id}.meta.json", "w") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    logger.info(f"📁 Uploaded file: {file.filename} -> {file_id}")

    return UploadedFile(
        file_id=file_id,
        filename=file.filename,
        size=len(content),
        upload_time=datetime.now(),
        file_type=file_ext[1:],
    )


@app.get("/api/files", response_model=list[UploadedFile])
async def list_files():
    """列出所有上傳的檔案"""
    files = []
    for meta_file in UPLOAD_DIR.glob("*.meta.json"):
        with open(meta_file) as f:
            meta = json.load(f)
            files.append(UploadedFile(
                file_id=meta["file_id"],
                filename=meta["filename"],
                size=meta["size"],
                upload_time=datetime.fromisoformat(meta["upload_time"]),
                file_type=meta["file_type"],
            ))
    return sorted(files, key=lambda x: x.upload_time, reverse=True)


@app.delete("/api/files/{file_id}")
async def delete_file(file_id: str):
    """刪除檔案"""
    meta_file = UPLOAD_DIR / f"{file_id}.meta.json"
    if not meta_file.exists():
        raise HTTPException(404, "檔案不存在")

    with open(meta_file) as f:
        meta = json.load(f)

    # 刪除檔案和元數據
    Path(meta["path"]).unlink(missing_ok=True)
    meta_file.unlink()

    logger.info(f"🗑️ Deleted file: {file_id}")
    return {"message": "已刪除"}


@app.get("/api/download/{file_id}")
async def download_result(file_id: str, file_type: str = Query("result", enum=["result", "report"])):
    """下載處理結果或報告"""
    if file_type == "result":
        search_dir = RESULTS_DIR
    else:
        search_dir = REPORTS_DIR

    # 找到對應的檔案
    matching_files = list(search_dir.glob(f"{file_id}*"))
    if not matching_files:
        raise HTTPException(404, "檔案不存在")

    file_path = matching_files[0]
    return FileResponse(
        file_path,
        filename=file_path.name,
        media_type="application/octet-stream"
    )


# ============================================================
# Data Preview APIs
# ============================================================

@app.get("/api/preview/{file_id}")
async def preview_file(
    file_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    """預覽上傳的檔案內容"""
    meta_file = UPLOAD_DIR / f"{file_id}.meta.json"
    if not meta_file.exists():
        raise HTTPException(404, "檔案不存在")

    with open(meta_file) as f:
        meta = json.load(f)

    file_path = Path(meta["path"])
    file_type = meta["file_type"]

    try:
        if file_type in ["csv", "xlsx", "xls"]:
            return await _preview_tabular(file_path, file_type, page, page_size)
        elif file_type == "txt":
            return await _preview_text(file_path, page, page_size)
        elif file_type == "json":
            return await _preview_json(file_path, page, page_size)
        else:
            return {"message": f"預覽不支援 {file_type} 格式", "preview_available": False}
    except Exception as e:
        logger.error(f"Preview error: {e}")
        raise HTTPException(500, f"預覽失敗: {e!s}")


async def _preview_tabular(file_path: Path, file_type: str, page: int, page_size: int):
    """預覽表格資料"""
    import pandas as pd

    if file_type == "csv":
        df = pd.read_csv(file_path, nrows=page * page_size + page_size)
    else:
        df = pd.read_excel(file_path, nrows=page * page_size + page_size)

    total_rows = len(df)
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size

    page_df = df.iloc[start_idx:end_idx]

    return {
        "type": "tabular",
        "columns": list(df.columns),
        "data": page_df.fillna("").to_dict(orient="records"),
        "total_rows": total_rows,
        "page": page,
        "page_size": page_size,
        "has_more": end_idx < total_rows,
    }


async def _preview_text(file_path: Path, page: int, page_size: int):
    """預覽文字檔"""
    with open(file_path, encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()

    total_lines = len(lines)
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size

    return {
        "type": "text",
        "lines": [line.rstrip() for line in lines[start_idx:end_idx]],
        "total_lines": total_lines,
        "page": page,
        "page_size": page_size,
        "has_more": end_idx < total_lines,
    }


async def _preview_json(file_path: Path, page: int, page_size: int):
    """預覽 JSON 檔案"""
    with open(file_path, encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, list):
        total_items = len(data)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        return {
            "type": "json_array",
            "data": data[start_idx:end_idx],
            "total_items": total_items,
            "page": page,
            "page_size": page_size,
            "has_more": end_idx < total_items,
        }
    else:
        return {
            "type": "json_object",
            "data": data,
            "total_items": 1,
            "page": 1,
            "page_size": 1,
            "has_more": False,
        }


# ============================================================
# PHI Processing APIs
# ============================================================

@app.post("/api/process", response_model=TaskStatus)
async def start_processing(request: ProcessRequest, background_tasks: BackgroundTasks):
    """開始 PHI 處理任務"""
    task_id = str(uuid.uuid4())[:8]

    # 驗證檔案存在
    for file_id in request.file_ids:
        meta_file = UPLOAD_DIR / f"{file_id}.meta.json"
        if not meta_file.exists():
            raise HTTPException(404, f"檔案不存在: {file_id}")

    # 建立任務
    task = {
        "task_id": task_id,
        "status": "pending",
        "progress": 0.0,
        "message": "任務已建立，等待處理...",
        "created_at": datetime.now(),
        "completed_at": None,
        "result_file": None,
        "report_file": None,
        "file_ids": request.file_ids,
        "config": request.config.model_dump() if request.config else PHIConfig().model_dump(),
        "job_name": request.job_name or f"job-{task_id}",
    }
    tasks_db[task_id] = task

    # 背景執行處理
    background_tasks.add_task(process_phi_task, task_id)

    logger.info(f"🚀 Created task: {task_id} for files: {request.file_ids}")

    return TaskStatus(**{k: v for k, v in task.items() if k in TaskStatus.model_fields})


# 處理速度統計（用於預估時間）
processing_stats = {
    "total_chars_processed": 0,
    "total_time_seconds": 0.0,
    "task_count": 0,
    "avg_chars_per_second": 50.0,  # 初始估計值（基於 LLM 推理速度）
}


def estimate_remaining_time(total_chars: int, processed_chars: int, elapsed: float) -> float | None:
    """估計剩餘時間"""
    if processed_chars <= 0 or elapsed <= 0:
        # 使用歷史平均值估計
        if processing_stats["avg_chars_per_second"] > 0:
            return (total_chars - processed_chars) / processing_stats["avg_chars_per_second"]
        return None

    # 基於當前速度估計
    current_speed = processed_chars / elapsed
    remaining_chars = total_chars - processed_chars
    return remaining_chars / current_speed if current_speed > 0 else None


def update_processing_stats(chars_processed: int, time_seconds: float):
    """更新處理速度統計"""
    global processing_stats
    if chars_processed > 0 and time_seconds > 0:
        processing_stats["total_chars_processed"] += chars_processed
        processing_stats["total_time_seconds"] += time_seconds
        processing_stats["task_count"] += 1
        processing_stats["avg_chars_per_second"] = (
            processing_stats["total_chars_processed"] /
            processing_stats["total_time_seconds"]
        )
        logger.info(f"📊 Updated processing stats: avg speed = {processing_stats['avg_chars_per_second']:.2f} chars/sec")


async def process_phi_task(task_id: str):
    """背景執行 PHI 處理"""
    task = tasks_db[task_id]
    task["status"] = "processing"
    task["message"] = "正在處理..."
    task["started_at"] = datetime.now()
    task["elapsed_seconds"] = 0.0

    try:
        # 載入處理引擎（必須成功）
        from core.application.processing.engine import DeidentificationEngine, EngineConfig
        logger.info("✅ DeidentificationEngine loaded successfully")

        file_ids = task["file_ids"]
        config = PHIConfig(**task["config"])
        results = []

        # 計算總字符數用於預估時間
        total_chars = 0
        file_chars = {}
        for file_id in file_ids:
            meta_file = UPLOAD_DIR / f"{file_id}.meta.json"
            if meta_file.exists():
                with open(meta_file) as f:
                    meta = json.load(f)
                file_path = Path(meta["path"])
                if file_path.exists():
                    try:
                        content = file_path.read_text(encoding="utf-8", errors="ignore")
                        chars = len(content)
                        file_chars[file_id] = chars
                        total_chars += chars
                    except:
                        file_chars[file_id] = meta.get("size", 1000)
                        total_chars += file_chars[file_id]

        task["total_chars"] = total_chars
        task["processed_chars"] = 0

        # 初始預估時間
        if processing_stats["avg_chars_per_second"] > 0:
            task["estimated_remaining_seconds"] = total_chars / processing_stats["avg_chars_per_second"]
            task["message"] = f"預計需要 {format_time(task['estimated_remaining_seconds'])}"

        for i, file_id in enumerate(file_ids):
            file_start_time = datetime.now()
            task["progress"] = (i / len(file_ids)) * 100

            # 更新計時資訊
            elapsed = (datetime.now() - task["started_at"]).total_seconds()
            task["elapsed_seconds"] = elapsed

            # 計算預估剩餘時間
            remaining = estimate_remaining_time(
                total_chars,
                task["processed_chars"],
                elapsed
            )
            task["estimated_remaining_seconds"] = remaining

            # 更新訊息
            elapsed_str = format_time(elapsed)
            remaining_str = format_time(remaining) if remaining else "計算中..."
            task["message"] = f"處理檔案 {i+1}/{len(file_ids)}... (已用時 {elapsed_str}, 預計剩餘 {remaining_str})"

            # 讀取檔案
            meta_file = UPLOAD_DIR / f"{file_id}.meta.json"
            with open(meta_file) as f:
                meta = json.load(f)

            file_path = Path(meta["path"])

            # 使用真正的處理引擎
            engine_config = EngineConfig(
                llm_provider="ollama",
                llm_model="qwen2.5:1.5b",
                use_rag=False,
            )
            engine = DeidentificationEngine(engine_config)
            result = engine.process_file(file_path)

            # 從改進後的 ProcessingResult 提取 PHI 詳細資訊
            phi_count = result.total_phi_entities
            doc_info = result.documents[0] if result.documents else {}

            # 直接從 documents[0] 獲取 PHI 詳細列表 (新結構)
            phi_entities = []
            doc_phi_list = doc_info.get("phi_entities", [])
            for entity in doc_phi_list:
                phi_entities.append({
                    "type": entity.get("type", "UNKNOWN"),
                    "value": entity.get("text", ""),
                    "masked_value": "[MASKED]",  # 遮罩後的值需要從 masked_content 解析
                    "field": None,  # 欄位資訊需要額外處理
                    "row": None,
                    "confidence": entity.get("confidence", 0.9),
                    "start_pos": entity.get("start_pos"),
                    "end_pos": entity.get("end_pos"),
                    "reason": entity.get("reason", ""),
                })

            # 也檢查 summary.phi_entities (備用)
            if not phi_entities:
                summary_phi = result.summary.get("phi_entities", [])
                for entity in summary_phi:
                    phi_entities.append({
                        "type": entity.get("type", "UNKNOWN"),
                        "value": entity.get("text", ""),
                        "masked_value": "[MASKED]",
                        "field": None,
                        "row": None,
                        "confidence": entity.get("confidence", 0.9),
                    })

            # 取得原始和遮罩後的內容 (新結構直接提供)
            original_content = doc_info.get("original_content", "")
            masked_content = doc_info.get("masked_content", "")
            output_path = doc_info.get("output_path", "")

            # 讀取原始和處理後的資料用於 diff 顯示
            original_data = None
            masked_data = None
            import pandas as pd
            try:
                if meta["file_type"] == "csv":
                    original_df = pd.read_csv(file_path)
                    original_data = original_df.head(100).to_dict(orient='records')
                elif meta["file_type"] == "xlsx":
                    original_df = pd.read_excel(file_path)
                    original_data = original_df.head(100).to_dict(orient='records')

                # 優先使用引擎返回的輸出路徑
                if output_path and Path(output_path).exists():
                    out_path = Path(output_path)
                    if out_path.suffix == ".csv":
                        masked_df = pd.read_csv(out_path)
                    else:
                        masked_df = pd.read_excel(out_path)
                    masked_data = masked_df.head(100).to_dict(orient='records')
                    logger.info(f"使用引擎輸出路徑: {output_path}")
                else:
                    # 備用：查找處理後的輸出檔案
                    output_dir = Path("data/output/results")
                    if output_dir.exists():
                        original_stem = file_path.stem
                        for output_file in sorted(output_dir.glob(f"*{original_stem}*"), key=lambda x: x.stat().st_mtime, reverse=True):
                            if output_file.suffix in [".csv", ".xlsx"]:
                                if output_file.suffix == ".csv":
                                    masked_df = pd.read_csv(output_file)
                                else:
                                    masked_df = pd.read_excel(output_file)
                                masked_data = masked_df.head(100).to_dict(orient='records')
                                logger.info(f"找到處理後檔案: {output_file}")
                                break
            except Exception as read_err:
                logger.warning(f"無法讀取原始/處理後資料: {read_err}")

            # 取得按類型統計
            phi_by_type = result.summary.get("phi_by_type", {})

            results.append({
                "file_id": file_id,
                "filename": meta["filename"],
                "phi_found": phi_count,
                "phi_by_type": phi_by_type,  # 新增：按類型統計
                "rows_processed": result.processed_documents,
                "status": "completed",
                "phi_entities": phi_entities,
                "original_data": original_data,
                "masked_data": masked_data,
                "original_content": original_content[:5000] if original_content else None,  # 限制大小
                "masked_content": masked_content[:5000] if masked_content else None,
                "output_path": output_path,
            })
            logger.info(f"Engine processed {meta['filename']}: found {phi_count} PHI, types: {phi_by_type}")

            # 更新已處理字符數
            task["processed_chars"] = task.get("processed_chars", 0) + file_chars.get(file_id, 0)

            # 記錄單檔處理時間
            file_elapsed = (datetime.now() - file_start_time).total_seconds()
            logger.info(f"⏱️ File {meta['filename']} processed in {file_elapsed:.2f}s")

        # 儲存結果
        result_id = task_id
        result_file = RESULTS_DIR / f"{result_id}_results.json"
        with open(result_file, "w", encoding="utf-8") as f:
            json.dump({
                "task_id": task_id,
                "job_name": task["job_name"],
                "config": task["config"],
                "results": results,
                "processed_at": datetime.now().isoformat(),
            }, f, indent=2, ensure_ascii=False)

        # 產生報告
        report_file = REPORTS_DIR / f"{result_id}_report.json"
        total_phi = sum(r.get("phi_found", 0) for r in results)

        # 計算總處理時間
        total_time = (datetime.now() - task["started_at"]).total_seconds()
        processing_speed = total_chars / total_time if total_time > 0 else 0

        report = {
            "task_id": task_id,
            "job_name": task["job_name"],
            "summary": {
                "files_processed": len(results),
                "total_phi_found": total_phi,
                "processing_time_seconds": round(total_time, 2),
                "total_chars": total_chars,
                "processing_speed_chars_per_sec": round(processing_speed, 2),
            },
            "file_details": results,
            "generated_at": datetime.now().isoformat(),
        }
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        # 更新處理速度統計
        update_processing_stats(total_chars, total_time)

        # 更新任務狀態
        task["status"] = "completed"
        task["progress"] = 100.0
        task["elapsed_seconds"] = total_time
        task["estimated_remaining_seconds"] = 0
        task["processing_speed"] = processing_speed
        task["message"] = f"處理完成！找到 {total_phi} 個 PHI (耗時 {format_time(total_time)}, 速度 {processing_speed:.1f} 字元/秒)"
        task["completed_at"] = datetime.now()
        task["result_file"] = str(result_file.name)
        task["report_file"] = str(report_file.name)

        logger.info(f"✅ Task completed: {task_id}, PHI found: {total_phi}")

    except Exception as e:
        task["status"] = "failed"
        task["message"] = f"處理失敗: {e!s}"
        task["completed_at"] = datetime.now()
        logger.error(f"❌ Task failed: {task_id}, error: {e}")


@app.get("/api/tasks", response_model=list[TaskStatus])
async def list_tasks():
    """列出所有任務"""
    return [
        TaskStatus(**{k: v for k, v in task.items() if k in TaskStatus.model_fields})
        for task in sorted(tasks_db.values(), key=lambda x: x["created_at"], reverse=True)
    ]


@app.get("/api/tasks/{task_id}", response_model=TaskStatus)
async def get_task(task_id: str):
    """取得任務狀態"""
    if task_id not in tasks_db:
        raise HTTPException(404, "任務不存在")
    task = tasks_db[task_id]

    # 如果任務正在處理中，即時更新計時資訊
    if task["status"] == "processing" and task.get("started_at"):
        elapsed = (datetime.now() - task["started_at"]).total_seconds()
        task["elapsed_seconds"] = elapsed

        # 更新預估剩餘時間
        total_chars = task.get("total_chars", 0)
        processed_chars = task.get("processed_chars", 0)
        if total_chars > 0 and processed_chars > 0 and elapsed > 0:
            current_speed = processed_chars / elapsed
            remaining_chars = total_chars - processed_chars
            task["estimated_remaining_seconds"] = remaining_chars / current_speed
            task["processing_speed"] = current_speed

    return TaskStatus(**{k: v for k, v in task.items() if k in TaskStatus.model_fields})


@app.get("/api/stats/processing")
async def get_processing_stats():
    """取得處理速度統計"""
    return {
        "avg_chars_per_second": processing_stats["avg_chars_per_second"],
        "total_chars_processed": processing_stats["total_chars_processed"],
        "total_time_seconds": processing_stats["total_time_seconds"],
        "task_count": processing_stats["task_count"],
    }


# ============================================================
# Results & Reports APIs
# ============================================================

@app.get("/api/results")
async def list_results():
    """列出所有處理結果"""
    results = []
    for result_file in RESULTS_DIR.glob("*_results.json"):
        try:
            with open(result_file, encoding="utf-8") as f:
                data = json.load(f)
                task_id = result_file.stem.replace("_results", "")

                # 計算總 PHI 數量
                phi_count = 0
                file_results = data.get("results", [])
                for fr in file_results:
                    phi_count += fr.get("phi_found", 0)

                # 取得檔案名稱
                filenames = [fr.get("filename", "Unknown") for fr in file_results]

                results.append({
                    "task_id": task_id,
                    "filename": ", ".join(filenames) if filenames else "Unknown",
                    "phi_count": phi_count,
                    "files_processed": len(file_results),
                    "status": "completed",
                    "created_at": data.get("processed_at"),
                })
        except Exception as e:
            logger.warning(f"Failed to read result file {result_file}: {e}")

    # 按時間排序，最新的在前面
    results.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return results


@app.get("/api/results/{task_id}")
async def get_results(task_id: str):
    """取得處理結果"""
    result_file = RESULTS_DIR / f"{task_id}_results.json"
    if not result_file.exists():
        raise HTTPException(404, "結果不存在")

    with open(result_file, encoding="utf-8") as f:
        return json.load(f)


@app.get("/api/reports/{task_id}")
async def get_report(task_id: str):
    """取得報告"""
    report_file = REPORTS_DIR / f"{task_id}_report.json"
    if not report_file.exists():
        raise HTTPException(404, "報告不存在")

    with open(report_file, encoding="utf-8") as f:
        return json.load(f)


@app.get("/api/reports")
async def list_reports():
    """列出所有報告"""
    reports = []
    for report_file in REPORTS_DIR.glob("*_report.json"):
        with open(report_file, encoding="utf-8") as f:
            report = json.load(f)
            reports.append({
                "task_id": report["task_id"],
                "job_name": report.get("job_name", ""),
                "files_processed": report["summary"]["files_processed"],
                "total_phi_found": report["summary"]["total_phi_found"],
                "generated_at": report["generated_at"],
            })
    return sorted(reports, key=lambda x: x["generated_at"], reverse=True)


# ============================================================
# Settings & Regulations APIs
# ============================================================

@app.get("/api/settings/phi-types")
async def get_phi_types():
    """取得可用的 PHI 類型"""
    return {
        "phi_types": [
            {"id": "NAME", "name": "姓名", "description": "患者或相關人員姓名", "category": "identifier"},
            {"id": "DATE", "name": "日期", "description": "出生日期、就診日期等", "category": "temporal"},
            {"id": "PHONE", "name": "電話", "description": "電話號碼", "category": "contact"},
            {"id": "EMAIL", "name": "電子郵件", "description": "電子郵件地址", "category": "contact"},
            {"id": "ADDRESS", "name": "地址", "description": "住址、工作地址等", "category": "geographic"},
            {"id": "ID_NUMBER", "name": "身份證號", "description": "身分證字號、護照號碼", "category": "identifier"},
            {"id": "MEDICAL_RECORD", "name": "病歷號", "description": "病歷號碼", "category": "identifier"},
            {"id": "SOCIAL_SECURITY", "name": "社會安全碼", "description": "健保卡號等", "category": "identifier"},
            {"id": "ACCOUNT_NUMBER", "name": "帳號", "description": "銀行帳號等", "category": "financial"},
            {"id": "LICENSE_NUMBER", "name": "執照號碼", "description": "駕照、證照號碼", "category": "identifier"},
            {"id": "VEHICLE_ID", "name": "車輛識別", "description": "車牌號碼", "category": "identifier"},
            {"id": "DEVICE_ID", "name": "設備識別", "description": "設備序號、IP 位址", "category": "technical"},
            {"id": "URL", "name": "網址", "description": "網站網址", "category": "technical"},
            {"id": "BIOMETRIC", "name": "生物識別", "description": "指紋、聲紋等", "category": "biometric"},
            {"id": "PHOTO", "name": "影像", "description": "全臉照片等", "category": "biometric"},
            {"id": "AGE", "name": "年齡", "description": "超過 89 歲的年齡", "category": "demographic"},
        ],
        "masking_types": [
            {"id": "redact", "name": "遮蔽", "description": "以 [REDACTED] 取代"},
            {"id": "hash", "name": "雜湊", "description": "以雜湊值取代，可追蹤同一人"},
            {"id": "pseudonymize", "name": "假名化", "description": "以假名取代"},
            {"id": "generalize", "name": "泛化", "description": "以更廣泛的類別取代"},
        ],
    }


@app.get("/api/settings/config")
async def get_config():
    """取得目前的處理設定"""
    config_file = DATA_DIR / "config.json"
    if config_file.exists():
        with open(config_file, encoding="utf-8") as f:
            return json.load(f)
    return PHIConfig().model_dump()


@app.put("/api/settings/config")
async def update_config(config: PHIConfig):
    """更新處理設定"""
    config_file = DATA_DIR / "config.json"
    with open(config_file, "w", encoding="utf-8") as f:
        json.dump(config.model_dump(), f, indent=2, ensure_ascii=False)
    logger.info(f"⚙️ Config updated: {config.masking_type}")
    return {"message": "設定已更新", "config": config.model_dump()}


@app.get("/api/regulations", response_model=list[RegulationRule])
async def list_regulations():
    """列出所有法規規則"""
    # 預設規則
    default_rules = [
        {
            "id": "hipaa-safe-harbor",
            "name": "HIPAA Safe Harbor",
            "description": "美國 HIPAA 法規的 18 項識別資訊",
            "phi_types": ["NAME", "DATE", "PHONE", "EMAIL", "ADDRESS", "ID_NUMBER",
                         "MEDICAL_RECORD", "SOCIAL_SECURITY", "ACCOUNT_NUMBER"],
            "source": "hipaa",
            "enabled": True,
        },
        {
            "id": "taiwan-pdpa",
            "name": "台灣個資法",
            "description": "台灣個人資料保護法定義的個人資料",
            "phi_types": ["NAME", "DATE", "PHONE", "EMAIL", "ADDRESS", "ID_NUMBER"],
            "source": "taiwan_pdpa",
            "enabled": True,
        },
    ]

    # 載入自訂規則
    custom_rules_file = REGULATIONS_DIR / "custom_rules.json"
    if custom_rules_file.exists():
        with open(custom_rules_file, encoding="utf-8") as f:
            custom_rules = json.load(f)
            default_rules.extend(custom_rules)

    return [RegulationRule(**r) for r in default_rules]


@app.post("/api/regulations/upload")
async def upload_regulation(file: UploadFile = File(...)):
    """上傳自訂法規檔案"""
    if not file.filename.endswith(".json"):
        raise HTTPException(400, "僅支援 JSON 格式")

    content = await file.read()
    try:
        rules = json.loads(content)

        # 驗證格式
        if not isinstance(rules, list):
            rules = [rules]

        for rule in rules:
            required_fields = ["id", "name", "description", "phi_types"]
            for field in required_fields:
                if field not in rule:
                    raise ValueError(f"缺少必要欄位: {field}")
            rule["source"] = "custom"
            rule["enabled"] = rule.get("enabled", True)

        # 儲存
        custom_rules_file = REGULATIONS_DIR / "custom_rules.json"
        existing_rules = []
        if custom_rules_file.exists():
            with open(custom_rules_file, encoding="utf-8") as f:
                existing_rules = json.load(f)

        existing_rules.extend(rules)

        with open(custom_rules_file, "w", encoding="utf-8") as f:
            json.dump(existing_rules, f, indent=2, ensure_ascii=False)

        logger.info(f"📜 Uploaded {len(rules)} regulation rules")
        return {"message": f"已上傳 {len(rules)} 條規則", "rules": rules}

    except json.JSONDecodeError:
        raise HTTPException(400, "無效的 JSON 格式")
    except ValueError as e:
        raise HTTPException(400, str(e))


@app.put("/api/regulations/{rule_id}")
async def update_regulation(rule_id: str, enabled: bool):
    """啟用/停用法規規則"""
    # 這裡簡化處理，實際應該更新資料庫
    logger.info(f"📜 Rule {rule_id} {'enabled' if enabled else 'disabled'}")
    return {"message": "規則已更新", "rule_id": rule_id, "enabled": enabled}


# ============================================================
# Health Check
# ============================================================

@app.get("/api/health")
async def health_check():
    """健康檢查，包含 LLM 狀態"""
    import subprocess

    # 檢查 Ollama LLM 狀態
    llm_status = "offline"
    llm_model = None
    try:
        result = subprocess.run(
            ["curl", "-s", "http://localhost:11434/api/tags"],
            check=False, capture_output=True,
            text=True,
            timeout=3
        )
        if result.returncode == 0:
            import json as json_lib
            data = json_lib.loads(result.stdout)
            models = [m.get("name") for m in data.get("models", [])]
            if models:
                llm_status = "online"
                llm_model = models[0] if len(models) == 1 else f"{len(models)} models"
    except Exception:
        pass

    # 檢查 PHI Engine 是否可用
    engine_available = False
    try:
        from core.application.processing.engine import DeidentificationEngine
        engine_available = True
    except ImportError:
        pass

    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "llm": {
            "status": llm_status,
            "model": llm_model,
            "provider": "ollama"
        },
        "engine_available": engine_available
    }


# ============================================================
# Run Server
# ============================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
