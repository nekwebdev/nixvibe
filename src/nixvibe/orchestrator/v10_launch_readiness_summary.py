"""v1.0 launch readiness summary helpers."""

from __future__ import annotations


def build_v10_launch_readiness_summary(
    *,
    v10_launch_evidence_bundle: dict[str, object],
    release_readiness: dict[str, object],
    benchmark_release_readiness: dict[str, object],
    migration_safety_policy: dict[str, object],
) -> dict[str, object]:
    evidence_status = str(v10_launch_evidence_bundle.get("evidence_status") or "blocked")
    release_ready = bool(release_readiness.get("ready", False))
    benchmark_ready = bool(benchmark_release_readiness.get("ready", False))
    migration_policy_decision = str(migration_safety_policy.get("policy_decision") or "block")

    checks = (
        _check(
            check_id="v10-launch-evidence-bundle-contract",
            passed=str(v10_launch_evidence_bundle.get("contract") or "")
            == "v10-launch-evidence-bundle/v1",
            reason=(
                "v1 launch evidence bundle contract is v10-launch-evidence-bundle/v1."
                if str(v10_launch_evidence_bundle.get("contract") or "")
                == "v10-launch-evidence-bundle/v1"
                else (
                    "v1 launch evidence bundle contract is "
                    f"`{v10_launch_evidence_bundle.get('contract') or 'missing'}`."
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
        _check(
            check_id="benchmark-release-readiness-contract",
            passed=str(benchmark_release_readiness.get("contract") or "")
            == "benchmark-release-readiness/v1",
            reason=(
                "Benchmark release readiness contract is benchmark-release-readiness/v1."
                if str(benchmark_release_readiness.get("contract") or "")
                == "benchmark-release-readiness/v1"
                else (
                    "Benchmark release readiness contract is "
                    f"`{benchmark_release_readiness.get('contract') or 'missing'}`."
                )
            ),
        ),
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
    )
    failed_checks = tuple(check for check in checks if not bool(check.get("passed")))
    summary_ready = len(failed_checks) == 0

    readiness_status = _readiness_status(
        summary_ready=summary_ready,
        evidence_status=evidence_status,
        release_ready=release_ready,
        benchmark_ready=benchmark_ready,
        migration_policy_decision=migration_policy_decision,
    )
    blockers = _blockers(
        readiness_status=readiness_status,
        evidence_status=evidence_status,
        release_ready=release_ready,
        benchmark_ready=benchmark_ready,
        migration_policy_decision=migration_policy_decision,
        failed_check_ids=tuple(str(check.get("id") or "") for check in failed_checks),
    )
    launch_gate = {
        "ready": "open",
        "hold": "review",
        "blocked": "closed",
    }[readiness_status]

    return {
        "contract": "v10-launch-readiness-summary/v1",
        "profile": "phase24-v10-launch-readiness-summary/v1",
        "summary_ready": summary_ready,
        "readiness_status": readiness_status,
        "launch_gate": launch_gate,
        "ga_ready": readiness_status == "ready",
        "evidence_status": evidence_status,
        "release_ready": release_ready,
        "benchmark_ready": benchmark_ready,
        "migration_policy_decision": migration_policy_decision,
        "blocker_count": len(blockers),
        "blockers": blockers,
        "check_count": len(checks),
        "failed_check_count": len(failed_checks),
        "failed_check_ids": tuple(str(check.get("id") or "") for check in failed_checks),
        "checks": checks,
        "next_launch_readiness_action": _next_action(readiness_status=readiness_status),
        "summary": (
            f"v1 launch readiness `{readiness_status}` "
            f"(evidence={evidence_status}, migration={migration_policy_decision}, "
            f"release={release_ready}, benchmark={benchmark_ready})."
        ),
    }


def _readiness_status(
    *,
    summary_ready: bool,
    evidence_status: str,
    release_ready: bool,
    benchmark_ready: bool,
    migration_policy_decision: str,
) -> str:
    if not summary_ready:
        return "blocked"
    if (
        evidence_status == "blocked"
        or not release_ready
        or not benchmark_ready
        or migration_policy_decision == "block"
    ):
        return "blocked"
    if evidence_status == "hold" or migration_policy_decision == "review":
        return "hold"
    return "ready"


def _blockers(
    *,
    readiness_status: str,
    evidence_status: str,
    release_ready: bool,
    benchmark_ready: bool,
    migration_policy_decision: str,
    failed_check_ids: tuple[str, ...],
) -> tuple[str, ...]:
    if readiness_status == "ready":
        return ()

    blockers: list[str] = [f"contract:{check_id}" for check_id in failed_check_ids if check_id]
    if evidence_status != "ready":
        blockers.append(f"evidence:{evidence_status}")
    if not release_ready:
        blockers.append("release-ready:false")
    if not benchmark_ready:
        blockers.append("benchmark-ready:false")
    if migration_policy_decision != "allow":
        blockers.append(f"migration:{migration_policy_decision}")
    return tuple(dict.fromkeys(blockers))[:12]


def _next_action(*, readiness_status: str) -> str:
    if readiness_status == "ready":
        return "Launch readiness is ready. Proceed to final GA acceptance and milestone closeout."
    if readiness_status == "hold":
        return "Launch readiness is on hold. Resolve guarded migration/evidence gates before closeout."
    return "Launch readiness is blocked. Resolve critical release and migration blockers first."


def _check(*, check_id: str, passed: bool, reason: str) -> dict[str, object]:
    return {
        "id": check_id,
        "passed": passed,
        "reason": reason,
    }
