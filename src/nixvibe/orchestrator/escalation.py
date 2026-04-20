"""Apply-time safety escalation contract helpers."""

from __future__ import annotations

from .types import Mode


def build_apply_safety_escalation(
    *,
    requested_mode: Mode | str | None,
    selected_mode: Mode,
    validation_failure_stage: str,
    conflict_forced_propose: bool,
    high_risk_guardrail_forced_propose: bool,
    ledger_summary: dict[str, object],
) -> dict[str, object]:
    apply_requested = _requested_apply(requested_mode)

    if apply_requested and conflict_forced_propose:
        return _summary(
            tier="blocked",
            score=3,
            apply_requested=True,
            reason="critical_conflict_forced_propose",
            triggers=("critical_conflict",),
            requires_recovery=True,
            recommended_mode="propose",
            human_confirmation_required=True,
            message="Apply was blocked by critical contradictions; resolve conflicts before apply.",
        )

    if apply_requested and high_risk_guardrail_forced_propose:
        return _summary(
            tier="blocked",
            score=3,
            apply_requested=True,
            reason="high_risk_mutation_guardrail",
            triggers=("high_risk_mutation_guardrail",),
            requires_recovery=True,
            recommended_mode="propose",
            human_confirmation_required=True,
            message="Apply was blocked by high-risk mutation guardrails.",
        )

    if apply_requested and validation_failure_stage == "pre_write":
        return _summary(
            tier="blocked",
            score=3,
            apply_requested=True,
            reason="pre_write_validation_failed",
            triggers=("validation_pre_write_failed",),
            requires_recovery=True,
            recommended_mode="propose",
            human_confirmation_required=True,
            message="Apply was blocked by pre-write validation failure.",
        )

    if apply_requested and validation_failure_stage == "post_write":
        return _summary(
            tier="guarded",
            score=2,
            apply_requested=True,
            reason="post_write_validation_failed",
            triggers=("validation_post_write_failed",),
            requires_recovery=True,
            recommended_mode="propose",
            human_confirmation_required=False,
            message="Apply succeeded but post-write validation failed; recovery actions required.",
        )

    if apply_requested and selected_mode is Mode.APPLY and bool(ledger_summary.get("dirty")):
        return _summary(
            tier="advisory",
            score=1,
            apply_requested=True,
            reason="apply_dirty_workspace",
            triggers=("workspace_dirty_after_apply",),
            requires_recovery=False,
            recommended_mode="apply",
            human_confirmation_required=False,
            message="Apply completed with workspace changes; review and checkpoint intentional changes.",
        )

    return _summary(
        tier="none",
        score=0,
        apply_requested=apply_requested,
        reason="no_escalation",
        triggers=(),
        requires_recovery=False,
        recommended_mode="none",
        human_confirmation_required=False,
        message="No apply-time escalation required.",
    )


def _requested_apply(requested_mode: Mode | str | None) -> bool:
    if requested_mode is None:
        return False
    if isinstance(requested_mode, Mode):
        return requested_mode is Mode.APPLY
    normalized = str(requested_mode).strip().lower()
    return normalized == Mode.APPLY.value


def _summary(
    *,
    tier: str,
    score: int,
    apply_requested: bool,
    reason: str,
    triggers: tuple[str, ...],
    requires_recovery: bool,
    recommended_mode: str,
    human_confirmation_required: bool,
    message: str,
) -> dict[str, object]:
    return {
        "tier": tier,
        "score": score,
        "apply_requested": apply_requested,
        "escalated": tier != "none",
        "reason": reason,
        "triggers": triggers,
        "requires_recovery": requires_recovery,
        "recommended_mode": recommended_mode,
        "human_confirmation_required": human_confirmation_required,
        "message": message,
    }
