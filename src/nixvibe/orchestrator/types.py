"""Shared orchestration types."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, FrozenSet, Mapping, Tuple


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


class SpecialistStatus(str, Enum):
    OK = "ok"
    WARNING = "warning"
    ERROR = "error"


class Severity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RecommendationPriority(str, Enum):
    NOW = "now"
    NEXT = "next"
    LATER = "later"


class SpecialistExecutionOutcome(str, Enum):
    OK = "ok"
    ERROR = "error"
    INVALID = "invalid"


@dataclass(frozen=True)
class OrchestrationRequest:
    user_input: str
    requested_mode: Mode | str | None = None
    explicit_apply_opt_in: bool = False


@dataclass(frozen=True)
class WorkspaceSnapshot:
    root: str
    max_entries: int
    entries: Tuple[str, ...]
    truncated: bool
    flake_present: bool
    nix_file_count: int
    module_paths: Tuple[str, ...]
    has_hosts_tree: bool
    has_home_tree: bool


@dataclass(frozen=True)
class ReferenceProfile:
    root: str
    max_entries: int
    entries: Tuple[str, ...]
    truncated: bool
    flake_present: bool
    module_paths: Tuple[str, ...]
    validation_patterns: Tuple[str, ...]
    notes: Tuple[str, ...]


@dataclass(frozen=True)
class ReferenceAdaptation:
    strategy: str
    preserve_existing_structure: bool
    suggested_module_aggregators: Tuple[str, ...]
    suggested_validation_commands: Tuple[str, ...]
    notes: Tuple[str, ...]


@dataclass(frozen=True)
class RepoContext:
    existing_config_present: bool | None = None
    usable_nix_structure_present: bool | None = None
    request_is_change: bool | None = None
    repository_state: str = "unknown"
    workspace_snapshot: WorkspaceSnapshot | None = None
    reference_profile: ReferenceProfile | None = None
    reference_adaptation: ReferenceAdaptation | None = None


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
class SpecialistFinding:
    id: str
    severity: Severity
    summary: str
    evidence: Tuple[str, ...]
    impact: str
    contradiction_key: str | None = None


@dataclass(frozen=True)
class SpecialistRecommendation:
    id: str
    action: str
    priority: RecommendationPriority
    maps_to_findings: Tuple[str, ...]
    reversible: bool
    policy_priority: Priority | str = Priority.USER_PREFERENCE
    conflict_group: str | None = None


@dataclass(frozen=True)
class SpecialistRisk:
    id: str
    category: str
    severity: str
    mitigation: str


@dataclass(frozen=True)
class SpecialistPayload:
    agent_id: str
    task_scope: str
    status: SpecialistStatus
    findings: Tuple[SpecialistFinding, ...]
    recommendations: Tuple[SpecialistRecommendation, ...]
    confidence: float
    risks: Tuple[SpecialistRisk, ...]
    artifacts: Mapping[str, Any]
    checks: Mapping[str, Any]
    timestamp: str


SpecialistRunner = Callable[[], Mapping[str, Any] | SpecialistPayload]


@dataclass(frozen=True)
class SpecialistTask:
    agent_id: str
    task_scope: str
    runner: SpecialistRunner


@dataclass(frozen=True)
class SpecialistExecutionResult:
    agent_id: str
    task_scope: str
    outcome: SpecialistExecutionOutcome
    raw_payload: Mapping[str, Any] | SpecialistPayload | None = None
    payload: SpecialistPayload | None = None
    error: str | None = None


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


@dataclass(frozen=True)
class MergeResult:
    payloads: Tuple[SpecialistPayload, ...]
    findings: Tuple[SpecialistFinding, ...]
    recommendations: Tuple[SpecialistRecommendation, ...]
    risks: Tuple[SpecialistRisk, ...]
    artifact_summary: Mapping[str, Any]
    next_action: str
    forced_mode: Mode | None = None
    reason: str = ""


@dataclass(frozen=True)
class ArtifactFile:
    path: str
    content: str
    description: str


@dataclass(frozen=True)
class ArtifactBundle:
    route: Route
    files: Tuple[ArtifactFile, ...]
    summary: Mapping[str, Any]


@dataclass(frozen=True)
class ArtifactMaterializationResult:
    mode: Mode
    proposed_files: Tuple[ArtifactFile, ...]
    written_paths: Tuple[str, ...]
    write_performed: bool


@dataclass(frozen=True)
class ValidationCommandResult:
    command: str
    exit_code: int
    success: bool
    stdout: str
    stderr: str


@dataclass(frozen=True)
class ValidationReport:
    required: bool
    executed: bool
    success: bool
    flake_present: bool
    results: Tuple[ValidationCommandResult, ...]
    reason: str = ""


@dataclass(frozen=True)
class OrchestrationResult:
    route_decision: RouteDecision
    mode_decision: ModeDecision
    selected_mode: Mode
    artifact_summary: Mapping[str, Any]
    next_action: str
    included_payloads: Tuple[SpecialistPayload, ...]
    excluded_specialists: Tuple[str, ...]
    specialist_results: Tuple[SpecialistExecutionResult, ...]
    merge_reason: str = ""
    generated_artifacts: Tuple[ArtifactFile, ...] = ()
    proposed_artifacts: Tuple[ArtifactFile, ...] = ()
    written_artifact_paths: Tuple[str, ...] = ()
    validation_report: ValidationReport | None = None
