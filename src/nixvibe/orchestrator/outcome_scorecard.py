"""Outcome scorecard contract helpers."""

from __future__ import annotations


def build_outcome_scorecard(
    *,
    benchmark_scenario_catalog: dict[str, object],
    benchmark_runner_report: dict[str, object],
    benchmark_baseline_snapshot: dict[str, object],
    release_readiness: dict[str, object],
    telemetry_regression: dict[str, object],
) -> dict[str, object]:
    release_ready = bool(release_readiness.get("ready", False))
    regression_detected = bool(telemetry_regression.get("regression_detected", False))
    baseline_recordable = bool(benchmark_baseline_snapshot.get("baseline_recordable", False))
    runner_ready = bool(benchmark_runner_report.get("ready_to_execute", False))
    trend_bucket = str(benchmark_baseline_snapshot.get("trend_bucket") or "unknown")

    scaffold_estimate_ms = _scenario_estimate_ms(
        scenarios=benchmark_scenario_catalog.get("scenarios"),
        scenario_id="init-apply-scaffold",
    )
    modularization_estimate_ms = _scenario_estimate_ms(
        scenarios=benchmark_scenario_catalog.get("scenarios"),
        scenario_id="audit-apply-refactor",
    )

    metrics = (
        _time_metric(
            metric_id="new-host-scaffold-time",
            description="New host scaffold benchmark estimate under 30 minutes.",
            target_ms=1_800_000,
            actual_ms=scaffold_estimate_ms,
            weight=30,
        ),
        _time_metric(
            metric_id="existing-config-modularization",
            description="Existing config modularization benchmark estimate under 2 hours with release-ready signal.",
            target_ms=7_200_000,
            actual_ms=modularization_estimate_ms,
            weight=40,
            additional_gate=release_ready,
            additional_gate_reason=(
                "release readiness is true" if release_ready else "release readiness is false"
            ),
        ),
        _flag_metric(
            metric_id="service-add-without-core-edits",
            description="Service-add confidence requires recordable baseline, no regression, and runner readiness.",
            weight=30,
            passed=baseline_recordable and not regression_detected and runner_ready,
            reason=(
                "Baseline recordable, regression clear, and runner ready."
                if baseline_recordable and not regression_detected and runner_ready
                else (
                    "Service-add confidence blocked by "
                    f"baseline_recordable={baseline_recordable}, "
                    f"regression_detected={regression_detected}, "
                    f"runner_ready={runner_ready}."
                )
            ),
            details={
                "baseline_recordable": baseline_recordable,
                "regression_detected": regression_detected,
                "runner_ready": runner_ready,
            },
        ),
    )

    checks = (
        _check(
            check_id="scenario-catalog-contract",
            passed=str(benchmark_scenario_catalog.get("contract") or "")
            == "benchmark-scenario-catalog/v1",
            reason=(
                "Benchmark scenario catalog contract is benchmark-scenario-catalog/v1."
                if str(benchmark_scenario_catalog.get("contract") or "")
                == "benchmark-scenario-catalog/v1"
                else (
                    "Benchmark scenario catalog contract is "
                    f"`{benchmark_scenario_catalog.get('contract') or 'missing'}`."
                )
            ),
        ),
        _check(
            check_id="runner-report-contract",
            passed=str(benchmark_runner_report.get("contract") or "") == "benchmark-runner-report/v1",
            reason=(
                "Benchmark runner report contract is benchmark-runner-report/v1."
                if str(benchmark_runner_report.get("contract") or "")
                == "benchmark-runner-report/v1"
                else (
                    "Benchmark runner report contract is "
                    f"`{benchmark_runner_report.get('contract') or 'missing'}`."
                )
            ),
        ),
        _check(
            check_id="baseline-snapshot-contract",
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
            check_id="release-readiness-contract",
            passed=str(release_readiness.get("contract") or "") == "release-readiness/v1",
            reason=(
                "Release readiness contract is release-readiness/v1."
                if str(release_readiness.get("contract") or "") == "release-readiness/v1"
                else f"Release readiness contract is `{release_readiness.get('contract') or 'missing'}`."
            ),
        ),
        _check(
            check_id="telemetry-regression-contract",
            passed=str(telemetry_regression.get("contract") or "") == "telemetry-regression/v1",
            reason=(
                "Telemetry regression contract is telemetry-regression/v1."
                if str(telemetry_regression.get("contract") or "") == "telemetry-regression/v1"
                else (
                    "Telemetry regression contract is "
                    f"`{telemetry_regression.get('contract') or 'missing'}`."
                )
            ),
        ),
    )

    achieved_score = sum(int(metric["score"]) for metric in metrics)
    max_score = sum(int(metric["weight"]) for metric in metrics)
    failed_metric_ids = tuple(
        str(metric["id"]) for metric in metrics if not bool(metric.get("passed"))
    )
    failed_checks = tuple(check for check in checks if not bool(check.get("passed")))
    scorecard_ready = len(failed_checks) == 0
    overall_status = _overall_status(
        scorecard_ready=scorecard_ready,
        achieved_score=achieved_score,
        max_score=max_score,
        release_ready=release_ready,
        regression_detected=regression_detected,
    )

    return {
        "contract": "outcome-scorecard/v1",
        "profile": "phase15-success-metrics/v1",
        "overall_status": overall_status,
        "scorecard_ready": scorecard_ready,
        "achieved_score": achieved_score,
        "max_score": max_score,
        "score_percent": _score_percent(achieved_score=achieved_score, max_score=max_score),
        "release_ready": release_ready,
        "regression_detected": regression_detected,
        "trend_bucket": trend_bucket,
        "failed_metric_count": len(failed_metric_ids),
        "failed_metric_ids": failed_metric_ids,
        "metrics": metrics,
        "check_count": len(checks),
        "failed_check_count": len(failed_checks),
        "failed_check_ids": tuple(str(check.get("id") or "") for check in failed_checks),
        "checks": checks,
        "next_outcome_action": _next_outcome_action(
            overall_status=overall_status,
            scorecard_ready=scorecard_ready,
            release_ready=release_ready,
            regression_detected=regression_detected,
        ),
        "summary": _summary(
            overall_status=overall_status,
            achieved_score=achieved_score,
            max_score=max_score,
            failed_metric_count=len(failed_metric_ids),
        ),
    }


