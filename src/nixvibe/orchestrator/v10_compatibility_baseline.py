"""v1.0 compatibility baseline helpers."""

from __future__ import annotations

import hashlib


def build_v10_compatibility_baseline(
    *,
    v10_pathway_scaffold: dict[str, object],
    governance_hardening_escalation: dict[str, object],
    release_policy_execution: dict[str, object],
    release_readiness: dict[str, object],
) -> dict[str, object]:
    pathway_status = str(v10_pathway_scaffold.get("pathway_status") or "blocked")
    escalation_level = str(governance_hardening_escalation.get("escalation_level") or "critical")
    release_policy_decision = str(release_policy_execution.get("decision") or "blocked")
    release_ready = bool(release_readiness.get("ready", False))

    checks = (
        _check(
            check_id="v10-pathway-scaffold-contract",
            passed=str(v10_pathway_scaffold.get("contract") or "") == "v10-pathway-scaffold/v1",
            reason=(
                "v1.0 pathway scaffold contract is v10-pathway-scaffold/v1."
                if str(v10_pathway_scaffold.get("contract") or "") == "v10-pathway-scaffold/v1"
                else (
                    "v1.0 pathway scaffold contract is "
                    f"`{v10_pathway_scaffold.get('contract') or 'missing'}`."
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
            check_id="release-readiness-contract",
            passed=str(release_readiness.get("contract") or "") == "release-readiness/v1",
            reason=(
                "Release readiness contract is release-readiness/v1."
                if str(release_readiness.get("contract") or "") == "release-readiness/v1"
                else (
                    "Release readiness contract is "
                    f"`{release_readiness.get('contract') or 'missing'}`."
                )
            ),
        ),
    )
    failed_checks = tuple(check for check in checks if not bool(check.get("passed")))
    baseline_ready = len(failed_checks) == 0

    compatibility_status = _compatibility_status(
        baseline_ready=baseline_ready,
        pathway_status=pathway_status,
        escalation_level=escalation_level,
        release_policy_decision=release_policy_decision,
        release_ready=release_ready,
    )
    blockers = _blockers(
        compatibility_status=compatibility_status,
        pathway_status=pathway_status,
        escalation_level=escalation_level,
        release_policy_decision=release_policy_decision,
        release_ready=release_ready,
        failed_check_ids=tuple(str(check.get("id") or "") for check in failed_checks),
    )
    compatibility_band = {
        "ready": "stable",
        "hold": "watch",
        "blocked": "risk",
    }[compatibility_status]
    baseline_id = _baseline_id(
        compatibility_status=compatibility_status,
        pathway_status=pathway_status,
        escalation_level=escalation_level,
        release_policy_decision=release_policy_decision,
        release_ready=release_ready,
    )

    return {
        "contract": "v10-compatibility-baseline/v1",
        "profile": "phase22-v10-compatibility-baseline/v1",
        "baseline_id": baseline_id,
        "baseline_ready": baseline_ready,
        "compatibility_status": compatibility_status,
        "compatibility_band": compatibility_band,
        "pathway_status": pathway_status,
        "governance_escalation_level": escalation_level,
        "release_policy_decision": release_policy_decision,
        "release_ready": release_ready,
        "blocker_count": len(blockers),
        "blockers": blockers,
        "check_count": len(checks),
        "failed_check_count": len(failed_checks),
        "failed_check_ids": tuple(str(check.get("id") or "") for check in failed_checks),
        "checks": checks,
        "next_compatibility_action": _next_action(compatibility_status=compatibility_status),
        "summary": (
            f"v1 compatibility baseline `{compatibility_status}` "
            f"(pathway={pathway_status}, governance={escalation_level}, release_policy={release_policy_decision})."
        ),
    }


def _compatibility_status(
    *,
    baseline_ready: bool,
    pathway_status: str,
    escalation_level: str,
    release_policy_decision: str,
    release_ready: bool,
) -> str:
    if not baseline_ready:
        return "blocked"
    if (
        pathway_status == "blocked"
        or escalation_level == "critical"
        or release_policy_decision == "blocked"
        or not release_ready
    ):
        return "blocked"
    if pathway_status == "hold" or escalation_level in {"review", "escalate"}:
        return "hold"
    if release_policy_decision == "manual-ack":
        return "hold"
    return "ready"


def _blockers(
    *,
    compatibility_status: str,
    pathway_status: str,
    escalation_level: str,
    release_policy_decision: str,
    release_ready: bool,
    failed_check_ids: tuple[str, ...],
) -> tuple[str, ...]:
    if compatibility_status == "ready":
        return ()

    blockers: list[str] = [f"contract:{check_id}" for check_id in failed_check_ids if check_id]
    if pathway_status != "ready":
        blockers.append(f"pathway:{pathway_status}")
    if escalation_level != "none":
        blockers.append(f"governance:{escalation_level}")
    if release_policy_decision != "automated":
        blockers.append(f"release-policy:{release_policy_decision}")
    if not release_ready:
        blockers.append("release-readiness:false")
    return tuple(dict.fromkeys(blockers))[:12]


def _next_action(*, compatibility_status: str) -> str:
    if compatibility_status == "ready":
        return "Compatibility baseline is ready. Proceed to migration-safety policy integration."
    if compatibility_status == "hold":
        return "Compatibility baseline is on hold. Resolve governance/pathway holds before migration policy work."
    return "Compatibility baseline is blocked. Resolve critical release/governance blockers first."


def _baseline_id(
    *,
    compatibility_status: str,
    pathway_status: str,
    escalation_level: str,
    release_policy_decision: str,
    release_ready: bool,
) -> str:
    basis = (
        f"{compatibility_status}|{pathway_status}|{escalation_level}|"
        f"{release_policy_decision}|{int(release_ready)}"
    )
    digest = hashlib.sha256(basis.encode("utf-8")).hexdigest()[:12]
    return f"v10-compat-{digest}"


def _check(*, check_id: str, passed: bool, reason: str) -> dict[str, object]:
    return {
        "id": check_id,
        "passed": passed,
        "reason": reason,
    }
