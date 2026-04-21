"""Release-candidate evidence bundle helpers."""

from __future__ import annotations

import hashlib


def build_release_candidate_evidence(
    *,
    release_readiness: dict[str, object],
    outcome_alert: dict[str, object],
    alert_policy_gate: dict[str, object],
) -> dict[str, object]:
    alert_status = str(outcome_alert.get("alert_status") or "blocked")
    gate_status = str(alert_policy_gate.get("gate_status") or "blocked")
    release_ready = bool(release_readiness.get("ready"))

    checks = (
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
            check_id="outcome-alert-contract",
            passed=str(outcome_alert.get("contract") or "") == "outcome-alert/v1",
            reason=(
                "Outcome alert contract is outcome-alert/v1."
                if str(outcome_alert.get("contract") or "") == "outcome-alert/v1"
                else f"Outcome alert contract is `{outcome_alert.get('contract') or 'missing'}`."
            ),
        ),
        _check(
            check_id="alert-policy-gate-contract",
            passed=str(alert_policy_gate.get("contract") or "") == "alert-policy-gate/v1",
            reason=(
                "Alert policy gate contract is alert-policy-gate/v1."
                if str(alert_policy_gate.get("contract") or "") == "alert-policy-gate/v1"
                else (
                    f"Alert policy gate contract is `{alert_policy_gate.get('contract') or 'missing'}`."
                )
            ),
        ),
    )
    failed_checks = tuple(check for check in checks if not bool(check.get("passed")))
    evidence_ready = len(failed_checks) == 0

    checklist = (
        _item(
            item_id="release-ready",
            required=True,
            passed=release_ready,
            severity="high",
            reason="Release readiness is true." if release_ready else "Release readiness is false.",
        ),
        _item(
            item_id="alert-clear",
            required=True,
            passed=alert_status == "none",
            severity="critical",
            reason=(
                "Outcome alert status is none."
                if alert_status == "none"
                else f"Outcome alert status is `{alert_status}`."
            ),
        ),
        _item(
            item_id="policy-open",
            required=True,
            passed=gate_status == "open",
            severity="critical",
            reason=(
                "Alert policy gate status is open."
                if gate_status == "open"
                else f"Alert policy gate status is `{gate_status}`."
            ),
        ),
    )
    failed_required_items = tuple(item for item in checklist if not bool(item.get("passed")))
    readiness_category = _readiness_category(
        evidence_ready=evidence_ready,
        alert_status=alert_status,
        gate_status=gate_status,
        failed_required_items=failed_required_items,
    )
    evidence_id = _evidence_id(
        readiness_category=readiness_category,
        alert_status=alert_status,
        gate_status=gate_status,
        release_ready=release_ready,
    )

    return {
        "contract": "release-candidate-evidence/v1",
        "profile": "phase18-release-candidate-evidence/v1",
        "evidence_id": evidence_id,
        "evidence_ready": evidence_ready,
        "readiness_category": readiness_category,
        "release_ready": release_ready,
        "alert_status": alert_status,
        "gate_status": gate_status,
        "check_count": len(checks),
        "failed_check_count": len(failed_checks),
        "failed_check_ids": tuple(str(check.get("id") or "") for check in failed_checks),
        "checks": checks,
        "required_item_count": len(checklist),
        "passed_item_count": len(checklist) - len(failed_required_items),
        "failed_item_count": len(failed_required_items),
        "failed_item_ids": tuple(str(item.get("id") or "") for item in failed_required_items),
        "checklist": checklist,
        "next_evidence_action": _next_evidence_action(readiness_category=readiness_category),
        "summary": (
            f"Release candidate evidence `{readiness_category}` "
            f"(release_ready={release_ready}, alert={alert_status}, gate={gate_status})."
        ),
    }


def _readiness_category(
    *,
    evidence_ready: bool,
    alert_status: str,
    gate_status: str,
    failed_required_items: tuple[dict[str, object], ...],
) -> str:
    if not evidence_ready:
        return "blocked"
    if alert_status in {"critical", "blocked"} or gate_status == "blocked":
        return "blocked"
    if len(failed_required_items) > 0:
        return "hold"
    return "ready"


def _evidence_id(
    *,
    readiness_category: str,
    alert_status: str,
    gate_status: str,
    release_ready: bool,
) -> str:
    basis = f"{readiness_category}|{alert_status}|{gate_status}|{int(release_ready)}"
    digest = hashlib.sha256(basis.encode("utf-8")).hexdigest()[:12]
    return f"release-evidence-{digest}"


def _next_evidence_action(*, readiness_category: str) -> str:
    if readiness_category == "ready":
        return "Evidence bundle is release-candidate ready. Proceed to readiness summary."
    if readiness_category == "hold":
        return "Evidence bundle is on hold. Clear warning conditions and reopen policy gates."
    return "Evidence bundle is blocked. Resolve critical alert/policy failures before release."


def _check(*, check_id: str, passed: bool, reason: str) -> dict[str, object]:
    return {
        "id": check_id,
        "passed": passed,
        "reason": reason,
    }


def _item(*, item_id: str, required: bool, passed: bool, severity: str, reason: str) -> dict[str, object]:
    return {
        "id": item_id,
        "required": required,
        "passed": passed,
        "severity": severity,
        "reason": reason,
    }
