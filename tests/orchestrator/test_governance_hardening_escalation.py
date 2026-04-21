from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from nixvibe.orchestrator.governance_hardening_escalation import build_governance_hardening_escalation
from nixvibe.orchestrator.pipeline import run_pipeline
from nixvibe.orchestrator.policy_loader import load_policy
from nixvibe.orchestrator.types import Mode, OrchestrationRequest, RepoContext, SpecialistTask


class _StepClock:
    def __init__(self, *, step_seconds: float) -> None:
        self._current = 0.0
        self._step = step_seconds

    def __call__(self) -> float:
        value = self._current
        self._current += self._step
        return value


def _payload(*, agent_id: str) -> dict[str, object]:
    return {
        "agent_id": agent_id,
        "task_scope": "governance-hardening-escalation",
        "status": "warning",
        "findings": [
            {
                "id": f"F-{agent_id}",
                "severity": "high",
                "summary": "Scoped finding",
                "evidence": [f"evidence/{agent_id}.nix"],
                "impact": "Governance hardening escalation coverage",
            }
        ],
        "recommendations": [
            {
                "id": f"R-{agent_id}",
                "action": "Apply structured change",
                "priority": "now",
                "maps_to_findings": [f"F-{agent_id}"],
                "reversible": True,
            }
        ],
        "confidence": 0.9,
        "risks": [
            {
                "id": f"K-{agent_id}",
                "category": "regression",
                "severity": "medium",
                "mitigation": "review changes",
            }
        ],
        "artifacts": {"notes": [f"note-{agent_id}"], "next_actions": [f"review-{agent_id}"]},
        "checks": {"schema_checked": True},
        "timestamp": "2026-04-21T00:00:00-10:00",
    }


class TestGovernanceHardeningEscalation(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.policy = load_policy(ROOT / ".agents/carl/nixvibe-domain.md")

    def test_helper_reports_none_for_stable_governance_signals(self) -> None:
        escalation = build_governance_hardening_escalation(
            operator_observability_digest={
                "contract": "operator-observability-digest/v1",
                "observability_band": "healthy",
                "focus_items": ("No immediate operator action required.",),
            },
            release_policy_execution={"contract": "release-policy-execution/v1", "decision": "automated"},
            controlled_override_workflow={
                "contract": "controlled-override-workflow/v1",
                "override_requested": False,
                "decision": "none",
                "blocked_overrides": (),
            },
            apply_safety_escalation={"contract": "apply-safety-escalation/v1", "tier": "none"},
        )

        self.assertEqual(escalation["escalation_level"], "none")
        self.assertEqual(escalation["governance_posture"], "stable")
        self.assertFalse(escalation["escalation_required"])

    def test_helper_reports_review_for_advisory_or_confirmation_signals(self) -> None:
        escalation = build_governance_hardening_escalation(
            operator_observability_digest={
                "contract": "operator-observability-digest/v1",
                "observability_band": "healthy",
                "focus_items": (),
            },
            release_policy_execution={"contract": "release-policy-execution/v1", "decision": "automated"},
            controlled_override_workflow={
                "contract": "controlled-override-workflow/v1",
                "override_requested": True,
                "decision": "allow-with-confirmation",
                "blocked_overrides": (),
            },
            apply_safety_escalation={"contract": "apply-safety-escalation/v1", "tier": "advisory"},
        )

        self.assertEqual(escalation["escalation_level"], "review")
        self.assertEqual(escalation["governance_posture"], "watch")

    def test_helper_reports_escalate_for_attention_signals(self) -> None:
        escalation = build_governance_hardening_escalation(
            operator_observability_digest={
                "contract": "operator-observability-digest/v1",
                "observability_band": "attention",
                "focus_items": ("Review warning signal.",),
            },
            release_policy_execution={"contract": "release-policy-execution/v1", "decision": "manual-ack"},
            controlled_override_workflow={
                "contract": "controlled-override-workflow/v1",
                "override_requested": False,
                "decision": "none",
                "blocked_overrides": (),
            },
            apply_safety_escalation={"contract": "apply-safety-escalation/v1", "tier": "none"},
        )

        self.assertEqual(escalation["escalation_level"], "escalate")
        self.assertEqual(escalation["governance_posture"], "harden")
        self.assertTrue(escalation["escalation_required"])

    def test_helper_reports_critical_for_blocking_signals(self) -> None:
        escalation = build_governance_hardening_escalation(
            operator_observability_digest={
                "contract": "operator-observability-digest/v1",
                "observability_band": "critical",
                "focus_items": ("Resolve blocker now.",),
            },
            release_policy_execution={
                "contract": "release-policy-execution/v1",
                "decision": "blocked",
                "blockers": ("override-skip-validation",),
            },
            controlled_override_workflow={
                "contract": "controlled-override-workflow/v1",
                "override_requested": True,
                "decision": "deny",
                "blocked_overrides": ({"id": "skip-validation"},),
            },
            apply_safety_escalation={"contract": "apply-safety-escalation/v1", "tier": "blocked"},
        )

        self.assertEqual(escalation["escalation_level"], "critical")
        self.assertEqual(escalation["governance_posture"], "blocked")
        self.assertIn("override:skip-validation", escalation["blockers"])

    def test_helper_reports_critical_when_contracts_missing(self) -> None:
        escalation = build_governance_hardening_escalation(
            operator_observability_digest={"contract": "missing"},
            release_policy_execution={"contract": "missing"},
            controlled_override_workflow={"contract": "missing"},
            apply_safety_escalation={"contract": "missing"},
        )

        self.assertFalse(escalation["governance_ready"])
        self.assertEqual(escalation["escalation_level"], "critical")
        self.assertIn("operator-observability-digest-contract", escalation["failed_check_ids"])

    def test_pipeline_emits_governance_hardening_escalation_contract(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "flake.nix").write_text("{ }")
            result = run_pipeline(
                request=OrchestrationRequest(
                    user_input="Apply scaffold now.",
                    requested_mode=Mode.APPLY,
                    explicit_apply_opt_in=True,
                ),
                context=RepoContext(
                    existing_config_present=False,
                    usable_nix_structure_present=False,
                    request_is_change=False,
                    repository_state="known",
                ),
                specialist_tasks=[SpecialistTask("arch", "scope", lambda: _payload(agent_id="arch"))],
                policy=self.policy,
                workspace_root=root,
                validation_runner=lambda _command, _cwd: (0, "ok", ""),
                monotonic_clock=_StepClock(step_seconds=0.01),
            )

        escalation = result.artifact_summary["governance_hardening_escalation"]
        self.assertEqual(escalation["contract"], "governance-hardening-escalation/v1")
        self.assertEqual(escalation["escalation_level"], "escalate")
        self.assertEqual(escalation["governance_posture"], "harden")


if __name__ == "__main__":
    unittest.main()
