"""Evaluation harness.

Runs the analyzer against labeled samples and measures how well the model
maps activity to MITRE techniques. We score at *parent technique* level
(T1566.001 counts as a hit for T1566) since sub-technique granularity is
where models tend to be optimistic.

Usage:
    python -m eval.benchmark
    python -m eval.benchmark --strict   # require exact sub-technique match
    python -m eval.benchmark --runs 3   # average over multiple runs
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
from tabulate import tabulate

from neural_architect.core.analyzer import Analyzer
from neural_architect.core.models import AttackChain
from neural_architect.llm.gemini_client import GeminiClient, GeminiUnavailableError

ROOT = Path(__file__).resolve().parents[1]
GOLDEN_DIR = ROOT / "eval" / "golden"
RESULTS_DIR = ROOT / "eval" / "results"


def parent_id(technique_id: str) -> str:
    return technique_id.split(".", 1)[0]


def score(predicted: list[str], expected: list[str], *, strict: bool) -> dict:
    pred = set(predicted) if strict else {parent_id(t) for t in predicted}
    exp = set(expected) if strict else {parent_id(t) for t in expected}
    tp = len(pred & exp)
    fp = len(pred - exp)
    fn = len(exp - pred)
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = (
        2 * precision * recall / (precision + recall)
        if (precision + recall)
        else 0.0
    )
    return {
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "predicted": sorted(pred),
        "expected": sorted(exp),
        "missed": sorted(exp - pred),
        "extra": sorted(pred - exp),
    }


def run_one(analyzer: Analyzer, golden_path: Path, *, strict: bool) -> dict:
    spec = json.loads(golden_path.read_text())
    log_path = ROOT / spec["log_file"]
    raw = log_path.read_text()

    start = time.perf_counter()
    chain: AttackChain = analyzer.analyze(raw)
    elapsed = time.perf_counter() - start

    metrics = score(chain.technique_ids, spec["expected_techniques"], strict=strict)
    metrics["name"] = spec["name"]
    metrics["latency_s"] = round(elapsed, 2)
    metrics["severity_predicted"] = chain.severity.value
    metrics["severity_expected"] = spec["expected_severity"]
    metrics["severity_match"] = chain.severity.value == spec["expected_severity"]
    return metrics


def main(argv: list[str] | None = None) -> int:
    load_dotenv()
    parser = argparse.ArgumentParser(description="Run the eval harness.")
    parser.add_argument("--strict", action="store_true",
                        help="Require exact sub-technique match (T1566.001 vs T1566).")
    parser.add_argument("--runs", type=int, default=1,
                        help="Average metrics over this many runs per sample.")
    parser.add_argument("--out", type=Path, default=RESULTS_DIR / "latest.json",
                        help="Where to write JSON results.")
    args = parser.parse_args(argv)

    try:
        analyzer = Analyzer(client=GeminiClient())
    except GeminiUnavailableError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2

    golden_files = sorted(GOLDEN_DIR.glob("*.json"))
    if not golden_files:
        print(f"no golden files in {GOLDEN_DIR}", file=sys.stderr)
        return 3

    all_runs: list[list[dict]] = []
    for run_idx in range(args.runs):
        print(f"\n=== Run {run_idx + 1}/{args.runs} ===")
        results: list[dict] = []
        for gp in golden_files:
            print(f"  • {gp.stem} ...", flush=True)
            try:
                results.append(run_one(analyzer, gp, strict=args.strict))
            except Exception as e:  # noqa: BLE001
                print(f"    failed: {e}")
                results.append({"name": gp.stem, "error": str(e)})
        all_runs.append(results)

    # Average across runs (skipping errored entries)
    aggregated: list[dict] = []
    for i, name in enumerate([r["name"] for r in all_runs[0]]):
        per_run = [run[i] for run in all_runs if "error" not in run[i]]
        if not per_run:
            aggregated.append({"name": name, "error": "all runs failed"})
            continue
        aggregated.append({
            "name": name,
            "precision": round(statistics.mean(r["precision"] for r in per_run), 3),
            "recall": round(statistics.mean(r["recall"] for r in per_run), 3),
            "f1": round(statistics.mean(r["f1"] for r in per_run), 3),
            "latency_s": round(statistics.mean(r["latency_s"] for r in per_run), 2),
            "severity_match_rate": round(
                sum(r["severity_match"] for r in per_run) / len(per_run), 2
            ),
        })

    print("\n=== Summary ===")
    print(tabulate(
        [
            [r.get("name"), r.get("precision", "—"), r.get("recall", "—"),
             r.get("f1", "—"), r.get("latency_s", "—"),
             r.get("severity_match_rate", "—")]
            for r in aggregated
        ],
        headers=["Sample", "Precision", "Recall", "F1", "Latency (s)", "Sev match"],
        tablefmt="github",
    ))

    # Macro averages
    valid = [r for r in aggregated if "error" not in r]
    if valid:
        macro_p = statistics.mean(r["precision"] for r in valid)
        macro_r = statistics.mean(r["recall"] for r in valid)
        macro_f1 = statistics.mean(r["f1"] for r in valid)
        print(f"\nMacro precision: {macro_p:.3f}")
        print(f"Macro recall:    {macro_r:.3f}")
        print(f"Macro F1:        {macro_f1:.3f}")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps({
        "strict": args.strict,
        "runs": args.runs,
        "samples": aggregated,
        "raw_runs": all_runs,
    }, indent=2, default=str))
    print(f"\nWrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
