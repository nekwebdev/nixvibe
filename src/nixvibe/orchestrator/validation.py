"""Validation gate execution for flake-first workflows."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Callable

from .types import ValidationCommandResult, ValidationReport

CommandRunner = Callable[[tuple[str, ...], Path], tuple[int, str, str] | ValidationCommandResult]


def run_validation(
    *,
    workspace_root: str | Path,
    command_runner: CommandRunner | None = None,
) -> ValidationReport:
    root = Path(workspace_root)
    flake_present = (root / "flake.nix").exists()
    if not flake_present:
        return ValidationReport(
            required=True,
            executed=False,
            success=False,
            flake_present=False,
            results=(),
            reason="flake.nix not found; validation requires a flake-first workspace.",
        )

    runner = command_runner or _default_command_runner
    commands = (
        ("nix", "flake", "check"),
        ("nix", "fmt"),
    )

    results: list[ValidationCommandResult] = []
    for command in commands:
        results.append(_run_one(command, root, runner))

    success = all(result.success for result in results)
    return ValidationReport(
        required=True,
        executed=True,
        success=success,
        flake_present=True,
        results=tuple(results),
        reason="validation passed" if success else "validation failed",
    )


def _run_one(
    command: tuple[str, ...],
    workspace_root: Path,
    runner: CommandRunner,
) -> ValidationCommandResult:
    executed = runner(command, workspace_root)
    if isinstance(executed, ValidationCommandResult):
        return executed

    exit_code, stdout, stderr = executed
    return ValidationCommandResult(
        command=" ".join(command),
        exit_code=int(exit_code),
        success=int(exit_code) == 0,
        stdout=str(stdout),
        stderr=str(stderr),
    )


def _default_command_runner(command: tuple[str, ...], workspace_root: Path) -> tuple[int, str, str]:
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

