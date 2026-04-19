"""Write-mode resolver with confirm-first safety behavior."""

from __future__ import annotations

from .types import Mode, ModeDecision, Route


def resolve_mode(
    route: Route,
    requested_mode: Mode | str | None,
    *,
    explicit_apply_opt_in: bool,
) -> ModeDecision:
    mode = _normalize_mode(requested_mode)

    if mode is None:
        if route is Route.AUDIT:
            return ModeDecision(
                mode=Mode.PROPOSE,
                reason="Audit route defaults to propose mode.",
                write_allowed=False,
                requires_confirmation=True,
            )
        return ModeDecision(
            mode=Mode.PROPOSE,
            reason="Init route defaults to propose mode to avoid surprise writes.",
            write_allowed=False,
            requires_confirmation=True,
        )

    if mode is Mode.APPLY and not explicit_apply_opt_in:
        fallback = Mode.PROPOSE
        return ModeDecision(
            mode=fallback,
            reason="Apply requested without explicit opt-in; downgraded to propose.",
            write_allowed=False,
            requires_confirmation=True,
        )

    if mode is Mode.APPLY:
        return ModeDecision(
            mode=Mode.APPLY,
            reason="Explicit apply opt-in received; writes are allowed.",
            write_allowed=True,
            requires_confirmation=False,
        )

    if mode is Mode.PROPOSE:
        return ModeDecision(
            mode=Mode.PROPOSE,
            reason="Propose mode keeps writes gated behind explicit confirmation.",
            write_allowed=False,
            requires_confirmation=True,
        )

    return ModeDecision(
        mode=Mode.ADVICE,
        reason="Advice mode returns guidance only and performs no writes.",
        write_allowed=False,
        requires_confirmation=False,
    )


def _normalize_mode(mode: Mode | str | None) -> Mode | None:
    if mode is None:
        return None
    if isinstance(mode, Mode):
        return mode

    normalized = str(mode).strip().lower()
    for candidate in Mode:
        if candidate.value == normalized:
            return candidate

    valid = ", ".join(m.value for m in Mode)
    raise ValueError(f"Unsupported mode: {mode!r}. Valid modes: {valid}")

