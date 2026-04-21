"""Benchmark trend delta helpers."""

from __future__ import annotations

import hashlib


def build_benchmark_trend_delta(
    *,
    benchmark_trend_entry: dict[str, object],
    previous_benchmark_trend_entry: dict[str, object] | None = None,
) -> dict[str, object]:
    previous = previous_benchmark_trend_entry or {}
    current_key = str(benchmark_trend_entry.get("trend_key") or "unknown")
    previous_key = str(previous.get("trend_key") or "")
    has_previous = bool(previous_key)
    current_score = _metric_int(benchmark_trend_entry.get("outcome_score_percent"))
    previous_score = _metric_int(previous.get("outcome_score_percent"))
    score_delta = current_score - previous_score if has_previous else 0
    current_duration_ms = _timing_total_ms(benchmark_trend_entry.get("timing"))
    previous_duration_ms = _timing_total_ms(previous.get("timing"))
    duration_delta_ms = current_duration_ms - previous_duration_ms if has_previous else 0
    current_status = str(benchmark_trend_entry.get("trend_status") or "unknown")
    previous_status = str(previous.get("trend_status") or "none")

    checks = (
        _check(
            check_id="current-trend-contract",
            passed=str(benchmark_trend_entry.get("contract") or "") == "benchmark-trend-entry/v1",
            reason=(
                "Current trend entry contract is benchmark-trend-entry/v1."
                if str(benchmark_trend_entry.get("contract") or "") == "benchmark-trend-entry/v1"
                else (
                    "Current trend entry contract is "
                    f"`{benchmark_trend_entry.get('contract') or 'missing'}`."
                )
            ),
        ),
        _check(
            check_id="previous-trend-contract",
            passed=(not has_previous) or str(previous.get("contract") or "") == "benchmark-trend-entry/v1",
            reason=(
                "No previous trend entry provided."
                if not has_previous
                else (
                    "Previous trend entry contract is benchmark-trend-entry/v1."
                    if str(previous.get("contract") or "") == "benchmark-trend-entry/v1"
                    else (
                        "Previous trend entry contract is "
                        f"`{previous.get('contract') or 'missing'}`."
                    )
                )
            ),
        ),
    )
    failed_checks = tuple(check for check in checks if not bool(check.get("passed")))
    delta_ready = len(failed_checks) == 0

    delta_status = _delta_status(
        delta_ready=delta_ready,
        has_previous=has_previous,
        current_status=current_status,
        previous_status=previous_status,
        score_delta=score_delta,
        duration_delta_ms=duration_delta_ms,
    )

    status_transition = f"{previous_status}->{current_status}" if has_previous else "none->" + current_status
    delta_key = _delta_key(
        current_key=current_key,
        previous_key=previous_key,
        delta_status=delta_status,
        score_delta=score_delta,
        duration_delta_ms=duration_delta_ms,
    )

    return {
        "contract": "benchmark-trend-delta/v1",
        "profile": "phase16-trend-delta/v1",
        "delta_key": delta_key,
        "delta_ready": delta_ready,
        "has_previous": has_previous,
        "delta_status": delta_status,
        "status_transition": status_transition,
        "current_trend_key": current_key,
        "previous_trend_key": previous_key if has_previous else None,
        "current_outcome_score_percent": current_score,
        "previous_outcome_score_percent": previous_score if has_previous else None,
        "score_delta": score_delta,
        "current_duration_ms": current_duration_ms,
        "previous_duration_ms": previous_duration_ms if has_previous else None,
        "duration_delta_ms": duration_delta_ms,
        "check_count": len(checks),
        "failed_check_count": len(failed_checks),
        "failed_check_ids": tuple(str(check.get("id") or "") for check in failed_checks),
        "checks": checks,
        "next_delta_action": _next_delta_action(
            delta_ready=delta_ready,
            delta_status=delta_status,
            has_previous=has_previous,
        ),
        "summary": (
            f"Trend delta `{delta_status}` with score delta {score_delta} and "
            f"duration delta {duration_delta_ms} ms."
        ),
    }


def _delta_status(
    *,
    delta_ready: bool,
    has_previous: bool,
    current_status: str,
    previous_status: str,
    score_delta: int,
    duration_delta_ms: int,
) -> str:
    if not delta_ready:
        return "blocked"
    if not has_previous:
        return "no_baseline"
    if current_status == "degradation_alert":
        return "regression"
    if score_delta > 0 and duration_delta_ms <= 0:
        return "improvement"
    if score_delta < 0 or duration_delta_ms > 0:
        return "regression"
    if current_status == previous_status:
        return "stable"
    return "stable"


def _next_delta_action(*, delta_ready: bool, delta_status: str, has_previous: bool) -> str:
    if not delta_ready:
        return "Resolve failed trend-delta dependency checks."
    if not has_previous:
        return "Persist current trend entry and wait for next run to compute baseline delta."
    if delta_status == "improvement":
        return "Record improvement and continue trend capture cadence."
    if delta_status == "regression":
        return "Open regression remediation workflow from trend-delta signal."
    return "Trend delta stable; continue scheduled benchmark runs."


def _delta_key(
    *,
    current_key: str,
    previous_key: str,
    delta_status: str,
    score_delta: int,
    duration_delta_ms: int,
) -> str:
    basis = f"{current_key}|{previous_key}|{delta_status}|{score_delta}|{duration_delta_ms}"
    digest = hashlib.sha256(basis.encode("utf-8")).hexdigest()[:12]
    return f"trend-delta-{digest}"


def _timing_total_ms(value: object) -> int:
    if not isinstance(value, dict):
        return 0
    raw = value.get("total_duration_ms")
    if isinstance(raw, bool):
        return int(raw)
    if isinstance(raw, (int, float)):
        return max(0, int(raw))
    return 0


def _metric_int(value: object) -> int:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, (int, float)):
        return int(value)
    return 0


def _check(*, check_id: str, passed: bool, reason: str) -> dict[str, object]:
    return {
        "id": check_id,
        "passed": passed,
        "reason": reason,
    }
