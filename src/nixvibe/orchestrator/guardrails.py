"""High-risk mutation guardrail contract helpers."""

from __future__ import annotations

from .types import Mode, SpecialistPayload


def evaluate_high_risk_mutation_guardrails(
    *,
    requested_mode: Mode | str | None,
    selected_mode: Mode,
    payloads: tuple[SpecialistPayload, ...],
) -> dict[str, object]:
    irreversible_recommendation_detected = any(
        not recommendation.reversible
        for payload in payloads
        for recommendation in payload.recommendations
    )
    critical_risk_detected = any(
        str(risk.severity).strip().lower() == "critical"
        for payload in payloads
        for risk in payload.risks
    )

    triggers: list[str] = []
    if irreversible_recommendation_detected:
        triggers.append("irreversible_recommendation")
    if critical_risk_detected:
        triggers.append("critical_risk")

    apply_requested = _requested_apply(requested_mode)
    high_risk_detected = bool(triggers)
    apply_blocked = apply_requested and selected_mode is Mode.APPLY and high_risk_detected

    return {
        "high_risk_detected": high_risk_detected,
        "apply_requested": apply_requested,
        "apply_blocked": apply_blocked,
        "trigger_count": len(triggers),
        "triggers": tuple(triggers),
        "recommended_mode": Mode.PROPOSE.value if apply_blocked else selected_mode.value,
        "message": _message(
            high_risk_detected=high_risk_detected,
            apply_blocked=apply_blocked,
        ),
    }


def _requested_apply(requested_mode: Mode | str | None) -> bool:
    if requested_mode is None:
        return False
    if isinstance(requested_mode, Mode):
        return requested_mode is Mode.APPLY
    return str(requested_mode).strip().lower() == Mode.APPLY.value


def _message(*, high_risk_detected: bool, apply_blocked: bool) -> str:
    if apply_blocked:
        return "Apply blocked by high-risk mutation guardrail; review reversible path first."
    if high_risk_detected:
        return "High-risk mutation signals detected; apply remains blocked unless explicitly safe."
    return "No high-risk mutation guardrails triggered."
