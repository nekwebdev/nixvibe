"""End-to-end orchestration pipeline for route/mode/specialist merge."""

from __future__ import annotations

from pathlib import Path
from typing import Sequence

from .artifacts import generate_artifact_bundle, materialize_artifacts
from .merge import merge_specialist_payloads
from .modes import resolve_mode
from .payloads import PayloadValidationError, validate_payload
from .policy_loader import load_policy
from .router import select_route
from .specialists import run_specialists
from .types import (
    Mode,
    OrchestrationPolicy,
    OrchestrationRequest,
    OrchestrationResult,
    RepoContext,
    SpecialistExecutionOutcome,
    SpecialistExecutionResult,
    SpecialistTask,
    ValidationReport,
)
from .validation import CommandRunner, run_validation


class OrchestrationPipelineError(RuntimeError):
    """Raised when pipeline cannot produce a valid orchestration result."""


def run_pipeline(
    request: OrchestrationRequest,
    context: RepoContext,
    specialist_tasks: Sequence[SpecialistTask],
    *,
    policy: OrchestrationPolicy | None = None,
    workspace_root: str | Path = ".",
    validation_runner: CommandRunner | None = None,
) -> OrchestrationResult:
    active_policy = policy or load_policy()

    route_decision = select_route(request, context, active_policy)
    mode_decision = resolve_mode(
        route=route_decision.route,
        requested_mode=request.requested_mode,
        explicit_apply_opt_in=request.explicit_apply_opt_in,
    )

    specialist_results = run_specialists(specialist_tasks)
    validated_results = _validate_specialist_results(specialist_results)

    valid_payloads = tuple(
        result.payload
        for result in validated_results
        if result.outcome is SpecialistExecutionOutcome.OK and result.payload is not None
    )
    excluded = tuple(
        result.agent_id
        for result in validated_results
        if result.outcome is not SpecialistExecutionOutcome.OK
    )

    if not valid_payloads:
        raise OrchestrationPipelineError(
            "No valid specialist payloads available for merge; cannot produce final output."
        )

    merge_result = merge_specialist_payloads(valid_payloads, active_policy)
    selected_mode = mode_decision.mode
    if merge_result.forced_mode is not None:
        selected_mode = merge_result.forced_mode

    validation_report: ValidationReport | None = None
    if selected_mode is Mode.APPLY:
        validation_report = run_validation(
            workspace_root=workspace_root,
            command_runner=validation_runner,
        )
        if not validation_report.success:
            selected_mode = Mode.PROPOSE

    artifact_bundle = generate_artifact_bundle(route_decision.route, merge_result)
    materialization_result = materialize_artifacts(
        artifact_bundle,
        selected_mode,
        workspace_root=workspace_root,
    )
    artifact_summary = _build_artifact_summary(
        base_summary=merge_result.artifact_summary,
        route=route_decision.route.value,
        generated_files=tuple(file.path for file in artifact_bundle.files),
        proposed_files=tuple(file.path for file in materialization_result.proposed_files),
        written_files=materialization_result.written_paths,
        mode=selected_mode.value,
        validation_report=validation_report,
    )
    next_action = _next_action_for_mode(
        mode=selected_mode,
        merge_next_action=merge_result.next_action,
        validation_report=validation_report,
    )

    return OrchestrationResult(
        route_decision=route_decision,
        mode_decision=mode_decision,
        selected_mode=selected_mode,
        artifact_summary=artifact_summary,
        next_action=next_action,
        included_payloads=valid_payloads,
        excluded_specialists=excluded,
        specialist_results=validated_results,
        merge_reason=merge_result.reason,
        generated_artifacts=artifact_bundle.files,
        proposed_artifacts=materialization_result.proposed_files,
        written_artifact_paths=materialization_result.written_paths,
        validation_report=validation_report,
    )


def _validate_specialist_results(
    specialist_results: tuple[SpecialistExecutionResult, ...],
) -> tuple[SpecialistExecutionResult, ...]:
    validated: list[SpecialistExecutionResult] = []
    for result in specialist_results:
        if result.outcome is not SpecialistExecutionOutcome.OK:
            validated.append(result)
            continue

        try:
            payload = validate_payload(result.raw_payload)
        except PayloadValidationError as exc:
            validated.append(
                SpecialistExecutionResult(
                    agent_id=result.agent_id,
                    task_scope=result.task_scope,
                    outcome=SpecialistExecutionOutcome.INVALID,
                    raw_payload=result.raw_payload,
                    error=str(exc),
                )
            )
            continue
        validated.append(
            SpecialistExecutionResult(
                agent_id=result.agent_id,
                task_scope=result.task_scope,
                outcome=SpecialistExecutionOutcome.OK,
                raw_payload=result.raw_payload,
                payload=payload,
            )
        )
    return tuple(validated)


def _build_artifact_summary(
    *,
    base_summary,
    route: str,
    generated_files: tuple[str, ...],
    proposed_files: tuple[str, ...],
    written_files: tuple[str, ...],
    mode: str,
    validation_report: ValidationReport | None,
):
    merged = dict(base_summary)
    merged.update(
        {
            "route": route,
            "mode": mode,
            "generated_files": generated_files,
            "generated_file_count": len(generated_files),
            "proposed_files": proposed_files,
            "written_files": written_files,
            "write_performed": bool(written_files),
        }
    )
    if validation_report is not None:
        merged["validation"] = {
            "required": validation_report.required,
            "executed": validation_report.executed,
            "success": validation_report.success,
            "flake_present": validation_report.flake_present,
            "reason": validation_report.reason,
            "commands": tuple(
                {
                    "command": result.command,
                    "exit_code": result.exit_code,
                    "success": result.success,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                }
                for result in validation_report.results
            ),
        }
    return merged


def _next_action_for_mode(
    *,
    mode: Mode,
    merge_next_action: str,
    validation_report: ValidationReport | None,
) -> str:
    if validation_report is not None and not validation_report.success:
        return "Validation failed (`nix flake check` / `nix fmt`). Fix issues and retry apply."
    if mode is Mode.ADVICE:
        return "Switch to propose mode to preview generated artifacts."
    if mode is Mode.PROPOSE:
        return "Review proposed artifacts and confirm apply to write files."
    return merge_next_action.strip() or "Review written artifacts and continue."
