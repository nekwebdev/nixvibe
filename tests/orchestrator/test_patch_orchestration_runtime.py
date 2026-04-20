from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from nixvibe.orchestrator.pipeline import run_pipeline
from nixvibe.orchestrator.policy_loader import load_policy
from nixvibe.orchestrator.runtime import default_runtime_contract
from nixvibe.orchestrator.types import OrchestrationRequest, RepoContext, Route, RuntimeSpecialistRole, SpecialistTask


def _payload(*, agent_id: str, patches: list[dict] | None = None) -> dict:
    artifacts: dict = {
        "notes": [f"note-{agent_id}"],
        "next_actions": [f"review-{agent_id}"],
    }
    if patches is not None:
        artifacts["patches"] = patches

    return {
        "agent_id": agent_id,
        "task_scope": "patch-orchestration-runtime",
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
        "artifacts": artifacts,
        "checks": {"schema_checked": True},
        "timestamp": "2026-04-19T00:00:00-10:00",
    }


class TestPatchOrchestrationRuntime(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.policy = load_policy(ROOT / ".agents/carl/nixvibe-domain.md")

    def test_patch_orchestration_is_deterministic_across_specialists(self) -> None:
        tasks = [
            SpecialistTask(
                "architecture",
                "scope",
                lambda: _payload(
                    agent_id="architecture",
                    patches=[
                        {"id": "A-1", "path": "tmp/first.diff"},
                        {"path": "patches/009-existing.patch"},
                    ],
                ),
            ),
            SpecialistTask(
                "audit",
                "scope",
                lambda: _payload(
                    agent_id="audit",
                    patches=[
                        {"path": "../escape.patch"},
                        {"id": "A-dup", "path": "patches/009-existing.patch"},
                    ],
                ),
            ),
        ]
        result = run_pipeline(
            request=OrchestrationRequest(
                user_input="Audit and propose patches.",
            ),
            context=RepoContext(
                existing_config_present=True,
                usable_nix_structure_present=True,
                request_is_change=True,
                repository_state="known",
            ),
            specialist_tasks=tasks,
            policy=self.policy,
        )

        patch_orchestration = result.artifact_summary["patch_orchestration"]
        self.assertEqual(patch_orchestration["count"], 3)
        self.assertEqual(
            patch_orchestration["paths"],
            (
                "patches/001-first-diff.patch",
                "patches/009-existing.patch",
                "patches/003-escape.patch",
            ),
        )
        self.assertEqual(patch_orchestration["ids"], ("A-1", "P-002", "P-003"))
        self.assertEqual(
            patch_orchestration["source_agents"],
            ("architecture", "architecture", "audit"),
        )

        generated_patch_paths = tuple(
            artifact.path
            for artifact in result.generated_artifacts
            if artifact.path.startswith("patches/")
        )
        self.assertEqual(generated_patch_paths, patch_orchestration["paths"])

    def test_runtime_contract_path_emits_patch_orchestration_summary(self) -> None:
        contract = default_runtime_contract(Route.AUDIT)
        handlers = {
            RuntimeSpecialistRole.ARCHITECTURE: lambda _ctx: _payload(
                agent_id="architecture",
                patches=[{"path": "tmp/arch.diff"}],
            ),
            RuntimeSpecialistRole.AUDIT: lambda _ctx: _payload(
                agent_id="audit",
                patches=[{"path": "tmp/audit.diff"}],
            ),
            RuntimeSpecialistRole.VALIDATE: lambda _ctx: _payload(agent_id="validate"),
        }
        result = run_pipeline(
            request=OrchestrationRequest(user_input="Audit my setup."),
            context=RepoContext(
                existing_config_present=True,
                usable_nix_structure_present=True,
                request_is_change=True,
                repository_state="known",
            ),
            policy=self.policy,
            runtime_contract=contract,
            runtime_handlers=handlers,
        )

        patch_orchestration = result.artifact_summary["patch_orchestration"]
        self.assertEqual(patch_orchestration["count"], 2)
        self.assertEqual(
            patch_orchestration["paths"],
            ("patches/001-arch-diff.patch", "patches/002-audit-diff.patch"),
        )
        self.assertEqual(
            result.artifact_summary["specialist_dispatch"]["runtime_contract_name"],
            "audit-default",
        )


if __name__ == "__main__":
    unittest.main()
