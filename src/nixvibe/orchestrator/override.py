"""Controlled override workflow contract helpers."""

from __future__ import annotations

from .types import Mode


def build_controlled_override_workflow(
    *,
    user_input: str,
    selected_mode: Mode,
    run_failure_classification: dict[str, object],
    apply_safety_escalation: dict[str, object],
    release_readiness: dict[str, object],
    retry_backoff_guardrails: dict[str, object],
) -> dict[str, object]:
    requested_overrides = _requested_overrides(user_input)
    classification = str(run_failure_classification.get("classification") or "none")
    escalation_tier = str(apply_safety_escalation.get("tier") or "none")
    failed_gate_ids = tuple(str(gate) for gate in release_readiness.get("failed_gate_ids", ()))

    allowed_overrides: list[str] = []
    blocked_overrides: list[dict[str, str]] = []
    required_checks: list[str] = []

    if "skip-validation" in requested_overrides:
        blocked_overrides.append(
            {
                "id": "skip-validation",
                "severity": "critical",
                "reason": "Validation gates cannot be bypassed.",
            }
        )

    if "force-apply" in requested_overrides:
        non_mode_release_failures = tuple(gate for gate in failed_gate_ids if gate != "mode-apply")
        if escalation_tier in {"blocked", "guarded"}:
            blocked_overrides.append(
                {
                    "id": "force-apply",
                    "severity": "critical",
                    "reason": "Apply safety escalation blocks override.",
                }
            )
        elif classification in {"blocked", "failed"}:
            blocked_overrides.append(
                {
                    "id": "force-apply",
                    "severity": "high",
                    "reason": "Failure classification requires remediation before apply override.",
                }
            )
        elif non_mode_release_failures:
            blocked_overrides.append(
                {
                    "id": "force-apply",
                    "severity": "high",
                    "reason": "Release blockers beyond mode gate must be resolved first.",
                }
            )
        elif selected_mode is not Mode.PROPOSE:
            blocked_overrides.append(
                {
                    "id": "force-apply",
                    "severity": "medium",
                    "reason": "Force-apply override only applies from propose mode.",
                }
            )
        else:
            allowed_overrides.append("force-apply")
            required_checks.extend(("nix flake check", "nix fmt"))

    if "auto-retry" in requested_overrides:
        if bool(retry_backoff_guardrails.get("automatic_retry_allowed", False)):
            allowed_overrides.append("auto-retry")
            required_checks.append("bounded retry window")
        elif bool(retry_backoff_guardrails.get("manual_retry_recommended", False)):
            blocked_overrides.append(
                {
                    "id": "auto-retry",
                    "severity": "high",
                    "reason": "Current guardrails require manual remediation before retry.",
                }
            )
        else:
            blocked_overrides.append(
                {
                    "id": "auto-retry",
                    "severity": "low",
                    "reason": "No retry override needed for current run state.",
                }
            )

    override_requested = len(requested_overrides) > 0
    critical_blocked = any(item.get("severity") == "critical" for item in blocked_overrides)
    if critical_blocked:
        allowed_overrides = []
        required_checks = []
    override_eligible = len(allowed_overrides) > 0 and not critical_blocked
    decision = (
        "none"
        if not override_requested
        else ("allow-with-confirmation" if override_eligible else "deny")
    )
    requires_human_confirmation = override_eligible
    deduped_checks = tuple(dict.fromkeys(required_checks))

    next_override_action = (
        "No override requested."
        if decision == "none"
        else (
            "Override allowed with explicit confirmation after required checks."
            if decision == "allow-with-confirmation"
            else "Override denied; resolve blockers before requesting override again."
        )
    )

    return {
        "contract": "controlled-override-workflow/v1",
        "override_requested": override_requested,
        "override_eligible": override_eligible,
        "decision": decision,
        "requested_overrides": requested_overrides,
        "allowed_overrides": tuple(allowed_overrides),
        "blocked_overrides": tuple(blocked_overrides),
        "requires_human_confirmation": requires_human_confirmation,
        "required_checks": deduped_checks,
        "next_override_action": next_override_action,
        "summary": _summary(decision=decision, allowed_count=len(allowed_overrides)),
    }


def _requested_overrides(user_input: str) -> tuple[str, ...]:
    text = user_input.strip().lower()
    requested: list[str] = []

    if any(term in text for term in ("force apply", "override apply", "bypass propose")):
        requested.append("force-apply")
    if any(term in text for term in ("skip validation", "ignore flake check", "ignore fmt")):
        requested.append("skip-validation")
    if any(term in text for term in ("auto retry", "retry automatically", "force retry")):
        requested.append("auto-retry")

    return tuple(dict.fromkeys(requested))


def _summary(*, decision: str, allowed_count: int) -> str:
    if decision == "none":
        return "No override workflow activated."
    if decision == "allow-with-confirmation":
        return f"{allowed_count} override path(s) allowed with confirmation."
    return "Override request denied by policy guardrails."
