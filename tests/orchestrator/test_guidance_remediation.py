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


def _payload(*, agent_id: str, critical_summary: str = "Scoped finding", critical_impact: str = "Risk") -> dict:
    return {
        "agent_id": agent_id,
        "task_scope": "guidance-remediation",
        "status": "warning",
        "findings": [
            {
                "id": f"F-{agent_id}",
                "severity": "critical",
                "summary": critical_summary,
                "evidence": [f"evidence/{agent_id}.nix"],
                "impact": critical_impact,
                "contradiction_key": "root-access",
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
        "artifacts": {"notes": [f"note-{agent_id}"], "next_actions": [f"review-{agent_id}"]},
        "checks": {"schema_checked": True},
        "timestamp": "2026-04-20T00:00:00-10:00",
    }


class TestGuidanceRemediation(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.policy = load_policy(ROOT / ".agents/carl/nixvibe-domain.md")

    def test_pre_write_validation_failure_emits_validation_remediation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "flake.nix").write_text("{ }")

            def _runner(command, _cwd):
                if command == ("nix", "flake", "check"):
                    return 1, "", "flake check failed"
                return 0, "", ""

            result = run_pipeline(
                request=OrchestrationRequest(
                    user_input="Please apply this change.",
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

        guidance = result.artifact_summary["guidance"]
        remediation = guidance["remediation"]
        self.assertEqual(guidance["validation_failure_stage"], "pre_write")
        self.assertTrue(remediation["required"])
        self.assertEqual(remediation["category"], "validation-pre-write")
        self.assertIn("pre_write_validation_failed", remediation["blockers"])

    def test_post_write_validation_failure_emits_post_write_remediation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "flake.nix").write_text("{ }")
            call_index = {"value": 0}

            def _runner(_command, _cwd):
                call_index["value"] += 1
                if call_index["value"] == 3:
                    return 1, "", "post-write flake check failed"
                return 0, "ok", ""

            result = run_pipeline(
                request=OrchestrationRequest(
                    user_input="Apply and validate this now.",
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

        guidance = result.artifact_summary["guidance"]
        remediation = guidance["remediation"]
        self.assertEqual(result.selected_mode, Mode.APPLY)
        self.assertEqual(guidance["validation_failure_stage"], "post_write")
        self.assertTrue(remediation["required"])
        self.assertEqual(remediation["category"], "validation-post-write")
        self.assertIn("post_write_validation_failed", remediation["blockers"])

    def test_conflict_forced_propose_emits_conflict_remediation(self) -> None:
        result = run_pipeline(
            request=OrchestrationRequest(
                user_input="Apply root ssh setting now.",
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
                    "audit-a",
                    "scope",
                    lambda: _payload(
                        agent_id="audit-a",
                        critical_summary="Enable root SSH login",
                        critical_impact="Broad remote attack surface",
                    ),
                ),
                SpecialistTask(
                    "audit-b",
                    "scope",
                    lambda: _payload(
                        agent_id="audit-b",
                        critical_summary="Disable root SSH login",
                        critical_impact="Prevents direct privileged remote access",
                    ),
                ),
            ],
            policy=self.policy,
        )

        guidance = result.artifact_summary["guidance"]
        remediation = guidance["remediation"]
        self.assertEqual(result.selected_mode, Mode.PROPOSE)
        self.assertTrue(guidance["conflict_forced_propose"])
        self.assertTrue(remediation["required"])
        self.assertEqual(remediation["category"], "conflict-critical")
        self.assertIn("critical_conflict_unresolved", remediation["blockers"])


if __name__ == "__main__":
    unittest.main()
