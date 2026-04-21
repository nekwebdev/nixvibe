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


class _StepClock:
    def __init__(self, *, step_seconds: float = 0.01) -> None:
        self._current = 0.0
        self._step = step_seconds

    def __call__(self) -> float:
        value = self._current
        self._current += self._step
        return value


def _payload(*, agent_id: str, reversible: bool = True, risk_severity: str = "medium") -> dict:
    return {
        "agent_id": agent_id,
        "task_scope": "benchmark-baseline-report",
        "status": "warning",
        "findings": [
            {
                "id": f"F-{agent_id}",
                "severity": "high",
                "summary": "Scoped finding",
                "evidence": [f"evidence/{agent_id}.nix"],
                "impact": "Benchmark baseline coverage",
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


class TestBenchmarkBaselineReport(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.policy = load_policy(ROOT / ".agents/carl/nixvibe-domain.md")

    def test_apply_success_is_baseline_eligible(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "flake.nix").write_text("{ }")
            clock = _StepClock(step_seconds=0.01)
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
                monotonic_clock=clock,
            )

        report = result.artifact_summary["benchmark_baseline_report"]
        self.assertEqual(report["contract"], "benchmark-baseline-report/v1")
        self.assertTrue(report["baseline_eligible"])
        self.assertEqual(report["failed_check_ids"], ())
        self.assertEqual(report["baseline_tier"], "strong")
        self.assertEqual(report["timing"]["total_duration_ms"], 110)

    def test_propose_mode_is_not_eligible(self) -> None:
        clock = _StepClock(step_seconds=0.01)
        result = run_pipeline(
            request=OrchestrationRequest(user_input="Generate scaffold plan."),
            context=RepoContext(
                existing_config_present=False,
                usable_nix_structure_present=False,
                request_is_change=False,
                repository_state="known",
            ),
            specialist_tasks=[SpecialistTask("arch", "scope", lambda: _payload(agent_id="arch"))],
            policy=self.policy,
            monotonic_clock=clock,
        )

        report = result.artifact_summary["benchmark_baseline_report"]
        self.assertFalse(report["baseline_eligible"])
        self.assertIn("mode-apply", report["failed_check_ids"])
        self.assertIn("release-ready", report["failed_check_ids"])

    def test_guardrail_blocked_path_is_not_eligible(self) -> None:
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

        report = result.artifact_summary["benchmark_baseline_report"]
        self.assertFalse(report["baseline_eligible"])
        self.assertIn("failure-classification-clear", report["failed_check_ids"])
        self.assertIn("release-ready", report["failed_check_ids"])


if __name__ == "__main__":
    unittest.main()
