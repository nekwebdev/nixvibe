"""Benchmark runner report emitter helpers."""

from __future__ import annotations


def build_benchmark_runner_report(
    *,
    benchmark_scenario_catalog: dict[str, object],
    benchmark_baseline_report: dict[str, object],
    telemetry_regression: dict[str, object],
    max_scenarios: int = 3,
) -> dict[str, object]:
    catalog_contract = str(benchmark_scenario_catalog.get("contract") or "")
    regression_detected = bool(telemetry_regression.get("regression_detected", False))
    baseline_eligible = bool(benchmark_baseline_report.get("baseline_eligible", False))

    recommended_ids = tuple(
        str(item)
        for item in benchmark_scenario_catalog.get("recommended_scenario_ids", ())
        if str(item).strip()
    )
    scenario_index = _scenario_index(benchmark_scenario_catalog.get("scenarios"))

    bounded_max_scenarios = max(1, int(max_scenarios))
    selected_ids = recommended_ids[:bounded_max_scenarios]
    plan_entries: list[dict[str, object]] = []
    for order, scenario_id in enumerate(selected_ids, start=1):
        scenario = scenario_index.get(scenario_id)
        if scenario is None:
            continue
        estimated_runtime_ms = _metric_ms(scenario.get("estimated_runtime_ms"))
        plan_entries.append(
            {
                "order": order,
                "scenario_id": scenario_id,
                "scenario_name": str(scenario.get("name") or scenario_id),
                "estimated_runtime_ms": estimated_runtime_ms,
                "runner_command": _runner_command(scenario_id),
                "tags": tuple(str(tag) for tag in scenario.get("tags", ()) if str(tag).strip()),
            }
        )

    run_mode = _run_mode(regression_detected=regression_detected, baseline_eligible=baseline_eligible)

    checks = (
        _check(
            check_id="scenario-catalog-contract",
            passed=catalog_contract == "benchmark-scenario-catalog/v1",
            reason=(
                "Scenario catalog contract is benchmark-scenario-catalog/v1."
                if catalog_contract == "benchmark-scenario-catalog/v1"
                else f"Scenario catalog contract is `{catalog_contract or 'missing'}`."
            ),
        ),
        _check(
            check_id="recommended-scenarios-available",
            passed=len(selected_ids) > 0,
            reason=(
                "Recommended scenarios available for runner plan."
                if len(selected_ids) > 0
                else "No recommended scenarios available for runner plan."
            ),
        ),
    )
    failed_checks = tuple(check for check in checks if not bool(check.get("passed")))

    total_estimated_runtime_ms = sum(
        int(entry.get("estimated_runtime_ms") or 0) for entry in plan_entries
    )

    ready_to_execute = len(failed_checks) == 0 and len(plan_entries) > 0

    return {
        "contract": "benchmark-runner-report/v1",
        "run_mode": run_mode,
        "ready_to_execute": ready_to_execute,
        "planned_scenario_count": len(plan_entries),
        "planned_scenario_ids": tuple(entry["scenario_id"] for entry in plan_entries),
        "plan": tuple(plan_entries),
        "total_estimated_runtime_ms": total_estimated_runtime_ms,
        "check_count": len(checks),
        "failed_check_count": len(failed_checks),
        "failed_check_ids": tuple(str(check.get("id") or "") for check in failed_checks),
        "checks": checks,
        "next_runner_action": (
            "Execute benchmark runner plan in listed order."
            if ready_to_execute
            else "Runner plan not ready. Resolve failed checks first."
        ),
    }


def _run_mode(*, regression_detected: bool, baseline_eligible: bool) -> str:
    if regression_detected:
        return "regression"
    if baseline_eligible:
        return "baseline"
    return "recovery"


def _scenario_index(value: object) -> dict[str, dict[str, object]]:
    if not isinstance(value, (tuple, list)):
        return {}
    index: dict[str, dict[str, object]] = {}
    for raw in value:
        if not isinstance(raw, dict):
            continue
        scenario_id = str(raw.get("id") or "").strip()
        if not scenario_id:
            continue
        index[scenario_id] = raw
    return index


def _runner_command(scenario_id: str) -> str:
    return f"nixvibe benchmark run --scenario {scenario_id}"


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
