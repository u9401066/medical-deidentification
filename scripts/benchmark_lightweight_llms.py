#!/usr/bin/env python3
"""
Benchmark Lightweight LLMs for PHI Extraction
輕量 LLM PHI 提取效能評測

Tests JSON output capability and speed for:
- qwen2.5:1.5b (986MB)
- granite4:1b (3.3GB - dense but good at tools)
- llama3.2:1b (1.3GB)
- smollm2:360m (725MB)

Usage:
    python scripts/benchmark_lightweight_llms.py
    python scripts/benchmark_lightweight_llms.py --models qwen2.5:1.5b granite4:1b
    python scripts/benchmark_lightweight_llms.py --runs 5
"""

import json
import re
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


@dataclass
class BenchmarkResult:
    """Single benchmark result"""
    model: str
    test_case: str
    response_time: float  # seconds
    json_valid: bool
    phi_count: int
    phi_correct: int
    phi_expected: int
    raw_output: str
    error: str | None = None


@dataclass
class ModelSummary:
    """Summary for one model"""
    model: str
    avg_response_time: float
    json_success_rate: float
    phi_precision: float
    phi_recall: float
    f1_score: float
    total_runs: int
    results: list = field(default_factory=list)


# Test cases with expected PHI
TEST_CASES = [
    {
        "id": "simple_name",
        "text": "Patient John Smith was admitted on 2024-01-15.",
        "expected_phi": [
            {"text": "John Smith", "type": "NAME"},
            {"text": "2024-01-15", "type": "DATE"},
        ]
    },
    {
        "id": "complex_medical",
        "text": "Dr. Mary Johnson treated patient Wang Wei (MRN: A12345678) at Taipei General Hospital. Contact: 0912-345-678.",
        "expected_phi": [
            {"text": "Mary Johnson", "type": "NAME"},
            {"text": "Wang Wei", "type": "NAME"},
            {"text": "A12345678", "type": "ID"},
            {"text": "Taipei General Hospital", "type": "FACILITY"},
            {"text": "0912-345-678", "type": "PHONE"},
        ]
    },
    {
        "id": "chinese_text",
        "text": "病患陳大明，男性，92歲，住址：台北市信義區松仁路100號，於2024年3月1日入院。",
        "expected_phi": [
            {"text": "陳大明", "type": "NAME"},
            {"text": "92歲", "type": "AGE"},
            {"text": "台北市信義區松仁路100號", "type": "LOCATION"},
            {"text": "2024年3月1日", "type": "DATE"},
        ]
    },
    {
        "id": "email_mixed",
        "text": "Please contact patient's family at john.doe@email.com or call 02-2345-6789. Patient DOB: 1985-06-15.",
        "expected_phi": [
            {"text": "john.doe@email.com", "type": "EMAIL"},
            {"text": "02-2345-6789", "type": "PHONE"},
            {"text": "1985-06-15", "type": "DATE"},
        ]
    },
]


PROMPT_TEMPLATE = """You are a medical PHI (Protected Health Information) extractor.

Identify ALL PHI in the following medical text and return as JSON array.

PHI Types:
- NAME: Patient names, doctor names, family member names
- DATE: Birth dates, admission dates, any specific dates
- AGE: Patient ages (especially over 89)
- PHONE: Phone numbers in any format
- EMAIL: Email addresses
- ID: Medical record numbers, SSN, account numbers
- LOCATION: Addresses, cities (smaller than state/province)
- FACILITY: Hospital names, clinic names

Medical Text:
{text}

Return ONLY a valid JSON array in this exact format (no explanation, no markdown):
[{{"text": "exact PHI text", "type": "PHI_TYPE"}}]

If no PHI found, return: []
JSON:"""


def call_ollama(model: str, prompt: str, timeout: int = 60) -> tuple[str, float, str | None]:
    """
    Call Ollama model and return response with timing
    
    Returns: (response, time_seconds, error_message)
    """
    start = time.time()
    try:
        result = subprocess.run(
            ["ollama", "run", model, prompt],
            check=False, capture_output=True,
            text=True,
            timeout=timeout,
        )
        elapsed = time.time() - start

        if result.returncode != 0:
            return "", elapsed, f"Exit code {result.returncode}: {result.stderr}"

        return result.stdout.strip(), elapsed, None

    except subprocess.TimeoutExpired:
        elapsed = time.time() - start
        return "", elapsed, f"Timeout after {timeout}s"
    except Exception as e:
        elapsed = time.time() - start
        return "", elapsed, str(e)


