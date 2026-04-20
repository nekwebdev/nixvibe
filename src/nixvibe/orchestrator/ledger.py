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
