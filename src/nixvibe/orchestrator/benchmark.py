"""Benchmark baseline report contract helpers."""

from __future__ import annotations

import hashlib


def build_benchmark_baseline_report(
    *,
    run_telemetry: dict[str, object],
    run_manifest: dict[str, object],
    run_failure_classification: dict[str, object],
    release_readiness: dict[str, object],
) -> dict[str, object]:
    route = str(run_manifest.get("route") or run_telemetry.get("route") or "unknown")
    modes = _mapping(run_manifest.get("modes"))
    mode = str(modes.get("selected") or run_telemetry.get("mode") or "unknown")

    classification = str(run_failure_classification.get("classification") or "none")
    severity = str(run_failure_classification.get("severity") or "none")
    release_ready = bool(release_readiness.get("ready", False))

    total_duration_ms = _metric_ms(run_telemetry.get("total_duration_ms"))
    specialist_execution_ms = _metric_ms(run_telemetry.get("specialist_execution_ms"))
    validation_total_ms = _metric_ms(run_telemetry.get("validation_total_ms"))
    materialization_ms = _metric_ms(run_telemetry.get("artifact_materialization_ms"))
    specialist_count = max(0, int(run_telemetry.get("specialist_count") or 0))
    validation_checkpoint_count = max(
        0,
        int(run_telemetry.get("validation_checkpoint_count") or 0),
    )

    checks = _checks(
        mode=mode,
        classification=classification,
        release_ready=release_ready,
        telemetry_contract=str(run_telemetry.get("contract") or ""),
        total_duration_ms=total_duration_ms,
    )
    failed_checks = tuple(check for check in checks if not bool(check.get("passed")))

    baseline_eligible = len(failed_checks) == 0
    baseline_tier = _baseline_tier(total_duration_ms)

    benchmark_id = _benchmark_id(
        route=route,
        mode=mode,
        baseline_eligible=baseline_eligible,
        classification=classification,
        total_duration_ms=total_duration_ms,
    )

    return {
        "contract": "benchmark-baseline-report/v1",
        "benchmark_id": benchmark_id,
        "route": route,
        "mode": mode,
        "baseline_eligible": baseline_eligible,
        "baseline_tier": baseline_tier,
        "classification": classification,
        "severity": severity,
        "release_ready": release_ready,
        "check_count": len(checks),
        "failed_check_count": len(failed_checks),
        "failed_check_ids": tuple(str(check.get("id") or "") for check in failed_checks),
        "checks": checks,
        "timing": {
            "total_duration_ms": total_duration_ms,
            "specialist_execution_ms": specialist_execution_ms,
            "validation_total_ms": validation_total_ms,
            "artifact_materialization_ms": materialization_ms,
        },
        "throughput": {
            "specialist_count": specialist_count,
            "validation_checkpoint_count": validation_checkpoint_count,
        },
        "next_benchmark_action": (
            "Baseline eligible. Persist report for benchmark trend tracking."
            if baseline_eligible
            else "Baseline not eligible. Resolve failed checks before recording baseline."
        ),
        "summary": _summary(
            baseline_eligible=baseline_eligible,
            baseline_tier=baseline_tier,
            failed_check_count=len(failed_checks),
        ),
    }


def _checks(
    *,
    mode: str,
    classification: str,
    release_ready: bool,
    telemetry_contract: str,
    total_duration_ms: int,
) -> tuple[dict[str, object], ...]:
    return (
        _check(
            check_id="mode-apply",
            passed=mode == "apply",
            reason=(
                "Selected mode is apply."
                if mode == "apply"
                else f"Selected mode `{mode}` is not apply."
            ),
        ),
        _check(
            check_id="failure-classification-clear",
            passed=classification == "none",
            reason=(
                "Run failure classification is clear."
                if classification == "none"
                else f"Run failure classification is `{classification}`."
            ),
        ),
        _check(
            check_id="release-ready",
            passed=release_ready,
            reason=(
                "Release readiness is true."
                if release_ready
                else "Release readiness is false."
            ),
        ),
        _check(
            check_id="telemetry-contract",
            passed=telemetry_contract == "run-telemetry/v1",
            reason=(
                "Telemetry contract is run-telemetry/v1."
                if telemetry_contract == "run-telemetry/v1"
                else f"Telemetry contract is `{telemetry_contract or 'missing'}`."
            ),
        ),
        _check(
            check_id="timing-captured",
            passed=total_duration_ms > 0,
            reason=(
                "Total duration timing captured."
                if total_duration_ms > 0
                else "Total duration timing missing."
            ),
        ),
    )


def _check(*, check_id: str, passed: bool, reason: str) -> dict[str, object]:
    return {
        "id": check_id,
        "passed": passed,
        "reason": reason,
    }


def _baseline_tier(total_duration_ms: int) -> str:
    if total_duration_ms <= 1_000:
        return "strong"
    if total_duration_ms <= 10_000:
        return "acceptable"
    return "slow"


def _summary(*, baseline_eligible: bool, baseline_tier: str, failed_check_count: int) -> str:
    if baseline_eligible:
        return f"Benchmark baseline eligible with `{baseline_tier}` timing tier."
    return f"Benchmark baseline blocked by {failed_check_count} failed check(s)."


def _benchmark_id(
    *,
    route: str,
    mode: str,
    baseline_eligible: bool,
    classification: str,
    total_duration_ms: int,
) -> str:
    basis = (
        f"{route}|{mode}|{int(baseline_eligible)}|"
        f"{classification}|{total_duration_ms}"
    )
    digest = hashlib.sha256(basis.encode("utf-8")).hexdigest()[:12]
    return f"bm-{digest}"


def _mapping(value: object) -> dict[str, object]:
    if isinstance(value, dict):
        return value
    return {}


def _metric_ms(value: object) -> int:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, (int, float)):
        return max(0, int(value))
    return 0
