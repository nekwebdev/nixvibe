"""Runtime specialist execution contract planning."""

from __future__ import annotations

from .types import (
    Route,
    RuntimeSpecialistContract,
    RuntimeSpecialistHandler,
    RuntimeSpecialistHandlerRegistry,
    RuntimeSpecialistRole,
    RuntimeSpecialistSpec,
    SpecialistDispatchContext,
    SpecialistTask,
)


class RuntimeSpecialistContractError(RuntimeError):
    """Raised when runtime contract cannot be planned safely."""


def default_runtime_contract(route: Route) -> RuntimeSpecialistContract:
    if route is Route.AUDIT:
        return RuntimeSpecialistContract(
            name="audit-default",
            route=Route.AUDIT,
            specialists=(
                RuntimeSpecialistSpec(
                    role=RuntimeSpecialistRole.ARCHITECTURE,
                    agent_id="architecture",
                    task_scope="Assess structure and modular boundaries.",
                    required=True,
                ),
                RuntimeSpecialistSpec(
                    role=RuntimeSpecialistRole.AUDIT,
                    agent_id="audit",
                    task_scope="Analyze existing config risks and refactor path.",
                    required=True,
                ),
                RuntimeSpecialistSpec(
                    role=RuntimeSpecialistRole.VALIDATE,
                    agent_id="validate",
                    task_scope="Assess validation and safety checks.",
                    required=True,
                ),
                RuntimeSpecialistSpec(
                    role=RuntimeSpecialistRole.EXPLAIN,
                    agent_id="explain",
                    task_scope="Summarize rationale and teaching notes.",
                    required=False,
                ),
            ),
        )

    return RuntimeSpecialistContract(
        name="init-default",
        route=Route.INIT,
        specialists=(
            RuntimeSpecialistSpec(
                role=RuntimeSpecialistRole.ARCHITECTURE,
                agent_id="architecture",
                task_scope="Design dendritic scaffold layout.",
                required=True,
            ),
            RuntimeSpecialistSpec(
                role=RuntimeSpecialistRole.MODULE,
                agent_id="module",
                task_scope="Define module partitioning and composition.",
                required=True,
            ),
            RuntimeSpecialistSpec(
                role=RuntimeSpecialistRole.VALIDATE,
                agent_id="validate",
                task_scope="Assess validation/readiness checks.",
                required=True,
            ),
            RuntimeSpecialistSpec(
                role=RuntimeSpecialistRole.EXPLAIN,
                agent_id="explain",
                task_scope="Summarize scaffold rationale for user.",
                required=False,
            ),
        ),
    )


def plan_runtime_specialists(
    *,
    contract: RuntimeSpecialistContract,
    handlers: RuntimeSpecialistHandlerRegistry,
    dispatch_context: SpecialistDispatchContext,
) -> tuple[SpecialistTask, ...]:
    if contract.route is not dispatch_context.resolved_route:
        raise RuntimeSpecialistContractError(
            f"Contract route '{contract.route.value}' does not match resolved route "
            f"'{dispatch_context.resolved_route.value}'."
        )

    resolved_handlers = _normalize_handlers(handlers)
    tasks: list[SpecialistTask] = []
    missing_required: list[str] = []

    for spec in contract.specialists:
        handler = resolved_handlers.get(spec.role)
        if handler is None:
            if spec.required:
                missing_required.append(spec.role.value)
            continue

        tasks.append(
            SpecialistTask(
                agent_id=spec.agent_id,
                task_scope=spec.task_scope,
                runner=handler,
                dispatch_context=dispatch_context,
            )
        )

    if missing_required:
        missing = ", ".join(sorted(set(missing_required)))
        raise RuntimeSpecialistContractError(
            f"Missing required specialist handlers for roles: {missing}"
        )

    if not tasks:
        raise RuntimeSpecialistContractError(
            "Runtime contract planning produced zero specialist tasks."
        )

    return tuple(tasks)


def _normalize_handlers(
    handlers: RuntimeSpecialistHandlerRegistry,
):
    normalized: dict[RuntimeSpecialistRole, RuntimeSpecialistHandler] = {}
    for key, handler in handlers.items():
        role = _normalize_role_key(key)
        normalized[role] = handler
    return normalized


def _normalize_role_key(key: RuntimeSpecialistRole | str) -> RuntimeSpecialistRole:
    if isinstance(key, RuntimeSpecialistRole):
        return key

    normalized = str(key).strip().lower()
    for candidate in RuntimeSpecialistRole:
        if candidate.value == normalized:
            return candidate

    valid = ", ".join(role.value for role in RuntimeSpecialistRole)
    raise RuntimeSpecialistContractError(
        f"Unsupported runtime specialist role key: {key!r}. Valid roles: {valid}"
    )
