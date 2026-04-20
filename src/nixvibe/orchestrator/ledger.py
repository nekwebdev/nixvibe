"""Git ledger inspection helpers for orchestration context."""

from __future__ import annotations

import subprocess
from pathlib import Path


def inspect_git_ledger(workspace_root: str | Path) -> dict[str, object]:
    root = Path(workspace_root)
    if not root.exists():
        return {
            "available": False,
            "reason": "workspace root does not exist",
        }

    inside = _run_git(root, "rev-parse", "--is-inside-work-tree")
    if inside is None or inside[0] != 0 or inside[1].strip() != "true":
        return {
            "available": False,
            "reason": "workspace is not a git repository",
        }

    branch = _run_git(root, "rev-parse", "--abbrev-ref", "HEAD")
    head = _run_git(root, "rev-parse", "--short", "HEAD")
    status = _run_git(root, "status", "--short")
    status_lines = _status_lines(status)
    staged, unstaged, untracked, changed_paths = _status_counts(status_lines)
    change_signals = _change_signals(
        staged_count=staged,
        unstaged_count=unstaged,
        untracked_count=untracked,
    )

    return {
        "available": True,
        "branch": _stdout(branch),
        "head": _stdout(head),
        "dirty": bool(status_lines),
        "staged_count": staged,
        "unstaged_count": unstaged,
        "untracked_count": untracked,
        "changed_paths": changed_paths,
        "status_lines": status_lines,
        "change_classification": change_signals["change_classification"],
        "has_staged_changes": change_signals["has_staged_changes"],
        "has_unstaged_changes": change_signals["has_unstaged_changes"],
        "has_untracked_changes": change_signals["has_untracked_changes"],
        "drift_detected": change_signals["drift_detected"],
        "drift_reasons": change_signals["drift_reasons"],
        "drift_severity": change_signals["drift_severity"],
    }


def _run_git(root: Path, *args: str) -> tuple[int, str, str] | None:
    try:
        completed = subprocess.run(
            ("git", *args),
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
        )
        return completed.returncode, completed.stdout, completed.stderr
    except OSError:
        return None


def _stdout(result: tuple[int, str, str] | None) -> str:
    if result is None:
        return ""
    return result[1].strip()


def _status_lines(result: tuple[int, str, str] | None) -> tuple[str, ...]:
    if result is None or result[0] != 0:
        return ()
    lines = []
    for line in result[1].splitlines():
        stripped = line.rstrip()
        if stripped:
            lines.append(stripped)
    return tuple(lines)


def _status_counts(status_lines: tuple[str, ...]) -> tuple[int, int, int, tuple[str, ...]]:
    staged = 0
    unstaged = 0
    untracked = 0
    paths: list[str] = []

    for line in status_lines:
        if line.startswith("?? "):
            untracked += 1
            path = line[3:].strip()
            if path:
                paths.append(path)
            continue

        if len(line) < 3:
            continue

        index_state = line[0]
        worktree_state = line[1]
        path = line[3:].strip()
        if path:
            paths.append(path)

        if index_state != " ":
            staged += 1
        if worktree_state != " ":
            unstaged += 1

    deduped_paths = tuple(dict.fromkeys(paths))
    return staged, unstaged, untracked, deduped_paths


def _change_signals(
    *,
    staged_count: int,
    unstaged_count: int,
    untracked_count: int,
) -> dict[str, object]:
    has_staged = staged_count > 0
    has_unstaged = unstaged_count > 0
    has_untracked = untracked_count > 0

    classification_map = {
        (False, False, False): "clean",
        (True, False, False): "staged-only",
        (False, True, False): "unstaged-only",
        (False, False, True): "untracked-only",
        (True, True, False): "staged-unstaged",
        (True, False, True): "staged-untracked",
        (False, True, True): "unstaged-untracked",
        (True, True, True): "mixed",
    }
    classification = classification_map[(has_staged, has_unstaged, has_untracked)]

    drift_detected = has_unstaged or has_untracked
    drift_reasons: list[str] = []
    if has_unstaged:
        drift_reasons.append("unstaged_changes")
    if has_untracked:
        drift_reasons.append("untracked_changes")

    if not drift_detected:
        drift_severity = "none"
    elif has_unstaged and has_untracked:
        drift_severity = "high"
    elif has_unstaged:
        drift_severity = "high"
    else:
        drift_severity = "medium"

    return {
        "change_classification": classification,
        "has_staged_changes": has_staged,
        "has_unstaged_changes": has_unstaged,
        "has_untracked_changes": has_untracked,
        "drift_detected": drift_detected,
        "drift_reasons": tuple(drift_reasons),
        "drift_severity": drift_severity,
    }
