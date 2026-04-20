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


def _payload(*, agent_id: str) -> dict:
    return {
        "agent_id": agent_id,
        "task_scope": "test",
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
                "action": "Do one thing",
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


class TestPipelineValidationGating(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.policy = load_policy(ROOT / ".agents/carl/nixvibe-domain.md")

    def test_apply_mode_with_validation_success_keeps_apply_and_writes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "flake.nix").write_text("{ }")
            result = run_pipeline(
                request=OrchestrationRequest(
                    user_input="Create scaffold and apply.",
                    requested_mode=Mode.APPLY,
                    explicit_apply_opt_in=True,
                ),
                context=RepoContext(
                    existing_config_present=False,
                    usable_nix_structure_present=False,
                    request_is_change=False,
                    repository_state="known",
                ),
                specialist_tasks=[SpecialistTask("architecture", "scope", lambda: _payload(agent_id="arch"))],
                policy=self.policy,
                workspace_root=tmp,
                validation_runner=lambda _command, _cwd: (0, "ok", ""),
            )

            self.assertEqual(result.selected_mode, Mode.APPLY)
            self.assertTrue(result.written_artifact_paths)
            self.assertEqual(result.proposed_artifacts, ())
            self.assertIsNotNone(result.validation_report)
            self.assertTrue(result.validation_report.success)
            validation = result.artifact_summary["validation"]
            self.assertTrue(validation["success"])
            self.assertEqual(
                tuple(checkpoint["stage"] for checkpoint in validation["checkpoints"]),
                ("pre_write", "post_write"),
            )
            self.assertEqual(validation["final_checkpoint"], "post_write")
            self.assertTrue(validation["final_success"])

    def test_apply_mode_with_validation_failure_forces_propose_and_blocks_writes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "flake.nix").write_text("{ }")

            def _runner(command, _cwd):
                if command == ("nix", "flake", "check"):
                    return 1, "", "flake check failed"
                return 0, "", ""

            result = run_pipeline(
                request=OrchestrationRequest(
                    user_input="Create scaffold and apply.",
                    requested_mode=Mode.APPLY,
                    explicit_apply_opt_in=True,
                ),
                context=RepoContext(
                    existing_config_present=False,
                    usable_nix_structure_present=False,
                    request_is_change=False,
                    repository_state="known",
                ),
                specialist_tasks=[SpecialistTask("architecture", "scope", lambda: _payload(agent_id="arch"))],
                policy=self.policy,
                workspace_root=tmp,
                validation_runner=_runner,
            )

            self.assertEqual(result.selected_mode, Mode.PROPOSE)
            self.assertFalse(result.written_artifact_paths)
            self.assertTrue(result.proposed_artifacts)
            self.assertIsNotNone(result.validation_report)
            self.assertFalse(result.validation_report.success)
            self.assertIn("Validation failed", result.next_action)
            validation = result.artifact_summary["validation"]
            self.assertFalse(validation["success"])
            self.assertEqual(
                tuple(checkpoint["stage"] for checkpoint in validation["checkpoints"]),
                ("pre_write",),
            )
            self.assertEqual(validation["final_checkpoint"], "pre_write")
            self.assertFalse(validation["final_success"])
            self.assertEqual(result.artifact_summary["mode"], "propose")

    def test_validation_summary_includes_command_level_details(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "flake.nix").write_text("{ }")

            def _runner(command, _cwd):
                if command == ("nix", "flake", "check"):
                    return 0, "flake check ok", ""
                return 0, "fmt ok", ""

            result = run_pipeline(
                request=OrchestrationRequest(
                    user_input="Create scaffold and apply.",
                    requested_mode=Mode.APPLY,
                    explicit_apply_opt_in=True,
                ),
                context=RepoContext(
                    existing_config_present=False,
                    usable_nix_structure_present=False,
                    request_is_change=False,
                    repository_state="known",
                ),
                specialist_tasks=[SpecialistTask("architecture", "scope", lambda: _payload(agent_id="arch"))],
                policy=self.policy,
                workspace_root=tmp,
                validation_runner=_runner,
            )

            validation = result.artifact_summary["validation"]
            self.assertTrue(validation["executed"])
            self.assertEqual(len(validation["commands"]), 2)
            self.assertEqual(validation["commands"][0]["command"], "nix flake check")
            self.assertEqual(validation["commands"][1]["command"], "nix fmt")
            self.assertEqual(validation["commands"][0]["exit_code"], 0)
            self.assertEqual(validation["commands"][1]["exit_code"], 0)
            self.assertEqual(validation["checkpoint_count"], 2)
            self.assertEqual(validation["final_checkpoint"], "post_write")


if __name__ == "__main__":
    unittest.main()
