"""Release-check command contract helpers."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Callable

ReleaseCheckRunner = Callable[[tuple[str, ...], Path], tuple[int, str, str]]


def build_release_check_command_contract(
    *,
    workspace_root: str | Path,
    release_artifact_manifest: dict[str, object],
    command_runner: ReleaseCheckRunner | None = None,
) -> dict[str, object]:
    root = Path(workspace_root)
    script_path = root / "scripts" / "release-check.sh"
    command = ("bash", "scripts/release-check.sh")
    release_ready = bool(release_artifact_manifest.get("release_ready", False))
    script_exists = script_path.exists()

    if not script_exists:
        return _summary(
            command=command,
            release_ready=release_ready,
            script_exists=False,
            executed=False,
            status="skipped",
            reason="release_check_script_missing",
            exit_code=None,
            stdout="",
            stderr="scripts/release-check.sh not found.",
        )

    if not release_ready:
        return _summary(
            command=command,
            release_ready=release_ready,
            script_exists=True,
            executed=False,
            status="skipped",
            reason="release_manifest_not_ready",
            exit_code=None,
            stdout="",
            stderr="Release artifact manifest has unmet checklist items.",
        )

    if command_runner is None:
        return _summary(
            command=command,
            release_ready=release_ready,
            script_exists=True,
            executed=False,
            status="pending",
            reason="runner_unavailable_for_release_ready",
            exit_code=None,
            stdout="",
            stderr="Release check runner not provided.",
        )

    exit_code, stdout, stderr = command_runner(command, root)
    status = "passed" if int(exit_code) == 0 else "failed"
    reason = "release_check_passed" if int(exit_code) == 0 else "release_check_failed"
    return _summary(
        command=command,
        release_ready=release_ready,
        script_exists=True,
        executed=True,
        status=status,
        reason=reason,
        exit_code=int(exit_code),
        stdout=str(stdout),
        stderr=str(stderr),
    )


def _summary(
    *,
    command: tuple[str, ...],
    release_ready: bool,
    script_exists: bool,
    executed: bool,
    status: str,
    reason: str,
    exit_code: int | None,
    stdout: str,
    stderr: str,
) -> dict[str, object]:
    ready_for_tagging = release_ready and status == "passed"
    next_action = (
        "Release checks passed. Safe to continue release tagging."
        if ready_for_tagging
        else (
            "Run release-check workflow after release manifest passes."
            if status in {"skipped", "pending"}
            else "Release checks failed. Resolve failures before release tagging."
        )
    )
    return {
        "contract": "release-check-command/v1",
        "command": " ".join(command),
        "script_exists": script_exists,
        "release_ready": release_ready,
        "executed": executed,
        "status": status,
        "reason": reason,
        "exit_code": exit_code,
        "stdout": stdout,
        "stderr": stderr,
        "ready_for_tagging": ready_for_tagging,
        "next_action": next_action,
    }


def default_release_check_runner(
    command: tuple[str, ...],
    workspace_root: Path,
) -> tuple[int, str, str]:
    try:
        completed = subprocess.run(
            command,
            cwd=workspace_root,
            capture_output=True,
            text=True,
            check=False,
        )
        return completed.returncode, completed.stdout, completed.stderr
    except OSError as exc:
        return 127, "", str(exc)
