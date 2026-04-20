from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from nixvibe.orchestrator.pipeline import run_pipeline
from nixvibe.orchestrator.policy_loader import load_policy
from nixvibe.orchestrator.types import Mode, OrchestrationRequest, RepoContext, SpecialistTask


def _payload(*, patch_paths: tuple[str, ...]) -> dict:
    patches = [{"id": f"P-{index + 1}", "path": path} for index, path in enumerate(patch_paths)]
    return {
        "agent_id": "audit",
        "task_scope": "patch-hygiene",
        "status": "warning",
        "findings": [
            {
                "id": "F-audit",
                "severity": "high",
                "summary": "Scoped finding",
                "evidence": ["evidence/audit.nix"],
                "impact": "Patch hygiene test",
            }
        ],
        "recommendations": [
            {
                "id": "R-audit",
                "action": "Propose patch set",
                "priority": "now",
                "maps_to_findings": ["F-audit"],
                "reversible": True,
            }
        ],
        "confidence": 0.9,
        "risks": [
            {
                "id": "K-audit",
                "category": "regression",
                "severity": "medium",
                "mitigation": "review patch paths",
            }
        ],
        "artifacts": {
            "notes": ["note-audit"],
            "next_actions": ["review-audit"],
            "target_tree": {"modules": {"services": ["default.nix"]}},
            "patches": patches,
        },
        "checks": {"schema_checked": True},
        "timestamp": "2026-04-19T00:00:00-10:00",
    }


class TestPatchHygiene(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.policy = load_policy(ROOT / ".agents/carl/nixvibe-domain.md")

    def test_compliant_patch_path_is_preserved(self) -> None:
        result = run_pipeline(
            request=OrchestrationRequest(
                user_input="Audit and propose patches.",
                requested_mode=Mode.PROPOSE,
            ),
            context=RepoContext(
                existing_config_present=True,
                usable_nix_structure_present=True,
                request_is_change=True,
                repository_state="known",
            ),
            specialist_tasks=[
                SpecialistTask("audit", "scope", lambda: _payload(patch_paths=("patches/009-refactor.patch",)))
            ],
            policy=self.policy,
        )

        generated_paths = {artifact.path for artifact in result.generated_artifacts}
        self.assertIn("patches/009-refactor.patch", generated_paths)

    def test_non_patch_input_is_normalized_into_patches_directory(self) -> None:
        result = run_pipeline(
            request=OrchestrationRequest(
                user_input="Audit and propose patches.",
                requested_mode=Mode.PROPOSE,
            ),
            context=RepoContext(
                existing_config_present=True,
                usable_nix_structure_present=True,
                request_is_change=True,
                repository_state="known",
            ),
            specialist_tasks=[
                SpecialistTask("audit", "scope", lambda: _payload(patch_paths=("tmp/My Refactor.diff",)))
            ],
            policy=self.policy,
        )

        generated_paths = {artifact.path for artifact in result.generated_artifacts}
        self.assertIn("patches/001-my-refactor-diff.patch", generated_paths)

    def test_traversal_or_absolute_patch_input_is_sanitized(self) -> None:
        result = run_pipeline(
            request=OrchestrationRequest(
                user_input="Audit and propose patches.",
                requested_mode=Mode.PROPOSE,
            ),
            context=RepoContext(
                existing_config_present=True,
                usable_nix_structure_present=True,
                request_is_change=True,
                repository_state="known",
            ),
            specialist_tasks=[
                SpecialistTask("audit", "scope", lambda: _payload(patch_paths=("../escape.patch",)))
            ],
            policy=self.policy,
        )

        patch_paths = [artifact.path for artifact in result.generated_artifacts if artifact.path.startswith("patches/")]
        self.assertIn("patches/001-escape.patch", patch_paths)
        self.assertTrue(all(path.startswith("patches/") for path in patch_paths))
        self.assertTrue(all(".." not in path for path in patch_paths))

    def test_duplicate_inputs_deduplicate_after_normalization(self) -> None:
        result = run_pipeline(
            request=OrchestrationRequest(
                user_input="Audit and propose patches.",
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
                        patch_paths=(
                            "./patches/007-fix.patch",
                            "patches/007-fix.patch",
                        )
                    ),
                )
            ],
            policy=self.policy,
        )

        patch_paths = [artifact.path for artifact in result.generated_artifacts if artifact.path.startswith("patches/")]
        self.assertEqual(patch_paths.count("patches/007-fix.patch"), 1)


if __name__ == "__main__":
    unittest.main()
