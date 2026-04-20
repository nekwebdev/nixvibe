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
        "task_scope": "resume-checkpoint",
        "status": "warning",
        "findings": [
            {
                "id": f"F-{agent_id}",
                "severity": "high",
                "summary": "Scoped finding",
                "evidence": [f"evidence/{agent_id}.nix"],
                "impact": "Resume checkpoint coverage",
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


class TestResumeCheckpoint(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.policy = load_policy(ROOT / ".agents/carl/nixvibe-domain.md")

    def test_apply_success_does_not_require_resume(self) -> None:
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

        checkpoint = result.artifact_summary["resume_checkpoint"]
        self.assertEqual(checkpoint["contract"], "resume-checkpoint/v1")
        self.assertFalse(checkpoint["resume_required"])
        self.assertEqual(checkpoint["resume_stage"], "none")
        self.assertEqual(checkpoint["action_count"], 0)

    def test_clean_propose_run_does_not_require_resume(self) -> None:
        result = run_pipeline(
            request=OrchestrationRequest(
                user_input="Generate a fresh scaffold.",
            ),
            context=RepoContext(
                existing_config_present=False,
                usable_nix_structure_present=False,
                request_is_change=False,
                repository_state="known",
            ),
            specialist_tasks=[SpecialistTask("arch", "scope", lambda: _payload(agent_id="arch"))],
            policy=self.policy,
        )

        checkpoint = result.artifact_summary["resume_checkpoint"]
        self.assertFalse(checkpoint["resume_required"])
        self.assertEqual(checkpoint["resume_stage"], "none")
        self.assertFalse(checkpoint["release_ready"])

    def test_pre_write_validation_failure_requires_resume(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "flake.nix").write_text("{ }")

            def _runner(command, _cwd):
                if command == ("nix", "flake", "check"):
                    return 1, "", "flake check failed"
                return 0, "", ""

            result = run_pipeline(
                request=OrchestrationRequest(
                    user_input="Apply this now.",
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
                workspace_root=tmp,
                validation_runner=_runner,
            )

        checkpoint = result.artifact_summary["resume_checkpoint"]
        self.assertTrue(checkpoint["resume_required"])
        self.assertEqual(checkpoint["resume_stage"], "validation-pre-write")
        self.assertEqual(checkpoint["recommended_mode"], "propose")
        self.assertFalse(checkpoint["can_auto_resume"])

    def test_invalid_specialist_payload_allows_auto_resume(self) -> None:
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
                        "task_scope": "resume-checkpoint",
                        "status": "warning",
                        "findings": [],
                        "recommendations": [],
                        "confidence": 0.5,
                        "risks": [],
                        "artifacts": {},
                        "timestamp": "2026-04-20T00:00:00-10:00",
                    },
                ),
            ],
            policy=self.policy,
        )

        checkpoint = result.artifact_summary["resume_checkpoint"]
        self.assertTrue(checkpoint["resume_required"])
        self.assertEqual(checkpoint["resume_stage"], "specialist-payload")
        self.assertTrue(checkpoint["can_auto_resume"])

    def test_specialist_runtime_error_requires_explicit_resume(self) -> None:
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
                    "boom",
                    "scope",
                    lambda: (_ for _ in ()).throw(RuntimeError("runner crashed")),
                ),
            ],
            policy=self.policy,
        )

        checkpoint = result.artifact_summary["resume_checkpoint"]
        self.assertTrue(checkpoint["resume_required"])
        self.assertEqual(checkpoint["resume_stage"], "specialist-runtime")
        self.assertFalse(checkpoint["can_auto_resume"])

    def test_high_risk_guardrail_requires_human_confirmation(self) -> None:
        result = run_pipeline(
            request=OrchestrationRequest(
                user_input="Apply risky change now.",
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

        checkpoint = result.artifact_summary["resume_checkpoint"]
        self.assertTrue(checkpoint["resume_required"])
        self.assertTrue(checkpoint["requires_human_confirmation"])
        self.assertEqual(checkpoint["resume_stage"], "safety-escalation")
        self.assertFalse(checkpoint["can_auto_resume"])


if __name__ == "__main__":
    unittest.main()
