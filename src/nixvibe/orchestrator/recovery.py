"""Apply-time recovery playbook contract helpers."""

from __future__ import annotations

from .types import Mode

VALIDATION_COMMANDS = ("nix flake check", "nix fmt")


def build_recovery_playbook(
    *,
    escalation: dict[str, object],
    mode: Mode,
    next_action: str,
    ledger_summary: dict[str, object],
) -> dict[str, object]:
    tier = str(escalation.get("tier") or "none")
    reason = str(escalation.get("reason") or "no_escalation")

    if reason == "pre_write_validation_failed":
        return _summary(
            required=True,
            stage="validation-pre-write",
            severity="high",
            strategy="fix-before-apply",
            reversible=True,
            suggested_mode="propose",
            actions=(
                "Inspect failing `nix flake check` output and fix reported issues.",
                "Run `nix fmt` to normalize formatting before retrying apply.",
                "Re-run orchestration in propose mode to confirm clean validation baseline.",
            ),
            validation_commands=VALIDATION_COMMANDS,
            checkpoint_required=False,
            next_step="Resolve validation failures, then retry apply with explicit opt-in.",
            source_tier=tier,
            source_reason=reason,
        )

    if reason == "post_write_validation_failed":
        return _summary(
            required=True,
            stage="validation-post-write",
            severity="critical",
            strategy="stabilize-after-write",
            reversible=True,
            suggested_mode="propose",
            actions=(
                "Review post-write validation output and isolate failing files.",
                "Adjust generated changes until `nix flake check` and `nix fmt` both pass.",
                "Checkpoint the recovered state in git before the next apply attempt.",
            ),
            validation_commands=VALIDATION_COMMANDS,
            checkpoint_required=True,
            next_step="Stabilize current writes and checkpoint a passing state.",
            source_tier=tier,
            source_reason=reason,
        )

    if reason == "critical_conflict_forced_propose":
        return _summary(
            required=True,
            stage="conflict-critical",
            severity="critical",
            strategy="resolve-critical-contradiction",
            reversible=True,
            suggested_mode="propose",
            actions=(
                "Review contradictory critical findings and pick one coherent direction.",
                "Remove unresolved contradiction keys before requesting apply.",
                "Run one propose cycle to verify conflict resolution before apply.",
            ),
            validation_commands=(),
            checkpoint_required=False,
            next_step="Resolve critical contradictions before requesting apply again.",
            source_tier=tier,
            source_reason=reason,
        )

    if reason == "high_risk_mutation_guardrail":
        return _summary(
            required=True,
            stage="guardrail-high-risk",
            severity="high",
            strategy="reduce-risk-before-apply",
            reversible=True,
            suggested_mode="propose",
            actions=(
                "Review irreversible recommendations and convert to reversible steps when possible.",
                "Address critical risks or add explicit mitigations before apply.",
                "Re-run orchestration in propose mode and validate lower-risk output.",
            ),
            validation_commands=VALIDATION_COMMANDS,
            checkpoint_required=False,
            next_step="Reduce mutation risk and confirm reversible plan before apply.",
            source_tier=tier,
            source_reason=reason,
        )

    if reason == "apply_dirty_workspace":
        return _summary(
            required=False,
            stage="advisory-checkpoint",
            severity="low",
            strategy="checkpoint-intentional-changes",
            reversible=True,
            suggested_mode=mode.value,
            actions=(
                "Review staged/unstaged changes and confirm they match intended apply output.",
                "Checkpoint intentional changes in git before further mutations.",
            ),
            validation_commands=(),
            checkpoint_required=bool(ledger_summary.get("dirty")),
            next_step=next_action,
            source_tier=tier,
            source_reason=reason,
        )

    return _summary(
        required=False,
        stage="none",
        severity="none",
        strategy="none",
        reversible=True,
        suggested_mode=mode.value,
        actions=(),
        validation_commands=(),
        checkpoint_required=False,
        next_step=next_action,
        source_tier=tier,
        source_reason=reason,
    )


def _summary(
    *,
    required: bool,
    stage: str,
    severity: str,
    strategy: str,
    reversible: bool,
    suggested_mode: str,
    actions: tuple[str, ...],
    validation_commands: tuple[str, ...],
    checkpoint_required: bool,
    next_step: str,
    source_tier: str,
    source_reason: str,
) -> dict[str, object]:
    return {
        "required": required,
        "stage": stage,
        "severity": severity,
        "strategy": strategy,
        "reversible": reversible,
        "suggested_mode": suggested_mode,
        "actions": actions,
        "action_count": len(actions),
        "validation_commands": validation_commands,
        "checkpoint_required": checkpoint_required,
        "next_step": next_step,
        "source_tier": source_tier,
        "source_reason": source_reason,
    }
