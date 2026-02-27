"""Quality checks for the many-pyintact-to-nemo use case."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

PASS = "PASS"
FAIL = "FAIL"

SUCCESS_STATES = {"succeeded", "completed", "success", "done"}
FAILURE_STATES = {"failed", "error", "cancelled", "canceled", "timed_out", "timeout"}


@dataclass(frozen=True)
class CheckResult:
    name: str
    status: str
    target: str
    actual: str
    detail: str


def load_json(path: str | Path) -> Any:
    return json.loads(Path(path).read_text())


def _pct(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return 100.0 * numerator / denominator


def check_campaign_throughput(
    manifest_rows: list[dict[str, Any]],
    min_successes: int = 10,
    max_failure_rate_pct: float = 20.0,
) -> list[CheckResult]:
    total = len(manifest_rows)
    statuses = [str(row.get("status", "")).strip().lower() for row in manifest_rows]
    success_count = sum(1 for s in statuses if s in SUCCESS_STATES)
    failure_count = sum(1 for s in statuses if s in FAILURE_STATES)
    failure_rate_pct = _pct(failure_count, total)

    enough_successes = success_count >= min_successes
    failure_rate_ok = failure_rate_pct <= max_failure_rate_pct

    return [
        CheckResult(
            name="Successful simulations",
            status=PASS if enough_successes else FAIL,
            target=f">= {min_successes} cases",
            actual=f"{success_count} cases",
            detail=f"{success_count}/{total} cases finished in success states",
        ),
        CheckResult(
            name="Failure rate",
            status=PASS if failure_rate_ok else FAIL,
            target=f"<= {max_failure_rate_pct:.1f}%",
            actual=f"{failure_rate_pct:.1f}%",
            detail=f"{failure_count}/{total} cases in failure states",
        ),
    ]


def check_dataset_readiness(
    dataset_summary: dict[str, Any],
    min_samples: int = 10,
) -> list[CheckResult]:
    samples_ready = int(dataset_summary.get("samples_ready", 0))
    schema_valid = bool(dataset_summary.get("schema_valid", False))

    return [
        CheckResult(
            name="Dataset samples ready",
            status=PASS if samples_ready >= min_samples else FAIL,
            target=f">= {min_samples}",
            actual=str(samples_ready),
            detail="Count of samples available after filtering failed cases",
        ),
        CheckResult(
            name="Dataset schema validation",
            status=PASS if schema_valid else FAIL,
            target="true",
            actual=str(schema_valid).lower(),
            detail="All required fields/units present for training tensors",
        ),
    ]


def check_surrogate_metrics(
    metrics: dict[str, Any],
    max_normalized_mae: float = 0.08,
    min_r2: float = 0.90,
) -> list[CheckResult]:
    mae = float(metrics.get("val_normalized_mae", 999.0))
    r2 = float(metrics.get("val_r2", -1.0))

    return [
        CheckResult(
            name="Surrogate val normalized MAE",
            status=PASS if mae <= max_normalized_mae else FAIL,
            target=f"<= {max_normalized_mae:.2f}",
            actual=f"{mae:.2f}",
            detail="Lower is better",
        ),
        CheckResult(
            name="Surrogate val R2",
            status=PASS if r2 >= min_r2 else FAIL,
            target=f">= {min_r2:.2f}",
            actual=f"{r2:.2f}",
            detail="Higher is better",
        ),
    ]


def run_all_checks(
    manifest_rows: list[dict[str, Any]],
    dataset_summary: dict[str, Any],
    metrics: dict[str, Any],
) -> list[CheckResult]:
    results: list[CheckResult] = []
    results.extend(check_campaign_throughput(manifest_rows))
    results.extend(check_dataset_readiness(dataset_summary))
    results.extend(check_surrogate_metrics(metrics))
    return results


def format_report(results: list[CheckResult]) -> str:
    lines = []
    for result in results:
        status_text = result.status.ljust(4)
        lines.append(
            f"- {result.name:30} {status_text} "
            f"(target: {result.target}, actual: {result.actual})"
        )
    passed = sum(1 for r in results if r.status == PASS)
    lines.append(f"\nSummary: {passed}/{len(results)} checks passed")
    return "\n".join(lines)


def main() -> None:
    base_dir = Path(__file__).resolve().parent / "example-output"
    manifest = load_json(base_dir / "campaign_jobs_final.json")
    dataset = load_json(base_dir / "dataset_summary_final.json")
    metrics = load_json(base_dir / "surrogate_metrics_final.json")

    results = run_all_checks(manifest, dataset, metrics)
    print(format_report(results))


if __name__ == "__main__":
    main()
