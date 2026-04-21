"""Operator observability digest contract helpers."""

from __future__ import annotations

import hashlib


def build_operator_observability_digest(
    *,
    run_manifest: dict[str, object],
    operator_audit_trail: dict[str, object],
    run_telemetry: dict[str, object],
    release_policy_execution: dict[str, object],
) -> dict[str, object]:
    route = str(run_manifest.get("route") or "unknown")
    selected_mode = str(_mapping(run_manifest.get("modes")).get("selected") or "unknown")
    audit_level = str(operator_audit_trail.get("audit_level") or "info")
    release_policy_decision = str(release_policy_execution.get("decision") or "blocked")

    checks = (
        _check(
            check_id="run-manifest-contract",
            passed=str(run_manifest.get("contract") or "") == "operator-run-manifest/v1",
            reason=(
                "Run manifest contract is operator-run-manifest/v1."
                if str(run_manifest.get("contract") or "") == "operator-run-manifest/v1"
                else f"Run manifest contract is `{run_manifest.get('contract') or 'missing'}`."
            ),
        ),
        _check(
            check_id="operator-audit-trail-contract",
            passed=str(operator_audit_trail.get("contract") or "") == "operator-audit-trail/v1",
            reason=(
                "Operator audit-trail contract is operator-audit-trail/v1."
                if str(operator_audit_trail.get("contract") or "") == "operator-audit-trail/v1"
                else (
                    "Operator audit-trail contract is "
                    f"`{operator_audit_trail.get('contract') or 'missing'}`."
                )
            ),
        ),
        _check(
            check_id="run-telemetry-contract",
            passed=str(run_telemetry.get("contract") or "") == "run-telemetry/v1",
            reason=(
                "Run telemetry contract is run-telemetry/v1."
                if str(run_telemetry.get("contract") or "") == "run-telemetry/v1"
                else f"Run telemetry contract is `{run_telemetry.get('contract') or 'missing'}`."
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
    digest_ready = len(failed_checks) == 0

    severity_counts = _severity_counts(operator_audit_trail=operator_audit_trail)
    observability_band = _observability_band(
        digest_ready=digest_ready,
        release_policy_decision=release_policy_decision,
        audit_level=audit_level,
        severity_counts=severity_counts,
    )
    focus_items = _focus_items(
        operator_audit_trail=operator_audit_trail,
        release_policy_execution=release_policy_execution,
        observability_band=observability_band,
    )

    digest_id = _digest_id(
        route=route,
        selected_mode=selected_mode,
        observability_band=observability_band,
        release_policy_decision=release_policy_decision,
        audit_level=audit_level,
    )

    return {
        "contract": "operator-observability-digest/v1",
        "profile": "phase20-operator-observability-digest/v1",
        "digest_id": digest_id,
        "digest_ready": digest_ready,
        "observability_band": observability_band,
        "attention_required": observability_band in {"attention", "critical", "degraded"},
        "escalation_recommended": observability_band == "critical",
        "route": route,
        "mode": selected_mode,
        "audit_level": audit_level,
        "release_policy_decision": release_policy_decision,
        "severity_counts": severity_counts,
        "focus_items": focus_items,
        "focus_count": len(focus_items),
        "run_timing_ms": _timing_snapshot(run_telemetry=run_telemetry),
        "check_count": len(checks),
        "failed_check_count": len(failed_checks),
        "failed_check_ids": tuple(str(check.get("id") or "") for check in failed_checks),
        "checks": checks,
        "next_observability_action": _next_observability_action(observability_band=observability_band),
        "summary": (
            f"Operator observability digest `{observability_band}` "
            f"(audit={audit_level}, release_policy={release_policy_decision})."
        ),
    }


def _severity_counts(*, operator_audit_trail: dict[str, object]) -> dict[str, int]:
    info_count = 0
    warning_count = 0
    critical_count = 0

    for entry in operator_audit_trail.get("entries", ()):
        if not isinstance(entry, dict):
            continue
        severity = str(entry.get("severity") or "info")
        if severity in {"critical", "high"}:
            critical_count += 1
        elif severity in {"warning", "medium"}:
            warning_count += 1
        else:
            info_count += 1

    return {
        "info_count": info_count,
        "warning_count": warning_count,
        "critical_count": critical_count,
    }


def _observability_band(
    *,
    digest_ready: bool,
    release_policy_decision: str,
    audit_level: str,
    severity_counts: dict[str, int],
) -> str:
    if not digest_ready:
        return "degraded"
    if (
        release_policy_decision == "blocked"
        or audit_level == "critical"
        or int(severity_counts.get("critical_count", 0)) > 0
    ):
        return "critical"
    if (
        release_policy_decision == "manual-ack"
        or audit_level == "warning"
        or int(severity_counts.get("warning_count", 0)) > 0
    ):
        return "attention"
    return "healthy"


def _focus_items(
    *,
    operator_audit_trail: dict[str, object],
    release_policy_execution: dict[str, object],
    observability_band: str,
) -> tuple[str, ...]:
    items: list[str] = []
    for action in operator_audit_trail.get("action_items", ()):
        action_text = str(action).strip()
        if action_text:
            items.append(action_text)
    for blocker in release_policy_execution.get("blockers", ()):
        blocker_text = str(blocker).strip()
        if blocker_text:
            items.append(f"Resolve release policy blocker: {blocker_text}.")

    deduped = tuple(dict.fromkeys(items))
    if deduped:
        return deduped[:5]
    if observability_band == "healthy":
        return ("No immediate operator action required.",)
    return ("Review observability signals and remediate highlighted issues.",)


def _timing_snapshot(*, run_telemetry: dict[str, object]) -> dict[str, int]:
    return {
        "total_duration_ms": _metric_ms(run_telemetry.get("total_duration_ms")),
        "specialist_execution_ms": _metric_ms(run_telemetry.get("specialist_execution_ms")),
        "validation_total_ms": _metric_ms(run_telemetry.get("validation_total_ms")),
    }


def _next_observability_action(*, observability_band: str) -> str:
    if observability_band == "healthy":
        return "Observability signals are healthy. Continue standard operator workflow."
    if observability_band == "attention":
        return "Observability signals require attention. Review manual acknowledgements and warning signals."
    if observability_band == "critical":
        return "Observability signals are critical. Escalate and resolve blocking policy signals."
    return "Observability digest is degraded. Repair missing contracts before operator decisions."


def _digest_id(
    *,
    route: str,
    selected_mode: str,
    observability_band: str,
    release_policy_decision: str,
    audit_level: str,
) -> str:
    basis = (
        f"{route}|{selected_mode}|{observability_band}|{release_policy_decision}|{audit_level}"
    )
    digest = hashlib.sha256(basis.encode("utf-8")).hexdigest()[:12]
    return f"ood-{digest}"


def _check(*, check_id: str, passed: bool, reason: str) -> dict[str, object]:
    return {
        "id": check_id,
        "passed": passed,
        "reason": reason,
    }


def _mapping(value: object) -> dict[str, object]:
    if isinstance(value, dict):
        return value
    return {}


def _metric_ms(value: object) -> int:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, (int, float)):
        return max(0, int(value))
    return 0
