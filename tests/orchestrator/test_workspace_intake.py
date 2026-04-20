from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from nixvibe.orchestrator.pipeline import run_pipeline
from nixvibe.orchestrator.policy_loader import load_policy
from nixvibe.orchestrator.router import select_route
from nixvibe.orchestrator.types import OrchestrationRequest, RepoContext, SpecialistTask
from nixvibe.orchestrator.workspace import build_repo_context, snapshot_workspace


def _payload(*, agent_id: str) -> dict:
    return {
        "agent_id": agent_id,
        "task_scope": "workspace-intake",
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


class TestWorkspaceIntake(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.policy = load_policy(ROOT / ".agents/carl/nixvibe-domain.md")

    def test_snapshot_workspace_respects_entry_boundaries(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for index in range(10):
                (root / f"file-{index}.txt").write_text("x")
            snapshot = snapshot_workspace(workspace_root=root, max_entries=3)
            self.assertEqual(len(snapshot.entries), 3)
            self.assertTrue(snapshot.truncated)

    def test_build_repo_context_detects_usable_nix_structure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "flake.nix").write_text("{ }")
            (root / "modules/core").mkdir(parents=True)
            (root / "modules/core/default.nix").write_text("{ ... }: { }")
            context = build_repo_context(workspace_root=root, max_entries=50)
            self.assertEqual(context.repository_state, "known")
            self.assertTrue(context.existing_config_present)
            self.assertTrue(context.usable_nix_structure_present)
            self.assertIsNotNone(context.workspace_snapshot)
            self.assertTrue(context.workspace_snapshot.flake_present)

    def test_reference_profile_captures_validation_patterns(self) -> None:
        with tempfile.TemporaryDirectory() as workspace_tmp, tempfile.TemporaryDirectory() as reference_tmp:
            workspace_root = Path(workspace_tmp)
            reference_root = Path(reference_tmp)
            (workspace_root / "flake.nix").write_text("{ }")
            (reference_root / "flake.nix").write_text("# nix flake check\n# nix fmt\n")
            (reference_root / "scripts").mkdir(parents=True)
            (reference_root / "scripts/check.sh").write_text("nix flake check\n")
            (reference_root / "scripts/fmt.sh").write_text("nix fmt\n")
            (reference_root / "modules/core").mkdir(parents=True)
            (reference_root / "modules/core/default.nix").write_text("{ ... }: { }")

            context = build_repo_context(
                workspace_root=workspace_root,
                reference_root=reference_root,
                max_entries=50,
            )
            self.assertIsNotNone(context.reference_profile)
            self.assertIn("nix flake check", context.reference_profile.validation_patterns)
            self.assertIn("nix fmt", context.reference_profile.validation_patterns)
            self.assertTrue(any("adapt to target constraints" in note for note in context.reference_profile.notes))

    def test_route_uses_profile_hints_when_flags_unknown(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "flake.nix").write_text("{ }")
            (root / "modules/services").mkdir(parents=True)
            (root / "modules/services/default.nix").write_text("{ ... }: { }")

            profiled = build_repo_context(workspace_root=root, max_entries=50)
            context = RepoContext(
                existing_config_present=None,
                usable_nix_structure_present=None,
                request_is_change=None,
                repository_state="unknown",
                workspace_snapshot=profiled.workspace_snapshot,
            )
            decision = select_route(
                request=OrchestrationRequest(user_input="Need guidance."),
                context=context,
                policy=self.policy,
            )
            self.assertEqual(decision.route.value, "audit")
            self.assertFalse(decision.needs_clarification)

    def test_pipeline_summary_includes_context_profile_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as workspace_tmp, tempfile.TemporaryDirectory() as reference_tmp:
            workspace_root = Path(workspace_tmp)
            reference_root = Path(reference_tmp)
            (workspace_root / "flake.nix").write_text("{ }")
            (workspace_root / "modules/roles").mkdir(parents=True)
            (workspace_root / "modules/roles/default.nix").write_text("{ ... }: { }")
            (reference_root / "flake.nix").write_text("# nix flake check\n")

            context = build_repo_context(
                workspace_root=workspace_root,
                reference_root=reference_root,
                max_entries=50,
            )
            result = run_pipeline(
                request=OrchestrationRequest(user_input="Create a clean scaffold."),
                context=context,
                specialist_tasks=[SpecialistTask("architecture", "scope", lambda: _payload(agent_id="arch"))],
                policy=self.policy,
                workspace_root=workspace_root,
            )
            self.assertIn("context_profile", result.artifact_summary)
            self.assertIn("workspace", result.artifact_summary["context_profile"])
            self.assertIn("reference", result.artifact_summary["context_profile"])
            self.assertTrue(result.artifact_summary["context_profile"]["workspace"]["flake_present"])


if __name__ == "__main__":
    unittest.main()
