"""v0.6 readiness summary helpers."""

from __future__ import annotations


def build_v06_readiness_summary(
    *,
    release_candidate_evidence: dict[str, object],
    release_check_command: dict[str, object],
    release_readiness: dict[str, object],
    alert_policy_gate: dict[str, object],
) -> dict[str, object]:
    evidence_category = str(release_candidate_evidence.get("readiness_category") or "blocked")
    release_check_status = str(release_check_command.get("status") or "skipped")
    gate_status = str(alert_policy_gate.get("gate_status") or "blocked")
    release_ready = bool(release_readiness.get("ready"))

    checks = (
        _check(
            check_id="evidence-contract",
            passed=str(release_candidate_evidence.get("contract") or "")
            == "release-candidate-evidence/v1",
            reason=(
                "Release candidate evidence contract is release-candidate-evidence/v1."
                if str(release_candidate_evidence.get("contract") or "")
                == "release-candidate-evidence/v1"
                else (
                    "Release candidate evidence contract is "
                    f"`{release_candidate_evidence.get('contract') or 'missing'}`."
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
        _check(
            check_id="release-readiness-contract",
            passed=str(release_readiness.get("contract") or "") == "release-readiness/v1",
            reason=(
                "Release readiness contract is release-readiness/v1."
                if str(release_readiness.get("contract") or "") == "release-readiness/v1"
                else f"Release readiness contract is `{release_readiness.get('contract') or 'missing'}`."
            ),
        ),
        _check(
            check_id="alert-policy-gate-contract",
            passed=str(alert_policy_gate.get("contract") or "") == "alert-policy-gate/v1",
            reason=(
                "Alert policy gate contract is alert-policy-gate/v1."
                if str(alert_policy_gate.get("contract") or "") == "alert-policy-gate/v1"
                else f"Alert policy gate contract is `{alert_policy_gate.get('contract') or 'missing'}`."
            ),
        ),
    )
    failed_checks = tuple(check for check in checks if not bool(check.get("passed")))
    summary_ready = len(failed_checks) == 0

    readiness_band = _readiness_band(
        summary_ready=summary_ready,
        evidence_category=evidence_category,
        release_check_status=release_check_status,
    )
    blockers = _blockers(
        readiness_band=readiness_band,
        evidence_category=evidence_category,
        release_check_status=release_check_status,
        gate_status=gate_status,
        release_ready=release_ready,
    )

    return {
        "contract": "v06-readiness-summary/v1",
        "profile": "phase18-v06-readiness-summary/v1",
        "summary_ready": summary_ready,
        "readiness_band": readiness_band,
        "evidence_category": evidence_category,
        "release_check_status": release_check_status,
        "release_ready": release_ready,
        "gate_status": gate_status,
        "blocker_count": len(blockers),
        "blockers": blockers,
        "check_count": len(checks),
        "failed_check_count": len(failed_checks),
        "failed_check_ids": tuple(str(check.get("id") or "") for check in failed_checks),
        "checks": checks,
        "next_readiness_action": _next_readiness_action(readiness_band=readiness_band),
        "summary": (
            f"v0.6 readiness `{readiness_band}` "
            f"(evidence={evidence_category}, release_check={release_check_status})."
        ),
    }


def _readiness_band(
    *,
    summary_ready: bool,
    evidence_category: str,
    release_check_status: str,
) -> str:
    if not summary_ready:
        return "blocked"
    if evidence_category == "blocked" or release_check_status == "failed":
        return "blocked"
    if evidence_category == "hold" or release_check_status in {"pending", "skipped"}:
        return "hold"
    return "ready"


def _blockers(
    *,
    readiness_band: str,
    evidence_category: str,
    release_check_status: str,
    gate_status: str,
    release_ready: bool,
) -> tuple[str, ...]:
    blockers: list[str] = []
    if evidence_category == "blocked":
        blockers.append("release-candidate-evidence-blocked")
    if evidence_category == "hold":
        blockers.append("release-candidate-evidence-hold")
    if release_check_status == "failed":
        blockers.append("release-check-failed")
    if release_check_status in {"pending", "skipped"}:
        blockers.append(f"release-check-{release_check_status}")
    if gate_status != "open":
        blockers.append(f"policy-gate-{gate_status}")
    if not release_ready:
        blockers.append("release-readiness-false")
    if readiness_band == "ready":
        return ()
    return tuple(dict.fromkeys(blockers))


def _next_readiness_action(*, readiness_band: str) -> str:
    if readiness_band == "ready":
        return "v0.6 readiness is ready. Proceed to milestone closeout acceptance."
    if readiness_band == "hold":
        return "v0.6 readiness is on hold. Clear remaining warning and release-check blockers."
    return "v0.6 readiness is blocked. Resolve critical evidence/policy/release-check failures."


def _check(*, check_id: str, passed: bool, reason: str) -> dict[str, object]:
    return {
        "id": check_id,
        "passed": passed,
        "reason": reason,
    }
