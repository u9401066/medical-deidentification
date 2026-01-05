"""
Presidio Evaluator Integration | Presidio Evaluator 整合

使用 Microsoft Presidio Evaluator 產生合成 PHI 資料並評估

Presidio Evaluator 特點：
- 使用 Faker 產生真實格式的合成資料
- 支援多種 templates 和 entity types
- 可自訂擴充

安裝：
    uv add presidio-evaluator

使用：
    python -m scripts.benchmark.presidio_integration generate --count 100 --output data/benchmark/presidio_test.jsonl
    python -m scripts.benchmark.presidio_integration evaluate --data data/benchmark/presidio_test.jsonl
"""

import argparse
import json
import logging
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

logger = logging.getLogger(__name__)


def check_presidio_installed() -> bool:
    """檢查 presidio-evaluator 是否已安裝"""
    try:
        import presidio_evaluator
        return True
    except ImportError:
        return False


def generate_synthetic_data(
    count: int = 100,
    output_path: Path | None = None,
    locale: str = "en_US",
    templates: list[str] | None = None,
) -> list[dict]:
    """
    使用 Presidio Evaluator 產生合成 PHI 資料
    
    Args:
        count: 產生的樣本數
        output_path: 輸出檔案路徑
        locale: Faker locale (en_US, zh_TW, etc.)
        templates: 使用的 templates (None = 使用預設)
    
    Returns:
        產生的資料列表
    """
    if not check_presidio_installed():
        raise ImportError(
            "presidio-evaluator not installed. Run: uv add presidio-evaluator"
        )

    from presidio_evaluator.data_generator import PresidioDataGenerator
    from presidio_evaluator.data_generator.faker_extensions import (
        FakerSpansResult,
    )

    # 建立 generator
    generator = PresidioDataGenerator(
        locale=locale,
        lower_case_ratio=0.0,  # 保持原始大小寫
    )

    # 使用預設 templates 或自訂
    if templates is None:
        # Presidio Evaluator 內建 templates
        templates = [
            "My name is {{name}} and I live at {{address}}",
            "Contact me at {{phone_number}} or {{email}}",
            "My SSN is {{ssn}} and my credit card is {{credit_card_number}}",
            "Born on {{date_of_birth}}, I work at {{organization}}",
            "Patient {{name}} was admitted on {{date}} with ID {{medical_record_number}}",
            "Send records to {{name}} at {{address}}, phone {{phone_number}}",
            "The patient, {{name}}, age {{age}}, was seen on {{date}}",
            "Insurance ID: {{insurance_id}}, Member: {{name}}",
            "{{name}} scheduled for {{date}} at {{time}} in room {{room_number}}",
            "Doctor {{name}} referred patient to {{organization}}",
        ]

    # 產生資料
    samples = []
    for i in range(count):
        template = templates[i % len(templates)]

        try:
            result: FakerSpansResult = generator.generate(template)

            sample = {
                "id": f"presidio_{i:05d}",
                "full_text": result.full_text,
                "masked": result.masked,
                "spans": [
                    {
                        "entity_type": span.entity_type,
                        "entity_value": span.entity_value,
                        "start_position": span.start_position,
                        "end_position": span.end_position,
                    }
                    for span in result.spans
                ],
                "template": template,
            }
            samples.append(sample)

        except Exception as e:
            logger.warning(f"Failed to generate sample {i}: {e}")

    # 儲存
    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            for sample in samples:
                f.write(json.dumps(sample, ensure_ascii=False) + "\n")

        print(f"✅ 產生 {len(samples)} 筆資料，儲存至 {output_path}")

    return samples


def generate_taiwan_templates() -> list[str]:
    """
    產生台灣醫療情境 templates
    
    注意：需要使用 zh_TW locale 的 Faker
    """
    return [
        "病患{{name}}，身分證號{{id_number}}，於{{date}}就診",
        "{{name}}先生/女士，出生日期{{date_of_birth}}，電話{{phone_number}}",
        "病歷號：{{medical_record_number}}，姓名：{{name}}，地址：{{address}}",
        "主治醫師{{name}}於{{date}}開立處方",
        "轉診單：病患{{name}}轉至{{organization}}{{department}}",
        "聯絡人：{{name}}，手機{{phone_number}}，Email: {{email}}",
        "住院日期：{{date}}，預定出院：{{date}}，病房{{room_number}}",
        "{{name}}（{{age}}歲），健保卡號{{insurance_id}}",
    ]


