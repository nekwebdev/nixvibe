"""End-to-end orchestration pipeline for route/mode/specialist merge."""

from __future__ import annotations

from pathlib import Path
from typing import Sequence

from .artifacts import generate_artifact_bundle, materialize_artifacts
from .escalation import build_apply_safety_escalation
from .failure import build_run_failure_classification
from .guardrails import evaluate_high_risk_mutation_guardrails
from .guidance import build_guidance_summary
from .ledger import inspect_git_ledger
from .manifest import build_operator_run_manifest
from .merge import merge_specialist_payloads
from .modes import resolve_mode
from .payloads import PayloadValidationError, validate_payload
from .policy_loader import load_policy
from .release import build_release_readiness
from .recovery import build_recovery_playbook
from .runtime import RuntimeSpecialistContractError, plan_runtime_specialists
from .router import select_route
from .specialists import build_dispatch_context, run_specialists, with_dispatch_context
from .types import (
    Mode,
    OrchestrationPolicy,
    OrchestrationRequest,
    OrchestrationResult,
    RepoContext,
    RuntimeSpecialistContract,
    RuntimeSpecialistHandlerRegistry,
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
    specialist_tasks: Sequence[SpecialistTask] = (),
    *,
    policy: OrchestrationPolicy | None = None,
    workspace_root: str | Path = ".",
    validation_runner: CommandRunner | None = None,
    runtime_contract: RuntimeSpecialistContract | None = None,
    runtime_handlers: RuntimeSpecialistHandlerRegistry | None = None,
) -> OrchestrationResult:
    workspace_root_path = Path(workspace_root)
    active_policy = policy or load_policy()

    route_decision = select_route(request, context, active_policy)
    mode_decision = resolve_mode(
        route=route_decision.route,
        requested_mode=request.requested_mode,
        explicit_apply_opt_in=request.explicit_apply_opt_in,
    )

    dispatch_context = build_dispatch_context(
        request=request,
        context=context,
        route_decision=route_decision,
        mode_decision=mode_decision,
    )
    dispatch_tasks = _dispatch_tasks(
        specialist_tasks=specialist_tasks,
        dispatch_context=dispatch_context,
        runtime_contract=runtime_contract,
        runtime_handlers=runtime_handlers,
    )
    specialist_results = run_specialists(dispatch_tasks)
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
    mutation_guardrails = evaluate_high_risk_mutation_guardrails(
        requested_mode=request.requested_mode,
        selected_mode=selected_mode,
        payloads=valid_payloads,
    )
    if bool(mutation_guardrails.get("apply_blocked")):
        selected_mode = Mode.PROPOSE

    pre_write_validation_report: ValidationReport | None = None
    post_write_validation_report: ValidationReport | None = None
    validation_report: ValidationReport | None = None
    if selected_mode is Mode.APPLY:
        pre_write_validation_report = run_validation(
            workspace_root=workspace_root,
            command_runner=validation_runner,
        )
        validation_report = pre_write_validation_report
        if not pre_write_validation_report.success:
            selected_mode = Mode.PROPOSE

    artifact_bundle = generate_artifact_bundle(route_decision.route, merge_result)
    materialization_result = materialize_artifacts(
        artifact_bundle,
        selected_mode,
        workspace_root=workspace_root,
    )
    if (
        selected_mode is Mode.APPLY
        and materialization_result.write_performed
        and pre_write_validation_report is not None
        and pre_write_validation_report.success
    ):
        post_write_validation_report = run_validation(
            workspace_root=workspace_root,
            command_runner=validation_runner,
        )
        validation_report = post_write_validation_report

    ledger_summary = inspect_git_ledger(workspace_root_path)
    artifact_summary = _build_artifact_summary(
        base_summary=merge_result.artifact_summary,
        context=context,
        dispatch_context=dispatch_context,
        dispatch_task_count=len(dispatch_tasks),
        dispatch_agent_ids=tuple(task.agent_id for task in dispatch_tasks),
        runtime_contract=runtime_contract,
        route=route_decision.route.value,
        generated_files=tuple(file.path for file in artifact_bundle.files),
        proposed_files=tuple(file.path for file in materialization_result.proposed_files),
        written_files=materialization_result.written_paths,
        ledger_summary=ledger_summary,
        mode=selected_mode.value,
        pre_write_validation_report=pre_write_validation_report,
        post_write_validation_report=post_write_validation_report,
        validation_report=validation_report,
    )
    next_action = _next_action_for_mode(
        mode=selected_mode,
        merge_next_action=merge_result.next_action,
        ledger_summary=ledger_summary,
        pre_write_validation_report=pre_write_validation_report,
        post_write_validation_report=post_write_validation_report,
    )
    validation_failure_stage = _validation_failure_stage(
        pre_write_validation_report=pre_write_validation_report,
        post_write_validation_report=post_write_validation_report,
    )
    conflict_forced_propose = bool(
        merge_result.forced_mode is Mode.PROPOSE
        and "Contradictory critical findings" in merge_result.reason
    )
    high_risk_guardrail_forced_propose = bool(mutation_guardrails.get("apply_blocked"))
    apply_safety_escalation = build_apply_safety_escalation(
        requested_mode=request.requested_mode,
        selected_mode=selected_mode,
        validation_failure_stage=validation_failure_stage,
        conflict_forced_propose=conflict_forced_propose,
        high_risk_guardrail_forced_propose=high_risk_guardrail_forced_propose,
        ledger_summary=ledger_summary,
    )
    recovery_playbook = build_recovery_playbook(
        escalation=apply_safety_escalation,
        mode=selected_mode,
        next_action=next_action,
        ledger_summary=ledger_summary,
    )
    guidance_summary = build_guidance_summary(
        user_input=request.user_input,
        context=context,
        route=route_decision.route,
        mode=selected_mode,
        next_action=next_action,
        validation_failed=bool(validation_report is not None and not validation_report.success),
        validation_failure_stage=validation_failure_stage,
        conflict_forced_propose=conflict_forced_propose,
        high_risk_guardrail_forced_propose=high_risk_guardrail_forced_propose,
        merge_reason=merge_result.reason,
        ledger_summary=ledger_summary,
        apply_safety_escalation=apply_safety_escalation,
        recovery_playbook=recovery_playbook,
    )
    artifact_summary = dict(artifact_summary)
    artifact_summary["mutation_guardrails"] = mutation_guardrails
    artifact_summary["apply_safety_escalation"] = apply_safety_escalation
    artifact_summary["recovery_playbook"] = recovery_playbook
    artifact_summary["guidance"] = guidance_summary
    artifact_summary["run_manifest"] = build_operator_run_manifest(
        route=route_decision.route.value,
        requested_mode=request.requested_mode,
        selected_mode=selected_mode,
        merge_reason=merge_result.reason,
        next_action=next_action,
        dispatch_task_count=len(dispatch_tasks),
        specialist_results=validated_results,
        included_payload_count=len(valid_payloads),
        excluded_count=len(excluded),
        generated_files=tuple(file.path for file in artifact_bundle.files),
        proposed_files=tuple(file.path for file in materialization_result.proposed_files),
        written_files=materialization_result.written_paths,
        validation_summary=artifact_summary.get("validation"),
        ledger_summary=ledger_summary,
        mutation_guardrails=mutation_guardrails,
        apply_safety_escalation=apply_safety_escalation,
        recovery_playbook=recovery_playbook,
    )
    artifact_summary["run_failure_classification"] = build_run_failure_classification(
        run_manifest=artifact_summary["run_manifest"],
        apply_safety_escalation=apply_safety_escalation,
        validation_failure_stage=validation_failure_stage,
    )
    artifact_summary["release_readiness"] = build_release_readiness(
        run_manifest=artifact_summary["run_manifest"]
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
    context: RepoContext,
    dispatch_context,
    dispatch_task_count: int,
    dispatch_agent_ids: tuple[str, ...],
    runtime_contract: RuntimeSpecialistContract | None,
    route: str,
    generated_files: tuple[str, ...],
    proposed_files: tuple[str, ...],
    written_files: tuple[str, ...],
    ledger_summary: dict[str, object],
    mode: str,
    pre_write_validation_report: ValidationReport | None,
    post_write_validation_report: ValidationReport | None,
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
            "ledger": ledger_summary,
            "specialist_dispatch": {
                "route": dispatch_context.resolved_route.value,
                "mode": dispatch_context.resolved_mode.value,
                "task_count": dispatch_task_count,
                "agent_ids": dispatch_agent_ids,
                "repository_state": dispatch_context.repository_state,
                "has_workspace_snapshot": dispatch_context.workspace_snapshot is not None,
                "has_reference_adaptation": dispatch_context.reference_adaptation is not None,
                "runtime_contract_name": runtime_contract.name if runtime_contract is not None else "",
                "runtime_contract_route": (
                    runtime_contract.route.value if runtime_contract is not None else ""
                ),
            },
        }
    )
    context_profile = _context_profile_summary(context)
    if context_profile is not None:
        merged["context_profile"] = context_profile
    if validation_report is not None:
        validation_summary = _serialize_validation_report(validation_report)
        checkpoints = _validation_checkpoint_summaries(
            pre_write_validation_report=pre_write_validation_report,
            post_write_validation_report=post_write_validation_report,
        )
        if checkpoints:
            validation_summary["checkpoints"] = checkpoints
            validation_summary["checkpoint_count"] = len(checkpoints)
            validation_summary["final_checkpoint"] = checkpoints[-1]["stage"]
            validation_summary["final_success"] = checkpoints[-1]["success"]
        merged["validation"] = validation_summary
    return merged


