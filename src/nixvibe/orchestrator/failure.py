"""Run failure classification contract helpers."""

from __future__ import annotations


def build_run_failure_classification(
    *,
    run_manifest: dict[str, object],
    apply_safety_escalation: dict[str, object],
    validation_failure_stage: str,
) -> dict[str, object]:
    specialists = _mapping(run_manifest.get("specialists"))
    outcomes = _mapping(specialists.get("outcomes"))

    invalid_count = int(outcomes.get("invalid") or 0)
    error_count = int(outcomes.get("error") or 0)

    escalation_tier = str(apply_safety_escalation.get("tier") or "none")
    escalation_reason = str(apply_safety_escalation.get("reason") or "no_escalation")

    classification, severity = _classify(
        escalation_tier=escalation_tier,
        invalid_count=invalid_count,
        error_count=error_count,
    )
    signals = _signals(
        escalation_tier=escalation_tier,
        escalation_reason=escalation_reason,
        validation_failure_stage=validation_failure_stage,
        invalid_count=invalid_count,
        error_count=error_count,
    )
    recommended_mode = str(apply_safety_escalation.get("recommended_mode") or "none")
    if recommended_mode == "none":
        modes = _mapping(run_manifest.get("modes"))
        recommended_mode = str(modes.get("selected") or "none")

    return {
        "contract": "run-failure-classification/v1",
        "classification": classification,
        "severity": severity,
        "recoverable": classification != "none",
        "requires_human_confirmation": bool(
            apply_safety_escalation.get("human_confirmation_required", False)
        ),
        "recommended_mode": recommended_mode,
        "signals": signals,
        "signal_count": len(signals),
        "specialist_invalid_count": invalid_count,
        "specialist_error_count": error_count,
        "validation_failure_stage": validation_failure_stage,
        "escalation_tier": escalation_tier,
        "escalation_reason": escalation_reason,
        "summary": _summary(classification=classification),
    }


def _classify(
    *,
    escalation_tier: str,
    invalid_count: int,
    error_count: int,
) -> tuple[str, str]:
    if escalation_tier == "blocked":
        return "blocked", "critical"
    if escalation_tier == "guarded":
        return "failed", "high"
    if error_count > 0:
        return "failed", "high"
    if invalid_count > 0:
        return "degraded", "medium"
    if escalation_tier == "advisory":
        return "degraded", "low"
    return "none", "none"


def _signals(
    *,
    escalation_tier: str,
    escalation_reason: str,
    validation_failure_stage: str,
    invalid_count: int,
    error_count: int,
) -> tuple[str, ...]:
    signals: list[str] = []
    if escalation_tier != "none":
        signals.append(f"escalation:{escalation_reason}")
    if validation_failure_stage == "pre_write":
        signals.append("validation-pre-write")
    elif validation_failure_stage == "post_write":
        signals.append("validation-post-write")
    if invalid_count > 0:
        signals.append("specialist-invalid")
    if error_count > 0:
        signals.append("specialist-error")
    return tuple(signals)


def _summary(*, classification: str) -> str:
    if classification == "blocked":
        return "Run was safety-blocked and requires recovery before apply."
    if classification == "failed":
        return "Run completed with failure conditions requiring remediation."
    if classification == "degraded":
        return "Run completed with degradations that should be reviewed."
    return "Run completed without classified failures."


def _mapping(value: object) -> dict[str, object]:
    if isinstance(value, dict):
        return value
    return {}
