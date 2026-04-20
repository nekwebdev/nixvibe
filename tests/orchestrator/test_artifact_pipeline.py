from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from nixvibe.orchestrator.pipeline import run_pipeline
from nixvibe.orchestrator.policy_loader import load_policy
from nixvibe.orchestrator.types import Mode, OrchestrationRequest, RepoContext, Route, SpecialistTask


def _payload(
    *,
    agent_id: str,
    target_tree: dict | None = None,
    patch_path: str | None = None,
) -> dict:
    artifacts: dict = {
        "notes": [f"note-{agent_id}"],
        "next_actions": [f"review-{agent_id}"],
    }
    if target_tree is not None:
        artifacts["target_tree"] = target_tree
    if patch_path is not None:
        artifacts["patches"] = [{"id": f"P-{agent_id}", "path": patch_path}]

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
        "confidence": 0.8,
        "risks": [
            {
                "id": f"K-{agent_id}",
                "category": "regression",
                "severity": "medium",
                "mitigation": "review changes",
            }
        ],
        "artifacts": artifacts,
        "checks": {"schema_checked": True},
        "timestamp": "2026-04-19T00:00:00-10:00",
    }


class TestArtifactPipeline(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.policy = load_policy(ROOT / ".agents/carl/nixvibe-domain.md")

    def test_init_route_generates_scaffold_bundle_in_propose_mode(self) -> None:
        result = run_pipeline(
            request=OrchestrationRequest(user_input="Create a new greenfield scaffold."),
            context=RepoContext(
                existing_config_present=False,
                usable_nix_structure_present=False,
                request_is_change=False,
                repository_state="known",
            ),
            specialist_tasks=[SpecialistTask("architecture", "scope", lambda: _payload(agent_id="arch"))],
            policy=self.policy,
        )

        self.assertEqual(result.route_decision.route, Route.INIT)
        self.assertEqual(result.selected_mode, Mode.PROPOSE)
        generated = {artifact.path for artifact in result.generated_artifacts}
        self.assertIn("flake.nix", generated)
        self.assertIn("modules/core/default.nix", generated)
        self.assertIn("modules/roles/default.nix", generated)
        self.assertIn("modules/services/default.nix", generated)
        self.assertIn("ARCHITECTURE.md", generated)
        self.assertIn("NEXT_STEPS.md", generated)
        self.assertEqual(len(result.proposed_artifacts), len(result.generated_artifacts))
        self.assertEqual(result.written_artifact_paths, ())
        self.assertEqual(result.artifact_summary.get("route"), "init")
        self.assertEqual(result.artifact_summary.get("mode"), "propose")

    def test_audit_route_generates_refactor_bundle(self) -> None:
        patch_path = "patches/009-refactor.patch"
        result = run_pipeline(
            request=OrchestrationRequest(
                user_input="Audit and refactor this existing NixOS config.",
                requested_mode=Mode.PROPOSE,
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
                    lambda: _payload(
                        agent_id="audit",
                        target_tree={"modules": {"services": ["default.nix"]}},
                        patch_path=patch_path,
                    ),
                )
            ],
            policy=self.policy,
        )

        self.assertEqual(result.route_decision.route, Route.AUDIT)
        generated = {artifact.path for artifact in result.generated_artifacts}
        self.assertIn("REFACTOR_PLAN.md", generated)
        self.assertIn("TARGET_TREE.md", generated)
        self.assertIn(patch_path, generated)
        self.assertIn("NEXT_STEPS.md", generated)
        self.assertEqual(result.artifact_summary.get("route"), "audit")
        self.assertEqual(result.artifact_summary.get("mode"), "propose")

    def test_advice_mode_does_not_propose_or_write_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = run_pipeline(
                request=OrchestrationRequest(
                    user_input="Audit this setup with guidance only.",
                    requested_mode=Mode.ADVICE,
                ),
                context=RepoContext(
                    existing_config_present=True,
                    request_is_change=True,
                ),
                specialist_tasks=[SpecialistTask("audit", "scope", lambda: _payload(agent_id="audit"))],
                policy=self.policy,
                workspace_root=tmp,
            )

            self.assertEqual(result.selected_mode, Mode.ADVICE)
            self.assertEqual(result.proposed_artifacts, ())
            self.assertEqual(result.written_artifact_paths, ())
            self.assertFalse((Path(tmp) / "REFACTOR_PLAN.md").exists())
            self.assertEqual(result.next_action, "Switch to propose mode to preview generated artifacts.")

    def test_apply_mode_writes_generated_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = run_pipeline(
                request=OrchestrationRequest(
                    user_input="Create scaffold and apply now.",
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
            )

            self.assertEqual(result.selected_mode, Mode.APPLY)
            self.assertGreaterEqual(len(result.written_artifact_paths), 1)
            self.assertIn("flake.nix", set(result.written_artifact_paths))
            self.assertTrue((Path(tmp) / "flake.nix").exists())
            self.assertIn("nixvibe generated scaffold", (Path(tmp) / "flake.nix").read_text())
            self.assertEqual(result.proposed_artifacts, ())
            self.assertTrue(result.artifact_summary.get("write_performed"))


if __name__ == "__main__":
    unittest.main()

