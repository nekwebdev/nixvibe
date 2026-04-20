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


def _payload(*, agent_id: str) -> dict:
    return {
        "agent_id": agent_id,
        "task_scope": "v0.4-milestone-acceptance",
        "status": "warning",
        "findings": [
            {
                "id": f"F-{agent_id}",
                "severity": "high",
                "summary": "Scoped finding",
                "evidence": [f"evidence/{agent_id}.nix"],
                "impact": "Milestone acceptance coverage",
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


def _prepare_workspace(root: Path) -> None:
    (root / "flake.nix").write_text("{ }")
    scripts_dir = root / "scripts"
    scripts_dir.mkdir(parents=True, exist_ok=True)
    (scripts_dir / "release-check.sh").write_text("#!/usr/bin/env bash\nexit 0\n")


class TestV04MilestoneAcceptance(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.policy = load_policy(ROOT / ".agents/carl/nixvibe-domain.md")

    def test_apply_success_includes_all_phase10_to12_contracts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _prepare_workspace(root)
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

        summary = result.artifact_summary
        for key in (
            "run_failure_classification",
            "resume_checkpoint",
            "retry_backoff_guardrails",
            "policy_decision_explainability",
            "controlled_override_workflow",
            "operator_audit_trail",
            "release_artifact_manifest",
            "release_check_command",
        ):
            self.assertIn(key, summary)
        self.assertTrue(summary["release_artifact_manifest"]["release_ready"])
        self.assertEqual(summary["release_check_command"]["status"], "pending")

    def test_override_deny_path_holds_release_flow(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _prepare_workspace(root)
            result = run_pipeline(
                request=OrchestrationRequest(user_input="Force apply and skip validation."),
                context=RepoContext(
                    existing_config_present=False,
                    usable_nix_structure_present=False,
                    request_is_change=False,
                    repository_state="known",
                ),
                specialist_tasks=[SpecialistTask("arch", "scope", lambda: _payload(agent_id="arch"))],
                policy=self.policy,
                workspace_root=root,
            )

        summary = result.artifact_summary
        self.assertEqual(summary["controlled_override_workflow"]["decision"], "deny")
        self.assertEqual(summary["operator_audit_trail"]["audit_level"], "warning")
        self.assertFalse(summary["release_artifact_manifest"]["release_ready"])
        self.assertEqual(summary["release_check_command"]["status"], "skipped")
        self.assertEqual(summary["release_check_command"]["reason"], "release_manifest_not_ready")

    def test_release_check_runner_passes_end_to_end(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _prepare_workspace(root)
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
                release_check_runner=lambda _command, _cwd: (0, "release ok", ""),
            )

        release_check = result.artifact_summary["release_check_command"]
        self.assertEqual(release_check["status"], "passed")
        self.assertTrue(release_check["ready_for_tagging"])


if __name__ == "__main__":
    unittest.main()