def parse_json_output(output: str) -> tuple[list, bool]:
    """
    Try to parse JSON from LLM output
    
    Returns: (parsed_list, is_valid_json)
    """
    # Try direct parse first
    try:
        parsed = json.loads(output)
        if isinstance(parsed, list):
            return parsed, True
        return [parsed], True
    except json.JSONDecodeError:
        pass

    # Try to extract JSON array
    match = re.search(r'\[.*?\]', output, re.DOTALL)
    if match:
        try:
            parsed = json.loads(match.group())
            return parsed, True
        except json.JSONDecodeError:
            pass

    # Try to extract JSON objects
    objects = []
    for match in re.finditer(r'\{[^{}]+\}', output):
        try:
            obj = json.loads(match.group())
            objects.append(obj)
        except json.JSONDecodeError:
            continue

    if objects:
        return objects, True  # Partial success

    return [], False


def normalize_type(phi_type: str) -> str:
    """Normalize PHI type for comparison"""
    mapping = {
        "PERSON": "NAME",
        "PATIENT": "NAME",
        "DOCTOR": "NAME",
        "PERSON_NAME": "NAME",
        "PATIENT_NAME": "NAME",
        "DATETIME": "DATE",
        "DOB": "DATE",
        "BIRTHDATE": "DATE",
        "TELEPHONE": "PHONE",
        "PHONE_NUMBER": "PHONE",
        "ADDRESS": "LOCATION",
        "MEDICAL_RECORD": "ID",
        "MRN": "ID",
        "HOSPITAL": "FACILITY",
        "CLINIC": "FACILITY",
    }
    return mapping.get(phi_type.upper(), phi_type.upper())


def evaluate_extraction(
    extracted: list,
    expected: list,
    source_text: str
) -> tuple[int, int, int]:
    """
    Evaluate PHI extraction results
    
    Returns: (correct_count, extracted_count, expected_count)
    """
    correct = 0
    extracted_texts = set()

    for item in extracted:
        text = item.get("text", "")
        if text:
            extracted_texts.add(text.lower())

    for exp in expected:
        exp_text = exp["text"].lower()
        # Check if extracted (fuzzy match)
        for ext_text in extracted_texts:
            if exp_text in ext_text or ext_text in exp_text:
                correct += 1
                break

    return correct, len(extracted), len(expected)


def run_benchmark(
    models: list[str],
    test_cases: list[dict],
    runs_per_case: int = 3,
) -> dict[str, ModelSummary]:
    """Run benchmark for all models"""

    summaries = {}

    for model in models:
        print(f"\n{'='*60}")
        print(f"Testing model: {model}")
        print(f"{'='*60}")

        results = []

        for test in test_cases:
            print(f"\n  Test: {test['id']}")

            for run in range(runs_per_case):
                prompt = PROMPT_TEMPLATE.format(text=test["text"])

                # Call model
                output, elapsed, error = call_ollama(model, prompt)

                if error:
                    print(f"    Run {run+1}: ERROR - {error}")
                    results.append(BenchmarkResult(
                        model=model,
                        test_case=test["id"],
                        response_time=elapsed,
                        json_valid=False,
                        phi_count=0,
                        phi_correct=0,
                        phi_expected=len(test["expected_phi"]),
                        raw_output="",
                        error=error,
                    ))
                    continue

                # Parse JSON
                parsed, json_valid = parse_json_output(output)

                # Evaluate
                correct, extracted, expected = evaluate_extraction(
                    parsed,
                    test["expected_phi"],
                    test["text"]
                )

                print(f"    Run {run+1}: {elapsed:.2f}s | JSON: {'✓' if json_valid else '✗'} | PHI: {correct}/{expected}")

                results.append(BenchmarkResult(
                    model=model,
                    test_case=test["id"],
                    response_time=elapsed,
                    json_valid=json_valid,
                    phi_count=extracted,
                    phi_correct=correct,
                    phi_expected=expected,
                    raw_output=output[:500],
                ))

        # Calculate summary
        valid_results = [r for r in results if r.error is None]

        if valid_results:
            avg_time = sum(r.response_time for r in valid_results) / len(valid_results)
            json_rate = sum(1 for r in valid_results if r.json_valid) / len(valid_results)

            total_correct = sum(r.phi_correct for r in valid_results)
            total_extracted = sum(r.phi_count for r in valid_results)
            total_expected = sum(r.phi_expected for r in valid_results)

            precision = total_correct / total_extracted if total_extracted > 0 else 0
            recall = total_correct / total_expected if total_expected > 0 else 0
            f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
        else:
            avg_time = 0
            json_rate = 0
            precision = recall = f1 = 0

        summaries[model] = ModelSummary(
            model=model,
            avg_response_time=avg_time,
            json_success_rate=json_rate,
            phi_precision=precision,
            phi_recall=recall,
            f1_score=f1,
            total_runs=len(results),
            results=results,
        )

    return summaries


