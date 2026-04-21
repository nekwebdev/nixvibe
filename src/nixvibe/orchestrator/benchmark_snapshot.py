"""Benchmark baseline snapshot and regression check helpers."""

from __future__ import annotations

import hashlib


def build_benchmark_baseline_snapshot(
    *,
    run_manifest: dict[str, object],
    run_telemetry: dict[str, object],
    benchmark_baseline_report: dict[str, object],
    telemetry_regression: dict[str, object],
    benchmark_scenario_catalog: dict[str, object],
    benchmark_runner_report: dict[str, object],
) -> dict[str, object]:
    route = str(
        run_manifest.get("route")
        or benchmark_baseline_report.get("route")
        or run_telemetry.get("route")
        or "unknown"
    )
    mode = _selected_mode(run_manifest)
    benchmark_id = str(benchmark_baseline_report.get("benchmark_id") or "unknown")
    baseline_eligible = bool(benchmark_baseline_report.get("baseline_eligible", False))
    regression_detected = bool(telemetry_regression.get("regression_detected", False))
    regression_status = str(telemetry_regression.get("status") or "unknown")
    runner_ready_to_execute = bool(benchmark_runner_report.get("ready_to_execute", False))
    run_mode = str(benchmark_runner_report.get("run_mode") or "unknown")
    expected_run_mode = _expected_run_mode(
        regression_detected=regression_detected,
        baseline_eligible=baseline_eligible,
    )
    planned_scenario_ids = tuple(
        str(item)
        for item in benchmark_runner_report.get("planned_scenario_ids", ())
        if str(item).strip()
    )
    total_duration_ms = _metric_ms(run_telemetry.get("total_duration_ms"))
    specialist_execution_ms = _metric_ms(run_telemetry.get("specialist_execution_ms"))
    validation_total_ms = _metric_ms(run_telemetry.get("validation_total_ms"))
    checks = (
        _check(
            check_id="baseline-report-contract",
            passed=str(benchmark_baseline_report.get("contract") or "")
            == "benchmark-baseline-report/v1",
            reason=(
                "Benchmark baseline report contract is benchmark-baseline-report/v1."
                if str(benchmark_baseline_report.get("contract") or "")
                == "benchmark-baseline-report/v1"
                else (
                    "Benchmark baseline report contract is "
                    f"`{benchmark_baseline_report.get('contract') or 'missing'}`."
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
            check_id="regression-status-consistency",
            passed=regression_detected == (regression_status == "regression"),
            reason=(
                "Telemetry regression status aligns with regression flag."
                if regression_detected == (regression_status == "regression")
                else (
                    f"Regression status `{regression_status}` does not match "
                    f"regression_detected={regression_detected}."
                )
            ),
        ),
        _check(
            check_id="run-mode-consistency",
            passed=run_mode == expected_run_mode,
            reason=(
                f"Runner mode `{run_mode}` matches expected mode."
                if run_mode == expected_run_mode
                else f"Runner mode `{run_mode}` does not match expected `{expected_run_mode}`."
            ),
        ),
        _check(
            check_id="runner-ready",
            passed=runner_ready_to_execute and len(planned_scenario_ids) > 0,
            reason=(
                "Runner report is ready with at least one planned scenario."
                if runner_ready_to_execute and len(planned_scenario_ids) > 0
                else "Runner report is not ready or has no planned scenarios."
            ),
        ),
    )
    failed_checks = tuple(check for check in checks if not bool(check.get("passed")))
    snapshot_ready = len(failed_checks) == 0
    baseline_recordable = (
        snapshot_ready
        and baseline_eligible
        and not regression_detected
        and run_mode == "baseline"
    )
    trend_bucket = _trend_bucket(
        baseline_recordable=baseline_recordable,
        baseline_eligible=baseline_eligible,
        regression_detected=regression_detected,
    )
    snapshot_id = _snapshot_id(
        benchmark_id=benchmark_id,
        route=route,
        mode=mode,
        run_mode=run_mode,
        baseline_eligible=baseline_eligible,
        regression_detected=regression_detected,
        total_duration_ms=total_duration_ms,
        failed_check_count=len(failed_checks),
    )

    return {
        "contract": "benchmark-baseline-snapshot/v1",
        "snapshot_profile": "phase14-baseline-snapshot/v1",
        "snapshot_id": snapshot_id,
        "benchmark_id": benchmark_id,
        "route": route,
        "mode": mode,
        "run_mode": run_mode,
        "expected_run_mode": expected_run_mode,
        "baseline_eligible": baseline_eligible,
        "regression_detected": regression_detected,
        "regression_status": regression_status,
        "runner_ready_to_execute": runner_ready_to_execute,
        "snapshot_ready": snapshot_ready,
        "baseline_recordable": baseline_recordable,
        "trend_bucket": trend_bucket,
        "planned_scenario_count": len(planned_scenario_ids),
        "planned_scenario_ids": planned_scenario_ids,
        "timing": {
            "total_duration_ms": total_duration_ms,
            "specialist_execution_ms": specialist_execution_ms,
            "validation_total_ms": validation_total_ms,
        },
        "check_count": len(checks),
        "failed_check_count": len(failed_checks),
        "failed_check_ids": tuple(str(check.get("id") or "") for check in failed_checks),
        "checks": checks,
        "next_snapshot_action": _next_snapshot_action(
            baseline_recordable=baseline_recordable,
            regression_detected=regression_detected,
            snapshot_ready=snapshot_ready,
            trend_bucket=trend_bucket,
        ),
        "summary": _summary(
            snapshot_ready=snapshot_ready,
            baseline_recordable=baseline_recordable,
            trend_bucket=trend_bucket,
            failed_check_count=len(failed_checks),
        ),
    }


def _check(*, check_id: str, passed: bool, reason: str) -> dict[str, object]:
    return {
        "id": check_id,
        "passed": passed,
        "reason": reason,
    }


def _expected_run_mode(*, regression_detected: bool, baseline_eligible: bool) -> str:
    if regression_detected:
        return "regression"
    if baseline_eligible:
        return "baseline"
    return "recovery"


def _trend_bucket(
    *,
    baseline_recordable: bool,
    baseline_eligible: bool,
    regression_detected: bool,
) -> str:
    if baseline_recordable:
        return "baseline-candidate"
    if regression_detected:
        return "regression-investigate"
    if baseline_eligible:
        return "baseline-blocked"
    return "recovery-needed"


def _selected_mode(run_manifest: dict[str, object]) -> str:
    modes = run_manifest.get("modes")
    if isinstance(modes, dict):
        return str(modes.get("selected") or "unknown")
    return "unknown"


def _snapshot_id(
    *,
    benchmark_id: str,
    route: str,
    mode: str,
    run_mode: str,
    baseline_eligible: bool,
    regression_detected: bool,
    total_duration_ms: int,
    failed_check_count: int,
) -> str:
    basis = (
        f"{benchmark_id}|{route}|{mode}|{run_mode}|{int(baseline_eligible)}|"
        f"{int(regression_detected)}|{total_duration_ms}|{failed_check_count}"
    )
    digest = hashlib.sha256(basis.encode("utf-8")).hexdigest()[:12]
    return f"bms-{digest}"


def _metric_ms(value: object) -> int:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, (int, float)):
        return max(0, int(value))
    return 0


def _next_snapshot_action(
    *,
    baseline_recordable: bool,
    regression_detected: bool,
    snapshot_ready: bool,
    trend_bucket: str,
) -> str:
    if baseline_recordable:
        return "Persist baseline snapshot and include in milestone trend rollup."
    if regression_detected:
        return "Run regression scenario plan and resolve threshold failures."
    if not snapshot_ready:
        return "Resolve failed snapshot checks before publishing trend snapshot."
    return f"Publish non-baseline snapshot in trend bucket `{trend_bucket}` for tracking."


def _summary(
    *,
    snapshot_ready: bool,
    baseline_recordable: bool,
    trend_bucket: str,
    failed_check_count: int,
) -> str:
    if not snapshot_ready:
        return f"Baseline snapshot blocked by {failed_check_count} failed check(s)."
    if baseline_recordable:
        return "Baseline snapshot ready and recordable for trend tracking."
    return f"Baseline snapshot ready in `{trend_bucket}` bucket."
