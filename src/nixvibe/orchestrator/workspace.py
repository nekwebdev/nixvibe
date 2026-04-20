"""Bounded workspace/reference profiling helpers."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable

from .types import ReferenceAdaptation, ReferenceProfile, RepoContext, WorkspaceSnapshot

_IGNORED_DIRS = {
    ".git",
    "__pycache__",
    ".direnv",
    ".devenv",
    ".mypy_cache",
    ".pytest_cache",
    "node_modules",
    "result",
}


def build_repo_context(
    *,
    workspace_root: str | Path,
    reference_root: str | Path | None = None,
    max_entries: int = 200,
    request_is_change: bool | None = None,
) -> RepoContext:
    """Build RepoContext from bounded filesystem inspection."""
    snapshot = snapshot_workspace(workspace_root=workspace_root, max_entries=max_entries)
    reference_profile = (
        inspect_reference(reference_root=reference_root, max_entries=max_entries)
        if reference_root is not None
        else None
    )
    reference_adaptation = (
        derive_reference_adaptation(
            workspace_snapshot=snapshot,
            reference_profile=reference_profile,
        )
        if reference_profile is not None
        else None
    )
    existing_config_present = snapshot.flake_present or snapshot.nix_file_count > 0
    usable_nix_structure_present = bool(
        snapshot.flake_present
        and (snapshot.module_paths or snapshot.has_hosts_tree or snapshot.has_home_tree)
    )

    repository_state = "known" if (snapshot.entries or snapshot.flake_present) else "empty"
    return RepoContext(
        existing_config_present=existing_config_present,
        usable_nix_structure_present=usable_nix_structure_present,
        request_is_change=request_is_change,
        repository_state=repository_state,
        workspace_snapshot=snapshot,
        reference_profile=reference_profile,
        reference_adaptation=reference_adaptation,
    )


def snapshot_workspace(
    *,
    workspace_root: str | Path,
    max_entries: int = 200,
) -> WorkspaceSnapshot:
    """Collect a deterministic bounded snapshot of workspace structure."""
    root = Path(workspace_root).resolve()
    entries, truncated = _collect_entries(root=root, max_entries=max_entries)
    flake_present = (root / "flake.nix").exists()
    nix_file_count = sum(1 for entry in entries if entry.endswith(".nix"))
    module_paths = tuple(
        entry
        for entry in entries
        if entry.startswith("modules/") and entry.endswith(".nix")
    )
    has_hosts_tree = any(
        entry.startswith("hosts/") or entry.startswith("modules/nixosModules/hosts/")
        for entry in entries
    )
    has_home_tree = any(
        entry.startswith("home/") or entry.startswith("modules/homeModules/")
        for entry in entries
    )
    return WorkspaceSnapshot(
        root=str(root),
        max_entries=max_entries,
        entries=entries,
        truncated=truncated,
        flake_present=flake_present,
        nix_file_count=nix_file_count,
        module_paths=module_paths,
        has_hosts_tree=has_hosts_tree,
        has_home_tree=has_home_tree,
    )


def inspect_reference(
    *,
    reference_root: str | Path,
    max_entries: int = 200,
) -> ReferenceProfile:
    """Inspect an optional reference repo and extract adaptation hints."""
    root = Path(reference_root).resolve()
    entries, truncated = _collect_entries(root=root, max_entries=max_entries)
    flake_present = (root / "flake.nix").exists()
    module_paths = tuple(
        entry
        for entry in entries
        if entry.startswith("modules/") and entry.endswith(".nix")
    )
    validation_patterns = _validation_patterns(root=root, entries=entries)
    notes = _reference_notes(entries=entries)
    return ReferenceProfile(
        root=str(root),
        max_entries=max_entries,
        entries=entries,
        truncated=truncated,
        flake_present=flake_present,
        module_paths=module_paths,
        validation_patterns=validation_patterns,
        notes=notes,
    )


def derive_reference_adaptation(
    *,
    workspace_snapshot: WorkspaceSnapshot,
    reference_profile: ReferenceProfile,
) -> ReferenceAdaptation:
    preserve_existing_structure = bool(
        workspace_snapshot.module_paths
        or workspace_snapshot.has_hosts_tree
        or workspace_snapshot.has_home_tree
    )
    strategy = "preserve-and-extend" if preserve_existing_structure else "bootstrap-from-reference-patterns"
    suggested_module_aggregators = _suggested_module_aggregators(reference_profile)
    suggested_validation_commands = (
        reference_profile.validation_patterns
        if reference_profile.validation_patterns
        else ("nix flake check", "nix fmt")
    )
    notes = tuple(
        dict.fromkeys(
            (
                "Inspect and emulate structure, conventions, and validation patterns from user-provided path; adapt to target constraints; never blindly copy.",
                *reference_profile.notes,
            )
        )
    )
    return ReferenceAdaptation(
        strategy=strategy,
        preserve_existing_structure=preserve_existing_structure,
        suggested_module_aggregators=suggested_module_aggregators,
        suggested_validation_commands=suggested_validation_commands,
        notes=notes,
    )


def _collect_entries(*, root: Path, max_entries: int) -> tuple[tuple[str, ...], bool]:
    if max_entries < 1:
        raise ValueError("max_entries must be >= 1")
    if not root.exists():
        raise FileNotFoundError(f"Path does not exist: {root}")

    entries: list[str] = []
    truncated = False

    for entry in _iter_entries(root):
        if len(entries) >= max_entries:
            truncated = True
            break
        entries.append(entry)
    return tuple(entries), truncated


def _iter_entries(root: Path) -> Iterable[str]:
    for current_root, dirs, files in os.walk(root):
        dirs[:] = sorted(
            directory
            for directory in dirs
            if directory not in _IGNORED_DIRS
        )
        rel_root = Path(current_root).relative_to(root)
        for file_name in sorted(files):
            relative_path = rel_root / file_name if rel_root != Path(".") else Path(file_name)
            yield relative_path.as_posix()


def _validation_patterns(*, root: Path, entries: tuple[str, ...]) -> tuple[str, ...]:
    patterns: list[str] = []
    candidates = [
        entry for entry in entries
        if entry == "flake.nix" or entry.startswith("scripts/") or entry.endswith(".nix")
    ]
    for entry in candidates[:40]:
        content = _read_text(root / entry)
        if "nix flake check" in content:
            patterns.append("nix flake check")
        if "nix fmt" in content:
            patterns.append("nix fmt")
    return tuple(dict.fromkeys(patterns))


def _reference_notes(*, entries: tuple[str, ...]) -> tuple[str, ...]:
    notes = [
        "Inspect and emulate structure, conventions, and validation patterns from user-provided path; adapt to target constraints; never blindly copy.",
    ]

    if "modules/core/default.nix" in entries:
        notes.append("Reference exposes modules/core/default.nix pattern.")
    if "modules/roles/default.nix" in entries:
        notes.append("Reference exposes modules/roles/default.nix pattern.")
    if "modules/services/default.nix" in entries:
        notes.append("Reference exposes modules/services/default.nix pattern.")
    return tuple(dict.fromkeys(notes))


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def _suggested_module_aggregators(reference_profile: ReferenceProfile) -> tuple[str, ...]:
    canonical = (
        "modules/core/default.nix",
        "modules/roles/default.nix",
        "modules/services/default.nix",
    )
    from_reference = tuple(
        path
        for path in canonical
        if path in reference_profile.module_paths
    )
    if from_reference:
        return from_reference
    return canonical
