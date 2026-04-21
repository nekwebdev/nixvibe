"""Benchmark trend entry helpers."""

from __future__ import annotations

import hashlib


def build_benchmark_trend_entry(
    *,
    run_manifest: dict[str, object],
    run_telemetry: dict[str, object],
    benchmark_baseline_snapshot: dict[str, object],
    outcome_scorecard: dict[str, object],
    benchmark_release_readiness: dict[str, object],
) -> dict[str, object]:
    route = str(run_manifest.get("route") or "unknown")
    selected_mode = _selected_mode(run_manifest)
    total_duration_ms = _metric_ms(run_telemetry.get("total_duration_ms"))
    snapshot_id = str(benchmark_baseline_snapshot.get("snapshot_id") or "unknown")
    trend_bucket = str(benchmark_baseline_snapshot.get("trend_bucket") or "unknown")
    baseline_recordable = bool(benchmark_baseline_snapshot.get("baseline_recordable", False))
    regression_detected = bool(benchmark_baseline_snapshot.get("regression_detected", False))
    outcome_status = str(outcome_scorecard.get("overall_status") or "unknown")
    outcome_score_percent = _metric_int(outcome_scorecard.get("score_percent"))
    benchmark_release_ready = bool(benchmark_release_readiness.get("ready", False))

    checks = (
        _check(
            check_id="snapshot-contract",
            passed=str(benchmark_baseline_snapshot.get("contract") or "")
            == "benchmark-baseline-snapshot/v1",
            reason=(
                "Benchmark baseline snapshot contract is benchmark-baseline-snapshot/v1."
                if str(benchmark_baseline_snapshot.get("contract") or "")
                == "benchmark-baseline-snapshot/v1"
                else (
                    "Benchmark baseline snapshot contract is "
                    f"`{benchmark_baseline_snapshot.get('contract') or 'missing'}`."
                )
            ),
        ),
        _check(
            check_id="outcome-contract",
            passed=str(outcome_scorecard.get("contract") or "") == "outcome-scorecard/v1",
            reason=(
                "Outcome scorecard contract is outcome-scorecard/v1."
                if str(outcome_scorecard.get("contract") or "") == "outcome-scorecard/v1"
                else f"Outcome scorecard contract is `{outcome_scorecard.get('contract') or 'missing'}`."
            ),
        ),
        _check(
            check_id="benchmark-release-contract",
            passed=str(benchmark_release_readiness.get("contract") or "")
            == "benchmark-release-readiness/v1",
            reason=(
                "Benchmark release readiness contract is benchmark-release-readiness/v1."
                if str(benchmark_release_readiness.get("contract") or "")
                == "benchmark-release-readiness/v1"
                else (
                    "Benchmark release readiness contract is "
                    f"`{benchmark_release_readiness.get('contract') or 'missing'}`."
                )
            ),
        ),
        _check(
            check_id="telemetry-contract",
            passed=str(run_telemetry.get("contract") or "") == "run-telemetry/v1",
            reason=(
                "Run telemetry contract is run-telemetry/v1."
                if str(run_telemetry.get("contract") or "") == "run-telemetry/v1"
                else f"Run telemetry contract is `{run_telemetry.get('contract') or 'missing'}`."
            ),
        ),
    )
    failed_checks = tuple(check for check in checks if not bool(check.get("passed")))
    trend_entry_ready = len(failed_checks) == 0
    trend_status = _trend_status(
        trend_entry_ready=trend_entry_ready,
        baseline_recordable=baseline_recordable,
        regression_detected=regression_detected,
        outcome_status=outcome_status,
        outcome_score_percent=outcome_score_percent,
        benchmark_release_ready=benchmark_release_ready,
    )
    trend_key = _trend_key(
        route=route,
        mode=selected_mode,
        snapshot_id=snapshot_id,
        trend_bucket=trend_bucket,
        outcome_status=outcome_status,
        outcome_score_percent=outcome_score_percent,
        benchmark_release_ready=benchmark_release_ready,
        total_duration_ms=total_duration_ms,
    )

    return {
        "contract": "benchmark-trend-entry/v1",
        "profile": "phase16-trend-entry/v1",
        "trend_key": trend_key,
        "trend_entry_ready": trend_entry_ready,
        "trend_status": trend_status,
        "route": route,
        "mode": selected_mode,
        "snapshot_id": snapshot_id,
        "trend_bucket": trend_bucket,
        "baseline_recordable": baseline_recordable,
        "regression_detected": regression_detected,
        "outcome_status": outcome_status,
        "outcome_score_percent": outcome_score_percent,
        "benchmark_release_ready": benchmark_release_ready,
        "timing": {
            "total_duration_ms": total_duration_ms,
            "duration_band": _duration_band(total_duration_ms),
        },
        "check_count": len(checks),
        "failed_check_count": len(failed_checks),
        "failed_check_ids": tuple(str(check.get("id") or "") for check in failed_checks),
        "checks": checks,
        "next_trend_action": _next_trend_action(
            trend_entry_ready=trend_entry_ready,
            trend_status=trend_status,
            regression_detected=regression_detected,
        ),
        "summary": (
            f"Trend entry `{trend_status}` with score {outcome_score_percent}% "
            f"and duration band `{_duration_band(total_duration_ms)}`."
        ),
    }


