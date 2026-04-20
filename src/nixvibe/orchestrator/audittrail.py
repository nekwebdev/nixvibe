"""Operator audit-trail summary contract helpers."""

from __future__ import annotations

import hashlib


def build_operator_audit_trail_summary(
    *,
    run_manifest: dict[str, object],
    run_failure_classification: dict[str, object],
    release_readiness: dict[str, object],
    resume_checkpoint: dict[str, object],
    retry_backoff_guardrails: dict[str, object],
    policy_decision_explainability: dict[str, object],
    controlled_override_workflow: dict[str, object],
) -> dict[str, object]:
    route = str(run_manifest.get("route") or "unknown")
    modes = _mapping(run_manifest.get("modes"))
    selected_mode = str(modes.get("selected") or "unknown")

    classification = str(run_failure_classification.get("classification") or "none")
    failure_severity = str(run_failure_classification.get("severity") or "none")
    release_ready = bool(release_readiness.get("ready", False))
    override_decision = str(controlled_override_workflow.get("decision") or "none")
    override_requested = bool(controlled_override_workflow.get("override_requested", False))
    resume_required = bool(resume_checkpoint.get("resume_required", False))
    automatic_retry_allowed = bool(retry_backoff_guardrails.get("automatic_retry_allowed", False))

    entries = (
        {
            "stage": "routing",
            "status": route,
            "severity": "info",
            "message": f"Route resolved to `{route}` with mode `{selected_mode}`.",
        },
        {
            "stage": "failure-classification",
            "status": classification,
            "severity": failure_severity,
            "message": str(run_failure_classification.get("summary") or "No failure summary."),
        },
        {
            "stage": "release-readiness",
            "status": "ready" if release_ready else "blocked",
            "severity": "info" if release_ready else "high",
            "message": str(release_readiness.get("next_gate_action") or ""),
        },
        {
            "stage": "resume-checkpoint",
            "status": "required" if resume_required else "none",
            "severity": "high" if resume_required else "info",
            "message": str(resume_checkpoint.get("next_safe_action") or ""),
        },
        {
            "stage": "retry-guardrails",
            "status": "auto" if automatic_retry_allowed else "manual",
            "severity": "medium" if automatic_retry_allowed else "info",
            "message": str(retry_backoff_guardrails.get("next_retry_action") or ""),
        },
        {
            "stage": "override-workflow",
            "status": override_decision,
            "severity": _override_severity(override_decision),
            "message": str(controlled_override_workflow.get("next_override_action") or ""),
        },
    )

    action_items = _action_items(
        release_readiness=release_readiness,
        resume_checkpoint=resume_checkpoint,
        controlled_override_workflow=controlled_override_workflow,
    )
    requires_attention = (
        classification in {"blocked", "failed", "degraded"}
        or not release_ready
        or override_decision == "deny"
        or resume_required
    )
    audit_level = _audit_level(
        classification=classification,
        failure_severity=failure_severity,
        override_decision=override_decision,
        release_ready=release_ready,
    )
    summary_id = _summary_id(
        route=route,
        selected_mode=selected_mode,
        classification=classification,
        release_ready=release_ready,
        override_decision=override_decision,
        override_requested=override_requested,
    )

    next_operator_action = (
        action_items[0]
        if action_items
        else str(run_manifest.get("next_action") or "No operator action required.")
    )

    return {
        "contract": "operator-audit-trail/v1",
        "summary_id": summary_id,
        "route": route,
        "mode": selected_mode,
        "audit_level": audit_level,
        "requires_attention": requires_attention,
        "entries": entries,
        "entry_count": len(entries),
        "action_items": action_items,
        "action_count": len(action_items),
        "next_operator_action": next_operator_action,
        "explainability_summary": str(policy_decision_explainability.get("summary") or ""),
    }


def _action_items(
    *,
    release_readiness: dict[str, object],
    resume_checkpoint: dict[str, object],
    controlled_override_workflow: dict[str, object],
) -> tuple[str, ...]:
    items: list[str] = []
    if not bool(release_readiness.get("ready", False)):
        items.append(str(release_readiness.get("next_gate_action") or "Resolve failed release gates."))
    for action in resume_checkpoint.get("required_actions", ()):
        action_text = str(action).strip()
        if action_text:
            items.append(action_text)
    if str(controlled_override_workflow.get("decision") or "") == "deny":
        items.append("Resolve override blockers before requesting override again.")
    return tuple(dict.fromkeys(items))


def _audit_level(
    *,
    classification: str,
    failure_severity: str,
    override_decision: str,
    release_ready: bool,
) -> str:
    if classification == "blocked" or failure_severity == "critical":
        return "critical"
    if classification in {"failed", "degraded"} or override_decision == "deny" or not release_ready:
        return "warning"
    return "info"


def _override_severity(decision: str) -> str:
    if decision == "deny":
        return "high"
    if decision == "allow-with-confirmation":
        return "medium"
    return "info"


def _summary_id(
    *,
    route: str,
    selected_mode: str,
    classification: str,
    release_ready: bool,
    override_decision: str,
    override_requested: bool,
) -> str:
    basis = (
        f"{route}|{selected_mode}|{classification}|{int(release_ready)}|"
        f"{override_decision}|{int(override_requested)}"
    )
    digest = hashlib.sha256(basis.encode("utf-8")).hexdigest()[:12]
    return f"oa-{digest}"


def _mapping(value: object) -> dict[str, object]:
    if isinstance(value, dict):
        return value
    return {}
