"""Policy decision explainability contract helpers."""

from __future__ import annotations

from .types import Mode, ModeDecision, RouteDecision


def build_policy_decision_explainability(
    *,
    route_decision: RouteDecision,
    mode_decision: ModeDecision,
    selected_mode: Mode,
    merge_reason: str,
    mutation_guardrails: dict[str, object],
    apply_safety_escalation: dict[str, object],
    run_failure_classification: dict[str, object],
    release_readiness: dict[str, object],
    conflict_priority_order: tuple[str, ...],
) -> dict[str, object]:
    guardrail_triggers = tuple(str(trigger) for trigger in mutation_guardrails.get("triggers", ()))
    guardrail_blocked = bool(mutation_guardrails.get("apply_blocked", False))

    escalation_tier = str(apply_safety_escalation.get("tier") or "none")
    escalation_reason = str(apply_safety_escalation.get("reason") or "no_escalation")

    failure_classification = str(run_failure_classification.get("classification") or "none")
    failure_summary = str(run_failure_classification.get("summary") or "No classified failures.")

    release_ready = bool(release_readiness.get("ready", False))
    failed_gate_ids = tuple(str(gate) for gate in release_readiness.get("failed_gate_ids", ()))

    decisions = (
        {
            "stage": "route-selection",
            "decision": route_decision.route.value,
            "reason": route_decision.reason,
            "signals": ("needs-clarification",) if route_decision.needs_clarification else (),
        },
        {
            "stage": "mode-resolution",
            "decision": mode_decision.mode.value,
            "reason": mode_decision.reason,
            "signals": _mode_signals(mode_decision),
        },
        {
            "stage": "merge-resolution",
            "decision": "forced-propose"
            if "Contradictory critical findings" in merge_reason
            else "merged",
            "reason": merge_reason,
            "signals": ("critical-conflict",)
            if "Contradictory critical findings" in merge_reason
            else (),
        },
        {
            "stage": "mutation-guardrails",
            "decision": "blocked" if guardrail_blocked else "clear",
            "reason": (
                "Mutation guardrails blocked apply."
                if guardrail_blocked
                else "Mutation guardrails clear."
            ),
            "signals": guardrail_triggers,
        },
        {
            "stage": "safety-escalation",
            "decision": escalation_tier,
            "reason": escalation_reason,
            "signals": tuple(str(trigger) for trigger in apply_safety_escalation.get("triggers", ())),
        },
        {
            "stage": "run-failure-classification",
            "decision": failure_classification,
            "reason": failure_summary,
            "signals": tuple(str(signal) for signal in run_failure_classification.get("signals", ())),
        },
        {
            "stage": "release-readiness",
            "decision": "ready" if release_ready else "blocked",
            "reason": str(release_readiness.get("next_gate_action") or ""),
            "signals": failed_gate_ids,
        },
    )

    blocked_stages = tuple(
        decision["stage"]
        for decision in decisions
        if decision["decision"] in {"blocked", "failed", "guarded", "degraded"}
    )
    summary = (
        "Policy path clear."
        if not blocked_stages
        else f"Policy path has blockers at {', '.join(blocked_stages)}."
    )

    return {
        "contract": "policy-decision-explainability/v1",
        "final_route": route_decision.route.value,
        "final_mode": selected_mode.value,
        "selected_mode_changed": mode_decision.mode is not selected_mode,
        "conflict_priority_order": conflict_priority_order,
        "decisions": decisions,
        "decision_count": len(decisions),
        "blocked_stages": blocked_stages,
        "summary": summary,
    }


def _mode_signals(mode_decision: ModeDecision) -> tuple[str, ...]:
    signals: list[str] = []
    if mode_decision.write_allowed:
        signals.append("write-allowed")
    if mode_decision.requires_confirmation:
        signals.append("confirmation-required")
    return tuple(signals)
