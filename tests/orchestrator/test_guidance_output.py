from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from nixvibe.orchestrator.pipeline import run_pipeline
from nixvibe.orchestrator.policy_loader import load_policy
from nixvibe.orchestrator.types import OrchestrationRequest, RepoContext, SpecialistTask


def _payload(*, agent_id: str) -> dict:
    return {
        "agent_id": agent_id,
        "task_scope": "guidance-contract",
        "status": "warning",
        "findings": [
            {
                "id": f"F-{agent_id}",
                "severity": "medium",
                "summary": "Scoped finding",
                "evidence": [f"evidence/{agent_id}.nix"],
                "impact": "Test impact",
            }
        ],
        "recommendations": [
            {
                "id": f"R-{agent_id}",
                "action": "Apply structured change",
                "priority": "next",
                "maps_to_findings": [f"F-{agent_id}"],
                "reversible": True,
            }
        ],
        "confidence": 0.8,
        "risks": [
            {
                "id": f"K-{agent_id}",
                "category": "regression",
                "severity": "low",
                "mitigation": "review changes",
            }
        ],
        "artifacts": {
            "notes": [f"note-{agent_id}"],
            "next_actions": [f"review-{agent_id}"],
        },
        "checks": {"schema_checked": True},
        "timestamp": "2026-04-20T00:00:00-10:00",
    }


class TestGuidanceOutput(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.policy = load_policy(ROOT / ".agents/carl/nixvibe-domain.md")

    def test_guidance_contract_profiles_novice_users(self) -> None:
        result = run_pipeline(
            request=OrchestrationRequest(
                user_input="I am new to NixOS, explain like a beginner and help me start.",
            ),
            context=RepoContext(
                existing_config_present=False,
                usable_nix_structure_present=False,
                request_is_change=False,
                repository_state="known",
            ),
            specialist_tasks=[SpecialistTask("architecture", "scope", lambda: _payload(agent_id="arch"))],
            policy=self.policy,
        )

        guidance = result.artifact_summary["guidance"]
        self.assertEqual(guidance["skill_level"], "novice")
        self.assertEqual(guidance["response_style"], "stepwise")
        self.assertEqual(guidance["explanation_depth"], "expanded")
        self.assertTrue(guidance["prefer_fewer_files_initially"])
        self.assertEqual(guidance["scaffold_strategy"], "start-small-dendritic")
        self.assertEqual(guidance["immediate_next_action"], result.next_action)

    def test_guidance_contract_profiles_expert_users(self) -> None:
        result = run_pipeline(
            request=OrchestrationRequest(
                user_input="I am an expert. Refactor my flake module graph and keep structure stable.",
            ),
            context=RepoContext(
                existing_config_present=True,
                usable_nix_structure_present=True,
                request_is_change=True,
                repository_state="known",
            ),
            specialist_tasks=[SpecialistTask("audit", "scope", lambda: _payload(agent_id="audit"))],
            policy=self.policy,
        )

        guidance = result.artifact_summary["guidance"]
        self.assertEqual(guidance["skill_level"], "expert")
        self.assertEqual(guidance["response_style"], "concise")
        self.assertEqual(guidance["explanation_depth"], "compact")
        self.assertTrue(guidance["preserve_existing_structure"])
        self.assertEqual(guidance["scaffold_strategy"], "preserve-and-extend")
        self.assertEqual(guidance["immediate_next_action"], result.next_action)

    def test_guidance_contract_defaults_to_intermediate(self) -> None:
        result = run_pipeline(
            request=OrchestrationRequest(
                user_input="Please help structure my host configuration.",
            ),
            context=RepoContext(
                existing_config_present=True,
                usable_nix_structure_present=False,
                request_is_change=True,
                repository_state="known",
            ),
            specialist_tasks=[SpecialistTask("audit", "scope", lambda: _payload(agent_id="audit"))],
            policy=self.policy,
        )

        guidance = result.artifact_summary["guidance"]
        self.assertEqual(guidance["skill_level"], "intermediate")
        self.assertEqual(guidance["response_style"], "balanced")
        self.assertEqual(guidance["explanation_depth"], "standard")
        self.assertEqual(
            guidance["explanation_sections"],
            ("summary", "rationale", "next_step"),
        )


if __name__ == "__main__":
    unittest.main()
