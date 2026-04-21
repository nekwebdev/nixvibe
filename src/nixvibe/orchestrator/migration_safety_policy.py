"""Migration safety policy integration helpers."""

from __future__ import annotations


def build_migration_safety_policy(
    *,
    v10_compatibility_baseline: dict[str, object],
    apply_safety_escalation: dict[str, object],
    controlled_override_workflow: dict[str, object],
    release_policy_execution: dict[str, object],
) -> dict[str, object]:
    compatibility_status = str(v10_compatibility_baseline.get("compatibility_status") or "blocked")
    apply_tier = str(apply_safety_escalation.get("tier") or "blocked")
    override_decision = str(controlled_override_workflow.get("decision") or "none")
    release_policy_decision = str(release_policy_execution.get("decision") or "blocked")

    checks = (
        _check(
            check_id="v10-compatibility-baseline-contract",
            passed=str(v10_compatibility_baseline.get("contract") or "")
            == "v10-compatibility-baseline/v1",
            reason=(
                "v1 compatibility baseline contract is v10-compatibility-baseline/v1."
                if str(v10_compatibility_baseline.get("contract") or "")
                == "v10-compatibility-baseline/v1"
                else (
                    "v1 compatibility baseline contract is "
                    f"`{v10_compatibility_baseline.get('contract') or 'missing'}`."
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
    policy_ready = len(failed_checks) == 0

    policy_decision = _policy_decision(
        policy_ready=policy_ready,
        compatibility_status=compatibility_status,
        apply_tier=apply_tier,
        override_decision=override_decision,
        release_policy_decision=release_policy_decision,
    )
    blockers = _blockers(
        policy_decision=policy_decision,
        compatibility_status=compatibility_status,
        apply_tier=apply_tier,
        override_decision=override_decision,
        release_policy_decision=release_policy_decision,
        failed_check_ids=tuple(str(check.get("id") or "") for check in failed_checks),
    )

    policy_level = {
        "allow": "open",
        "review": "guarded",
        "block": "strict",
    }[policy_decision]

    return {
        "contract": "migration-safety-policy/v1",
        "profile": "phase22-migration-safety-policy/v1",
        "policy_ready": policy_ready,
        "policy_decision": policy_decision,
        "policy_level": policy_level,
        "compatibility_status": compatibility_status,
        "apply_tier": apply_tier,
        "override_decision": override_decision,
        "release_policy_decision": release_policy_decision,
        "migration_ready": policy_decision == "allow",
        "requires_human_confirmation": policy_decision == "review",
        "blocker_count": len(blockers),
        "blockers": blockers,
        "check_count": len(checks),
        "failed_check_count": len(failed_checks),
        "failed_check_ids": tuple(str(check.get("id") or "") for check in failed_checks),
        "checks": checks,
        "next_migration_action": _next_action(policy_decision=policy_decision),
        "summary": (
            f"Migration safety policy `{policy_decision}` "
            f"(compatibility={compatibility_status}, apply={apply_tier}, release_policy={release_policy_decision})."
        ),
    }


def _policy_decision(
    *,
    policy_ready: bool,
    compatibility_status: str,
    apply_tier: str,
    override_decision: str,
    release_policy_decision: str,
) -> str:
    if not policy_ready:
        return "block"
    if (
        compatibility_status == "blocked"
        or apply_tier == "blocked"
        or release_policy_decision == "blocked"
        or override_decision == "deny"
    ):
        return "block"
    if (
        compatibility_status == "hold"
        or apply_tier in {"guarded", "advisory"}
        or release_policy_decision == "manual-ack"
        or override_decision == "allow-with-confirmation"
    ):
        return "review"
    return "allow"


def _blockers(
    *,
    policy_decision: str,
    compatibility_status: str,
    apply_tier: str,
    override_decision: str,
    release_policy_decision: str,
    failed_check_ids: tuple[str, ...],
) -> tuple[str, ...]:
    if policy_decision == "allow":
        return ()

    blockers: list[str] = [f"contract:{check_id}" for check_id in failed_check_ids if check_id]
    if compatibility_status != "ready":
        blockers.append(f"compatibility:{compatibility_status}")
    if apply_tier != "none":
        blockers.append(f"apply-tier:{apply_tier}")
    if override_decision != "none":
        blockers.append(f"override:{override_decision}")
    if release_policy_decision != "automated":
        blockers.append(f"release-policy:{release_policy_decision}")
    return tuple(dict.fromkeys(blockers))[:12]


def _next_action(*, policy_decision: str) -> str:
    if policy_decision == "allow":
        return "Migration safety policy allows progress. Continue compatibility hardening work."
    if policy_decision == "review":
        return "Migration safety policy requires review. Complete guarded checks before migration steps."
    return "Migration safety policy blocks progress. Resolve critical blockers before migration steps."


def _check(*, check_id: str, passed: bool, reason: str) -> dict[str, object]:
    return {
        "id": check_id,
        "passed": passed,
        "reason": reason,
    }
