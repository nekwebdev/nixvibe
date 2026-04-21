"""Governance workflow consolidation integration helpers."""

from __future__ import annotations


def build_governance_workflow_consolidation(
    *,
    operator_control_plane_summary: dict[str, object],
    governance_hardening_escalation: dict[str, object],
    controlled_override_workflow: dict[str, object],
    release_policy_execution: dict[str, object],
) -> dict[str, object]:
    control_plane_status = str(operator_control_plane_summary.get("control_plane_status") or "blocked")
    escalation_level = str(governance_hardening_escalation.get("escalation_level") or "critical")
    override_decision = str(controlled_override_workflow.get("decision") or "none")
    release_policy_decision = str(release_policy_execution.get("decision") or "blocked")

    checks = (
        _check(
            check_id="operator-control-plane-summary-contract",
            passed=str(operator_control_plane_summary.get("contract") or "")
            == "operator-control-plane-summary/v1",
            reason=(
                "Operator control-plane summary contract is operator-control-plane-summary/v1."
                if str(operator_control_plane_summary.get("contract") or "")
                == "operator-control-plane-summary/v1"
                else (
                    "Operator control-plane summary contract is "
                    f"`{operator_control_plane_summary.get('contract') or 'missing'}`."
                )
            ),
        ),
        _check(
            check_id="governance-hardening-escalation-contract",
            passed=str(governance_hardening_escalation.get("contract") or "")
            == "governance-hardening-escalation/v1",
            reason=(
                "Governance hardening escalation contract is governance-hardening-escalation/v1."
                if str(governance_hardening_escalation.get("contract") or "")
                == "governance-hardening-escalation/v1"
                else (
                    "Governance hardening escalation contract is "
                    f"`{governance_hardening_escalation.get('contract') or 'missing'}`."
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
    )
    failed_checks = tuple(check for check in checks if not bool(check.get("passed")))
    consolidation_ready = len(failed_checks) == 0

    consolidation_status = _consolidation_status(
        consolidation_ready=consolidation_ready,
        control_plane_status=control_plane_status,
        escalation_level=escalation_level,
        override_decision=override_decision,
        release_policy_decision=release_policy_decision,
    )
    blockers = _blockers(
        consolidation_status=consolidation_status,
        control_plane_status=control_plane_status,
        escalation_level=escalation_level,
        override_decision=override_decision,
        release_policy_decision=release_policy_decision,
        failed_check_ids=tuple(str(check.get("id") or "") for check in failed_checks),
    )

    workflow_mode = {
        "consolidated": "automated",
        "review": "guarded",
        "blocked": "manual-only",
    }[consolidation_status]

    return {
        "contract": "governance-workflow-consolidation/v1",
        "profile": "phase23-governance-workflow-consolidation/v1",
        "consolidation_ready": consolidation_ready,
        "consolidation_status": consolidation_status,
        "workflow_mode": workflow_mode,
        "control_plane_status": control_plane_status,
        "escalation_level": escalation_level,
        "override_decision": override_decision,
        "release_policy_decision": release_policy_decision,
        "workflow_ready": consolidation_status == "consolidated",
        "requires_human_review": consolidation_status == "review",
        "blocker_count": len(blockers),
        "blockers": blockers,
        "check_count": len(checks),
        "failed_check_count": len(failed_checks),
        "failed_check_ids": tuple(str(check.get("id") or "") for check in failed_checks),
        "checks": checks,
        "next_governance_workflow_action": _next_action(consolidation_status=consolidation_status),
        "summary": (
            f"Governance workflow consolidation `{consolidation_status}` "
            f"(control_plane={control_plane_status}, escalation={escalation_level}, "
            f"release_policy={release_policy_decision})."
        ),
    }


def _consolidation_status(
    *,
    consolidation_ready: bool,
    control_plane_status: str,
    escalation_level: str,
    override_decision: str,
    release_policy_decision: str,
) -> str:
    if not consolidation_ready:
        return "blocked"
    if (
        control_plane_status == "blocked"
        or escalation_level == "critical"
        or override_decision == "deny"
        or release_policy_decision == "blocked"
    ):
        return "blocked"
    if (
        control_plane_status == "attention"
        or escalation_level in {"review", "escalate"}
        or override_decision == "allow-with-confirmation"
        or release_policy_decision == "manual-ack"
    ):
        return "review"
    return "consolidated"


def _blockers(
    *,
    consolidation_status: str,
    control_plane_status: str,
    escalation_level: str,
    override_decision: str,
    release_policy_decision: str,
    failed_check_ids: tuple[str, ...],
) -> tuple[str, ...]:
    if consolidation_status == "consolidated":
        return ()

    blockers: list[str] = [f"contract:{check_id}" for check_id in failed_check_ids if check_id]
    if control_plane_status != "aligned":
        blockers.append(f"control-plane:{control_plane_status}")
    if escalation_level != "none":
        blockers.append(f"governance:{escalation_level}")
    if override_decision != "none":
        blockers.append(f"override:{override_decision}")
    if release_policy_decision != "automated":
        blockers.append(f"release-policy:{release_policy_decision}")
    return tuple(dict.fromkeys(blockers))[:12]


def _next_action(*, consolidation_status: str) -> str:
    if consolidation_status == "consolidated":
        return "Governance workflow is consolidated. Proceed to phase23 acceptance closeout."
    if consolidation_status == "review":
        return "Governance workflow needs review. Resolve guarded controls before closeout."
    return "Governance workflow is blocked. Resolve critical governance blockers first."


def _check(*, check_id: str, passed: bool, reason: str) -> dict[str, object]:
    return {
        "id": check_id,
        "passed": passed,
        "reason": reason,
    }
