"""Skill-adaptive guidance contract helpers."""

from __future__ import annotations

from .types import Mode, RepoContext, Route

NOVICE_KEYWORDS = (
    "new to nix",
    "beginner",
    "first time",
    "i don't know",
    "i do not know",
    "noob",
    "explain like",
    "my mom",
)

EXPERT_KEYWORDS = (
    "expert",
    "advanced",
    "already have",
    "refactor",
    "module graph",
    "flake",
    "home-manager",
    "nixosmodule",
)


def infer_skill_level(user_input: str) -> str:
    text = user_input.strip().lower()
    if not text:
        return "intermediate"

    if any(keyword in text for keyword in NOVICE_KEYWORDS):
        return "novice"
    if any(keyword in text for keyword in EXPERT_KEYWORDS):
        return "expert"
    return "intermediate"


def build_guidance_summary(
    *,
    user_input: str,
    context: RepoContext,
    route: Route,
    mode: Mode,
    next_action: str,
    validation_failed: bool,
    validation_failure_stage: str,
    conflict_forced_propose: bool,
    high_risk_guardrail_forced_propose: bool,
    merge_reason: str,
    ledger_summary: dict[str, object],
    apply_safety_escalation: dict[str, object],
    recovery_playbook: dict[str, object],
) -> dict[str, object]:
    skill_level = infer_skill_level(user_input)
    response_style, explanation_depth, explanation_sections = _guidance_profile(skill_level)

    preserve_existing_structure = bool(context.usable_nix_structure_present)
    prefer_fewer_files_initially = skill_level == "novice"
    if route is Route.AUDIT and preserve_existing_structure:
        scaffold_strategy = "preserve-and-extend"
    elif prefer_fewer_files_initially:
        scaffold_strategy = "start-small-dendritic"
    else:
        scaffold_strategy = "full-dendritic"

    remediation = _build_remediation_summary(
        validation_failed=validation_failed,
        validation_failure_stage=validation_failure_stage,
        conflict_forced_propose=conflict_forced_propose,
        high_risk_guardrail_forced_propose=high_risk_guardrail_forced_propose,
    )
    ledger_available = bool(ledger_summary.get("available"))
    ledger_change_classification = str(ledger_summary.get("change_classification") or "")
    ledger_drift_detected = bool(ledger_summary.get("drift_detected"))
    ledger_drift_severity = str(ledger_summary.get("drift_severity") or "none")
    ledger_action_hint = _ledger_action_hint(
        mode=mode,
        available=ledger_available,
        drift_detected=ledger_drift_detected,
    )

    return {
        "skill_level": skill_level,
        "response_style": response_style,
        "explanation_depth": explanation_depth,
        "explanation_sections": explanation_sections,
        "preserve_existing_structure": preserve_existing_structure,
        "prefer_fewer_files_initially": prefer_fewer_files_initially,
        "scaffold_strategy": scaffold_strategy,
        "mode": mode.value,
        "validation_failed": validation_failed,
        "validation_failure_stage": validation_failure_stage,
        "conflict_forced_propose": conflict_forced_propose,
        "high_risk_guardrail_forced_propose": high_risk_guardrail_forced_propose,
        "merge_reason": merge_reason,
        "ledger_available": ledger_available,
        "ledger_change_classification": ledger_change_classification,
        "ledger_drift_detected": ledger_drift_detected,
        "ledger_drift_severity": ledger_drift_severity,
        "ledger_action_hint": ledger_action_hint,
        "apply_safety_tier": str(apply_safety_escalation.get("tier") or "none"),
        "apply_safety_reason": str(apply_safety_escalation.get("reason") or ""),
        "recovery_required": bool(recovery_playbook.get("required")),
        "recovery_stage": str(recovery_playbook.get("stage") or "none"),
        "recovery_strategy": str(recovery_playbook.get("strategy") or "none"),
        "recovery_reversible": bool(recovery_playbook.get("reversible", True)),
        "remediation": remediation,
        "immediate_next_action": next_action,
    }


def _guidance_profile(skill_level: str) -> tuple[str, str, tuple[str, ...]]:
    if skill_level == "novice":
        return (
            "stepwise",
            "expanded",
            ("what_happened", "why_it_matters", "safe_next_step"),
        )
    if skill_level == "expert":
        return (
            "concise",
            "compact",
            ("summary", "constraints", "next_step"),
        )
    return (
        "balanced",
        "standard",
        ("summary", "rationale", "next_step"),
    )


def _build_remediation_summary(
    *,
    validation_failed: bool,
    validation_failure_stage: str,
    conflict_forced_propose: bool,
    high_risk_guardrail_forced_propose: bool,
) -> dict[str, object]:
    if validation_failed:
        if validation_failure_stage == "post_write":
            return {
                "required": True,
                "category": "validation-post-write",
                "severity": "high",
                "summary": "Validation failed after writes were applied.",
                "actions": (
                    "Review failing `nix flake check` / `nix fmt` output from post-write checkpoint.",
                    "Adjust written artifacts to satisfy validation constraints.",
                    "Re-run orchestration in propose mode to verify clean remediation before apply.",
                ),
                "retry_mode": "propose",
                "blockers": ("post_write_validation_failed",),
            }
        return {
            "required": True,
            "category": "validation-pre-write",
            "severity": "high",
            "summary": "Validation failed before write and apply was blocked.",
            "actions": (
                "Run `nix flake check` and fix reported issues.",
                "Run `nix fmt` and re-check formatting correctness.",
                "Retry orchestration with explicit apply opt-in after checks pass.",
            ),
            "retry_mode": "apply",
            "blockers": ("pre_write_validation_failed",),
        }

    if conflict_forced_propose:
        return {
            "required": True,
            "category": "conflict-critical",
            "severity": "critical",
            "summary": "Critical contradictory findings forced propose mode.",
            "actions": (
                "Review contradictory critical findings and choose the safest recommendation.",
                "Resolve conflict-group direction before enabling apply.",
                "Re-run orchestration in propose mode and confirm conflict is cleared.",
            ),
            "retry_mode": "propose",
            "blockers": ("critical_conflict_unresolved",),
        }

    if high_risk_guardrail_forced_propose:
        return {
            "required": True,
            "category": "guardrail-high-risk",
            "severity": "high",
            "summary": "High-risk mutation guardrails blocked apply mode.",
            "actions": (
                "Review irreversible recommendations and critical risks before applying changes.",
                "Refine recommendations to preserve reversibility where possible.",
                "Re-run orchestration in propose mode and confirm guardrails are cleared.",
            ),
            "retry_mode": "propose",
            "blockers": ("high_risk_mutation_guardrail",),
        }

    return {
        "required": False,
        "category": "none",
        "severity": "none",
        "summary": "No safety remediation required.",
        "actions": (),
        "retry_mode": "none",
        "blockers": (),
    }


def _ledger_action_hint(
    *,
    mode: Mode,
    available: bool,
    drift_detected: bool,
) -> str:
    if not available:
        return "ledger-unavailable"
    if mode is Mode.PROPOSE and drift_detected:
        return "reconcile-drift-before-apply"
    if mode is Mode.APPLY and drift_detected:
        return "review-and-checkpoint-post-apply"
    if mode is Mode.ADVICE and drift_detected:
        return "inspect-ledger-before-propose"
    return "none"
