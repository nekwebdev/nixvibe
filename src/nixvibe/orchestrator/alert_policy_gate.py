"""Alert-aware policy gate helpers."""

from __future__ import annotations


def build_alert_policy_gate(
    *,
    outcome_alert: dict[str, object],
    release_readiness: dict[str, object],
    apply_safety_escalation: dict[str, object],
) -> dict[str, object]:
    alert_status = str(outcome_alert.get("alert_status") or "blocked")
    release_ready = bool(release_readiness.get("ready"))
    escalation_tier = str(apply_safety_escalation.get("tier") or "none")

    checks = (
        _check(
            check_id="outcome-alert-contract",
            passed=str(outcome_alert.get("contract") or "") == "outcome-alert/v1",
            reason=(
                "Outcome alert contract is outcome-alert/v1."
                if str(outcome_alert.get("contract") or "") == "outcome-alert/v1"
                else f"Outcome alert contract is `{outcome_alert.get('contract') or 'missing'}`."
            ),
        ),
        _check(
            check_id="release-readiness-contract",
            passed=str(release_readiness.get("contract") or "") == "release-readiness/v1",
            reason=(
                "Release readiness contract is release-readiness/v1."
                if str(release_readiness.get("contract") or "") == "release-readiness/v1"
                else (
                    f"Release readiness contract is `{release_readiness.get('contract') or 'missing'}`."
                )
            ),
        ),
        _check(
            check_id="apply-escalation-shape",
            passed=isinstance(apply_safety_escalation.get("tier"), str),
            reason=(
                "Apply safety escalation tier present."
                if isinstance(apply_safety_escalation.get("tier"), str)
                else "Apply safety escalation tier missing."
            ),
        ),
    )
    failed_checks = tuple(check for check in checks if not bool(check.get("passed")))
    gate_ready = len(failed_checks) == 0

    apply_gate, release_gate = _gate_decisions(
        gate_ready=gate_ready,
        alert_status=alert_status,
        release_ready=release_ready,
        escalation_tier=escalation_tier,
    )
    gate_status = _gate_status(
        gate_ready=gate_ready,
        alert_status=alert_status,
        apply_gate=apply_gate,
        release_gate=release_gate,
        escalation_tier=escalation_tier,
    )
    policy_actions = _policy_actions(
        gate_status=gate_status,
        apply_gate=apply_gate,
        release_gate=release_gate,
        alert_status=alert_status,
    )

    return {
        "contract": "alert-policy-gate/v1",
        "profile": "phase17-alert-policy-gate/v1",
        "gate_ready": gate_ready,
        "gate_status": gate_status,
        "alert_status": alert_status,
        "apply_gate": apply_gate,
        "release_gate": release_gate,
        "release_ready": release_ready,
        "escalation_tier": escalation_tier,
        "requires_acknowledgement": gate_status == "warn",
        "policy_actions": policy_actions,
        "check_count": len(checks),
        "failed_check_count": len(failed_checks),
        "failed_check_ids": tuple(str(check.get("id") or "") for check in failed_checks),
        "checks": checks,
        "next_policy_action": _next_policy_action(gate_status=gate_status),
        "summary": (
            f"Alert policy gate `{gate_status}` "
            f"(apply={apply_gate}, release={release_gate}, alert={alert_status})."
        ),
    }


def _gate_decisions(
    *,
    gate_ready: bool,
    alert_status: str,
    release_ready: bool,
    escalation_tier: str,
) -> tuple[str, str]:
    if not gate_ready:
        return "deny", "deny"

    base_apply_gate = "allow"
    if escalation_tier in {"blocked", "guarded"}:
        base_apply_gate = "deny"
    elif escalation_tier == "advisory":
        base_apply_gate = "allow_with_warning"

    if alert_status in {"critical", "blocked"}:
        return "deny", "deny"
    if alert_status == "warning":
        if base_apply_gate == "allow":
            base_apply_gate = "allow_with_warning"
        return base_apply_gate, "deny"

    release_gate = "allow" if release_ready else "deny"
    return base_apply_gate, release_gate


def _gate_status(
    *,
    gate_ready: bool,
    alert_status: str,
    apply_gate: str,
    release_gate: str,
    escalation_tier: str,
) -> str:
    if not gate_ready or alert_status in {"critical", "blocked"}:
        return "blocked"
    if apply_gate == "deny" and escalation_tier in {"blocked", "guarded"}:
        return "blocked"
    if apply_gate == "allow_with_warning" or release_gate == "deny":
        return "warn"
    return "open"


def _policy_actions(
    *,
    gate_status: str,
    apply_gate: str,
    release_gate: str,
    alert_status: str,
) -> tuple[str, ...]:
    actions: list[str] = []
    if gate_status == "blocked":
        actions.append("hold-apply")
        actions.append("hold-release")
    elif apply_gate == "allow_with_warning":
        actions.append("require-operator-ack")

    if release_gate == "deny":
        actions.append("hold-release")
    if alert_status == "warning":
        actions.append("track-warning-alert")
    if alert_status == "critical":
        actions.append("escalate-critical-alert")
    return tuple(dict.fromkeys(actions))


def _next_policy_action(*, gate_status: str) -> str:
    if gate_status == "blocked":
        return "Policy gates blocked. Resolve critical/blocked alert conditions before apply or release."
    if gate_status == "warn":
        return "Policy gates warn. Require operator acknowledgement and keep release on hold."
    return "Policy gates open. Continue apply/release flow under normal checks."


def _check(*, check_id: str, passed: bool, reason: str) -> dict[str, object]:
    return {
        "id": check_id,
        "passed": passed,
        "reason": reason,
    }
