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
        "task_scope": "run-failure-classification",
        "status": "warning",
        "findings": [
            {
                "id": f"F-{agent_id}",
                "severity": "high",
                "summary": "Scoped finding",
                "evidence": [f"evidence/{agent_id}.nix"],
                "impact": "Failure classification coverage",
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


class TestRunFailureClassification(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.policy = load_policy(ROOT / ".agents/carl/nixvibe-domain.md")

    def test_apply_success_classifies_none(self) -> None:
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

        classification = result.artifact_summary["run_failure_classification"]
        self.assertEqual(classification["contract"], "run-failure-classification/v1")
        self.assertEqual(classification["classification"], "none")
        self.assertEqual(classification["severity"], "none")
        self.assertEqual(classification["signal_count"], 0)
        self.assertEqual(classification["signals"], ())

    def test_pre_write_validation_failure_classifies_blocked(self) -> None:
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
                specialist_tasks=[SpecialistTask("architecture", "scope", lambda: _payload(agent_id="arch"))],
                policy=self.policy,
                workspace_root=tmp,
                validation_runner=_runner,
            )

        classification = result.artifact_summary["run_failure_classification"]
        self.assertEqual(classification["classification"], "blocked")
        self.assertEqual(classification["severity"], "critical")
        self.assertIn("validation-pre-write", classification["signals"])

    def test_post_write_validation_failure_classifies_failed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "flake.nix").write_text("{ }")
            call_index = {"value": 0}

            def _runner(_command, _cwd):
                call_index["value"] += 1
                if call_index["value"] == 3:
                    return 1, "", "post-write check failed"
                return 0, "ok", ""

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
                specialist_tasks=[SpecialistTask("architecture", "scope", lambda: _payload(agent_id="arch"))],
                policy=self.policy,
                workspace_root=tmp,
                validation_runner=_runner,
            )

        classification = result.artifact_summary["run_failure_classification"]
        self.assertEqual(classification["classification"], "failed")
        self.assertEqual(classification["severity"], "high")
        self.assertIn("validation-post-write", classification["signals"])

    def test_invalid_specialist_payload_classifies_degraded(self) -> None:
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
                        "task_scope": "run-failure-classification",
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

        classification = result.artifact_summary["run_failure_classification"]
        self.assertEqual(classification["classification"], "degraded")
        self.assertEqual(classification["severity"], "medium")
        self.assertIn("specialist-invalid", classification["signals"])

    def test_specialist_runner_error_classifies_failed(self) -> None:
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
                SpecialistTask("broken", "scope", lambda: (_ for _ in ()).throw(RuntimeError("runner failed"))),
            ],
            policy=self.policy,
        )

        classification = result.artifact_summary["run_failure_classification"]
        self.assertEqual(classification["classification"], "failed")
        self.assertEqual(classification["severity"], "high")
        self.assertIn("specialist-error", classification["signals"])


if __name__ == "__main__":
    unittest.main()
