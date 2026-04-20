"""Deterministic route selection for init vs audit."""

from __future__ import annotations

import re
from dataclasses import replace

from .types import OrchestrationPolicy, OrchestrationRequest, RepoContext, Route, RouteDecision

_TOKEN_RE = re.compile(r"[a-zA-Z][a-zA-Z0-9/-]*")

_AMBIGUOUS_QUESTIONS = (
    "Do you want a fresh scaffold or changes to an existing configuration?",
    "Is there already a usable flake/module layout in this repository?",
    "Should nixvibe return a target tree and patches, or a new scaffold?",
    "Do you want write mode kept at propose until review?",
)


def select_route(
    request: OrchestrationRequest,
    context: RepoContext,
    policy: OrchestrationPolicy,
) -> RouteDecision:
    effective_context = _context_with_profile_hints(context)
    text_tokens = _tokenize(request.user_input)
    init_score = len(text_tokens & policy.route.init_keywords)
    audit_score = len(text_tokens & policy.route.audit_keywords)

    if init_score > audit_score:
        return RouteDecision(
            route=Route.INIT,
            reason=f"Matched init intent keywords ({init_score} > {audit_score}).",
        )

    if audit_score > init_score:
        return RouteDecision(
            route=Route.AUDIT,
            reason=f"Matched audit intent keywords ({audit_score} > {init_score}).",
        )

    if effective_context.usable_nix_structure_present is False:
        return RouteDecision(
            route=Route.INIT,
            reason="No usable Nix structure detected; route policy prefers init.",
        )

    if (
        effective_context.existing_config_present is True
        and effective_context.request_is_change is not False
    ):
        return RouteDecision(
            route=Route.AUDIT,
            reason="Existing config with requested changes; route policy prefers audit.",
        )

    repository_unknown = effective_context.repository_state.strip().lower() in {"", "unknown"}
    context_ambiguous = (
        effective_context.existing_config_present is None
        and effective_context.usable_nix_structure_present is None
    )
    if repository_unknown or context_ambiguous:
        fallback = _fallback_route(effective_context)
        return RouteDecision(
            route=fallback,
            reason=(
                "Repository context is ambiguous. Clarifications requested; "
                f"using deterministic fallback route '{fallback.value}'."
            ),
            needs_clarification=True,
            clarification_questions=_AMBIGUOUS_QUESTIONS,
        )

    fallback = _fallback_route(effective_context)
    return RouteDecision(
        route=fallback,
        reason=f"Ambiguous intent; using deterministic fallback route '{fallback.value}'.",
    )


def _tokenize(text: str) -> set[str]:
    return {token.lower() for token in _TOKEN_RE.findall(text)}


def _fallback_route(context: RepoContext) -> Route:
    if context.existing_config_present is True:
        return Route.AUDIT
    return Route.INIT


def _context_with_profile_hints(context: RepoContext) -> RepoContext:
    snapshot = context.workspace_snapshot
    if snapshot is None:
        return context

    existing_config_present = context.existing_config_present
    usable_nix_structure_present = context.usable_nix_structure_present
    repository_state = context.repository_state

    if existing_config_present is None:
        existing_config_present = snapshot.flake_present or snapshot.nix_file_count > 0

    if usable_nix_structure_present is None:
        usable_nix_structure_present = bool(
            snapshot.flake_present
            and (snapshot.module_paths or snapshot.has_hosts_tree or snapshot.has_home_tree)
        )

    if repository_state.strip().lower() in {"", "unknown"}:
        repository_state = "known"

    return replace(
        context,
        existing_config_present=existing_config_present,
        usable_nix_structure_present=usable_nix_structure_present,
        repository_state=repository_state,
    )
