"""Deterministic specialist payload merge behavior."""

from __future__ import annotations

from collections import defaultdict
from typing import Iterable

from .conflicts import resolve_conflict
from .patches import orchestrate_patch_proposals, patch_orchestration_summary
from .types import (
    ConflictCandidate,
    MergeResult,
    Mode,
    OrchestrationPolicy,
    Priority,
    Severity,
    SpecialistFinding,
    SpecialistPayload,
    SpecialistRecommendation,
    SpecialistRisk,
)


def merge_specialist_payloads(
    payloads: Iterable[SpecialistPayload],
    policy: OrchestrationPolicy,
) -> MergeResult:
    payload_list = tuple(payloads)
    if not payload_list:
        raise ValueError("At least one specialist payload is required for merge.")

    findings = _sort_findings(
        finding
        for payload in payload_list
        for finding in payload.findings
    )
    recommendations = _resolve_recommendation_conflicts(payload_list, policy)
    risks = _sort_risks(
        risk
        for payload in payload_list
        for risk in payload.risks
    )
    artifact_summary = _merge_artifacts(payload_list)
    next_action = _select_next_action(payload_list, recommendations)

    forced_mode: Mode | None = None
    reason = "Merged specialist payloads successfully."
    if _has_contradictory_critical_findings(findings):
        forced_mode = Mode.PROPOSE
        reason = "Contradictory critical findings detected; forcing propose mode."

    return MergeResult(
        payloads=payload_list,
        findings=findings,
        recommendations=recommendations,
        risks=risks,
        artifact_summary=artifact_summary,
        next_action=next_action,
        forced_mode=forced_mode,
        reason=reason,
    )


def _resolve_recommendation_conflicts(
    payloads: tuple[SpecialistPayload, ...],
    policy: OrchestrationPolicy,
) -> tuple[SpecialistRecommendation, ...]:
    grouped: dict[str, list[tuple[SpecialistPayload, SpecialistRecommendation]]] = defaultdict(list)
    for payload in payloads:
        for recommendation in payload.recommendations:
            group = recommendation.conflict_group or f"{payload.agent_id}:{recommendation.id}"
            grouped[group].append((payload, recommendation))

    winners: list[SpecialistRecommendation] = []
    for group in sorted(grouped):
        group_items = grouped[group]
        if len(group_items) == 1:
            winners.append(group_items[0][1])
            continue

        candidates: list[ConflictCandidate] = []
        recommendation_by_candidate: dict[str, SpecialistRecommendation] = {}
        for payload, recommendation in group_items:
            candidate_id = f"{payload.agent_id}:{recommendation.id}"
            candidates.append(
                ConflictCandidate(
                    candidate_id=candidate_id,
                    priority=recommendation.policy_priority,
                    confidence=payload.confidence,
                    reversible=recommendation.reversible,
                    rationale=recommendation.action,
                )
            )
            recommendation_by_candidate[candidate_id] = recommendation

        winner = resolve_conflict(candidates, policy)
        winners.append(recommendation_by_candidate[winner.candidate_id])

    rank = _priority_rank_map(policy)
    winners.sort(
        key=lambda recommendation: (
            rank[_normalize_priority(recommendation.policy_priority)],
            recommendation.id,
            recommendation.action,
        )
    )
    return tuple(winners)


def _merge_artifacts(payloads: tuple[SpecialistPayload, ...]) -> dict[str, object]:
    target_trees: list[object] = []
    notes: list[str] = []
    next_actions: list[str] = []

    for payload in payloads:
        target_tree = payload.artifacts.get("target_tree")
        if target_tree is not None:
            target_trees.append(target_tree)

        payload_notes = payload.artifacts.get("notes")
        if isinstance(payload_notes, list):
            for note in payload_notes:
                if isinstance(note, str) and note.strip():
                    notes.append(note.strip())

        payload_next_actions = payload.artifacts.get("next_actions")
        if isinstance(payload_next_actions, list):
            for action in payload_next_actions:
                if isinstance(action, str) and action.strip():
                    next_actions.append(action.strip())

    deduped_notes = tuple(dict.fromkeys(notes))
    deduped_next_actions = tuple(dict.fromkeys(next_actions))
    patches = orchestrate_patch_proposals(payloads)

    return {
        "target_trees": tuple(target_trees),
        "patches": patches,
        "patch_orchestration": patch_orchestration_summary(patches),
        "notes": deduped_notes,
        "next_actions": deduped_next_actions,
        "payload_count": len(payloads),
    }


def _select_next_action(
    payloads: tuple[SpecialistPayload, ...],
    recommendations: tuple[SpecialistRecommendation, ...],
) -> str:
    for payload in payloads:
        actions = payload.artifacts.get("next_actions")
        if isinstance(actions, list):
            for action in actions:
                if isinstance(action, str) and action.strip():
                    return action.strip()

    if recommendations:
        return recommendations[0].action

    return "Review merged specialist outputs before selecting apply or propose."


def _has_contradictory_critical_findings(findings: tuple[SpecialistFinding, ...]) -> bool:
    buckets: dict[str, set[str]] = defaultdict(set)
    for finding in findings:
        if finding.severity is not Severity.CRITICAL:
            continue
        key = finding.contradiction_key or finding.id
        descriptor = f"{finding.summary}::{finding.impact}"
        buckets[key].add(descriptor)
    return any(len(values) > 1 for values in buckets.values())


def _sort_findings(findings: Iterable[SpecialistFinding]) -> tuple[SpecialistFinding, ...]:
    rank = {
        Severity.CRITICAL: 0,
        Severity.HIGH: 1,
        Severity.MEDIUM: 2,
        Severity.LOW: 3,
    }
    return tuple(sorted(findings, key=lambda finding: (rank[finding.severity], finding.id)))


def _sort_risks(risks: Iterable[SpecialistRisk]) -> tuple[SpecialistRisk, ...]:
    rank = {
        "critical": 0,
        "high": 1,
        "medium": 2,
        "low": 3,
    }
    return tuple(
        sorted(
            risks,
            key=lambda risk: (rank.get(risk.severity.strip().lower(), 4), risk.id),
        )
    )


def _priority_rank_map(policy: OrchestrationPolicy) -> dict[Priority, int]:
    return {
        priority: index
        for index, priority in enumerate(policy.conflict.ordered_priorities)
    }


def _normalize_priority(priority: Priority | str) -> Priority:
    if isinstance(priority, Priority):
        return priority

    normalized = str(priority).strip().lower().replace("-", " ").replace("_", " ")
    for candidate in Priority:
        if candidate.value == normalized:
            return candidate

    valid = ", ".join(value.value for value in Priority)
    raise ValueError(f"Unsupported priority: {priority!r}. Valid priorities: {valid}")