def _trend_status(
    *,
    trend_entry_ready: bool,
    baseline_recordable: bool,
    regression_detected: bool,
    outcome_status: str,
    outcome_score_percent: int,
    benchmark_release_ready: bool,
) -> str:
    if not trend_entry_ready:
        return "blocked"
    if regression_detected or outcome_status == "at_risk" or outcome_score_percent < 50:
        return "degradation_alert"
    if baseline_recordable and benchmark_release_ready and outcome_score_percent >= 80:
        return "improving_candidate"
    return "stable_watch"


def _next_trend_action(
    *,
    trend_entry_ready: bool,
    trend_status: str,
    regression_detected: bool,
) -> str:
    if not trend_entry_ready:
        return "Resolve failed trend-entry dependency checks."
    if trend_status == "improving_candidate":
        return "Persist trend entry for baseline progression tracking."
    if regression_detected:
        return "Investigate regression before promoting trend status."
    if trend_status == "degradation_alert":
        return "Open remediation path for degraded outcome score or release signal."
    return "Monitor trend entry and gather additional benchmark runs."


def _selected_mode(run_manifest: dict[str, object]) -> str:
    modes = run_manifest.get("modes")
    if isinstance(modes, dict):
        return str(modes.get("selected") or "unknown")
    return "unknown"


def _trend_key(
    *,
    route: str,
    mode: str,
    snapshot_id: str,
    trend_bucket: str,
    outcome_status: str,
    outcome_score_percent: int,
    benchmark_release_ready: bool,
    total_duration_ms: int,
) -> str:
    basis = (
        f"{route}|{mode}|{snapshot_id}|{trend_bucket}|{outcome_status}|"
        f"{outcome_score_percent}|{int(benchmark_release_ready)}|{total_duration_ms}"
    )
    digest = hashlib.sha256(basis.encode("utf-8")).hexdigest()[:12]
    return f"trend-{digest}"


def _duration_band(total_duration_ms: int) -> str:
    if total_duration_ms <= 1_000:
        return "fast"
    if total_duration_ms <= 10_000:
        return "moderate"
    return "slow"


def _check(*, check_id: str, passed: bool, reason: str) -> dict[str, object]:
    return {
        "id": check_id,
        "passed": passed,
        "reason": reason,
    }


def _metric_ms(value: object) -> int:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, (int, float)):
        return max(0, int(value))
    return 0


def _metric_int(value: object) -> int:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, (int, float)):
        return int(value)
    return 0