def _context_profile_summary(context: RepoContext):
    snapshot = context.workspace_snapshot
    reference = context.reference_profile
    adaptation = context.reference_adaptation
    if snapshot is None and reference is None and adaptation is None:
        return None

    profile: dict[str, object] = {}
    if snapshot is not None:
        profile["workspace"] = {
            "root": snapshot.root,
            "entry_count": len(snapshot.entries),
            "truncated": snapshot.truncated,
            "flake_present": snapshot.flake_present,
            "nix_file_count": snapshot.nix_file_count,
            "module_count": len(snapshot.module_paths),
            "has_hosts_tree": snapshot.has_hosts_tree,
            "has_home_tree": snapshot.has_home_tree,
        }
    if reference is not None:
        profile["reference"] = {
            "root": reference.root,
            "entry_count": len(reference.entries),
            "truncated": reference.truncated,
            "flake_present": reference.flake_present,
            "module_count": len(reference.module_paths),
            "validation_patterns": reference.validation_patterns,
            "notes": reference.notes,
        }
    if adaptation is not None:
        profile["reference_adaptation"] = {
            "strategy": adaptation.strategy,
            "preserve_existing_structure": adaptation.preserve_existing_structure,
            "suggested_module_aggregators": adaptation.suggested_module_aggregators,
            "suggested_validation_commands": adaptation.suggested_validation_commands,
            "notes": adaptation.notes,
        }
    return profile


