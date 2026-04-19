"""Deterministic conflict resolution based on fixed policy priority."""

from __future__ import annotations

from dataclasses import replace
from typing import Iterable

from .types import ConflictCandidate, OrchestrationPolicy, Priority


def resolve_conflict(
    candidates: Iterable[ConflictCandidate],
    policy: OrchestrationPolicy,
) -> ConflictCandidate:
    normalized_candidates = [_normalize_candidate(c) for c in candidates]
    if not normalized_candidates:
        raise ValueError("At least one conflict candidate is required.")

    rank_map = {priority: index for index, priority in enumerate(policy.conflict.ordered_priorities)}
    missing_priorities = {
        candidate.priority
        for candidate in normalized_candidates
        if candidate.priority not in rank_map
    }
    if missing_priorities:
        names = ", ".join(sorted(priority.value for priority in missing_priorities))
        raise ValueError(f"Candidate priority not in policy order: {names}")

    return sorted(
        normalized_candidates,
        key=lambda candidate: (
            rank_map[candidate.priority],
            -candidate.confidence,
            0 if candidate.reversible else 1,
            candidate.candidate_id,
        ),
    )[0]


def _normalize_candidate(candidate: ConflictCandidate) -> ConflictCandidate:
    priority = _normalize_priority(candidate.priority)
    confidence = float(candidate.confidence)
    if confidence < 0.0 or confidence > 1.0:
        raise ValueError(
            f"Candidate '{candidate.candidate_id}' has invalid confidence {candidate.confidence}."
        )
    return replace(candidate, priority=priority, confidence=confidence)


def _normalize_priority(priority: Priority | str) -> Priority:
    if isinstance(priority, Priority):
        return priority

    normalized = str(priority).strip().lower().replace("-", " ").replace("_", " ")
    for candidate in Priority:
        if candidate.value == normalized:
            return candidate

    valid = ", ".join(priority.value for priority in Priority)
    raise ValueError(f"Unsupported priority: {priority!r}. Valid priorities: {valid}")

