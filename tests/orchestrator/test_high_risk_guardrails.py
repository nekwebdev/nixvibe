from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from nixvibe.orchestrator.pipeline import run_pipeline
from nixvibe.orchestrator.policy_loader import load_policy
from nixvibe.orchestrator.types import Mode, OrchestrationRequest, RepoContext, SpecialistTask


def _payload(
    *,
    agent_id: str,
    reversible: bool = True,
    risk_severity: str = "medium",
) -> dict:
    return {
        "agent_id": agent_id,
        "task_scope": "high-risk-guardrail",
        "status": "warning",
        "findings": [
            {
                "id": f"F-{agent_id}",
                "severity": "high",
                "summary": "Scoped finding",
                "evidence": [f"evidence/{agent_id}.nix"],
                "impact": "Mutation risk analysis",
            }
        ],
        "recommendations": [
            {
                "id": f"R-{agent_id}",
                "action": "Apply structured change",
                "priority": "now",
                "maps_to_findings": [f"F-{agent_id}"],
                "reversible": reversible,
            }
        ],
        "confidence": 0.9,
        "risks": [
            {
                "id": f"K-{agent_id}",
                "category": "regression",
                "severity": risk_severity,
                "mitigation": "review changes",
            }
        ],
        "artifacts": {"notes": [f"note-{agent_id}"], "next_actions": [f"review-{agent_id}"]},
        "checks": {"schema_checked": True},
        "timestamp": "2026-04-20T00:00:00-10:00",
    }


class TestHighRiskGuardrails(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.policy = load_policy(ROOT / ".agents/carl/nixvibe-domain.md")

    def test_apply_mode_is_blocked_for_irreversible_recommendation(self) -> None:
        result = run_pipeline(
            request=OrchestrationRequest(
                user_input="Apply this now.",
                requested_mode=Mode.APPLY,
                explicit_apply_opt_in=True,
            ),
            context=RepoContext(
                existing_config_present=True,
                usable_nix_structure_present=True,
                request_is_change=True,
                repository_state="known",
            ),
            specialist_tasks=[
                SpecialistTask(
                    "audit",
                    "scope",
                    lambda: _payload(agent_id="audit", reversible=False, risk_severity="medium"),
                )
            ],
            policy=self.policy,
        )

        self.assertEqual(result.selected_mode, Mode.PROPOSE)
        guardrails = result.artifact_summary["mutation_guardrails"]
        self.assertTrue(guardrails["apply_blocked"])
        self.assertIn("irreversible_recommendation", guardrails["triggers"])

        escalation = result.artifact_summary["apply_safety_escalation"]
        self.assertEqual(escalation["tier"], "blocked")
        self.assertEqual(escalation["reason"], "high_risk_mutation_guardrail")

        recovery = result.artifact_summary["recovery_playbook"]
        self.assertEqual(recovery["stage"], "guardrail-high-risk")
        self.assertTrue(recovery["required"])

        guidance = result.artifact_summary["guidance"]
        self.assertEqual(guidance["remediation"]["category"], "guardrail-high-risk")
        self.assertTrue(guidance["high_risk_guardrail_forced_propose"])

    def test_apply_mode_is_blocked_for_critical_risk(self) -> None:
        result = run_pipeline(
            request=OrchestrationRequest(
                user_input="Apply this now.",
                requested_mode=Mode.APPLY,
                explicit_apply_opt_in=True,
            ),
            context=RepoContext(
                existing_config_present=True,
                usable_nix_structure_present=True,
                request_is_change=True,
                repository_state="known",
            ),
            specialist_tasks=[
                SpecialistTask(
                    "audit",
                    "scope",
                    lambda: _payload(agent_id="audit", reversible=True, risk_severity="critical"),
                )
            ],
            policy=self.policy,
        )

        guardrails = result.artifact_summary["mutation_guardrails"]
        self.assertTrue(guardrails["apply_blocked"])
        self.assertIn("critical_risk", guardrails["triggers"])
        self.assertEqual(result.selected_mode, Mode.PROPOSE)

    def test_apply_mode_proceeds_when_no_high_risk_triggers(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "flake.nix").write_text("{ }")
            result = run_pipeline(
                request=OrchestrationRequest(
                    user_input="Apply this now.",
                    requested_mode=Mode.APPLY,
                    explicit_apply_opt_in=True,
                ),
                context=RepoContext(
                    existing_config_present=True,
                    usable_nix_structure_present=True,
                    request_is_change=True,
                    repository_state="known",
                ),
                specialist_tasks=[
                    SpecialistTask(
                        "audit",
                        "scope",
                        lambda: _payload(agent_id="audit", reversible=True, risk_severity="medium"),
                    )
                ],
                policy=self.policy,
                workspace_root=tmp,
                validation_runner=lambda _command, _cwd: (0, "ok", ""),
            )

        guardrails = result.artifact_summary["mutation_guardrails"]
        self.assertFalse(guardrails["apply_blocked"])
        self.assertFalse(guardrails["high_risk_detected"])
        self.assertEqual(result.selected_mode, Mode.APPLY)


if __name__ == "__main__":
    unittest.main()
