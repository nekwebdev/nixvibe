"""Benchmark trend history persistence helpers."""

from __future__ import annotations

from typing import Sequence


def build_benchmark_trend_history(
    *,
    benchmark_trend_entry: dict[str, object],
    prior_history: Sequence[dict[str, object]] = (),
    history_limit: int = 20,
) -> dict[str, object]:
    safe_limit = max(1, int(history_limit))
    normalized_prior = tuple(_normalize_trend_entry(entry) for entry in prior_history if _is_trend_entry(entry))
    retained_prior = normalized_prior[-safe_limit:]
    previous_entry = retained_prior[-1] if retained_prior else None

    current_valid = _is_trend_entry(benchmark_trend_entry)
    current_entry = _normalize_trend_entry(benchmark_trend_entry) if current_valid else None
    persisted_entries = retained_prior + ((current_entry,) if current_entry is not None else ())
    trimmed_entries = persisted_entries[-safe_limit:]

    dropped_count = max(0, len(normalized_prior) - len(retained_prior))
    if len(persisted_entries) > safe_limit:
        dropped_count += len(persisted_entries) - safe_limit

    history_status = _history_status(
        has_previous=previous_entry is not None,
        current_valid=current_valid,
    )

    return {
        "contract": "benchmark-trend-history/v1",
        "profile": "phase16-trend-history/v1",
        "history_status": history_status,
        "history_ready": current_valid,
        "history_limit": safe_limit,
        "history_count": len(trimmed_entries),
        "dropped_count": dropped_count,
        "has_previous": previous_entry is not None,
        "previous_trend_key": str(previous_entry.get("trend_key") or "") if previous_entry else None,
        "current_trend_key": str(current_entry.get("trend_key") or "unknown")
        if current_entry
        else str(benchmark_trend_entry.get("trend_key") or "unknown"),
        "previous_benchmark_trend_entry": previous_entry,
        "history_entries": trimmed_entries,
        "next_history_action": _next_history_action(
            history_status=history_status,
            has_previous=previous_entry is not None,
        ),
        "summary": (
            f"Trend history `{history_status}` with {len(trimmed_entries)} stored entries "
            f"(limit {safe_limit})."
        ),
    }


def _history_status(*, has_previous: bool, current_valid: bool) -> str:
    if not current_valid:
        return "blocked"
    if not has_previous:
        return "seeded"
    return "advanced"


def _next_history_action(*, history_status: str, has_previous: bool) -> str:
    if history_status == "blocked":
        return "Resolve current trend entry contract issues before persisting history."
    if not has_previous:
        return "Persist current trend history and run another benchmark cycle."
    return "Persist updated history and continue trend-delta monitoring."


def _is_trend_entry(value: object) -> bool:
    if not isinstance(value, dict):
        return False
    return str(value.get("contract") or "") == "benchmark-trend-entry/v1"


def _normalize_trend_entry(value: dict[str, object]) -> dict[str, object]:
    return dict(value)
