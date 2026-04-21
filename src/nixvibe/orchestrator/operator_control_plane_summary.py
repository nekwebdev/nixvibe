"""Operator control-plane summary helpers."""

from __future__ import annotations


def build_operator_control_plane_summary(
    *,
    migration_safety_policy: dict[str, object],
    governance_hardening_escalation: dict[str, object],
    operator_audit_trail: dict[str, object],
    policy_decision_explainability: dict[str, object],
) -> dict[str, object]:
    migration_decision = str(migration_safety_policy.get("policy_decision") or "block")
    governance_level = str(governance_hardening_escalation.get("escalation_level") or "critical")
    audit_level = str(operator_audit_trail.get("audit_level") or "critical")
    blocked_stages = tuple(str(stage) for stage in policy_decision_explainability.get("blocked_stages", ()))

    checks = (
        _check(
            check_id="migration-safety-policy-contract",
            passed=str(migration_safety_policy.get("contract") or "") == "migration-safety-policy/v1",
            reason=(
                "Migration safety policy contract is migration-safety-policy/v1."
                if str(migration_safety_policy.get("contract") or "") == "migration-safety-policy/v1"
                else (
                    "Migration safety policy contract is "
                    f"`{migration_safety_policy.get('contract') or 'missing'}`."
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
            check_id="operator-audit-trail-contract",
            passed=str(operator_audit_trail.get("contract") or "") == "operator-audit-trail/v1",
            reason=(
                "Operator audit trail contract is operator-audit-trail/v1."
                if str(operator_audit_trail.get("contract") or "") == "operator-audit-trail/v1"
                else (
                    "Operator audit trail contract is "
                    f"`{operator_audit_trail.get('contract') or 'missing'}`."
                )
            ),
        ),
        _check(
            check_id="policy-decision-explainability-contract",
            passed=str(policy_decision_explainability.get("contract") or "")
            == "policy-decision-explainability/v1",
            reason=(
                "Policy decision explainability contract is policy-decision-explainability/v1."
                if str(policy_decision_explainability.get("contract") or "")
                == "policy-decision-explainability/v1"
                else (
                    "Policy decision explainability contract is "
                    f"`{policy_decision_explainability.get('contract') or 'missing'}`."
                )
            ),
        ),
    )
    failed_checks = tuple(check for check in checks if not bool(check.get("passed")))
    summary_ready = len(failed_checks) == 0

    control_plane_status = _status(
        summary_ready=summary_ready,
        migration_decision=migration_decision,
        governance_level=governance_level,
        audit_level=audit_level,
        blocked_stages=blocked_stages,
    )
    blockers = _blockers(
        control_plane_status=control_plane_status,
        migration_decision=migration_decision,
        governance_level=governance_level,
        audit_level=audit_level,
        blocked_stages=blocked_stages,
        failed_check_ids=tuple(str(check.get("id") or "") for check in failed_checks),
    )

    return {
        "contract": "operator-control-plane-summary/v1",
        "profile": "phase23-operator-control-plane-summary/v1",
        "summary_ready": summary_ready,
        "control_plane_status": control_plane_status,
        "migration_decision": migration_decision,
        "governance_level": governance_level,
        "audit_level": audit_level,
        "blocked_stage_count": len(blocked_stages),
        "blocked_stages": blocked_stages,
        "blocker_count": len(blockers),
        "blockers": blockers,
        "check_count": len(checks),
        "failed_check_count": len(failed_checks),
        "failed_check_ids": tuple(str(check.get("id") or "") for check in failed_checks),
        "checks": checks,
        "next_control_plane_action": _next_action(control_plane_status=control_plane_status),
        "summary": (
            f"Operator control plane `{control_plane_status}` "
            f"(migration={migration_decision}, governance={governance_level}, audit={audit_level})."
        ),
    }


def _status(
    *,
    summary_ready: bool,
    migration_decision: str,
    governance_level: str,
    audit_level: str,
    blocked_stages: tuple[str, ...],
) -> str:
    if not summary_ready:
        return "blocked"
    if migration_decision == "block" or governance_level == "critical" or audit_level == "critical":
        return "blocked"
    if (
        migration_decision == "review"
        or governance_level in {"review", "escalate"}
        or audit_level == "warning"
        or len(blocked_stages) > 0
    ):
        return "attention"
    return "aligned"


def _blockers(
    *,
    control_plane_status: str,
    migration_decision: str,
    governance_level: str,
    audit_level: str,
    blocked_stages: tuple[str, ...],
    failed_check_ids: tuple[str, ...],
) -> tuple[str, ...]:
    if control_plane_status == "aligned":
        return ()

    blockers: list[str] = [f"contract:{check_id}" for check_id in failed_check_ids if check_id]
    if migration_decision != "allow":
        blockers.append(f"migration:{migration_decision}")
    if governance_level != "none":
        blockers.append(f"governance:{governance_level}")
    if audit_level != "info":
        blockers.append(f"audit:{audit_level}")
    for stage in blocked_stages:
        if stage:
            blockers.append(f"decision-stage:{stage}")
    return tuple(dict.fromkeys(blockers))[:14]


def _next_action(*, control_plane_status: str) -> str:
    if control_plane_status == "aligned":
        return "Operator control plane is aligned. Proceed to governance workflow consolidation."
    if control_plane_status == "attention":
        return "Operator control plane needs attention. Resolve warned stages before consolidation."
    return "Operator control plane is blocked. Resolve critical migration/governance blockers first."


def _check(*, check_id: str, passed: bool, reason: str) -> dict[str, object]:
    return {
        "id": check_id,
        "passed": passed,
        "reason": reason,
    }
