"""Release execution gate helpers."""

from __future__ import annotations


def build_release_execution_gate(
    *,
    v06_readiness_summary: dict[str, object],
    release_check_command: dict[str, object],
) -> dict[str, object]:
    readiness_band = str(v06_readiness_summary.get("readiness_band") or "blocked")
    release_check_status = str(release_check_command.get("status") or "skipped")

    checks = (
        _check(
            check_id="v06-readiness-summary-contract",
            passed=str(v06_readiness_summary.get("contract") or "") == "v06-readiness-summary/v1",
            reason=(
                "v0.6 readiness summary contract is v06-readiness-summary/v1."
                if str(v06_readiness_summary.get("contract") or "") == "v06-readiness-summary/v1"
                else (
                    "v0.6 readiness summary contract is "
                    f"`{v06_readiness_summary.get('contract') or 'missing'}`."
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
    gate_ready = len(failed_checks) == 0

    decision = _decision(
        gate_ready=gate_ready,
        readiness_band=readiness_band,
        release_check_status=release_check_status,
    )
    blockers = _blockers(
        decision=decision,
        readiness_band=readiness_band,
        release_check_status=release_check_status,
    )

    return {
        "contract": "release-execution-gate/v1",
        "profile": "phase19-release-execution-gate/v1",
        "gate_ready": gate_ready,
        "decision": decision,
        "automated_execution_allowed": decision == "allow",
        "requires_human_acknowledgement": decision == "hold",
        "readiness_band": readiness_band,
        "release_check_status": release_check_status,
        "blocker_count": len(blockers),
        "blockers": blockers,
        "check_count": len(checks),
        "failed_check_count": len(failed_checks),
        "failed_check_ids": tuple(str(check.get("id") or "") for check in failed_checks),
        "checks": checks,
        "next_execution_action": _next_execution_action(decision=decision),
        "summary": (
            f"Release execution gate `{decision}` "
            f"(readiness={readiness_band}, release_check={release_check_status})."
        ),
    }


def _decision(*, gate_ready: bool, readiness_band: str, release_check_status: str) -> str:
    if not gate_ready:
        return "deny"
    if readiness_band == "blocked" or release_check_status == "failed":
        return "deny"
    if readiness_band == "hold" or release_check_status in {"pending", "skipped"}:
        return "hold"
    return "allow"


def _blockers(*, decision: str, readiness_band: str, release_check_status: str) -> tuple[str, ...]:
    if decision == "allow":
        return ()
    blockers: list[str] = []
    if readiness_band != "ready":
        blockers.append(f"readiness-{readiness_band}")
    if release_check_status != "passed":
        blockers.append(f"release-check-{release_check_status}")
    return tuple(dict.fromkeys(blockers))


def _next_execution_action(*, decision: str) -> str:
    if decision == "allow":
        return "Release execution gate is open. Automated release execution may proceed."
    if decision == "hold":
        return "Release execution gate is on hold. Resolve hold blockers or require manual acknowledgement."
    return "Release execution gate is denied. Resolve blocked readiness/check failures before release."


def _check(*, check_id: str, passed: bool, reason: str) -> dict[str, object]:
    return {
        "id": check_id,
        "passed": passed,
        "reason": reason,
    }
