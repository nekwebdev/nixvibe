"""Parallel specialist execution primitives."""

from __future__ import annotations

import inspect
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import replace
from typing import Sequence

from .types import (
    ModeDecision,
    OrchestrationRequest,
    RepoContext,
    RouteDecision,
    SpecialistDispatchContext,
    SpecialistExecutionOutcome,
    SpecialistExecutionResult,
    SpecialistTask,
)


def run_specialists(
    tasks: Sequence[SpecialistTask],
    *,
    max_workers: int | None = None,
) -> tuple[SpecialistExecutionResult, ...]:
    if not tasks:
        return ()

    workers = max_workers if max_workers is not None else len(tasks)
    workers = max(1, min(workers, len(tasks)))

    results: list[SpecialistExecutionResult | None] = [None] * len(tasks)

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {
            executor.submit(_run_task, task): index
            for index, task in enumerate(tasks)
        }
        for future in as_completed(futures):
            index = futures[future]
            task = tasks[index]
            try:
                payload = future.result()
            except Exception as exc:  # pragma: no cover - guarded by tests
                results[index] = SpecialistExecutionResult(
                    agent_id=task.agent_id,
                    task_scope=task.task_scope,
                    outcome=SpecialistExecutionOutcome.ERROR,
                    error=str(exc),
                )
                continue
            results[index] = SpecialistExecutionResult(
                agent_id=task.agent_id,
                task_scope=task.task_scope,
                outcome=SpecialistExecutionOutcome.OK,
                raw_payload=payload,
            )

    return tuple(result for result in results if result is not None)


def _run_task(task: SpecialistTask):
    if task.dispatch_context is not None and _runner_accepts_context(task.runner):
        return task.runner(task.dispatch_context)
    return task.runner()


def build_dispatch_context(
    *,
    request: OrchestrationRequest,
    context: RepoContext,
    route_decision: RouteDecision,
    mode_decision: ModeDecision,
) -> SpecialistDispatchContext:
    return SpecialistDispatchContext(
        requested_mode=request.requested_mode,
        resolved_route=route_decision.route,
        resolved_mode=mode_decision.mode,
        repository_state=context.repository_state,
        existing_config_present=context.existing_config_present,
        usable_nix_structure_present=context.usable_nix_structure_present,
        request_is_change=context.request_is_change,
        workspace_snapshot=context.workspace_snapshot,
        reference_profile=context.reference_profile,
        reference_adaptation=context.reference_adaptation,
    )


def with_dispatch_context(
    tasks: Sequence[SpecialistTask],
    *,
    dispatch_context: SpecialistDispatchContext,
) -> tuple[SpecialistTask, ...]:
    return tuple(
        replace(task, dispatch_context=dispatch_context)
        for task in tasks
    )


def _runner_accepts_context(runner) -> bool:
    try:
        signature = inspect.signature(runner)
    except (TypeError, ValueError):
        return False
    for parameter in signature.parameters.values():
        if parameter.kind in (
            inspect.Parameter.POSITIONAL_ONLY,
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
            inspect.Parameter.VAR_POSITIONAL,
        ):
            return True
    return False
