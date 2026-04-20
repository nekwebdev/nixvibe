"""Operator-facing run manifest contract helpers."""

from __future__ import annotations

from .types import Mode, SpecialistExecutionOutcome, SpecialistExecutionResult


def build_operator_run_manifest(
    *,
    route: str,
    requested_mode: Mode | str | None,
    selected_mode: Mode,
    merge_reason: str,
    next_action: str,
    dispatch_task_count: int,
    specialist_results: tuple[SpecialistExecutionResult, ...],
    included_payload_count: int,
    excluded_count: int,
    generated_files: tuple[str, ...],
    proposed_files: tuple[str, ...],
    written_files: tuple[str, ...],
    validation_summary: dict[str, object] | None,
    ledger_summary: dict[str, object],
    mutation_guardrails: dict[str, object],
    apply_safety_escalation: dict[str, object],
    recovery_playbook: dict[str, object],
) -> dict[str, object]:
    requested_mode_value = _requested_mode_value(requested_mode)
    selected_mode_value = selected_mode.value

    outcome_counts = _specialist_outcome_counts(specialist_results)
    validation = validation_summary or {}

    return {
        "contract": "operator-run-manifest/v1",
        "route": route,
        "modes": {
            "requested": requested_mode_value,
            "selected": selected_mode_value,
            "changed": requested_mode_value not in ("auto", selected_mode_value),
        },
        "specialists": {
            "planned_count": dispatch_task_count,
            "included_count": included_payload_count,
            "excluded_count": excluded_count,
            "outcomes": outcome_counts,
        },
        "artifacts": {
            "generated_count": len(generated_files),
            "proposed_count": len(proposed_files),
            "written_count": len(written_files),
            "write_performed": bool(written_files),
        },
        "validation": {
            "executed": bool(validation.get("executed", False)),
            "success": bool(validation.get("success", False)),
            "final_checkpoint": str(validation.get("final_checkpoint") or "none"),
            "checkpoint_count": int(validation.get("checkpoint_count") or 0),
        },
        "safety": {
            "guardrail_blocked_apply": bool(mutation_guardrails.get("apply_blocked", False)),
            "guardrail_triggers": tuple(mutation_guardrails.get("triggers", ())),
            "escalation_tier": str(apply_safety_escalation.get("tier") or "none"),
            "escalation_reason": str(apply_safety_escalation.get("reason") or ""),
            "recovery_required": bool(recovery_playbook.get("required", False)),
            "recovery_stage": str(recovery_playbook.get("stage") or "none"),
        },
        "ledger": {
            "available": bool(ledger_summary.get("available")),
            "dirty": bool(ledger_summary.get("dirty")),
            "change_classification": str(ledger_summary.get("change_classification") or ""),
            "drift_detected": bool(ledger_summary.get("drift_detected")),
            "drift_severity": str(ledger_summary.get("drift_severity") or "none"),
        },
        "merge_reason": merge_reason,
        "next_action": next_action,
    }


def _specialist_outcome_counts(
    specialist_results: tuple[SpecialistExecutionResult, ...],
) -> dict[str, int]:
    counts = {
        SpecialistExecutionOutcome.OK.value: 0,
        SpecialistExecutionOutcome.INVALID.value: 0,
        SpecialistExecutionOutcome.ERROR.value: 0,
    }
    for result in specialist_results:
        counts[result.outcome.value] = counts.get(result.outcome.value, 0) + 1
    return counts


def _requested_mode_value(requested_mode: Mode | str | None) -> str:
    if requested_mode is None:
        return "auto"
    if isinstance(requested_mode, Mode):
        return requested_mode.value
    normalized = str(requested_mode).strip().lower()
    return normalized or "auto"
