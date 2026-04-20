"""Resume-safe checkpoint contract helpers."""

from __future__ import annotations

import hashlib


def build_resume_checkpoint(
    *,
    run_manifest: dict[str, object],
    run_failure_classification: dict[str, object],
    release_readiness: dict[str, object],
) -> dict[str, object]:
    modes = _mapping(run_manifest.get("modes"))
    selected_mode = str(modes.get("selected") or "none")

    classification = str(run_failure_classification.get("classification") or "none")
    severity = str(run_failure_classification.get("severity") or "none")
    signals = tuple(str(signal) for signal in run_failure_classification.get("signals", ()))
    recommended_mode = str(run_failure_classification.get("recommended_mode") or selected_mode or "none")
    requires_human_confirmation = bool(
        run_failure_classification.get("requires_human_confirmation", False)
    )
    release_ready = bool(release_readiness.get("ready", False))
    failed_release_gates = _failed_gate_ids(release_readiness.get("failed_gate_ids"))

    resume_required = classification in ("blocked", "failed", "degraded") or _has_resume_relevant_release_failure(
        selected_mode=selected_mode,
        failed_gate_ids=failed_release_gates,
    )
    resume_stage = _resume_stage(classification=classification, signals=signals)

    blockers = tuple(str(signal) for signal in signals if signal.startswith(("validation-", "escalation:")))
    required_actions = _required_actions(
        resume_stage=resume_stage,
        classification=classification,
    )
    if resume_required and not required_actions:
        required_actions = ("Review failed release gates before resuming.",)
    can_auto_resume = (
        resume_required
        and classification == "degraded"
        and not requires_human_confirmation
        and resume_stage in ("specialist-payload", "advisory-review")
    )
    checkpoint_id = _checkpoint_id(
        route=str(run_manifest.get("route") or ""),
        selected_mode=selected_mode,
        classification=classification,
        resume_stage=resume_stage,
        signal_count=len(signals),
    )

    next_safe_action = (
        "No resume needed; continue normal workflow."
        if not resume_required
        else (
            "Auto-resume is safe for this checkpoint; retry once with bounded guardrails."
            if can_auto_resume
            else "Resume requires explicit review before continuing."
        )
    )

    return {
        "contract": "resume-checkpoint/v1",
        "checkpoint_id": checkpoint_id,
        "resume_required": resume_required,
        "resume_stage": resume_stage,
        "classification": classification,
        "severity": severity,
        "recommended_mode": recommended_mode,
        "requires_human_confirmation": requires_human_confirmation,
        "can_auto_resume": can_auto_resume,
        "release_ready": release_ready,
        "blockers": blockers,
        "required_actions": required_actions,
        "action_count": len(required_actions),
        "next_safe_action": next_safe_action,
    }


def _resume_stage(*, classification: str, signals: tuple[str, ...]) -> str:
    if classification == "none":
        return "none"
    if any(signal == "validation-pre-write" for signal in signals):
        return "validation-pre-write"
    if any(signal == "validation-post-write" for signal in signals):
        return "validation-post-write"
    if any(signal == "specialist-error" for signal in signals):
        return "specialist-runtime"
    if any(signal == "specialist-invalid" for signal in signals):
        return "specialist-payload"
    if any(signal.startswith("escalation:") for signal in signals):
        return "safety-escalation"
    return "advisory-review"


def _required_actions(*, resume_stage: str, classification: str) -> tuple[str, ...]:
    if resume_stage == "validation-pre-write":
        return (
            "Fix pre-write validation issues and re-run checks.",
            "Resume from propose mode after validation passes.",
        )
    if resume_stage == "validation-post-write":
        return (
            "Review post-write validation failures and remediate written artifacts.",
            "Checkpoint a passing state before next apply attempt.",
        )
    if resume_stage == "specialist-runtime":
        return (
            "Review specialist runner errors and stabilize runtime dependencies.",
            "Retry orchestration with bounded retry policy.",
        )
    if resume_stage == "specialist-payload":
        return (
            "Correct invalid specialist payloads and rerun schema checks.",
            "Resume pipeline after payload integrity is restored.",
        )
    if resume_stage == "safety-escalation":
        return (
            "Resolve safety escalation blockers before resuming apply.",
            "Resume in propose mode and confirm blockers are cleared.",
        )
    if classification == "degraded":
        return ("Review degraded signals and confirm safe continuation.",)
    return ()


def _checkpoint_id(
    *,
    route: str,
    selected_mode: str,
    classification: str,
    resume_stage: str,
    signal_count: int,
) -> str:
    basis = f"{route}|{selected_mode}|{classification}|{resume_stage}|{signal_count}"
    digest = hashlib.sha256(basis.encode("utf-8")).hexdigest()[:12]
    return f"rc-{digest}"


def _mapping(value: object) -> dict[str, object]:
    if isinstance(value, dict):
        return value
    return {}


def _failed_gate_ids(value: object) -> tuple[str, ...]:
    if isinstance(value, (list, tuple)):
        return tuple(str(item) for item in value if str(item).strip())
    return ()


def _has_resume_relevant_release_failure(
    *,
    selected_mode: str,
    failed_gate_ids: tuple[str, ...],
) -> bool:
    if not failed_gate_ids:
        return False
    if selected_mode != "apply":
        return any(gate_id != "mode-apply" for gate_id in failed_gate_ids)
    return True
