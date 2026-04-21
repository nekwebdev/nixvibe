"""Outcome alert helpers built from benchmark trend contracts."""

from __future__ import annotations


def build_outcome_alert(
    *,
    benchmark_trend_entry: dict[str, object],
    benchmark_trend_history: dict[str, object],
    benchmark_trend_delta: dict[str, object],
) -> dict[str, object]:
    trend_status = str(benchmark_trend_entry.get("trend_status") or "unknown")
    delta_status = str(benchmark_trend_delta.get("delta_status") or "unknown")
    history_status = str(benchmark_trend_history.get("history_status") or "unknown")

    checks = (
        _check(
            check_id="trend-entry-contract",
            passed=str(benchmark_trend_entry.get("contract") or "") == "benchmark-trend-entry/v1",
            reason=(
                "Benchmark trend entry contract is benchmark-trend-entry/v1."
                if str(benchmark_trend_entry.get("contract") or "") == "benchmark-trend-entry/v1"
                else f"Benchmark trend entry contract is `{benchmark_trend_entry.get('contract') or 'missing'}`."
            ),
        ),
        _check(
            check_id="trend-history-contract",
            passed=str(benchmark_trend_history.get("contract") or "") == "benchmark-trend-history/v1",
            reason=(
                "Benchmark trend history contract is benchmark-trend-history/v1."
                if str(benchmark_trend_history.get("contract") or "") == "benchmark-trend-history/v1"
                else (
                    f"Benchmark trend history contract is `{benchmark_trend_history.get('contract') or 'missing'}`."
                )
            ),
        ),
        _check(
            check_id="trend-delta-contract",
            passed=str(benchmark_trend_delta.get("contract") or "") == "benchmark-trend-delta/v1",
            reason=(
                "Benchmark trend delta contract is benchmark-trend-delta/v1."
                if str(benchmark_trend_delta.get("contract") or "") == "benchmark-trend-delta/v1"
                else f"Benchmark trend delta contract is `{benchmark_trend_delta.get('contract') or 'missing'}`."
            ),
        ),
    )
    failed_checks = tuple(check for check in checks if not bool(check.get("passed")))
    alert_ready = len(failed_checks) == 0

    trigger_ids = _trigger_ids(
        alert_ready=alert_ready,
        trend_status=trend_status,
        delta_status=delta_status,
        history_status=history_status,
        benchmark_release_ready=bool(benchmark_trend_entry.get("benchmark_release_ready")),
    )
    alert_status = _alert_status(alert_ready=alert_ready, trigger_ids=trigger_ids)

    return {
        "contract": "outcome-alert/v1",
        "profile": "phase17-outcome-alert/v1",
        "alert_ready": alert_ready,
        "alert_status": alert_status,
        "severity": _severity(alert_status),
        "requires_operator_attention": alert_status in {"warning", "critical", "blocked"},
        "trend_status": trend_status,
        "delta_status": delta_status,
        "history_status": history_status,
        "trigger_count": len(trigger_ids),
        "trigger_ids": trigger_ids,
        "check_count": len(checks),
        "failed_check_count": len(failed_checks),
        "failed_check_ids": tuple(str(check.get("id") or "") for check in failed_checks),
        "checks": checks,
        "next_alert_action": _next_alert_action(alert_status=alert_status),
        "summary": f"Outcome alert `{alert_status}` with {len(trigger_ids)} trigger(s).",
    }


def _alert_status(*, alert_ready: bool, trigger_ids: tuple[str, ...]) -> str:
    if not alert_ready:
        return "blocked"
    if any(trigger.startswith("critical:") for trigger in trigger_ids):
        return "critical"
    if trigger_ids:
        return "warning"
    return "none"


def _trigger_ids(
    *,
    alert_ready: bool,
    trend_status: str,
    delta_status: str,
    history_status: str,
    benchmark_release_ready: bool,
) -> tuple[str, ...]:
    if not alert_ready:
        return ()

    triggers: list[str] = []
    if trend_status == "degradation_alert":
        triggers.append("critical:trend-degradation")
    if delta_status == "regression":
        triggers.append("critical:delta-regression")
    if history_status == "blocked":
        triggers.append("critical:history-blocked")

    if delta_status == "no_baseline":
        triggers.append("warning:no-baseline")
    if trend_status == "stable_watch":
        triggers.append("warning:stable-watch")
    if not benchmark_release_ready:
        triggers.append("warning:release-not-ready")

    return tuple(triggers)


def _next_alert_action(*, alert_status: str) -> str:
    if alert_status == "blocked":
        return "Resolve failed outcome-alert dependency checks."
    if alert_status == "critical":
        return "Escalate critical outcome alert and hold apply/release promotion."
    if alert_status == "warning":
        return "Track warning alerts and evaluate policy-gate impact."
    return "No active outcome alert; continue benchmark trend capture cadence."


def _severity(alert_status: str) -> str:
    if alert_status in {"blocked", "critical"}:
        return "critical"
    if alert_status == "warning":
        return "warning"
    return "info"


def _check(*, check_id: str, passed: bool, reason: str) -> dict[str, object]:
    return {
        "id": check_id,
        "passed": passed,
        "reason": reason,
    }
