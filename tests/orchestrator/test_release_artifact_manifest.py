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
    target_tree: dict | None = None,
    patch_path: str | None = None,
) -> dict:
    artifacts: dict[str, object] = {
        "notes": [f"note-{agent_id}"],
        "next_actions": [f"review-{agent_id}"],
    }
    if target_tree is not None:
        artifacts["target_tree"] = target_tree
    if patch_path is not None:
        artifacts["patches"] = [{"id": f"P-{agent_id}", "path": patch_path}]

    return {
        "agent_id": agent_id,
        "task_scope": "release-artifact-manifest",
        "status": "warning",
        "findings": [
            {
                "id": f"F-{agent_id}",
                "severity": "high",
                "summary": "Scoped finding",
                "evidence": [f"evidence/{agent_id}.nix"],
                "impact": "Release manifest coverage",
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
                "mitigation": "review patch set",
            }
        ],
        "artifacts": artifacts,
        "checks": {"schema_checked": True},
        "timestamp": "2026-04-20T00:00:00-10:00",
    }


def _check_by_id(manifest: dict[str, object], item_id: str) -> dict[str, object]:
    for check in manifest["checklist"]:
        if check["id"] == item_id:
            return check
    raise AssertionError(f"Missing checklist item: {item_id}")


class TestReleaseArtifactManifest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.policy = load_policy(ROOT / ".agents/carl/nixvibe-domain.md")

    def test_apply_success_has_release_ready_manifest(self) -> None:
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
            )

        manifest = result.artifact_summary["release_artifact_manifest"]
        self.assertEqual(manifest["contract"], "release-artifact-manifest/v1")
        self.assertTrue(manifest["release_ready"])
        self.assertEqual(manifest["failed_item_count"], 0)
        self.assertTrue(_check_by_id(manifest, "release-gates")["passed"])

    def test_init_propose_manifest_blocks_on_release_gate(self) -> None:
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

        manifest = result.artifact_summary["release_artifact_manifest"]
        self.assertFalse(manifest["release_ready"])
        self.assertIn("release-gates", manifest["failed_item_ids"])
        self.assertTrue(_check_by_id(manifest, "init-flake")["passed"])
        self.assertTrue(_check_by_id(manifest, "mode-materialization")["passed"])

    def test_audit_manifest_includes_refactor_artifacts(self) -> None:
        patch_path = "patches/042-release-refactor.patch"
        result = run_pipeline(
            request=OrchestrationRequest(
                user_input="Please audit and refactor.",
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

        manifest = result.artifact_summary["release_artifact_manifest"]
        self.assertTrue(_check_by_id(manifest, "audit-refactor-plan")["passed"])
        self.assertTrue(_check_by_id(manifest, "audit-target-tree")["passed"])
        self.assertTrue(_check_by_id(manifest, "audit-patch-set")["passed"])


if __name__ == "__main__":
    unittest.main()
