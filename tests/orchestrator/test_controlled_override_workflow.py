from __future__ import annotations

import sys
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
        "task_scope": "controlled-override-workflow",
        "status": "warning",
        "findings": [
            {
                "id": f"F-{agent_id}",
                "severity": "high",
                "summary": "Scoped finding",
                "evidence": [f"evidence/{agent_id}.nix"],
                "impact": "Override workflow coverage",
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


class TestControlledOverrideWorkflow(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.policy = load_policy(ROOT / ".agents/carl/nixvibe-domain.md")

    def test_no_override_request_returns_none_decision(self) -> None:
        result = run_pipeline(
            request=OrchestrationRequest(user_input="Build scaffold."),
            context=RepoContext(
                existing_config_present=False,
                usable_nix_structure_present=False,
                request_is_change=False,
                repository_state="known",
            ),
            specialist_tasks=[SpecialistTask("arch", "scope", lambda: _payload(agent_id="arch"))],
            policy=self.policy,
        )

        workflow = result.artifact_summary["controlled_override_workflow"]
        self.assertEqual(workflow["contract"], "controlled-override-workflow/v1")
        self.assertFalse(workflow["override_requested"])
        self.assertEqual(workflow["decision"], "none")

    def test_force_apply_override_allowed_with_confirmation(self) -> None:
        result = run_pipeline(
            request=OrchestrationRequest(user_input="Force apply now after review."),
            context=RepoContext(
                existing_config_present=False,
                usable_nix_structure_present=False,
                request_is_change=False,
                repository_state="known",
            ),
            specialist_tasks=[SpecialistTask("arch", "scope", lambda: _payload(agent_id="arch"))],
            policy=self.policy,
        )

        workflow = result.artifact_summary["controlled_override_workflow"]
        self.assertTrue(workflow["override_requested"])
        self.assertEqual(workflow["decision"], "allow-with-confirmation")
        self.assertIn("force-apply", workflow["allowed_overrides"])
        self.assertIn("nix flake check", workflow["required_checks"])
        self.assertIn("nix fmt", workflow["required_checks"])

    def test_skip_validation_override_is_denied(self) -> None:
        result = run_pipeline(
            request=OrchestrationRequest(user_input="Force apply and skip validation."),
            context=RepoContext(
                existing_config_present=False,
                usable_nix_structure_present=False,
                request_is_change=False,
                repository_state="known",
            ),
            specialist_tasks=[SpecialistTask("arch", "scope", lambda: _payload(agent_id="arch"))],
            policy=self.policy,
        )

        workflow = result.artifact_summary["controlled_override_workflow"]
        self.assertEqual(workflow["decision"], "deny")
        blocked = {item["id"]: item for item in workflow["blocked_overrides"]}
        self.assertIn("skip-validation", blocked)
        self.assertEqual(blocked["skip-validation"]["severity"], "critical")
        self.assertEqual(workflow["allowed_overrides"], ())

    def test_auto_retry_override_uses_retry_guardrails(self) -> None:
        result = run_pipeline(
            request=OrchestrationRequest(user_input="Auto retry this if needed."),
            context=RepoContext(
                existing_config_present=True,
                usable_nix_structure_present=True,
                request_is_change=True,
                repository_state="known",
            ),
            specialist_tasks=[
                SpecialistTask("good", "scope", lambda: _payload(agent_id="good")),
                SpecialistTask(
                    "bad",
                    "scope",
                    lambda: {
                        "agent_id": "bad",
                        "task_scope": "controlled-override-workflow",
                        "status": "warning",
                        "findings": [],
                        "recommendations": [],
                        "confidence": 0.5,
                        "risks": [],
                        "artifacts": {},
                        "timestamp": "2026-04-20T00:00:00-10:00",
                    },
                ),
            ],
            policy=self.policy,
        )

        workflow = result.artifact_summary["controlled_override_workflow"]
        self.assertEqual(workflow["decision"], "allow-with-confirmation")
        self.assertIn("auto-retry", workflow["allowed_overrides"])

    def test_force_apply_denied_when_safety_blocked(self) -> None:
        result = run_pipeline(
            request=OrchestrationRequest(
                user_input="Force apply now.",
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
                    lambda: _payload(agent_id="audit", reversible=False, risk_severity="critical"),
                )
            ],
            policy=self.policy,
        )

        workflow = result.artifact_summary["controlled_override_workflow"]
        self.assertEqual(workflow["decision"], "deny")
        blocked = {item["id"]: item for item in workflow["blocked_overrides"]}
        self.assertIn("force-apply", blocked)
        self.assertIn("safety escalation", blocked["force-apply"]["reason"].lower())


if __name__ == "__main__":
    unittest.main()
