"""Retry/backoff guardrail contract helpers."""

from __future__ import annotations


def build_retry_backoff_guardrails(
    *,
    run_failure_classification: dict[str, object],
    resume_checkpoint: dict[str, object],
    selected_mode: str,
) -> dict[str, object]:
    classification = str(run_failure_classification.get("classification") or "none")
    severity = str(run_failure_classification.get("severity") or "none")
    resume_required = bool(resume_checkpoint.get("resume_required", False))
    resume_stage = str(resume_checkpoint.get("resume_stage") or "none")
    can_auto_resume = bool(resume_checkpoint.get("can_auto_resume", False))
    requires_human_confirmation = bool(
        resume_checkpoint.get("requires_human_confirmation", False)
    )
    release_ready = bool(resume_checkpoint.get("release_ready", False))
    recommended_mode = _mode(
        resume_checkpoint.get("recommended_mode")
        or run_failure_classification.get("recommended_mode")
        or selected_mode
    )

    policy = _retry_policy(
        classification=classification,
        resume_required=resume_required,
        resume_stage=resume_stage,
        can_auto_resume=can_auto_resume,
        requires_human_confirmation=requires_human_confirmation,
        recommended_mode=recommended_mode,
    )
    stop_conditions = _stop_conditions(
        automatic_retry_allowed=policy["automatic_retry_allowed"],
        resume_stage=resume_stage,
        requires_human_confirmation=requires_human_confirmation,
    )
    max_attempts = int(policy["max_attempts"])
    backoff_seconds = tuple(policy["backoff_seconds"])

    next_retry_action = (
        "No retry needed for this run."
        if not policy["manual_retry_recommended"] and not policy["automatic_retry_allowed"]
        else (
            f"Auto-retry up to {max_attempts} time(s) in `{policy['retry_mode']}` mode with bounded backoff."
            if policy["automatic_retry_allowed"]
            else "Retry requires manual remediation before next run."
        )
    )

    return {
        "contract": "retry-backoff-guardrails/v1",
        "classification": classification,
        "severity": severity,
        "resume_required": resume_required,
        "resume_stage": resume_stage,
        "release_ready": release_ready,
        "retry_mode": policy["retry_mode"],
        "automatic_retry_allowed": policy["automatic_retry_allowed"],
        "manual_retry_recommended": policy["manual_retry_recommended"],
        "bounded_retry": policy["automatic_retry_allowed"] and max_attempts > 0,
        "max_attempts": max_attempts,
        "backoff_strategy": _backoff_strategy(backoff_seconds),
        "backoff_seconds": backoff_seconds,
        "stop_conditions": stop_conditions,
        "reason": policy["reason"],
        "next_retry_action": next_retry_action,
    }


def _retry_policy(
    *,
    classification: str,
    resume_required: bool,
    resume_stage: str,
    can_auto_resume: bool,
    requires_human_confirmation: bool,
    recommended_mode: str,
) -> dict[str, object]:
    if not resume_required or classification == "none":
        return {
            "retry_mode": "none",
            "automatic_retry_allowed": False,
            "manual_retry_recommended": False,
            "max_attempts": 0,
            "backoff_seconds": (),
            "reason": "no_retry_required",
        }

    if requires_human_confirmation:
        return {
            "retry_mode": "propose",
            "automatic_retry_allowed": False,
            "manual_retry_recommended": True,
            "max_attempts": 0,
            "backoff_seconds": (),
            "reason": "human_confirmation_required",
        }

    if classification == "blocked":
        return {
            "retry_mode": "propose",
            "automatic_retry_allowed": False,
            "manual_retry_recommended": True,
            "max_attempts": 0,
            "backoff_seconds": (),
            "reason": "blocked_requires_manual_remediation",
        }

    if classification == "failed" and resume_stage == "specialist-runtime":
        return {
            "retry_mode": "propose",
            "automatic_retry_allowed": True,
            "manual_retry_recommended": True,
            "max_attempts": 2,
            "backoff_seconds": (5, 15),
            "reason": "specialist_runtime_retry_window",
        }

    if classification == "degraded" and can_auto_resume:
        return {
            "retry_mode": recommended_mode,
            "automatic_retry_allowed": True,
            "manual_retry_recommended": True,
            "max_attempts": 1,
            "backoff_seconds": (5,),
            "reason": "degraded_auto_resume_window",
        }

    return {
        "retry_mode": "propose",
        "automatic_retry_allowed": False,
        "manual_retry_recommended": True,
        "max_attempts": 0,
        "backoff_seconds": (),
        "reason": "manual_remediation_required",
    }


def _stop_conditions(
    *,
    automatic_retry_allowed: bool,
    resume_stage: str,
    requires_human_confirmation: bool,
) -> tuple[str, ...]:
    if not automatic_retry_allowed:
        return ()

    stops: list[str] = ["classification-escalates", "max-attempts-reached"]
    if resume_stage == "specialist-runtime":
        stops.append("specialist-runtime-persists")
    else:
        stops.append("new-blockers-detected")
    if requires_human_confirmation:
        stops.append("human-confirmation-required")
    return tuple(stops)


def _backoff_strategy(backoff_seconds: tuple[int, ...]) -> str:
    if not backoff_seconds:
        return "none"
    if len(backoff_seconds) == 1:
        return "fixed"
    return "exponential"


def _mode(value: object) -> str:
    normalized = str(value or "").strip().lower()
    if normalized in {"apply", "propose", "advice"}:
        return normalized
    return "propose"
