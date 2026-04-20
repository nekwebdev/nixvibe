from __future__ import annotations

import shutil
import subprocess
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
    summary: str = "Scoped finding",
    impact: str = "Escalation impact",
    severity: str = "high",
    contradiction_key: str | None = None,
) -> dict:
    finding: dict[str, object] = {
        "id": f"F-{agent_id}",
        "severity": severity,
        "summary": summary,
        "evidence": [f"evidence/{agent_id}.nix"],
        "impact": impact,
    }
    if contradiction_key:
        finding["contradiction_key"] = contradiction_key

    return {
        "agent_id": agent_id,
        "task_scope": "apply-escalation",
        "status": "warning",
        "findings": [finding],
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
                "mitigation": "review",
            }
        ],
        "artifacts": {"notes": [f"note-{agent_id}"], "next_actions": [f"review-{agent_id}"]},
        "checks": {"schema_checked": True},
        "timestamp": "2026-04-20T00:00:00-10:00",
    }


class TestApplySafetyEscalation(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.policy = load_policy(ROOT / ".agents/carl/nixvibe-domain.md")

    def test_pre_write_validation_failure_is_blocked(self) -> None:
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
                specialist_tasks=[SpecialistTask("architecture", "scope", lambda: _payload(agent_id="architecture"))],
                policy=self.policy,
                workspace_root=tmp,
                validation_runner=_runner,
            )

        escalation = result.artifact_summary["apply_safety_escalation"]
        self.assertEqual(escalation["tier"], "blocked")
        self.assertEqual(escalation["reason"], "pre_write_validation_failed")
        self.assertTrue(escalation["requires_recovery"])
        self.assertEqual(escalation["recommended_mode"], "propose")

    def test_post_write_validation_failure_is_guarded(self) -> None:
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
                specialist_tasks=[SpecialistTask("architecture", "scope", lambda: _payload(agent_id="architecture"))],
                policy=self.policy,
                workspace_root=tmp,
                validation_runner=_runner,
            )

        escalation = result.artifact_summary["apply_safety_escalation"]
        self.assertEqual(escalation["tier"], "guarded")
        self.assertEqual(escalation["reason"], "post_write_validation_failed")
        self.assertTrue(escalation["requires_recovery"])

    def test_conflict_forced_propose_is_blocked(self) -> None:
        result = run_pipeline(
            request=OrchestrationRequest(
                user_input="Apply root ssh change now.",
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
                        summary="Enable root SSH login",
                        impact="Broad attack surface",
                        severity="critical",
                        contradiction_key="root-access",
                    ),
                ),
                SpecialistTask(
                    "audit-b",
                    "scope",
                    lambda: _payload(
                        agent_id="audit-b",
                        summary="Disable root SSH login",
                        impact="Prevents privileged remote access",
                        severity="critical",
                        contradiction_key="root-access",
                    ),
                ),
            ],
            policy=self.policy,
        )

        escalation = result.artifact_summary["apply_safety_escalation"]
        self.assertEqual(result.selected_mode, Mode.PROPOSE)
        self.assertEqual(escalation["tier"], "blocked")
        self.assertEqual(escalation["reason"], "critical_conflict_forced_propose")
        self.assertTrue(escalation["human_confirmation_required"])

    @unittest.skipUnless(shutil.which("git"), "git is required for advisory escalation test")
    def test_apply_dirty_workspace_is_advisory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._init_repo(root)
            result = run_pipeline(
                request=OrchestrationRequest(
                    user_input="Apply clean scaffold.",
                    requested_mode=Mode.APPLY,
                    explicit_apply_opt_in=True,
                ),
                context=RepoContext(
                    existing_config_present=False,
                    usable_nix_structure_present=False,
                    request_is_change=False,
                    repository_state="known",
                ),
                specialist_tasks=[SpecialistTask("architecture", "scope", lambda: _payload(agent_id="architecture"))],
                policy=self.policy,
                workspace_root=root,
                validation_runner=lambda _command, _cwd: (0, "ok", ""),
            )

        escalation = result.artifact_summary["apply_safety_escalation"]
        self.assertEqual(result.selected_mode, Mode.APPLY)
        self.assertEqual(escalation["tier"], "advisory")
        self.assertEqual(escalation["reason"], "apply_dirty_workspace")
        self.assertFalse(escalation["requires_recovery"])

    def _init_repo(self, root: Path) -> None:
        subprocess.run(("git", "init"), cwd=root, check=True, capture_output=True, text=True)
        (root / "flake.nix").write_text("{ }")
        subprocess.run(("git", "add", "flake.nix"), cwd=root, check=True, capture_output=True, text=True)
        subprocess.run(
            (
                "git",
                "-c",
                "commit.gpgsign=false",
                "-c",
                "user.name=nixvibe-test",
                "-c",
                "user.email=nixvibe@test.invalid",
                "commit",
                "-m",
                "init",
            ),
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        )


if __name__ == "__main__":
    unittest.main()
