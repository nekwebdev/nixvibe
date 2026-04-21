"""Benchmark scenario catalog and fixture loader helpers."""

from __future__ import annotations

from typing import Any


_SCENARIOS: tuple[dict[str, Any], ...] = (
    {
        "id": "init-propose-scaffold",
        "name": "Init Propose Scaffold",
        "route": "init",
        "preferred_mode": "propose",
        "goal": "Validate scaffold planning output without writes.",
        "tags": ("init", "propose", "scaffold"),
        "estimated_runtime_ms": 45_000,
    },
    {
        "id": "init-apply-scaffold",
        "name": "Init Apply Scaffold",
        "route": "init",
        "preferred_mode": "apply",
        "goal": "Validate scaffold writes with full validation checkpoints.",
        "tags": ("init", "apply", "validation"),
        "estimated_runtime_ms": 90_000,
    },
    {
        "id": "audit-propose-refactor",
        "name": "Audit Propose Refactor",
        "route": "audit",
        "preferred_mode": "propose",
        "goal": "Validate refactor plan and patch proposals without writes.",
        "tags": ("audit", "propose", "patches"),
        "estimated_runtime_ms": 75_000,
    },
    {
        "id": "audit-apply-refactor",
        "name": "Audit Apply Refactor",
        "route": "audit",
        "preferred_mode": "apply",
        "goal": "Validate refactor apply path with safety and release gates.",
        "tags": ("audit", "apply", "release"),
        "estimated_runtime_ms": 120_000,
    },
    {
        "id": "regression-replay",
        "name": "Regression Replay",
        "route": "any",
        "preferred_mode": "propose",
        "goal": "Replay telemetry regression conditions to isolate threshold failures.",
        "tags": ("regression", "telemetry", "diagnostics"),
        "estimated_runtime_ms": 60_000,
    },
    {
        "id": "baseline-repair",
        "name": "Baseline Repair",
        "route": "any",
        "preferred_mode": "apply",
        "goal": "Recover benchmark baseline eligibility before trend capture.",
        "tags": ("baseline", "repair", "stability"),
        "estimated_runtime_ms": 90_000,
    },
)

_SCENARIO_INDEX: dict[str, dict[str, Any]] = {scenario["id"]: scenario for scenario in _SCENARIOS}


def load_benchmark_scenario(scenario_id: str) -> dict[str, Any]:
    normalized = str(scenario_id).strip()
    scenario = _SCENARIO_INDEX.get(normalized)
    if scenario is None:
        available = ", ".join(sorted(_SCENARIO_INDEX))
        raise ValueError(
            f"Unknown benchmark scenario `{normalized}`. Available scenarios: {available}"
        )
    return dict(scenario)


def build_benchmark_scenario_catalog(
    *,
    route: str,
    mode: str,
    benchmark_baseline_report: dict[str, object],
    telemetry_regression: dict[str, object],
) -> dict[str, object]:
    normalized_route = str(route or "unknown")
    normalized_mode = str(mode or "unknown")
    regression_detected = bool(telemetry_regression.get("regression_detected", False))
    baseline_eligible = bool(benchmark_baseline_report.get("baseline_eligible", False))

    recommended_ids: list[str] = []
    if regression_detected:
        recommended_ids.append("regression-replay")
    if not baseline_eligible:
        recommended_ids.append("baseline-repair")

    if normalized_route == "init":
        recommended_ids.append(
            "init-apply-scaffold" if normalized_mode == "apply" else "init-propose-scaffold"
        )
    elif normalized_route == "audit":
        recommended_ids.append(
            "audit-apply-refactor" if normalized_mode == "apply" else "audit-propose-refactor"
        )

    deduped_recommended_ids = tuple(dict.fromkeys(recommended_ids))

    selection_reason_parts: list[str] = [
        f"route={normalized_route}",
        f"mode={normalized_mode}",
    ]
    if regression_detected:
        selection_reason_parts.append("telemetry-regression-detected")
    if not baseline_eligible:
        selection_reason_parts.append("baseline-not-eligible")

    return {
        "contract": "benchmark-scenario-catalog/v1",
        "catalog_version": "phase14-catalog/v1",
        "route": normalized_route,
        "mode": normalized_mode,
        "scenario_count": len(_SCENARIOS),
        "scenarios": tuple(dict(scenario) for scenario in _SCENARIOS),
        "recommended_scenario_ids": deduped_recommended_ids,
        "recommended_count": len(deduped_recommended_ids),
        "regression_detected": regression_detected,
        "baseline_eligible": baseline_eligible,
        "selection_reason": ", ".join(selection_reason_parts),
        "next_scenario_action": (
            "Load first recommended scenario and run benchmark harness."
            if deduped_recommended_ids
            else "No scenario recommendation generated; inspect route/mode context."
        ),
    }
