"""
Data Loader | 資料載入器

載入各種格式的 benchmark 資料：
- i2b2 2006/2014 格式
- CBLUE CMeEE 格式
- 自訂 JSON/JSONL 格式
- Presidio Evaluator 合成資料
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Optional, Iterator, Any, Union
import json
import re
from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)


@dataclass
class PHIAnnotation:
    """
    PHI 標註
    
    Attributes:
        text: 原始文字
        phi_type: PHI 類型
        start: 起始位置 (optional)
        end: 結束位置 (optional)
    """
    text: str
    phi_type: str
    start: Optional[int] = None
    end: Optional[int] = None
    
    def to_tuple(self) -> tuple:
        """轉為 (text, type) 格式"""
        return (self.text, self.phi_type)


@dataclass
class BenchmarkSample:
    """
    單個 benchmark 樣本
    
    Attributes:
        id: 樣本 ID
        text: 原始文字
        annotations: PHI 標註列表
        metadata: 其他元資料
    """
    id: str
    text: str
    annotations: List[PHIAnnotation] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def ground_truth(self) -> List[tuple]:
        """取得 ground truth 格式: [(text, type), ...]"""
        return [ann.to_tuple() for ann in self.annotations]
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "text": self.text,
            "annotations": [
                {"text": ann.text, "phi_type": ann.phi_type, "start": ann.start, "end": ann.end}
                for ann in self.annotations
            ],
            "metadata": self.metadata,
        }


class DataLoader(ABC):
    """資料載入器基類"""
    
    @abstractmethod
    def load(self, path: Union[str, Path]) -> Iterator[BenchmarkSample]:
        """載入資料"""
        pass


class JSONLoader(DataLoader):
    """
    JSON/JSONL 格式載入器
    
    支援格式:
    1. JSONL (每行一個 JSON):
       {"id": "1", "text": "...", "annotations": [...]}
    
    2. JSON Array:
       [{"id": "1", "text": "...", "annotations": [...]}, ...]
    
    3. JSON Object with samples key:
       {"samples": [...], "metadata": {...}}
    """
    
    def __init__(
        self,
        text_field: str = "text",
        annotations_field: str = "annotations",
        id_field: str = "id",
    ):
        self.text_field = text_field
        self.annotations_field = annotations_field
        self.id_field = id_field
    
    def load(self, path: Union[str, Path]) -> Iterator[BenchmarkSample]:
        path = Path(path)
        
        if path.suffix == ".jsonl":
            yield from self._load_jsonl(path)
        elif path.suffix == ".json":
            yield from self._load_json(path)
        else:
            raise ValueError(f"Unsupported format: {path.suffix}")
    
    def _load_jsonl(self, path: Path) -> Iterator[BenchmarkSample]:
        with open(path, "r", encoding="utf-8") as f:
            for i, line in enumerate(f):
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    yield self._parse_sample(data, i)
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse line {i}: {e}")
    
    def _load_json(self, path: Path) -> Iterator[BenchmarkSample]:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        if isinstance(data, list):
            samples = data
        elif isinstance(data, dict):
            samples = data.get("samples", data.get("data", [data]))
        else:
            raise ValueError(f"Unexpected JSON structure")
        
        for i, sample in enumerate(samples):
            yield self._parse_sample(sample, i)
    
    def _parse_sample(self, data: Dict, idx: int) -> BenchmarkSample:
        sample_id = str(data.get(self.id_field, idx))
        text = data.get(self.text_field, "")
        
        annotations = []
        for ann in data.get(self.annotations_field, []):
            if isinstance(ann, dict):
                annotations.append(PHIAnnotation(
                    text=ann.get("text", ann.get("value", "")),
                    phi_type=ann.get("phi_type", ann.get("type", ann.get("label", "UNKNOWN"))),
                    start=ann.get("start"),
                    end=ann.get("end"),
                ))
            elif isinstance(ann, (list, tuple)) and len(ann) >= 2:
                annotations.append(PHIAnnotation(text=ann[0], phi_type=ann[1]))
        
        return BenchmarkSample(
            id=sample_id,
            text=text,
            annotations=annotations,
            metadata=data.get("metadata", {}),
        )


class I2B2Loader(DataLoader):
    """
    i2b2 格式載入器
    
    i2b2 PHI 資料格式：
    - .txt 檔案：原始文字
    - .xml 或 .phi 檔案：標註資訊
    
    標註格式範例:
    <PATIENT id="P0" start="16" end="30" text="Sample Patient" TYPE="PATIENT"/>
    <DATE id="D0" start="45" end="55" text="2024-01-15" TYPE="DATE"/>
    """
    
    PHI_TAG_PATTERN = re.compile(
        r'<(?P<type>\w+)\s+id="[^"]*"\s+start="(?P<start>\d+)"\s+end="(?P<end>\d+)"\s+'
        r'text="(?P<text>[^"]*)"\s+TYPE="(?P<phi_type>\w+)"[^>]*/?>',
        re.IGNORECASE
    )
    
    ALT_PATTERN = re.compile(
        r'<PHI\s+TYPE="(?P<phi_type>\w+)"[^>]*>(?P<text>[^<]*)</PHI>',
        re.IGNORECASE
    )
    
    def __init__(self, text_dir: Optional[Path] = None, annotation_dir: Optional[Path] = None):
        self.text_dir = text_dir
        self.annotation_dir = annotation_dir
    
    def load(self, path: Union[str, Path]) -> Iterator[BenchmarkSample]:
        path = Path(path)
        
        if path.is_file():
            # 單檔案模式
            yield from self._load_single(path)
        elif path.is_dir():
            # 目錄模式
            yield from self._load_directory(path)
    
    def _load_directory(self, dir_path: Path) -> Iterator[BenchmarkSample]:
        # 找所有 .txt 檔案
        text_files = list(dir_path.glob("*.txt"))
        
        for txt_file in sorted(text_files):
            # 找對應的標註檔案
            ann_file = None
            for ext in [".xml", ".phi", ".tags"]:
                candidate = txt_file.with_suffix(ext)
                if candidate.exists():
                    ann_file = candidate
                    break
            
            if ann_file:
                yield from self._load_pair(txt_file, ann_file)
            else:
                logger.warning(f"No annotation file found for {txt_file}")
    
    def _load_single(self, path: Path) -> Iterator[BenchmarkSample]:
        """載入包含標註的單一檔案"""
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        
        # 提取文字和標註
        text = re.sub(r'<[^>]+>', '', content)  # 移除所有 XML tags
        annotations = self._extract_annotations(content)
        
        yield BenchmarkSample(
            id=path.stem,
            text=text,
            annotations=annotations,
            metadata={"source": str(path)},
        )
    
    def _load_pair(self, txt_file: Path, ann_file: Path) -> Iterator[BenchmarkSample]:
        """載入文字檔+標註檔配對"""
        with open(txt_file, "r", encoding="utf-8", errors="replace") as f:
            text = f.read()
        
        with open(ann_file, "r", encoding="utf-8", errors="replace") as f:
            annotation_content = f.read()
        
        annotations = self._extract_annotations(annotation_content)
        
        yield BenchmarkSample(
            id=txt_file.stem,
            text=text,
            annotations=annotations,
            metadata={"source_text": str(txt_file), "source_ann": str(ann_file)},
        )
    
    def _extract_annotations(self, content: str) -> List[PHIAnnotation]:
        annotations = []
        
        # 嘗試主要格式
        for match in self.PHI_TAG_PATTERN.finditer(content):
            annotations.append(PHIAnnotation(
                text=match.group("text"),
                phi_type=match.group("phi_type"),
                start=int(match.group("start")),
                end=int(match.group("end")),
            ))
        
        # 嘗試備用格式
        if not annotations:
            for match in self.ALT_PATTERN.finditer(content):
                annotations.append(PHIAnnotation(
                    text=match.group("text"),
                    phi_type=match.group("phi_type"),
                ))
        
        return annotations


class CBLUELoader(DataLoader):
    """
    CBLUE CMeEE 格式載入器
    
    CMeEE (Chinese Medical Entity Extraction) 格式:
    {"text": "...", "entities": [{"start_idx": 0, "end_idx": 5, "type": "dis", "entity": "糖尿病"}]}
    
    Entity types:
    - dis: 疾病
    - sym: 症狀
    - pro: 醫療程序
    - equ: 醫療設備
    - dru: 藥物
    - ite: 醫學檢驗項目
    - bod: 身體部位
    - dep: 科室
    - mic: 微生物
    """
    
    # 映射 CMeEE 類型到 PHI 類型
    TYPE_MAPPING = {
        "per": "NAME",  # 人名
        "loc": "LOCATION",  # 地點
        "org": "FACILITY",  # 機構
        "tim": "DATE",  # 時間
        # 非 PHI 類型保持原樣
    }
    
    def load(self, path: Union[str, Path]) -> Iterator[BenchmarkSample]:
        path = Path(path)
        loader = JSONLoader(
            text_field="text",
            annotations_field="entities",
        )
        
        for sample in loader.load(path):
            # 轉換 annotations
            new_annotations = []
            for ann in sample.annotations:
                phi_type = self.TYPE_MAPPING.get(ann.phi_type.lower(), ann.phi_type)
                new_annotations.append(PHIAnnotation(
                    text=ann.text,
                    phi_type=phi_type,
                    start=ann.start,
                    end=ann.end,
                ))
            
            sample.annotations = new_annotations
            yield sample


class PresidioEvaluatorLoader(DataLoader):
    """
    Presidio Evaluator 合成資料載入器
    
    Presidio Evaluator 產生的資料格式:
    {
        "full_text": "...",
        "masked": "...",
        "spans": [
            {"entity_type": "PERSON", "entity_value": "John Doe", "start_position": 10, "end_position": 18}
        ],
        "template_id": "...",
        "metadata": {...}
    }
    """
    
    def load(self, path: Union[str, Path]) -> Iterator[BenchmarkSample]:
        path = Path(path)
        
        with open(path, "r", encoding="utf-8") as f:
            if path.suffix == ".jsonl":
                data = [json.loads(line) for line in f if line.strip()]
            else:
                data = json.load(f)
                if isinstance(data, dict):
                    data = [data]
        
        for i, item in enumerate(data):
            annotations = []
            for span in item.get("spans", []):
                annotations.append(PHIAnnotation(
                    text=span.get("entity_value", ""),
                    phi_type=span.get("entity_type", "UNKNOWN"),
                    start=span.get("start_position"),
                    end=span.get("end_position"),
                ))
            
            yield BenchmarkSample(
                id=item.get("template_id", str(i)),
                text=item.get("full_text", ""),
                annotations=annotations,
                metadata=item.get("metadata", {}),
            )


def load_benchmark_data(
    path: Union[str, Path],
    format: str = "auto",
    **kwargs,
) -> Iterator[BenchmarkSample]:
    """
    載入 benchmark 資料
    
    Args:
        path: 資料路徑
        format: 格式 (auto, json, jsonl, i2b2, cblue, presidio)
        **kwargs: 傳給 loader 的參數
    
    Returns:
        Iterator[BenchmarkSample]
    """
    path = Path(path)
    
    # 自動偵測格式
    if format == "auto":
        if path.suffix in [".json", ".jsonl"]:
            format = "json"
        elif path.suffix in [".xml", ".phi"]:
            format = "i2b2"
        elif "i2b2" in str(path).lower():
            format = "i2b2"
        elif "cblue" in str(path).lower() or "cmee" in str(path).lower():
            format = "cblue"
        elif "presidio" in str(path).lower():
            format = "presidio"
        else:
            format = "json"  # 預設
    
    # 選擇 loader
    loaders = {
        "json": JSONLoader,
        "jsonl": JSONLoader,
        "i2b2": I2B2Loader,
        "cblue": CBLUELoader,
        "presidio": PresidioEvaluatorLoader,
    }
    
    loader_cls = loaders.get(format)
    if not loader_cls:
        raise ValueError(f"Unsupported format: {format}")
    
    loader = loader_cls(**kwargs)
    yield from loader.load(path)


def load_all(paths: List[Union[str, Path]], format: str = "auto") -> List[BenchmarkSample]:
    """載入多個檔案"""
    samples = []
    for path in paths:
        samples.extend(list(load_benchmark_data(path, format)))
    return samples
