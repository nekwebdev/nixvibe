"""Parallel specialist execution primitives."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Sequence

from .types import SpecialistExecutionOutcome, SpecialistExecutionResult, SpecialistTask


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
    return task.runner()

