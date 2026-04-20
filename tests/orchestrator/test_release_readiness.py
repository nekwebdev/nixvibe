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
    risk_severity: str = "medium",
) -> dict:
    return {
        "agent_id": agent_id,
        "task_scope": "release-readiness",
        "status": "warning",
        "findings": [
            {
                "id": f"F-{agent_id}",
                "severity": "high",
                "summary": "Scoped finding",
                "evidence": [f"evidence/{agent_id}.nix"],
                "impact": "Release readiness coverage",
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


class TestReleaseReadiness(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.policy = load_policy(ROOT / ".agents/carl/nixvibe-domain.md")

    def test_apply_success_is_release_ready(self) -> None:
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
                specialist_tasks=[SpecialistTask("architecture", "scope", lambda: _payload(agent_id="arch"))],
                policy=self.policy,
                workspace_root=root,
                validation_runner=lambda _command, _cwd: (0, "ok", ""),
            )

        readiness = result.artifact_summary["release_readiness"]
        self.assertTrue(readiness["ready"])
        self.assertEqual(readiness["failed_gate_count"], 0)
        self.assertEqual(readiness["failed_gate_ids"], ())

    def test_propose_mode_blocks_release_readiness(self) -> None:
        result = run_pipeline(
            request=OrchestrationRequest(
                user_input="Generate a scaffold plan.",
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

        readiness = result.artifact_summary["release_readiness"]
        self.assertFalse(readiness["ready"])
        self.assertIn("mode-apply", readiness["failed_gate_ids"])

    def test_specialist_integrity_failure_blocks_release(self) -> None:
        result = run_pipeline(
            request=OrchestrationRequest(
                user_input="Apply now.",
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
                SpecialistTask("good", "scope", lambda: _payload(agent_id="good")),
                SpecialistTask(
                    "bad",
                    "scope",
                    lambda: {
                        "agent_id": "bad",
                        "task_scope": "release-readiness",
                        "status": "warning",
                        "findings": [],
                        "recommendations": [],
                        "confidence": 0.6,
                        "risks": [],
                        "artifacts": {},
                        "timestamp": "2026-04-20T00:00:00-10:00",
                    },
                ),
            ],
            policy=self.policy,
        )

        readiness = result.artifact_summary["release_readiness"]
        self.assertFalse(readiness["ready"])
        self.assertIn("specialist-integrity", readiness["failed_gate_ids"])

    def test_high_risk_guardrail_blocks_release(self) -> None:
        result = run_pipeline(
            request=OrchestrationRequest(
                user_input="Apply this risky change now.",
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

        readiness = result.artifact_summary["release_readiness"]
        self.assertFalse(readiness["ready"])
        self.assertIn("safety-clear", readiness["failed_gate_ids"])


if __name__ == "__main__":
    unittest.main()
