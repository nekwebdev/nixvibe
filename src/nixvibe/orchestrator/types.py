"""Shared orchestration types."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import FrozenSet, Tuple


class Route(str, Enum):
    INIT = "init"
    AUDIT = "audit"


class Mode(str, Enum):
    ADVICE = "advice"
    PROPOSE = "propose"
    APPLY = "apply"


class Priority(str, Enum):
    SAFETY = "safety"
    CORRECTNESS = "correctness"
    REVERSIBILITY = "reversibility"
    SIMPLICITY = "simplicity"
    USER_PREFERENCE = "user preference"
    STYLE = "style"


@dataclass(frozen=True)
class OrchestrationRequest:
    user_input: str
    requested_mode: Mode | str | None = None
    explicit_apply_opt_in: bool = False


@dataclass(frozen=True)
class RepoContext:
    existing_config_present: bool | None = None
    usable_nix_structure_present: bool | None = None
    request_is_change: bool | None = None
    repository_state: str = "unknown"


@dataclass(frozen=True)
class RouteDecision:
    route: Route
    reason: str
    needs_clarification: bool = False
    clarification_questions: Tuple[str, ...] = ()


@dataclass(frozen=True)
class ModeDecision:
    mode: Mode
    reason: str
    write_allowed: bool
    requires_confirmation: bool


@dataclass(frozen=True)
class ConflictCandidate:
    candidate_id: str
    priority: Priority | str
    confidence: float
    reversible: bool
    rationale: str = ""


@dataclass(frozen=True)
class RoutePolicy:
    init_description: str
    audit_description: str
    init_keywords: FrozenSet[str]
    audit_keywords: FrozenSet[str]


@dataclass(frozen=True)
class WriteModePolicy:
    audit_default_mode: Mode
    apply_requires_explicit_opt_in: bool


@dataclass(frozen=True)
class ConflictPolicy:
    ordered_priorities: Tuple[Priority, ...]


@dataclass(frozen=True)
class OrchestrationPolicy:
    route: RoutePolicy
    write_mode: WriteModePolicy
    conflict: ConflictPolicy
    source_path: str

