"""Patch orchestration helpers for runtime specialist outputs."""

from __future__ import annotations

import re
from typing import Any

from .types import SpecialistPayload


def normalize_patch_path(*, raw_path: str, index: int) -> str:
    cleaned = raw_path.replace("\\", "/").strip()
    segments = [segment for segment in cleaned.split("/") if segment not in ("", ".", "..")]
    filename = segments[-1] if segments else ""

    stem = filename
    if stem.lower().endswith(".patch"):
        stem = stem[:-6]
    if not stem:
        stem = "proposed-refactor"

    match = re.match(r"^(\d+)[-_]?(.*)$", stem)
    if match:
        number = max(1, int(match.group(1)))
        suffix = match.group(2) or "proposed-refactor"
    else:
        number = index
        suffix = stem

    slug = _slugify(suffix) or "proposed-refactor"
    return f"patches/{number:03d}-{slug}.patch"


def orchestrate_patch_proposals(
    payloads: tuple[SpecialistPayload, ...],
) -> tuple[dict[str, object], ...]:
    proposals: list[dict[str, object]] = []
    seen_paths: set[str] = set()
    sequence = 1

    for payload in payloads:
        patch_items = payload.artifacts.get("patches")
        if not isinstance(patch_items, list):
            continue

        for item in patch_items:
            parsed = _parse_patch_item(item)
            if parsed is None:
                continue
            raw_path, patch_id = parsed
            normalized_path = normalize_patch_path(raw_path=raw_path, index=sequence)
            if normalized_path in seen_paths:
                sequence += 1
                continue
            seen_paths.add(normalized_path)
            proposals.append(
                {
                    "id": patch_id or f"P-{sequence:03d}",
                    "path": normalized_path,
                    "source_agent": payload.agent_id,
                    "sequence": sequence,
                }
            )
            sequence += 1

    return tuple(proposals)


def patch_orchestration_summary(
    patches: tuple[dict[str, object], ...],
) -> dict[str, object]:
    return {
        "count": len(patches),
        "paths": tuple(
            patch["path"]
            for patch in patches
            if isinstance(patch.get("path"), str)
        ),
        "ids": tuple(
            patch["id"]
            for patch in patches
            if isinstance(patch.get("id"), str)
        ),
        "source_agents": tuple(
            patch["source_agent"]
            for patch in patches
            if isinstance(patch.get("source_agent"), str)
        ),
    }


def _parse_patch_item(item: Any) -> tuple[str, str] | None:
    if isinstance(item, str):
        stripped = item.strip()
        if not stripped:
            return None
        return stripped, ""

    if isinstance(item, dict):
        path = item.get("path")
        if not isinstance(path, str) or not path.strip():
            return None
        patch_id = item.get("id")
        normalized_id = patch_id.strip() if isinstance(patch_id, str) and patch_id.strip() else ""
        return path.strip(), normalized_id

    return None


def _slugify(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]+", "-", value).strip("-").lower()
