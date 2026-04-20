from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from nixvibe.orchestrator.ledger import inspect_git_ledger
from nixvibe.orchestrator.pipeline import run_pipeline
from nixvibe.orchestrator.policy_loader import load_policy
from nixvibe.orchestrator.types import OrchestrationRequest, RepoContext, SpecialistTask


def _payload(*, agent_id: str) -> dict:
    return {
        "agent_id": agent_id,
        "task_scope": "git-ledger",
        "status": "warning",
        "findings": [
            {
                "id": f"F-{agent_id}",
                "severity": "medium",
                "summary": "Scoped finding",
                "evidence": [f"evidence/{agent_id}.nix"],
                "impact": "Ledger test impact",
            }
        ],
        "recommendations": [
            {
                "id": f"R-{agent_id}",
                "action": "Apply structured change",
                "priority": "next",
                "maps_to_findings": [f"F-{agent_id}"],
                "reversible": True,
            }
        ],
        "confidence": 0.8,
        "risks": [
            {
                "id": f"K-{agent_id}",
                "category": "regression",
                "severity": "low",
                "mitigation": "review changes",
            }
        ],
        "artifacts": {"notes": [f"note-{agent_id}"], "next_actions": [f"review-{agent_id}"]},
        "checks": {"schema_checked": True},
        "timestamp": "2026-04-20T00:00:00-10:00",
    }


@unittest.skipUnless(shutil.which("git"), "git is required for ledger tests")
class TestGitLedger(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.policy = load_policy(ROOT / ".agents/carl/nixvibe-domain.md")

    def test_inspect_git_ledger_reports_unavailable_for_non_repo(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ledger = inspect_git_ledger(tmp)

        self.assertFalse(ledger["available"])
        self.assertEqual(ledger["reason"], "workspace is not a git repository")

    def test_pipeline_emits_git_ledger_summary_for_workspace_repo(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._init_repo(root)
            (root / "scratch.txt").write_text("dirty\n")

            result = run_pipeline(
                request=OrchestrationRequest(user_input="Audit this repository."),
                context=RepoContext(
                    existing_config_present=True,
                    usable_nix_structure_present=True,
                    request_is_change=True,
                    repository_state="known",
                ),
                specialist_tasks=[SpecialistTask("audit", "scope", lambda: _payload(agent_id="audit"))],
                policy=self.policy,
                workspace_root=root,
            )

        ledger = result.artifact_summary["ledger"]
        self.assertTrue(ledger["available"])
        self.assertTrue(ledger["dirty"])
        self.assertGreaterEqual(ledger["untracked_count"], 1)
        self.assertIn("scratch.txt", ledger["changed_paths"])
        self.assertEqual(ledger["change_classification"], "untracked-only")
        self.assertTrue(ledger["drift_detected"])
        self.assertIn("untracked_changes", ledger["drift_reasons"])
        self.assertEqual(ledger["drift_severity"], "medium")
        self.assertTrue(ledger["status_lines"])

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

    def test_inspect_git_ledger_reports_clean_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._init_repo(root)
            ledger = inspect_git_ledger(root)

        self.assertTrue(ledger["available"])
        self.assertFalse(ledger["dirty"])
        self.assertEqual(ledger["change_classification"], "clean")
        self.assertFalse(ledger["drift_detected"])
        self.assertEqual(ledger["drift_reasons"], ())
        self.assertEqual(ledger["drift_severity"], "none")


if __name__ == "__main__":
    unittest.main()