def _dispatch_tasks(
    *,
    specialist_tasks: Sequence[SpecialistTask],
    dispatch_context,
    runtime_contract: RuntimeSpecialistContract | None,
    runtime_handlers: RuntimeSpecialistHandlerRegistry | None,
) -> tuple[SpecialistTask, ...]:
    if specialist_tasks:
        return with_dispatch_context(
            specialist_tasks,
            dispatch_context=dispatch_context,
        )

    if runtime_contract is None and runtime_handlers is None:
        return ()
    if runtime_contract is None or runtime_handlers is None:
        raise OrchestrationPipelineError(
            "Runtime contract execution requires both runtime_contract and runtime_handlers."
        )

    try:
        return plan_runtime_specialists(
            contract=runtime_contract,
            handlers=runtime_handlers,
            dispatch_context=dispatch_context,
        )
    except RuntimeSpecialistContractError as exc:
        raise OrchestrationPipelineError(str(exc)) from exc


def _next_action_for_mode(
    *,
    mode: Mode,
    merge_next_action: str,
    ledger_summary: dict[str, object],
    pre_write_validation_report: ValidationReport | None,
    post_write_validation_report: ValidationReport | None,
) -> str:
    if pre_write_validation_report is not None and not pre_write_validation_report.success:
        return "Validation failed before write (`nix flake check` / `nix fmt`). Fix issues and retry apply."
    if post_write_validation_report is not None and not post_write_validation_report.success:
        return (
            "Validation failed after write (`nix flake check` / `nix fmt`). "
            "Review written artifacts and remediate."
        )
    if mode is Mode.ADVICE:
        return "Switch to propose mode to preview generated artifacts."
    if mode is Mode.PROPOSE:
        if _ledger_has_drift(ledger_summary):
            classification = str(ledger_summary.get("change_classification") or "drift")
            return (
                f"Workspace drift detected (`{classification}`). "
                "Reconcile git changes, then review proposed artifacts and confirm apply."
            )
        return "Review proposed artifacts and confirm apply to write files."
    if bool(ledger_summary.get("available")) and bool(ledger_summary.get("dirty")):
        return "Apply completed with workspace changes. Review git ledger state and checkpoint intentional changes."
    return merge_next_action.strip() or "Review written artifacts and continue."


def _serialize_validation_report(
    validation_report: ValidationReport,
) -> dict[str, object]:
    return {
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


def _validation_checkpoint_summaries(
    *,
    pre_write_validation_report: ValidationReport | None,
    post_write_validation_report: ValidationReport | None,
) -> tuple[dict[str, object], ...]:
    checkpoints: list[dict[str, object]] = []
    if pre_write_validation_report is not None:
        checkpoint = _serialize_validation_report(pre_write_validation_report)
        checkpoint["stage"] = "pre_write"
        checkpoints.append(checkpoint)
    if post_write_validation_report is not None:
        checkpoint = _serialize_validation_report(post_write_validation_report)
        checkpoint["stage"] = "post_write"
        checkpoints.append(checkpoint)
    return tuple(checkpoints)


def _validation_failure_stage(
    *,
    pre_write_validation_report: ValidationReport | None,
    post_write_validation_report: ValidationReport | None,
) -> str:
    if pre_write_validation_report is not None and not pre_write_validation_report.success:
        return "pre_write"
    if post_write_validation_report is not None and not post_write_validation_report.success:
        return "post_write"
    return ""


def _ledger_has_drift(ledger_summary: dict[str, object]) -> bool:
    return bool(
        ledger_summary.get("available")
        and ledger_summary.get("drift_detected")
    )
