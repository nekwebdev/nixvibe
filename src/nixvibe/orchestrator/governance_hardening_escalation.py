"""Governance hardening escalation contract helpers."""

from __future__ import annotations


def build_governance_hardening_escalation(
    *,
    operator_observability_digest: dict[str, object],
    release_policy_execution: dict[str, object],
    controlled_override_workflow: dict[str, object],
    apply_safety_escalation: dict[str, object],
) -> dict[str, object]:
    observability_band = str(operator_observability_digest.get("observability_band") or "degraded")
    release_policy_decision = str(release_policy_execution.get("decision") or "blocked")
    override_decision = str(controlled_override_workflow.get("decision") or "none")
    override_requested = bool(controlled_override_workflow.get("override_requested", False))
    safety_tier = str(apply_safety_escalation.get("tier") or "none")

    checks = (
        _check(
            check_id="operator-observability-digest-contract",
            passed=str(operator_observability_digest.get("contract") or "")
            == "operator-observability-digest/v1",
            reason=(
                "Operator observability digest contract is operator-observability-digest/v1."
                if str(operator_observability_digest.get("contract") or "")
                == "operator-observability-digest/v1"
                else (
                    "Operator observability digest contract is "
                    f"`{operator_observability_digest.get('contract') or 'missing'}`."
                )
            ),
        ),
        _check(
            check_id="release-policy-execution-contract",
            passed=str(release_policy_execution.get("contract") or "") == "release-policy-execution/v1",
            reason=(
                "Release policy execution contract is release-policy-execution/v1."
                if str(release_policy_execution.get("contract") or "") == "release-policy-execution/v1"
                else (
                    "Release policy execution contract is "
                    f"`{release_policy_execution.get('contract') or 'missing'}`."
                )
            ),
        ),
        _check(
            check_id="controlled-override-workflow-contract",
            passed=str(controlled_override_workflow.get("contract") or "")
            == "controlled-override-workflow/v1",
            reason=(
                "Controlled override workflow contract is controlled-override-workflow/v1."
                if str(controlled_override_workflow.get("contract") or "")
                == "controlled-override-workflow/v1"
                else (
                    "Controlled override workflow contract is "
                    f"`{controlled_override_workflow.get('contract') or 'missing'}`."
                )
            ),
        ),
        _check(
            check_id="apply-safety-escalation-contract",
            passed=safety_tier in {"none", "advisory", "guarded", "blocked"},
            reason=(
                f"Apply safety escalation tier is `{safety_tier}`."
                if safety_tier in {"none", "advisory", "guarded", "blocked"}
                else (
                    "Apply safety escalation tier is "
                    f"`{safety_tier or 'missing'}`."
                )
            ),
        ),
    )
    failed_checks = tuple(check for check in checks if not bool(check.get("passed")))
    governance_ready = len(failed_checks) == 0

    escalation_level = _escalation_level(
        governance_ready=governance_ready,
        observability_band=observability_band,
        release_policy_decision=release_policy_decision,
        override_requested=override_requested,
        override_decision=override_decision,
        safety_tier=safety_tier,
    )
    governance_posture = _governance_posture(escalation_level=escalation_level)
    blockers = _blockers(
        escalation_level=escalation_level,
        operator_observability_digest=operator_observability_digest,
        release_policy_execution=release_policy_execution,
        controlled_override_workflow=controlled_override_workflow,
    )

    return {
        "contract": "governance-hardening-escalation/v1",
        "profile": "phase20-governance-hardening-escalation/v1",
        "governance_ready": governance_ready,
        "escalation_level": escalation_level,
        "governance_posture": governance_posture,
        "escalation_required": escalation_level in {"review", "escalate", "critical"},
        "observability_band": observability_band,
        "release_policy_decision": release_policy_decision,
        "override_requested": override_requested,
        "override_decision": override_decision,
        "safety_tier": safety_tier,
        "blocker_count": len(blockers),
        "blockers": blockers,
        "check_count": len(checks),
        "failed_check_count": len(failed_checks),
        "failed_check_ids": tuple(str(check.get("id") or "") for check in failed_checks),
        "checks": checks,
        "next_governance_action": _next_governance_action(escalation_level=escalation_level),
        "summary": (
            f"Governance hardening escalation `{escalation_level}` "
            f"(observability={observability_band}, release_policy={release_policy_decision})."
        ),
    }


def _escalation_level(
    *,
    governance_ready: bool,
    observability_band: str,
    release_policy_decision: str,
    override_requested: bool,
    override_decision: str,
    safety_tier: str,
) -> str:
    if not governance_ready:
        return "critical"
    if (
        observability_band in {"critical", "degraded"}
        or release_policy_decision == "blocked"
        or safety_tier == "blocked"
    ):
        return "critical"
    if (
        observability_band == "attention"
        or release_policy_decision == "manual-ack"
        or (override_requested and override_decision == "deny")
        or safety_tier == "guarded"
    ):
        return "escalate"
    if safety_tier == "advisory" or override_decision == "allow-with-confirmation":
        return "review"
    return "none"


def _governance_posture(*, escalation_level: str) -> str:
    if escalation_level == "none":
        return "stable"
    if escalation_level == "review":
        return "watch"
    if escalation_level == "escalate":
        return "harden"
    return "blocked"


def _blockers(
    *,
    escalation_level: str,
    operator_observability_digest: dict[str, object],
    release_policy_execution: dict[str, object],
    controlled_override_workflow: dict[str, object],
) -> tuple[str, ...]:
    if escalation_level == "none":
        return ()

    blockers: list[str] = []
    for item in operator_observability_digest.get("focus_items", ()):
        text = str(item).strip()
        if text:
            blockers.append(text)
    for blocker in release_policy_execution.get("blockers", ()):
        blocker_text = str(blocker).strip()
        if blocker_text:
            blockers.append(f"release-policy:{blocker_text}")
    for blocked_override in controlled_override_workflow.get("blocked_overrides", ()):
        if isinstance(blocked_override, dict):
            blocked_id = str(blocked_override.get("id") or "")
            if blocked_id:
                blockers.append(f"override:{blocked_id}")

    deduped = tuple(dict.fromkeys(blockers))
    return deduped[:8]


def _next_governance_action(*, escalation_level: str) -> str:
    if escalation_level == "none":
        return "Governance posture is stable. Continue normal operator flow."
    if escalation_level == "review":
        return "Governance posture requires review. Validate advisory and confirmation-required signals."
    if escalation_level == "escalate":
        return "Governance posture requires escalation. Harden policies and resolve attention-level blockers."
    return "Governance posture is critical. Block release operations until critical blockers are cleared."


def _check(*, check_id: str, passed: bool, reason: str) -> dict[str, object]:
    return {
        "id": check_id,
        "passed": passed,
        "reason": reason,
    }