def _time_metric(
    *,
    metric_id: str,
    description: str,
    target_ms: int,
    actual_ms: int,
    weight: int,
    additional_gate: bool = True,
    additional_gate_reason: str = "",
) -> dict[str, object]:
    has_measurement = actual_ms > 0
    within_target = actual_ms <= target_ms if has_measurement else False
    passed = has_measurement and within_target and additional_gate
    score = weight if passed else 0
    extra = ""
    if additional_gate_reason:
        extra = f"; {additional_gate_reason}"
    return {
        "id": metric_id,
        "description": description,
        "target_ms": target_ms,
        "actual_ms": actual_ms,
        "passed": passed,
        "weight": weight,
        "score": score,
        "reason": (
            f"Actual {actual_ms} ms within target {target_ms} ms{extra}."
            if passed
            else (
                f"Missing benchmark estimate for {metric_id}."
                if not has_measurement
                else (
                    f"Actual {actual_ms} ms exceeds target {target_ms} ms{extra}."
                    if not within_target
                    else f"Additional gate failed: {additional_gate_reason}."
                )
            )
        ),
    }


def _flag_metric(
    *,
    metric_id: str,
    description: str,
    weight: int,
    passed: bool,
    reason: str,
    details: dict[str, object],
) -> dict[str, object]:
    return {
        "id": metric_id,
        "description": description,
        "passed": passed,
        "weight": weight,
        "score": weight if passed else 0,
        "reason": reason,
        "details": details,
    }


def _check(*, check_id: str, passed: bool, reason: str) -> dict[str, object]:
    return {
        "id": check_id,
        "passed": passed,
        "reason": reason,
    }


def _scenario_estimate_ms(*, scenarios: object, scenario_id: str) -> int:
    if not isinstance(scenarios, (tuple, list)):
        return 0
    for scenario in scenarios:
        if not isinstance(scenario, dict):
            continue
        if str(scenario.get("id") or "") != scenario_id:
            continue
        value = scenario.get("estimated_runtime_ms")
        if isinstance(value, bool):
            return int(value)
        if isinstance(value, (int, float)):
            return max(0, int(value))
    return 0


def _overall_status(
    *,
    scorecard_ready: bool,
    achieved_score: int,
    max_score: int,
    release_ready: bool,
    regression_detected: bool,
) -> str:
    if not scorecard_ready:
        return "blocked"
    if max_score <= 0:
        return "at_risk"
    if regression_detected:
        return "watch" if achieved_score >= 80 else "at_risk"
    if achieved_score >= 80 and release_ready:
        return "on_track"
    if achieved_score >= 50:
        return "watch"
    return "at_risk"


def _score_percent(*, achieved_score: int, max_score: int) -> int:
    if max_score <= 0:
        return 0
    return int(round((achieved_score / max_score) * 100))


def _next_outcome_action(
    *,
    overall_status: str,
    scorecard_ready: bool,
    release_ready: bool,
    regression_detected: bool,
) -> str:
    if not scorecard_ready:
        return "Resolve failed scorecard dependency checks before using outcome signals."
    if overall_status == "on_track":
        return "Carry scorecard into milestone closeout readiness summary."
    if regression_detected:
        return "Prioritize regression remediation before milestone closeout decisions."
    if not release_ready:
        return "Improve release readiness gates to raise outcome scorecard confidence."
    return "Improve failed outcome metrics before closeout scoring."


def _summary(
    *,
    overall_status: str,
    achieved_score: int,
    max_score: int,
    failed_metric_count: int,
) -> str:
    return (
        f"Outcome scorecard status `{overall_status}` with score {achieved_score}/{max_score}; "
        f"{failed_metric_count} metric(s) below target."
    )
