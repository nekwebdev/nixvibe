"""Release policy execution integration helpers."""

from __future__ import annotations


def build_release_policy_execution(
    *,
    release_execution_gate: dict[str, object],
    controlled_override_workflow: dict[str, object],
    release_check_command: dict[str, object],
) -> dict[str, object]:
    gate_decision = str(release_execution_gate.get("decision") or "deny")
    gate_requires_ack = bool(release_execution_gate.get("requires_human_acknowledgement", False))
    override_requested = bool(controlled_override_workflow.get("override_requested", False))
    override_decision = str(controlled_override_workflow.get("decision") or "none")
    release_check_status = str(release_check_command.get("status") or "skipped")

    checks = (
        _check(
            check_id="release-execution-gate-contract",
            passed=str(release_execution_gate.get("contract") or "") == "release-execution-gate/v1",
            reason=(
                "Release execution gate contract is release-execution-gate/v1."
                if str(release_execution_gate.get("contract") or "") == "release-execution-gate/v1"
                else (
                    "Release execution gate contract is "
                    f"`{release_execution_gate.get('contract') or 'missing'}`."
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
            check_id="release-check-contract",
            passed=str(release_check_command.get("contract") or "") == "release-check-command/v1",
            reason=(
                "Release check command contract is release-check-command/v1."
                if str(release_check_command.get("contract") or "") == "release-check-command/v1"
                else f"Release check command contract is `{release_check_command.get('contract') or 'missing'}`."
            ),
        ),
    )
    failed_checks = tuple(check for check in checks if not bool(check.get("passed")))
    policy_ready = len(failed_checks) == 0

    blocked_override_ids = _blocked_override_ids(controlled_override_workflow=controlled_override_workflow)
    decision = _decision(
        policy_ready=policy_ready,
        gate_decision=gate_decision,
        gate_requires_ack=gate_requires_ack,
        override_requested=override_requested,
        override_decision=override_decision,
    )
    blockers = _blockers(
        decision=decision,
        gate_decision=gate_decision,
        gate_blockers=release_execution_gate.get("blockers"),
        override_requested=override_requested,
        override_decision=override_decision,
        blocked_override_ids=blocked_override_ids,
        release_check_status=release_check_status,
    )
    requires_human_acknowledgement = decision == "manual-ack"
    automated_release_enabled = decision == "automated"

    return {
        "contract": "release-policy-execution/v1",
        "profile": "phase19-release-policy-execution/v1",
        "policy_ready": policy_ready,
        "decision": decision,
        "automated_release_enabled": automated_release_enabled,
        "requires_human_acknowledgement": requires_human_acknowledgement,
        "gate_decision": gate_decision,
        "override_requested": override_requested,
        "override_decision": override_decision,
        "allowed_overrides": tuple(str(value) for value in controlled_override_workflow.get("allowed_overrides", ())),
        "blocked_override_ids": blocked_override_ids,
        "release_check_status": release_check_status,
        "blocker_count": len(blockers),
        "blockers": blockers,
        "check_count": len(checks),
        "failed_check_count": len(failed_checks),
        "failed_check_ids": tuple(str(check.get("id") or "") for check in failed_checks),
        "checks": checks,
        "execution_actions": _execution_actions(decision=decision),
        "next_policy_action": _next_policy_action(decision=decision),
        "summary": (
            f"Release policy execution `{decision}` "
            f"(gate={gate_decision}, override={override_decision}, release_check={release_check_status})."
        ),
    }


def _decision(
    *,
    policy_ready: bool,
    gate_decision: str,
    gate_requires_ack: bool,
    override_requested: bool,
    override_decision: str,
) -> str:
    if not policy_ready:
        return "blocked"
    if gate_decision == "deny":
        return "blocked"
    if override_requested and override_decision == "deny":
        return "blocked"
    if gate_decision == "hold":
        return "manual-ack"
    if gate_requires_ack:
        return "manual-ack"
    if override_decision == "allow-with-confirmation":
        return "manual-ack"
    return "automated"


def _blockers(
    *,
    decision: str,
    gate_decision: str,
    gate_blockers: object,
    override_requested: bool,
    override_decision: str,
    blocked_override_ids: tuple[str, ...],
    release_check_status: str,
) -> tuple[str, ...]:
    if decision == "automated":
        return ()

    blockers: list[str] = []
    if gate_decision != "allow":
        blockers.extend(str(item) for item in (gate_blockers or ()) if str(item))
    if override_requested and override_decision == "deny":
        blockers.extend(f"override-{override_id}" for override_id in blocked_override_ids)
    if release_check_status in {"pending", "skipped"}:
        blockers.append(f"release-check-{release_check_status}")
    if release_check_status == "failed":
        blockers.append("release-check-failed")
    return tuple(dict.fromkeys(blockers))


def _execution_actions(*, decision: str) -> tuple[str, ...]:
    if decision == "automated":
        return (
            "execute-release-check-command",
            "create-release-tag",
            "publish-release-notes",
        )
    if decision == "manual-ack":
        return (
            "require-human-acknowledgement",
            "rerun-release-check-and-confirm",
        )
    return (
        "resolve-release-policy-blockers",
        "re-evaluate-release-execution-gate",
    )


def _next_policy_action(*, decision: str) -> str:
    if decision == "automated":
        return "Release policy execution is automated. Proceed with release operations."
    if decision == "manual-ack":
        return "Release policy execution requires human acknowledgement before release operations."
    return "Release policy execution is blocked. Resolve blockers before release operations."


def _check(*, check_id: str, passed: bool, reason: str) -> dict[str, object]:
    return {
        "id": check_id,
        "passed": passed,
        "reason": reason,
    }


def _blocked_override_ids(*, controlled_override_workflow: dict[str, object]) -> tuple[str, ...]:
    blocked: list[str] = []
    for item in controlled_override_workflow.get("blocked_overrides", ()):
        if isinstance(item, dict):
            blocked_id = str(item.get("id") or "")
            if blocked_id:
                blocked.append(blocked_id)
    return tuple(dict.fromkeys(blocked))
