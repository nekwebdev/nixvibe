"""v1.0 launch evidence bundle helpers."""

from __future__ import annotations


def build_v10_launch_evidence_bundle(
    *,
    governance_workflow_consolidation: dict[str, object],
    operator_control_plane_summary: dict[str, object],
    benchmark_release_readiness: dict[str, object],
    release_policy_execution: dict[str, object],
) -> dict[str, object]:
    consolidation_status = str(
        governance_workflow_consolidation.get("consolidation_status") or "blocked"
    )
    control_plane_status = str(operator_control_plane_summary.get("control_plane_status") or "blocked")
    benchmark_ready = bool(benchmark_release_readiness.get("ready", False))
    release_policy_decision = str(release_policy_execution.get("decision") or "blocked")

    checks = (
        _check(
            check_id="governance-workflow-consolidation-contract",
            passed=str(governance_workflow_consolidation.get("contract") or "")
            == "governance-workflow-consolidation/v1",
            reason=(
                "Governance workflow consolidation contract is governance-workflow-consolidation/v1."
                if str(governance_workflow_consolidation.get("contract") or "")
                == "governance-workflow-consolidation/v1"
                else (
                    "Governance workflow consolidation contract is "
                    f"`{governance_workflow_consolidation.get('contract') or 'missing'}`."
                )
            ),
        ),
        _check(
            check_id="operator-control-plane-summary-contract",
            passed=str(operator_control_plane_summary.get("contract") or "")
            == "operator-control-plane-summary/v1",
            reason=(
                "Operator control-plane summary contract is operator-control-plane-summary/v1."
                if str(operator_control_plane_summary.get("contract") or "")
                == "operator-control-plane-summary/v1"
                else (
                    "Operator control-plane summary contract is "
                    f"`{operator_control_plane_summary.get('contract') or 'missing'}`."
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

    evidence_status = _evidence_status(
        evidence_ready=evidence_ready,
        consolidation_status=consolidation_status,
        control_plane_status=control_plane_status,
        benchmark_ready=benchmark_ready,
        release_policy_decision=release_policy_decision,
    )
    blockers = _blockers(
        evidence_status=evidence_status,
        consolidation_status=consolidation_status,
        control_plane_status=control_plane_status,
        benchmark_ready=benchmark_ready,
        release_policy_decision=release_policy_decision,
        failed_check_ids=tuple(str(check.get("id") or "") for check in failed_checks),
    )
    evidence_band = {
        "ready": "stable",
        "hold": "watch",
        "blocked": "risk",
    }[evidence_status]

    return {
        "contract": "v10-launch-evidence-bundle/v1",
        "profile": "phase24-v10-launch-evidence-bundle/v1",
        "evidence_ready": evidence_ready,
        "evidence_status": evidence_status,
        "evidence_band": evidence_band,
        "launch_ready": evidence_status == "ready",
        "consolidation_status": consolidation_status,
        "control_plane_status": control_plane_status,
        "benchmark_ready": benchmark_ready,
        "release_policy_decision": release_policy_decision,
        "blocker_count": len(blockers),
        "blockers": blockers,
        "check_count": len(checks),
        "failed_check_count": len(failed_checks),
        "failed_check_ids": tuple(str(check.get("id") or "") for check in failed_checks),
        "checks": checks,
        "next_launch_evidence_action": _next_action(evidence_status=evidence_status),
        "summary": (
            f"v1 launch evidence `{evidence_status}` "
            f"(consolidation={consolidation_status}, control_plane={control_plane_status}, "
            f"release_policy={release_policy_decision})."
        ),
    }


def _evidence_status(
    *,
    evidence_ready: bool,
    consolidation_status: str,
    control_plane_status: str,
    benchmark_ready: bool,
    release_policy_decision: str,
) -> str:
    if not evidence_ready:
        return "blocked"
    if (
        consolidation_status == "blocked"
        or control_plane_status == "blocked"
        or not benchmark_ready
        or release_policy_decision == "blocked"
    ):
        return "blocked"
    if (
        consolidation_status == "review"
        or control_plane_status == "attention"
        or release_policy_decision == "manual-ack"
    ):
        return "hold"
    return "ready"


def _blockers(
    *,
    evidence_status: str,
    consolidation_status: str,
    control_plane_status: str,
    benchmark_ready: bool,
    release_policy_decision: str,
    failed_check_ids: tuple[str, ...],
) -> tuple[str, ...]:
    if evidence_status == "ready":
        return ()

    blockers: list[str] = [f"contract:{check_id}" for check_id in failed_check_ids if check_id]
    if consolidation_status != "consolidated":
        blockers.append(f"consolidation:{consolidation_status}")
    if control_plane_status != "aligned":
        blockers.append(f"control-plane:{control_plane_status}")
    if not benchmark_ready:
        blockers.append("benchmark-ready:false")
    if release_policy_decision != "automated":
        blockers.append(f"release-policy:{release_policy_decision}")
    return tuple(dict.fromkeys(blockers))[:12]


def _next_action(*, evidence_status: str) -> str:
    if evidence_status == "ready":
        return "Launch evidence is ready. Proceed to launch-readiness summary integration."
    if evidence_status == "hold":
        return "Launch evidence is on hold. Resolve guarded controls before readiness summary."
    return "Launch evidence is blocked. Resolve critical release and governance blockers first."


def _check(*, check_id: str, passed: bool, reason: str) -> dict[str, object]:
    return {
        "id": check_id,
        "passed": passed,
        "reason": reason,
    }
