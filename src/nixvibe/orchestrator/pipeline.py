"""End-to-end orchestration pipeline for route/mode/specialist merge."""

from __future__ import annotations

from typing import Sequence

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
)


class OrchestrationPipelineError(RuntimeError):
    """Raised when pipeline cannot produce a valid orchestration result."""


def run_pipeline(
    request: OrchestrationRequest,
    context: RepoContext,
    specialist_tasks: Sequence[SpecialistTask],
    *,
    policy: OrchestrationPolicy | None = None,
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

    return OrchestrationResult(
        route_decision=route_decision,
        mode_decision=mode_decision,
        selected_mode=selected_mode,
        artifact_summary=merge_result.artifact_summary,
        next_action=merge_result.next_action,
        included_payloads=valid_payloads,
        excluded_specialists=excluded,
        specialist_results=validated_results,
        merge_reason=merge_result.reason,
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

