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
