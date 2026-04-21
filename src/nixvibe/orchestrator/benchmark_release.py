"""Benchmark-aware release readiness helpers."""

from __future__ import annotations


def build_benchmark_release_readiness(
    *,
    release_readiness: dict[str, object],
    outcome_scorecard: dict[str, object],
    benchmark_baseline_snapshot: dict[str, object],
    benchmark_runner_report: dict[str, object],
    telemetry_regression: dict[str, object],
) -> dict[str, object]:
    base_release_ready = bool(release_readiness.get("ready", False))
    scorecard_ready = bool(outcome_scorecard.get("scorecard_ready", False))
    score_percent = _metric_int(outcome_scorecard.get("score_percent"))
    regression_detected = bool(telemetry_regression.get("regression_detected", False))
    baseline_recordable = bool(benchmark_baseline_snapshot.get("baseline_recordable", False))
    trend_bucket = str(benchmark_baseline_snapshot.get("trend_bucket") or "unknown")
    runner_ready = bool(benchmark_runner_report.get("ready_to_execute", False))

    gates = (
        _gate(
            gate_id="release-ready-base",
            passed=base_release_ready,
            reason=(
                "Base release readiness gates passed."
                if base_release_ready
                else "Base release readiness gates are not ready."
            ),
            severity="critical",
        ),
        _gate(
            gate_id="outcome-scorecard-ready",
            passed=scorecard_ready,
            reason=(
                "Outcome scorecard dependency checks passed."
                if scorecard_ready
                else "Outcome scorecard dependency checks failed."
            ),
            severity="high",
        ),
        _gate(
            gate_id="outcome-score-threshold",
            passed=score_percent >= 80,
            reason=(
                f"Outcome score {score_percent}% meets threshold."
                if score_percent >= 80
                else f"Outcome score {score_percent}% below threshold 80%."
            ),
            severity="high",
        ),
        _gate(
            gate_id="regression-clear",
            passed=not regression_detected,
            reason=(
                "No telemetry regression detected."
                if not regression_detected
                else "Telemetry regression detected."
            ),
            severity="critical",
        ),
        _gate(
            gate_id="baseline-candidate",
            passed=baseline_recordable and trend_bucket == "baseline-candidate",
            reason=(
                "Baseline snapshot is recordable candidate."
                if baseline_recordable and trend_bucket == "baseline-candidate"
                else (
                    "Baseline snapshot is not baseline-candidate "
                    f"(baseline_recordable={baseline_recordable}, trend_bucket={trend_bucket})."
                )
            ),
            severity="high",
        ),
        _gate(
            gate_id="runner-ready",
            passed=runner_ready,
            reason=(
                "Benchmark runner plan is ready."
                if runner_ready
                else "Benchmark runner plan is not ready."
            ),
            severity="medium",
        ),
    )

    failed_gates = tuple(gate for gate in gates if not bool(gate.get("passed")))
    ready = len(failed_gates) == 0

    return {
        "contract": "benchmark-release-readiness/v1",
        "ready": ready,
        "status": "ready" if ready else "blocked",
        "base_release_ready": base_release_ready,
        "outcome_score_percent": score_percent,
        "regression_detected": regression_detected,
        "trend_bucket": trend_bucket,
        "runner_ready": runner_ready,
        "gate_count": len(gates),
        "failed_gate_count": len(failed_gates),
        "failed_gate_ids": tuple(str(gate.get("id") or "") for gate in failed_gates),
        "gates": gates,
        "next_action": (
            "Benchmark-aware release readiness passed. Proceed to milestone closeout flow."
            if ready
            else "Benchmark-aware release blocked. Resolve failed benchmark gates before closeout."
        ),
    }


def _gate(*, gate_id: str, passed: bool, reason: str, severity: str) -> dict[str, object]:
    return {
        "id": gate_id,
        "passed": passed,
        "reason": reason,
        "severity": severity,
    }


def _metric_int(value: object) -> int:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, (int, float)):
        return max(0, int(value))
    return 0