def run_evaluation(
    data_path: Path,
    model: str = "granite4:1b",
    save_path: Path | None = None,
    limit: int | None = None,
) -> dict:
    """
    使用本專案的 PHI 識別系統評估合成資料
    
    Args:
        data_path: 合成資料路徑
        model: Ollama model 名稱
        save_path: 報告儲存路徑
        limit: 限制樣本數
    
    Returns:
        評估結果摘要
    """
    from scripts.benchmark import PHIEvaluator

    # 嘗試載入專案的 PHI 識別系統
    try:
        from core.infrastructure.dspy import (
            create_phi_identifier_from_yaml as create_phi_identifier,
        )

        # 建立 detector wrapper
        phi_identifier = create_phi_identifier(model_name=model)

        def detector(text: str) -> list[tuple]:
            result = phi_identifier(text)
            if hasattr(result, 'phi_entities'):
                return [(e.text, e.phi_type) for e in result.phi_entities]
            elif hasattr(result, 'entities'):
                return [(e["text"], e["phi_type"]) for e in result.entities]
            return []

    except ImportError:
        # Fallback: 使用簡單的 regex detector 作為示範
        import re

        PATTERNS = {
            "EMAIL": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            "PHONE": r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
            "SSN": r'\b\d{3}-\d{2}-\d{4}\b',
            "DATE": r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',
        }

        def detector(text: str) -> list[tuple]:
            results = []
            for phi_type, pattern in PATTERNS.items():
                for match in re.finditer(pattern, text):
                    results.append((match.group(), phi_type))
            return results

        print("⚠️  使用 regex fallback detector (未載入專案 PHI 識別系統)")

    # 執行評估
    evaluator = PHIEvaluator(detector=detector, match_type="partial")
    report = evaluator.evaluate(
        data_path,
        format="presidio",
        limit=limit,
        save_path=save_path,
    )

    return {
        "precision": report.metrics.overall.precision,
        "recall": report.metrics.overall.recall,
        "f1": report.metrics.overall.f1,
        "samples": report.metrics.total_samples,
    }


def main():
    """CLI 入口點"""
    parser = argparse.ArgumentParser(
        description="Presidio Evaluator 整合工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
範例:
  # 產生合成資料
  python -m scripts.benchmark.presidio_integration generate --count 100
  
  # 評估
  python -m scripts.benchmark.presidio_integration evaluate --data data/benchmark/presidio_test.jsonl
  
  # 完整流程
  python -m scripts.benchmark.presidio_integration full --count 50
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="命令")

    # generate 子命令
    gen_parser = subparsers.add_parser("generate", help="產生合成資料")
    gen_parser.add_argument("--count", "-n", type=int, default=100, help="樣本數")
    gen_parser.add_argument(
        "--output", "-o",
        type=Path,
        default=Path("data/benchmark/presidio_synthetic.jsonl"),
        help="輸出路徑",
    )
    gen_parser.add_argument("--locale", default="en_US", help="Faker locale")

    # evaluate 子命令
    eval_parser = subparsers.add_parser("evaluate", help="評估")
    eval_parser.add_argument("--data", "-d", type=Path, required=True, help="資料路徑")
    eval_parser.add_argument("--model", "-m", default="granite4:1b", help="模型名稱")
    eval_parser.add_argument("--output", "-o", type=Path, help="報告輸出路徑")
    eval_parser.add_argument("--limit", type=int, help="限制樣本數")

    # full 子命令 (產生 + 評估)
    full_parser = subparsers.add_parser("full", help="完整流程 (產生 + 評估)")
    full_parser.add_argument("--count", "-n", type=int, default=50, help="樣本數")
    full_parser.add_argument("--model", "-m", default="granite4:1b", help="模型名稱")

    args = parser.parse_args()

    if args.command == "generate":
        if not check_presidio_installed():
            print("❌ presidio-evaluator 未安裝")
            print("   請執行: uv add presidio-evaluator")
            sys.exit(1)

        generate_synthetic_data(
            count=args.count,
            output_path=args.output,
            locale=args.locale,
        )

    elif args.command == "evaluate":
        result = run_evaluation(
            data_path=args.data,
            model=args.model,
            save_path=args.output,
            limit=args.limit,
        )
        print(f"\n📊 結果: P={result['precision']:.3f} R={result['recall']:.3f} F1={result['f1']:.3f}")

    elif args.command == "full":
        # 產生
        data_path = Path("data/benchmark/presidio_synthetic.jsonl")

        if check_presidio_installed():
            generate_synthetic_data(count=args.count, output_path=data_path)
        else:
            print("❌ presidio-evaluator 未安裝，使用範例資料")
            # 建立簡單範例資料
            data_path.parent.mkdir(parents=True, exist_ok=True)
            with open(data_path, "w") as f:
                samples = [
                    {
                        "id": "sample_1",
                        "full_text": "My name is John Smith and I live at 123 Main St.",
                        "spans": [
                            {"entity_type": "PERSON", "entity_value": "John Smith", "start_position": 11, "end_position": 21},
                            {"entity_type": "ADDRESS", "entity_value": "123 Main St", "start_position": 36, "end_position": 47},
                        ]
                    },
                    {
                        "id": "sample_2",
                        "full_text": "Contact me at 555-123-4567 or john@example.com",
                        "spans": [
                            {"entity_type": "PHONE", "entity_value": "555-123-4567", "start_position": 14, "end_position": 26},
                            {"entity_type": "EMAIL", "entity_value": "john@example.com", "start_position": 30, "end_position": 46},
                        ]
                    },
                ]
                for s in samples:
                    f.write(json.dumps(s) + "\n")

        # 評估
        result = run_evaluation(data_path=data_path, model=args.model)
        print(f"\n📊 結果: P={result['precision']:.3f} R={result['recall']:.3f} F1={result['f1']:.3f}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