def print_summary(summaries: dict[str, ModelSummary]) -> None:
    """Print benchmark summary table"""
    print("\n")
    print("=" * 90)
    print("BENCHMARK SUMMARY - Lightweight LLMs for PHI Extraction")
    print("=" * 90)
    print(f"{'Model':<20} {'Avg Time':>10} {'JSON %':>10} {'Precision':>10} {'Recall':>10} {'F1':>10}")
    print("-" * 90)

    # Sort by F1 score
    sorted_models = sorted(
        summaries.values(),
        key=lambda x: x.f1_score,
        reverse=True
    )

    for s in sorted_models:
        print(f"{s.model:<20} {s.avg_response_time:>9.2f}s {s.json_success_rate*100:>9.1f}% {s.phi_precision*100:>9.1f}% {s.phi_recall*100:>9.1f}% {s.f1_score*100:>9.1f}%")

    print("-" * 90)

    # Winner
    if sorted_models:
        winner = sorted_models[0]
        fastest = min(summaries.values(), key=lambda x: x.avg_response_time if x.avg_response_time > 0 else float('inf'))

        print(f"\n🏆 Best Quality: {winner.model} (F1: {winner.f1_score*100:.1f}%)")
        print(f"⚡ Fastest: {fastest.model} ({fastest.avg_response_time:.2f}s avg)")

        # Recommendation
        print("\n📋 Recommendation:")
        for s in sorted_models:
            if s.f1_score >= 0.5 and s.json_success_rate >= 0.8:
                print(f"   ✅ {s.model} - Good balance of quality and JSON reliability")
            elif s.avg_response_time < 5 and s.json_success_rate >= 0.6:
                print(f"   ⚡ {s.model} - Fast but may need post-processing")


def save_results(summaries: dict[str, ModelSummary], output_path: str) -> None:
    """Save detailed results to JSON"""
    data = {}
    for model, summary in summaries.items():
        data[model] = {
            "avg_response_time": summary.avg_response_time,
            "json_success_rate": summary.json_success_rate,
            "phi_precision": summary.phi_precision,
            "phi_recall": summary.phi_recall,
            "f1_score": summary.f1_score,
            "total_runs": summary.total_runs,
            "results": [
                {
                    "test_case": r.test_case,
                    "response_time": r.response_time,
                    "json_valid": r.json_valid,
                    "phi_correct": r.phi_correct,
                    "phi_expected": r.phi_expected,
                    "raw_output": r.raw_output,
                    "error": r.error,
                }
                for r in summary.results
            ]
        }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"\n📄 Detailed results saved to: {output_path}")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Benchmark lightweight LLMs for PHI extraction")
    parser.add_argument(
        "--models",
        nargs="+",
        default=["qwen2.5:1.5b", "granite4:1b", "llama3.2:1b", "smollm2:360m"],
        help="Models to test"
    )
    parser.add_argument(
        "--runs",
        type=int,
        default=2,
        help="Runs per test case"
    )
    parser.add_argument(
        "--output",
        default="data/output/benchmark_llm_results.json",
        help="Output file for detailed results"
    )

    args = parser.parse_args()

    print("🔬 Lightweight LLM Benchmark for PHI Extraction")
    print(f"   Models: {', '.join(args.models)}")
    print(f"   Test cases: {len(TEST_CASES)}")
    print(f"   Runs per case: {args.runs}")

    # Run benchmark
    summaries = run_benchmark(
        models=args.models,
        test_cases=TEST_CASES,
        runs_per_case=args.runs,
    )

    # Print summary
    print_summary(summaries)

    # Save results
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    save_results(summaries, str(output_path))


if __name__ == "__main__":
    main()
