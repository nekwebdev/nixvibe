from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from nixvibe.orchestrator.pipeline import run_pipeline
from nixvibe.orchestrator.policy_loader import load_policy
from nixvibe.orchestrator.types import OrchestrationRequest, SpecialistTask
from nixvibe.orchestrator.workspace import build_repo_context


def _payload(*, agent_id: str) -> dict:
    return {
        "agent_id": agent_id,
        "task_scope": "reference-adaptation",
        "status": "warning",
        "findings": [
            {
                "id": f"F-{agent_id}",
                "severity": "high",
                "summary": "Scoped finding",
                "evidence": [f"evidence/{agent_id}.nix"],
                "impact": "Test impact",
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
        "artifacts": {
            "notes": [f"note-{agent_id}"],
            "next_actions": [f"review-{agent_id}"],
        },
        "checks": {"schema_checked": True},
        "timestamp": "2026-04-19T00:00:00-10:00",
    }


class TestReferenceAdaptation(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.policy = load_policy(ROOT / ".agents/carl/nixvibe-domain.md")

    def test_reference_adaptation_uses_bootstrap_strategy_when_workspace_is_empty(self) -> None:
        with tempfile.TemporaryDirectory() as workspace_tmp, tempfile.TemporaryDirectory() as reference_tmp:
            workspace_root = Path(workspace_tmp)
            reference_root = Path(reference_tmp)

            (reference_root / "flake.nix").write_text("# nix flake check\n# nix fmt\n")
            (reference_root / "modules/core").mkdir(parents=True)
            (reference_root / "modules/roles").mkdir(parents=True)
            (reference_root / "modules/services").mkdir(parents=True)
            (reference_root / "modules/core/default.nix").write_text("{ ... }: { }")
            (reference_root / "modules/roles/default.nix").write_text("{ ... }: { }")
            (reference_root / "modules/services/default.nix").write_text("{ ... }: { }")

            context = build_repo_context(
                workspace_root=workspace_root,
                reference_root=reference_root,
                max_entries=100,
            )

            self.assertIsNotNone(context.reference_adaptation)
            self.assertEqual(context.reference_adaptation.strategy, "bootstrap-from-reference-patterns")
            self.assertFalse(context.reference_adaptation.preserve_existing_structure)
            self.assertEqual(
                context.reference_adaptation.suggested_module_aggregators,
                (
                    "modules/core/default.nix",
                    "modules/roles/default.nix",
                    "modules/services/default.nix",
                ),
            )
            self.assertIn("nix flake check", context.reference_adaptation.suggested_validation_commands)
            self.assertIn("nix fmt", context.reference_adaptation.suggested_validation_commands)

    def test_reference_adaptation_prefers_preserve_strategy_when_workspace_has_structure(self) -> None:
        with tempfile.TemporaryDirectory() as workspace_tmp, tempfile.TemporaryDirectory() as reference_tmp:
            workspace_root = Path(workspace_tmp)
            reference_root = Path(reference_tmp)

            (workspace_root / "flake.nix").write_text("{ }")
            (workspace_root / "modules/core").mkdir(parents=True)
            (workspace_root / "modules/core/default.nix").write_text("{ ... }: { }")

            (reference_root / "flake.nix").write_text("{ }")
            context = build_repo_context(
                workspace_root=workspace_root,
                reference_root=reference_root,
                max_entries=100,
            )

            self.assertIsNotNone(context.reference_adaptation)
            self.assertEqual(context.reference_adaptation.strategy, "preserve-and-extend")
            self.assertTrue(context.reference_adaptation.preserve_existing_structure)

    def test_reference_adaptation_defaults_validation_commands_when_missing(self) -> None:
        with tempfile.TemporaryDirectory() as workspace_tmp, tempfile.TemporaryDirectory() as reference_tmp:
            workspace_root = Path(workspace_tmp)
            reference_root = Path(reference_tmp)
            (reference_root / "flake.nix").write_text("{ }")

            context = build_repo_context(
                workspace_root=workspace_root,
                reference_root=reference_root,
                max_entries=100,
            )

            self.assertEqual(
                context.reference_adaptation.suggested_validation_commands,
                ("nix flake check", "nix fmt"),
            )

    def test_pipeline_summary_exposes_reference_adaptation_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as workspace_tmp, tempfile.TemporaryDirectory() as reference_tmp:
            workspace_root = Path(workspace_tmp)
            reference_root = Path(reference_tmp)
            (workspace_root / "flake.nix").write_text("{ }")
            (reference_root / "flake.nix").write_text("# nix flake check\n")

            context = build_repo_context(
                workspace_root=workspace_root,
                reference_root=reference_root,
                max_entries=100,
            )
            result = run_pipeline(
                request=OrchestrationRequest(user_input="Scaffold this setup."),
                context=context,
                specialist_tasks=[SpecialistTask("architecture", "scope", lambda: _payload(agent_id="arch"))],
                policy=self.policy,
                workspace_root=workspace_root,
            )

            context_profile = result.artifact_summary["context_profile"]
            self.assertIn("reference_adaptation", context_profile)
            adaptation = context_profile["reference_adaptation"]
            self.assertIn("strategy", adaptation)
            self.assertIn("suggested_module_aggregators", adaptation)
            self.assertIn("suggested_validation_commands", adaptation)
            self.assertTrue(
                any(
                    "never blindly copy" in note
                    for note in adaptation["notes"]
                )
            )


if __name__ == "__main__":
    unittest.main()
