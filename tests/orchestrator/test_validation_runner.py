from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from nixvibe.orchestrator.validation import run_validation


class TestValidationRunner(unittest.TestCase):
    def test_validation_runner_reports_success(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "flake.nix").write_text("{ }")

            def _runner(command, cwd):
                self.assertEqual(cwd, Path(tmp))
                return 0, f"{' '.join(command)} ok", ""

            report = run_validation(workspace_root=tmp, command_runner=_runner)

            self.assertTrue(report.required)
            self.assertTrue(report.executed)
            self.assertTrue(report.success)
            self.assertEqual(len(report.results), 2)
            self.assertEqual(report.results[0].command, "nix flake check")
            self.assertEqual(report.results[1].command, "nix fmt")

    def test_validation_runner_reports_failure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "flake.nix").write_text("{ }")

            def _runner(command, _cwd):
                if command == ("nix", "flake", "check"):
                    return 1, "", "flake check failed"
                return 0, "", ""

            report = run_validation(workspace_root=tmp, command_runner=_runner)

            self.assertTrue(report.executed)
            self.assertFalse(report.success)
            self.assertEqual(report.results[0].exit_code, 1)
            self.assertIn("failed", report.reason)

    def test_validation_requires_flake_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = run_validation(workspace_root=tmp, command_runner=lambda _c, _cwd: (0, "", ""))
            self.assertFalse(report.executed)
            self.assertFalse(report.success)
            self.assertFalse(report.flake_present)
            self.assertEqual(report.results, ())


if __name__ == "__main__":
    unittest.main()

