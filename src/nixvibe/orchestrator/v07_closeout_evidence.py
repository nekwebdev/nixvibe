"""v0.7 closeout evidence bundle helpers."""

from __future__ import annotations

import hashlib


def build_v07_closeout_evidence(
    *,
    governance_hardening_escalation: dict[str, object],
    operator_observability_digest: dict[str, object],
    release_policy_execution: dict[str, object],
) -> dict[str, object]:
    escalation_level = str(governance_hardening_escalation.get("escalation_level") or "critical")
    observability_band = str(operator_observability_digest.get("observability_band") or "degraded")
    release_policy_decision = str(release_policy_execution.get("decision") or "blocked")

    checks = (
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
    )
    failed_checks = tuple(check for check in checks if not bool(check.get("passed")))
    evidence_ready = len(failed_checks) == 0

    closeout_category = _closeout_category(
        evidence_ready=evidence_ready,
        escalation_level=escalation_level,
        observability_band=observability_band,
        release_policy_decision=release_policy_decision,
    )
    blockers = _blockers(
        closeout_category=closeout_category,
        governance_hardening_escalation=governance_hardening_escalation,
        release_policy_execution=release_policy_execution,
        observability_band=observability_band,
    )
    evidence_id = _evidence_id(
        closeout_category=closeout_category,
        escalation_level=escalation_level,
        observability_band=observability_band,
        release_policy_decision=release_policy_decision,
    )

    return {
        "contract": "v07-closeout-evidence/v1",
        "profile": "phase21-v07-closeout-evidence/v1",
        "evidence_id": evidence_id,
        "evidence_ready": evidence_ready,
        "closeout_category": closeout_category,
        "escalation_level": escalation_level,
        "observability_band": observability_band,
        "release_policy_decision": release_policy_decision,
        "blocker_count": len(blockers),
        "blockers": blockers,
        "check_count": len(checks),
        "failed_check_count": len(failed_checks),
        "failed_check_ids": tuple(str(check.get("id") or "") for check in failed_checks),
        "checks": checks,
        "next_closeout_action": _next_closeout_action(closeout_category=closeout_category),
        "summary": (
            f"v0.7 closeout evidence `{closeout_category}` "
            f"(governance={escalation_level}, observability={observability_band}, release_policy={release_policy_decision})."
        ),
    }


def _closeout_category(
    *,
    evidence_ready: bool,
    escalation_level: str,
    observability_band: str,
    release_policy_decision: str,
) -> str:
    if not evidence_ready:
        return "blocked"
    if escalation_level == "critical" or release_policy_decision == "blocked":
        return "blocked"
    if escalation_level in {"review", "escalate"} or observability_band == "attention":
        return "hold"
    return "ready"


def _blockers(
    *,
    closeout_category: str,
    governance_hardening_escalation: dict[str, object],
    release_policy_execution: dict[str, object],
    observability_band: str,
) -> tuple[str, ...]:
    if closeout_category == "ready":
        return ()

    blockers: list[str] = []
    for blocker in governance_hardening_escalation.get("blockers", ()):
        text = str(blocker).strip()
        if text:
            blockers.append(text)
    for blocker in release_policy_execution.get("blockers", ()):
        text = str(blocker).strip()
        if text:
            blockers.append(f"release-policy:{text}")
    if observability_band != "healthy":
        blockers.append(f"observability:{observability_band}")
    return tuple(dict.fromkeys(blockers))[:10]


def _next_closeout_action(*, closeout_category: str) -> str:
    if closeout_category == "ready":
        return "v0.7 closeout evidence is ready. Proceed to milestone closeout integration."
    if closeout_category == "hold":
        return "v0.7 closeout evidence is on hold. Resolve governance attention/review escalations."
    return "v0.7 closeout evidence is blocked. Resolve critical governance/release policy blockers."


def _evidence_id(
    *,
    closeout_category: str,
    escalation_level: str,
    observability_band: str,
    release_policy_decision: str,
) -> str:
    basis = f"{closeout_category}|{escalation_level}|{observability_band}|{release_policy_decision}"
    digest = hashlib.sha256(basis.encode("utf-8")).hexdigest()[:12]
    return f"v07-closeout-{digest}"


def _check(*, check_id: str, passed: bool, reason: str) -> dict[str, object]:
    return {
        "id": check_id,
        "passed": passed,
        "reason": reason,
    }
