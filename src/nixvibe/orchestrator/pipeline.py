"""End-to-end orchestration pipeline for route/mode/specialist merge."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Callable, Sequence

from .audittrail import build_operator_audit_trail_summary
from .artifacts import generate_artifact_bundle, materialize_artifacts
from .checkpoint import build_resume_checkpoint
from .benchmark import build_benchmark_baseline_report
from .benchmark_release import build_benchmark_release_readiness
from .benchmark_runner import build_benchmark_runner_report
from .benchmark_snapshot import build_benchmark_baseline_snapshot
from .benchmark_trend_delta import build_benchmark_trend_delta
from .benchmark_trend_history import build_benchmark_trend_history
from .benchmark_trend import build_benchmark_trend_entry
from .benchmark_scenarios import build_benchmark_scenario_catalog
from .escalation import build_apply_safety_escalation
from .explainability import build_policy_decision_explainability
from .failure import build_run_failure_classification
from .guardrails import evaluate_high_risk_mutation_guardrails
from .guidance import build_guidance_summary
from .ledger import inspect_git_ledger
from .manifest import build_operator_run_manifest
from .merge import merge_specialist_payloads
from .modes import resolve_mode
from .outcome_alert import build_outcome_alert
from .outcome_scorecard import build_outcome_scorecard
from .override import build_controlled_override_workflow
from .payloads import PayloadValidationError, validate_payload
from .policy_loader import load_policy
from .release import build_release_readiness
from .release_check import build_release_check_command_contract
from .release_manifest import build_release_artifact_manifest
from .recovery import build_recovery_playbook
from .retry import build_retry_backoff_guardrails
from .runtime import RuntimeSpecialistContractError, plan_runtime_specialists
from .router import select_route
from .specialists import build_dispatch_context, run_specialists, with_dispatch_context
from .telemetry import build_run_telemetry
from .telemetry_regression import build_telemetry_regression_report
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
    release_check_runner: CommandRunner | None = None,
    runtime_contract: RuntimeSpecialistContract | None = None,
    runtime_handlers: RuntimeSpecialistHandlerRegistry | None = None,
    benchmark_trend_history: Sequence[dict[str, object]] = (),
    monotonic_clock: Callable[[], float] | None = None,
) -> OrchestrationResult:
    workspace_root_path = Path(workspace_root)
    clock = monotonic_clock or time.perf_counter
    pipeline_started_at = clock()
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
    specialist_execution_ms = 0
    specialist_execution_started_at = clock()
    specialist_results = run_specialists(dispatch_tasks)
    specialist_execution_ms = _elapsed_ms(specialist_execution_started_at, clock())
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
    pre_write_validation_ms = 0
    post_write_validation_ms = 0
    if selected_mode is Mode.APPLY:
        pre_write_validation_started_at = clock()
        pre_write_validation_report = run_validation(
            workspace_root=workspace_root,
            command_runner=validation_runner,
        )
        pre_write_validation_ms = _elapsed_ms(pre_write_validation_started_at, clock())
        validation_report = pre_write_validation_report
        if not pre_write_validation_report.success:
            selected_mode = Mode.PROPOSE

    artifact_bundle = generate_artifact_bundle(route_decision.route, merge_result)
    artifact_materialization_started_at = clock()
    materialization_result = materialize_artifacts(
        artifact_bundle,
        selected_mode,
        workspace_root=workspace_root,
    )
    artifact_materialization_ms = _elapsed_ms(artifact_materialization_started_at, clock())
    if (
        selected_mode is Mode.APPLY
        and materialization_result.write_performed
        and pre_write_validation_report is not None
        and pre_write_validation_report.success
    ):
        post_write_validation_started_at = clock()
        post_write_validation_report = run_validation(
            workspace_root=workspace_root,
            command_runner=validation_runner,
        )
        post_write_validation_ms = _elapsed_ms(post_write_validation_started_at, clock())
        validation_report = post_write_validation_report

    ledger_inspection_started_at = clock()
    ledger_summary = inspect_git_ledger(workspace_root_path)
    ledger_inspection_ms = _elapsed_ms(ledger_inspection_started_at, clock())
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
    run_telemetry = build_run_telemetry(
        route=route_decision.route.value,
        mode=selected_mode.value,
        specialist_count=len(dispatch_tasks),
        generated_file_count=len(artifact_bundle.files),
        proposed_file_count=len(materialization_result.proposed_files),
        written_file_count=len(materialization_result.written_paths),
        pre_write_validation_executed=pre_write_validation_report is not None,
        post_write_validation_executed=post_write_validation_report is not None,
        specialist_execution_ms=specialist_execution_ms,
        artifact_materialization_ms=artifact_materialization_ms,
        validation_pre_write_ms=pre_write_validation_ms,
        validation_post_write_ms=post_write_validation_ms,
        ledger_inspection_ms=ledger_inspection_ms,
        total_duration_ms=_elapsed_ms(pipeline_started_at, clock()),
    )
    artifact_summary["run_telemetry"] = run_telemetry
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
        run_telemetry=run_telemetry,
    )
    artifact_summary["run_failure_classification"] = build_run_failure_classification(
        run_manifest=artifact_summary["run_manifest"],
        apply_safety_escalation=apply_safety_escalation,
        validation_failure_stage=validation_failure_stage,
    )
    artifact_summary["release_readiness"] = build_release_readiness(
        run_manifest=artifact_summary["run_manifest"]
    )
    artifact_summary["benchmark_baseline_report"] = build_benchmark_baseline_report(
        run_telemetry=run_telemetry,
        run_manifest=artifact_summary["run_manifest"],
        run_failure_classification=artifact_summary["run_failure_classification"],
        release_readiness=artifact_summary["release_readiness"],
    )
    artifact_summary["telemetry_regression"] = build_telemetry_regression_report(
        run_telemetry=run_telemetry,
        benchmark_baseline_report=artifact_summary["benchmark_baseline_report"],
    )
    artifact_summary["benchmark_scenario_catalog"] = build_benchmark_scenario_catalog(
        route=route_decision.route.value,
        mode=selected_mode.value,
        benchmark_baseline_report=artifact_summary["benchmark_baseline_report"],
        telemetry_regression=artifact_summary["telemetry_regression"],
    )
    artifact_summary["benchmark_runner_report"] = build_benchmark_runner_report(
        benchmark_scenario_catalog=artifact_summary["benchmark_scenario_catalog"],
        benchmark_baseline_report=artifact_summary["benchmark_baseline_report"],
        telemetry_regression=artifact_summary["telemetry_regression"],
    )
    artifact_summary["benchmark_baseline_snapshot"] = build_benchmark_baseline_snapshot(
        run_manifest=artifact_summary["run_manifest"],
        run_telemetry=artifact_summary["run_telemetry"],
        benchmark_baseline_report=artifact_summary["benchmark_baseline_report"],
        telemetry_regression=artifact_summary["telemetry_regression"],
        benchmark_scenario_catalog=artifact_summary["benchmark_scenario_catalog"],
        benchmark_runner_report=artifact_summary["benchmark_runner_report"],
    )
    artifact_summary["outcome_scorecard"] = build_outcome_scorecard(
        benchmark_scenario_catalog=artifact_summary["benchmark_scenario_catalog"],
        benchmark_runner_report=artifact_summary["benchmark_runner_report"],
        benchmark_baseline_snapshot=artifact_summary["benchmark_baseline_snapshot"],
        release_readiness=artifact_summary["release_readiness"],
        telemetry_regression=artifact_summary["telemetry_regression"],
    )
    artifact_summary["benchmark_release_readiness"] = build_benchmark_release_readiness(
        release_readiness=artifact_summary["release_readiness"],
        outcome_scorecard=artifact_summary["outcome_scorecard"],
        benchmark_baseline_snapshot=artifact_summary["benchmark_baseline_snapshot"],
        benchmark_runner_report=artifact_summary["benchmark_runner_report"],
        telemetry_regression=artifact_summary["telemetry_regression"],
    )
    artifact_summary["benchmark_trend_entry"] = build_benchmark_trend_entry(
        run_manifest=artifact_summary["run_manifest"],
        run_telemetry=artifact_summary["run_telemetry"],
        benchmark_baseline_snapshot=artifact_summary["benchmark_baseline_snapshot"],
        outcome_scorecard=artifact_summary["outcome_scorecard"],
        benchmark_release_readiness=artifact_summary["benchmark_release_readiness"],
    )
    artifact_summary["benchmark_trend_history"] = build_benchmark_trend_history(
        benchmark_trend_entry=artifact_summary["benchmark_trend_entry"],
        prior_history=benchmark_trend_history,
    )
    artifact_summary["benchmark_trend_delta"] = build_benchmark_trend_delta(
        benchmark_trend_entry=artifact_summary["benchmark_trend_entry"],
        previous_benchmark_trend_entry=artifact_summary["benchmark_trend_history"][
            "previous_benchmark_trend_entry"
        ],
    )
    artifact_summary["outcome_alert"] = build_outcome_alert(
        benchmark_trend_entry=artifact_summary["benchmark_trend_entry"],
        benchmark_trend_history=artifact_summary["benchmark_trend_history"],
        benchmark_trend_delta=artifact_summary["benchmark_trend_delta"],
    )
    artifact_summary["resume_checkpoint"] = build_resume_checkpoint(
        run_manifest=artifact_summary["run_manifest"],
        run_failure_classification=artifact_summary["run_failure_classification"],
        release_readiness=artifact_summary["release_readiness"],
    )
    artifact_summary["retry_backoff_guardrails"] = build_retry_backoff_guardrails(
        run_failure_classification=artifact_summary["run_failure_classification"],
        resume_checkpoint=artifact_summary["resume_checkpoint"],
        selected_mode=selected_mode.value,
    )
    artifact_summary["policy_decision_explainability"] = build_policy_decision_explainability(
        route_decision=route_decision,
        mode_decision=mode_decision,
        selected_mode=selected_mode,
        merge_reason=merge_result.reason,
        mutation_guardrails=mutation_guardrails,
        apply_safety_escalation=apply_safety_escalation,
        run_failure_classification=artifact_summary["run_failure_classification"],
        release_readiness=artifact_summary["release_readiness"],
        conflict_priority_order=tuple(
            priority.value for priority in active_policy.conflict.ordered_priorities
        ),
    )
    artifact_summary["controlled_override_workflow"] = build_controlled_override_workflow(
        user_input=request.user_input,
        selected_mode=selected_mode,
        run_failure_classification=artifact_summary["run_failure_classification"],
        apply_safety_escalation=apply_safety_escalation,
        release_readiness=artifact_summary["release_readiness"],
        retry_backoff_guardrails=artifact_summary["retry_backoff_guardrails"],
    )
    artifact_summary["operator_audit_trail"] = build_operator_audit_trail_summary(
        run_manifest=artifact_summary["run_manifest"],
        run_failure_classification=artifact_summary["run_failure_classification"],
        release_readiness=artifact_summary["release_readiness"],
        resume_checkpoint=artifact_summary["resume_checkpoint"],
        retry_backoff_guardrails=artifact_summary["retry_backoff_guardrails"],
        policy_decision_explainability=artifact_summary["policy_decision_explainability"],
        controlled_override_workflow=artifact_summary["controlled_override_workflow"],
    )
    artifact_summary["release_artifact_manifest"] = build_release_artifact_manifest(
        route=route_decision.route.value,
        mode=selected_mode.value,
        generated_files=tuple(file.path for file in artifact_bundle.files),
        proposed_files=tuple(file.path for file in materialization_result.proposed_files),
        written_files=materialization_result.written_paths,
        release_readiness=artifact_summary["release_readiness"],
        operator_audit_trail=artifact_summary["operator_audit_trail"],
    )
    artifact_summary["release_check_command"] = build_release_check_command_contract(
        workspace_root=workspace_root,
        release_artifact_manifest=artifact_summary["release_artifact_manifest"],
        command_runner=release_check_runner,
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


def _elapsed_ms(started_at: float, finished_at: float) -> int:
    return max(0, int(round((finished_at - started_at) * 1000)))
