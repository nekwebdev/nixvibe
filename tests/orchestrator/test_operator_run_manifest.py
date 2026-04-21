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
) -> dict:
    checks = {"schema_checked": True}
    return {
        "agent_id": agent_id,
        "task_scope": "operator-manifest",
        "status": "warning",
        "findings": [
            {
                "id": f"F-{agent_id}",
                "severity": "high",
                "summary": "Scoped finding",
                "evidence": [f"evidence/{agent_id}.nix"],
                "impact": "Manifest outcome coverage",
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
                "severity": "medium",
                "mitigation": "review changes",
            }
        ],
        "artifacts": {"notes": [f"note-{agent_id}"], "next_actions": [f"review-{agent_id}"]},
        "checks": checks,
        "timestamp": "2026-04-20T00:00:00-10:00",
    }


class TestOperatorRunManifest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.policy = load_policy(ROOT / ".agents/carl/nixvibe-domain.md")

    def test_apply_success_manifest_fields(self) -> None:
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
                specialist_tasks=[
                    SpecialistTask(
                        "architecture",
                        "scope",
                        lambda: _payload(agent_id="architecture", reversible=True),
                    )
                ],
                policy=self.policy,
                workspace_root=root,
                validation_runner=lambda _command, _cwd: (0, "ok", ""),
            )

        manifest = result.artifact_summary["run_manifest"]
        self.assertEqual(manifest["contract"], "operator-run-manifest/v1")
        self.assertEqual(manifest["route"], "init")
        self.assertEqual(manifest["modes"]["requested"], "apply")
        self.assertEqual(manifest["modes"]["selected"], "apply")
        self.assertFalse(manifest["modes"]["changed"])
        self.assertEqual(manifest["specialists"]["planned_count"], 1)
        self.assertEqual(manifest["specialists"]["included_count"], 1)
        self.assertEqual(manifest["specialists"]["excluded_count"], 0)
        self.assertEqual(manifest["validation"]["final_checkpoint"], "post_write")
        self.assertEqual(manifest["validation"]["checkpoint_count"], 2)
        self.assertIn("timing", manifest)
        self.assertGreaterEqual(manifest["timing"]["total_duration_ms"], 0)
        self.assertGreaterEqual(manifest["timing"]["specialist_execution_ms"], 0)

    def test_guardrail_forced_propose_manifest_fields(self) -> None:
        result = run_pipeline(
            request=OrchestrationRequest(
                user_input="Apply this change now.",
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
                    lambda: _payload(agent_id="audit", reversible=False),
                )
            ],
            policy=self.policy,
        )

        manifest = result.artifact_summary["run_manifest"]
        self.assertEqual(manifest["modes"]["requested"], "apply")
        self.assertEqual(manifest["modes"]["selected"], "propose")
        self.assertTrue(manifest["modes"]["changed"])
        self.assertTrue(manifest["safety"]["guardrail_blocked_apply"])
        self.assertIn("irreversible_recommendation", manifest["safety"]["guardrail_triggers"])
        self.assertEqual(manifest["safety"]["escalation_reason"], "high_risk_mutation_guardrail")
        self.assertEqual(manifest["safety"]["recovery_stage"], "guardrail-high-risk")

    def test_manifest_captures_invalid_specialist_outcomes(self) -> None:
        result = run_pipeline(
            request=OrchestrationRequest(
                user_input="Review config",
            ),
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
                        "task_scope": "operator-manifest",
                        "status": "warning",
                        "findings": [],
                        "recommendations": [],
                        "confidence": 0.7,
                        "risks": [],
                        "artifacts": {},
                        "timestamp": "2026-04-20T00:00:00-10:00",
                    },
                ),
            ],
            policy=self.policy,
        )

        manifest = result.artifact_summary["run_manifest"]
        outcomes = manifest["specialists"]["outcomes"]
        self.assertEqual(manifest["specialists"]["planned_count"], 2)
        self.assertEqual(manifest["specialists"]["included_count"], 1)
        self.assertEqual(manifest["specialists"]["excluded_count"], 1)
        self.assertEqual(outcomes["ok"], 1)
        self.assertEqual(outcomes["invalid"], 1)
        self.assertEqual(outcomes["error"], 0)


if __name__ == "__main__":
    unittest.main()
