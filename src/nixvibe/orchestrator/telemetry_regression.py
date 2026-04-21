"""Telemetry regression threshold contract helpers."""

from __future__ import annotations


def build_telemetry_regression_report(
    *,
    run_telemetry: dict[str, object],
    benchmark_baseline_report: dict[str, object],
) -> dict[str, object]:
    telemetry_contract = str(run_telemetry.get("contract") or "")
    total_duration_ms = _metric_ms(run_telemetry.get("total_duration_ms"))
    specialist_execution_ms = _metric_ms(run_telemetry.get("specialist_execution_ms"))
    validation_total_ms = _metric_ms(run_telemetry.get("validation_total_ms"))
    artifact_materialization_ms = _metric_ms(run_telemetry.get("artifact_materialization_ms"))
    ledger_inspection_ms = _metric_ms(run_telemetry.get("ledger_inspection_ms"))
    specialist_average_ms = _metric_ms(run_telemetry.get("specialist_average_ms"))
    specialist_count = max(0, int(run_telemetry.get("specialist_count") or 0))

    checks: list[dict[str, object]] = [
        _check(
            check_id="telemetry-contract",
            passed=telemetry_contract == "run-telemetry/v1",
            reason=(
                "Telemetry contract is run-telemetry/v1."
                if telemetry_contract == "run-telemetry/v1"
                else f"Telemetry contract is `{telemetry_contract or 'missing'}`."
            ),
            severity="critical",
        )
    ]

    thresholds = (
        _threshold(
            threshold_id="total-duration-ms",
            actual_ms=total_duration_ms,
            limit_ms=300_000,
            severity="critical",
        ),
        _threshold(
            threshold_id="specialist-execution-ms",
            actual_ms=specialist_execution_ms,
            limit_ms=180_000,
            severity="high",
        ),
        _threshold(
            threshold_id="validation-total-ms",
            actual_ms=validation_total_ms,
            limit_ms=120_000,
            severity="high",
        ),
        _threshold(
            threshold_id="artifact-materialization-ms",
            actual_ms=artifact_materialization_ms,
            limit_ms=60_000,
            severity="medium",
        ),
        _threshold(
            threshold_id="ledger-inspection-ms",
            actual_ms=ledger_inspection_ms,
            limit_ms=15_000,
            severity="medium",
        ),
        _threshold(
            threshold_id="specialist-average-ms",
            actual_ms=specialist_average_ms,
            limit_ms=90_000,
            severity="high",
            applicable=specialist_count > 0,
        ),
    )

    failed_checks = tuple(check for check in checks if not bool(check.get("passed")))
    failed_thresholds = tuple(
        threshold
        for threshold in thresholds
        if bool(threshold.get("applicable", True)) and not bool(threshold.get("passed"))
    )

    regression_detected = bool(failed_checks or failed_thresholds)
    status = "regression" if regression_detected else "pass"

    return {
        "contract": "telemetry-regression/v1",
        "profile": "phase13-default-thresholds/v1",
        "status": status,
        "regression_detected": regression_detected,
        "benchmark_baseline_eligible": bool(
            benchmark_baseline_report.get("baseline_eligible", False)
        ),
        "benchmark_baseline_tier": str(
            benchmark_baseline_report.get("baseline_tier") or "unknown"
        ),
        "check_count": len(checks),
        "failed_check_count": len(failed_checks),
        "failed_check_ids": tuple(str(check.get("id") or "") for check in failed_checks),
        "checks": tuple(checks),
        "threshold_count": len(thresholds),
        "failed_threshold_count": len(failed_thresholds),
        "failed_threshold_ids": tuple(
            str(threshold.get("id") or "") for threshold in failed_thresholds
        ),
        "thresholds": thresholds,
        "next_action": (
            "Telemetry thresholds stable. Continue benchmark trend capture."
            if not regression_detected
            else "Telemetry regression detected. Investigate failed checks and thresholds."
        ),
        "summary": (
            "Telemetry regression report passed all checks."
            if not regression_detected
            else (
                f"Telemetry regression report detected {len(failed_checks)} failed check(s) and "
                f"{len(failed_thresholds)} failed threshold(s)."
            )
        ),
    }


def _threshold(
    *,
    threshold_id: str,
    actual_ms: int,
    limit_ms: int,
    severity: str,
    applicable: bool = True,
) -> dict[str, object]:
    passed = (not applicable) or actual_ms <= limit_ms
    return {
        "id": threshold_id,
        "applicable": applicable,
        "actual_ms": actual_ms,
        "limit_ms": limit_ms,
        "passed": passed,
        "severity": severity,
        "reason": (
            "Threshold not applicable."
            if not applicable
            else (
                f"Actual {actual_ms} ms within limit {limit_ms} ms."
                if passed
                else f"Actual {actual_ms} ms exceeds limit {limit_ms} ms."
            )
        ),
    }


def _check(*, check_id: str, passed: bool, reason: str, severity: str) -> dict[str, object]:
    return {
        "id": check_id,
        "passed": passed,
        "reason": reason,
        "severity": severity,
    }


def _metric_ms(value: object) -> int:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, (int, float)):
        return max(0, int(value))
    return 0
