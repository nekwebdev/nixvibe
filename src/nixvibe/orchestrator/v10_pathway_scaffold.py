"""v1.0 pathway scaffold helpers."""

from __future__ import annotations

import hashlib


def build_v10_pathway_scaffold(
    *,
    v07_closeout_evidence: dict[str, object],
    governance_hardening_escalation: dict[str, object],
    benchmark_release_readiness: dict[str, object],
    release_policy_execution: dict[str, object],
) -> dict[str, object]:
    closeout_category = str(v07_closeout_evidence.get("closeout_category") or "blocked")
    escalation_level = str(governance_hardening_escalation.get("escalation_level") or "critical")
    benchmark_ready = bool(benchmark_release_readiness.get("ready", False))
    release_policy_decision = str(release_policy_execution.get("decision") or "blocked")

    checks = (
        _check(
            check_id="v07-closeout-evidence-contract",
            passed=str(v07_closeout_evidence.get("contract") or "") == "v07-closeout-evidence/v1",
            reason=(
                "v0.7 closeout evidence contract is v07-closeout-evidence/v1."
                if str(v07_closeout_evidence.get("contract") or "") == "v07-closeout-evidence/v1"
                else (
                    "v0.7 closeout evidence contract is "
                    f"`{v07_closeout_evidence.get('contract') or 'missing'}`."
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
    scaffold_ready = len(failed_checks) == 0

    pathway_status = _pathway_status(
        scaffold_ready=scaffold_ready,
        closeout_category=closeout_category,
        escalation_level=escalation_level,
        benchmark_ready=benchmark_ready,
        release_policy_decision=release_policy_decision,
    )
    blockers = _blockers(
        pathway_status=pathway_status,
        closeout_category=closeout_category,
        escalation_level=escalation_level,
        benchmark_ready=benchmark_ready,
        release_policy_decision=release_policy_decision,
        failed_check_ids=tuple(str(check.get("id") or "") for check in failed_checks),
    )
    scaffold_id = _scaffold_id(
        pathway_status=pathway_status,
        closeout_category=closeout_category,
        escalation_level=escalation_level,
        benchmark_ready=benchmark_ready,
        release_policy_decision=release_policy_decision,
    )
    phase_blueprint = _phase_blueprint(pathway_status=pathway_status)

    return {
        "contract": "v10-pathway-scaffold/v1",
        "profile": "phase21-v10-pathway-scaffold/v1",
        "scaffold_id": scaffold_id,
        "scaffold_ready": scaffold_ready,
        "pathway_status": pathway_status,
        "transition_gate": "open" if pathway_status == "ready" else "gated",
        "milestone_target": "v1.0.0",
        "milestone_name": "v1.0 General Availability",
        "v07_closeout_category": closeout_category,
        "governance_escalation_level": escalation_level,
        "benchmark_release_ready": benchmark_ready,
        "release_policy_decision": release_policy_decision,
        "phase_count": len(phase_blueprint),
        "phase_blueprint": phase_blueprint,
        "blocker_count": len(blockers),
        "blockers": blockers,
        "check_count": len(checks),
        "failed_check_count": len(failed_checks),
        "failed_check_ids": tuple(str(check.get("id") or "") for check in failed_checks),
        "checks": checks,
        "next_pathway_action": _next_pathway_action(pathway_status=pathway_status),
        "summary": (
            f"v1.0 pathway scaffold `{pathway_status}` "
            f"(closeout={closeout_category}, governance={escalation_level}, release_policy={release_policy_decision})."
        ),
    }


def _pathway_status(
    *,
    scaffold_ready: bool,
    closeout_category: str,
    escalation_level: str,
    benchmark_ready: bool,
    release_policy_decision: str,
) -> str:
    if not scaffold_ready:
        return "blocked"
    if closeout_category == "blocked" or escalation_level == "critical" or release_policy_decision == "blocked":
        return "blocked"
    if (
        closeout_category == "hold"
        or escalation_level in {"review", "escalate"}
        or release_policy_decision == "manual-ack"
        or not benchmark_ready
    ):
        return "hold"
    return "ready"


def _blockers(
    *,
    pathway_status: str,
    closeout_category: str,
    escalation_level: str,
    benchmark_ready: bool,
    release_policy_decision: str,
    failed_check_ids: tuple[str, ...],
) -> tuple[str, ...]:
    if pathway_status == "ready":
        return ()

    blockers: list[str] = [f"contract:{check_id}" for check_id in failed_check_ids if check_id]
    if closeout_category != "ready":
        blockers.append(f"closeout:{closeout_category}")
    if escalation_level != "none":
        blockers.append(f"governance:{escalation_level}")
    if not benchmark_ready:
        blockers.append("benchmark-release:not-ready")
    if release_policy_decision != "automated":
        blockers.append(f"release-policy:{release_policy_decision}")
    return tuple(dict.fromkeys(blockers))[:12]


def _phase_blueprint(*, pathway_status: str) -> tuple[dict[str, object], ...]:
    base_entry_gate = "v07-closeout-ready" if pathway_status == "ready" else "v07-closeout-gated"
    return (
        {
            "phase": 22,
            "slug": "v1-foundation-hardening-and-compatibility",
            "name": "v1 Foundation Hardening and Compatibility",
            "goal": "Lock v1.0 contract compatibility and migration-safe defaults.",
            "entry_plan": "22-01",
            "entry_gate": base_entry_gate,
        },
        {
            "phase": 23,
            "slug": "v1-operator-control-plane-consolidation",
            "name": "v1 Operator Control Plane Consolidation",
            "goal": "Unify operator control surfaces and enforce governance ergonomics.",
            "entry_plan": "23-01",
            "entry_gate": "phase22-complete",
        },
        {
            "phase": 24,
            "slug": "v1-general-availability-closeout",
            "name": "v1 General Availability Closeout",
            "goal": "Publish launch evidence, acceptance confidence, and v1.0 artifacts.",
            "entry_plan": "24-01",
            "entry_gate": "phase23-complete",
        },
    )


def _next_pathway_action(*, pathway_status: str) -> str:
    if pathway_status == "ready":
        return "v1.0 pathway scaffold is ready. Start phase 22 planning."
    if pathway_status == "hold":
        return "v1.0 pathway scaffold is gated. Resolve hold signals, then start phase 22 planning."
    return "v1.0 pathway scaffold is blocked. Resolve closeout and governance blockers before phase 22."


def _scaffold_id(
    *,
    pathway_status: str,
    closeout_category: str,
    escalation_level: str,
    benchmark_ready: bool,
    release_policy_decision: str,
) -> str:
    basis = (
        f"{pathway_status}|{closeout_category}|{escalation_level}|"
        f"{int(benchmark_ready)}|{release_policy_decision}"
    )
    digest = hashlib.sha256(basis.encode("utf-8")).hexdigest()[:12]
    return f"v10-pathway-{digest}"


def _check(*, check_id: str, passed: bool, reason: str) -> dict[str, object]:
    return {
        "id": check_id,
        "passed": passed,
        "reason": reason,
    }
