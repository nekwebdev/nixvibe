"""Release-readiness gate contract helpers."""

from __future__ import annotations


def build_release_readiness(
    *,
    run_manifest: dict[str, object],
) -> dict[str, object]:
    modes = _mapping(run_manifest.get("modes"))
    specialists = _mapping(run_manifest.get("specialists"))
    specialist_outcomes = _mapping(specialists.get("outcomes"))
    artifacts = _mapping(run_manifest.get("artifacts"))
    validation = _mapping(run_manifest.get("validation"))
    safety = _mapping(run_manifest.get("safety"))

    selected_mode = str(modes.get("selected") or "")
    mode_is_apply = selected_mode == "apply"

    invalid_count = int(specialist_outcomes.get("invalid") or 0)
    error_count = int(specialist_outcomes.get("error") or 0)

    gates = (
        _gate(
            gate_id="mode-apply",
            required=True,
            passed=mode_is_apply,
            reason=(
                "Selected mode is apply."
                if mode_is_apply
                else f"Selected mode is `{selected_mode or 'unknown'}`; release requires apply."
            ),
            severity="high",
        ),
        _gate(
            gate_id="specialist-integrity",
            required=True,
            passed=(invalid_count == 0 and error_count == 0),
            reason=(
                "All specialist outcomes are valid."
                if invalid_count == 0 and error_count == 0
                else f"Invalid={invalid_count}, Error={error_count} specialist outcomes detected."
            ),
            severity="high",
        ),
        _gate(
            gate_id="safety-clear",
            required=True,
            passed=(
                not bool(safety.get("guardrail_blocked_apply", False))
                and str(safety.get("escalation_tier") or "none") in ("none", "advisory")
                and not bool(safety.get("recovery_required", False))
            ),
            reason=_safety_reason(safety),
            severity="critical",
        ),
        _gate(
            gate_id="validation-success",
            required=mode_is_apply,
            passed=(not mode_is_apply)
            or (
                bool(validation.get("executed", False))
                and bool(validation.get("success", False))
            ),
            reason=(
                "Validation success confirmed."
                if (bool(validation.get("executed", False)) and bool(validation.get("success", False)))
                else "Validation was not executed successfully for apply mode."
            ),
            severity="critical",
        ),
        _gate(
            gate_id="writes-materialized",
            required=mode_is_apply,
            passed=(not mode_is_apply) or bool(artifacts.get("write_performed", False)),
            reason=(
                "Apply writes were materialized."
                if bool(artifacts.get("write_performed", False))
                else "Apply mode did not materialize writes."
            ),
            severity="high",
        ),
    )

    required_gates = tuple(gate for gate in gates if bool(gate.get("required")))
    failed_gates = tuple(gate for gate in required_gates if not bool(gate.get("passed")))
    ready = len(failed_gates) == 0

    failure_summary = tuple(str(gate.get("reason") or "") for gate in failed_gates)
    next_gate_action = (
        "Release readiness passed. Continue with release handoff."
        if ready
        else "Release readiness blocked. Resolve failed required gates before release."
    )

    return {
        "contract": "release-readiness/v1",
        "ready": ready,
        "required_gate_count": len(required_gates),
        "passed_gate_count": len(required_gates) - len(failed_gates),
        "failed_gate_count": len(failed_gates),
        "failed_gate_ids": tuple(str(gate.get("id")) for gate in failed_gates),
        "gates": gates,
        "failure_summary": failure_summary,
        "next_gate_action": next_gate_action,
    }


def _gate(
    *,
    gate_id: str,
    required: bool,
    passed: bool,
    reason: str,
    severity: str,
) -> dict[str, object]:
    return {
        "id": gate_id,
        "required": required,
        "passed": passed,
        "reason": reason,
        "severity": severity,
    }


def _mapping(value: object) -> dict[str, object]:
    if isinstance(value, dict):
        return value
    return {}


def _safety_reason(safety: dict[str, object]) -> str:
    guardrail_blocked = bool(safety.get("guardrail_blocked_apply", False))
    escalation_tier = str(safety.get("escalation_tier") or "none")
    recovery_required = bool(safety.get("recovery_required", False))
    if not guardrail_blocked and escalation_tier in ("none", "advisory") and not recovery_required:
        return "Safety gates are clear."

    reasons: list[str] = []
    if guardrail_blocked:
        reasons.append("guardrail blocked apply")
    if escalation_tier not in ("none", "advisory"):
        reasons.append(f"escalation tier `{escalation_tier}`")
    if recovery_required:
        reasons.append("recovery is required")
    return "Safety gate blocked: " + ", ".join(reasons) + "."
