from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from nixvibe.orchestrator.benchmark_release import build_benchmark_release_readiness
from nixvibe.orchestrator.pipeline import run_pipeline
from nixvibe.orchestrator.policy_loader import load_policy
from nixvibe.orchestrator.types import Mode, OrchestrationRequest, RepoContext, SpecialistTask


class _StepClock:
    def __init__(self, *, step_seconds: float) -> None:
        self._current = 0.0
        self._step = step_seconds

    def __call__(self) -> float:
        value = self._current
        self._current += self._step
        return value


def _payload(*, agent_id: str) -> dict:
    return {
        "agent_id": agent_id,
        "task_scope": "benchmark-release-readiness",
        "status": "warning",
        "findings": [
            {
                "id": f"F-{agent_id}",
                "severity": "high",
                "summary": "Scoped finding",
                "evidence": [f"evidence/{agent_id}.nix"],
                "impact": "Benchmark release readiness coverage",
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


class TestBenchmarkReleaseReadiness(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.policy = load_policy(ROOT / ".agents/carl/nixvibe-domain.md")

    def test_apply_fast_path_is_benchmark_release_ready(self) -> None:
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
                monotonic_clock=_StepClock(step_seconds=0.01),
            )

        readiness = result.artifact_summary["benchmark_release_readiness"]
        self.assertEqual(readiness["contract"], "benchmark-release-readiness/v1")
        self.assertTrue(readiness["ready"])
        self.assertEqual(readiness["failed_gate_ids"], ())

    def test_propose_path_is_blocked(self) -> None:
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
            monotonic_clock=_StepClock(step_seconds=0.01),
        )

        readiness = result.artifact_summary["benchmark_release_readiness"]
        self.assertFalse(readiness["ready"])
        self.assertIn("release-ready-base", readiness["failed_gate_ids"])

    def test_regression_path_is_blocked(self) -> None:
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
                monotonic_clock=_StepClock(step_seconds=60.0),
            )

        readiness = result.artifact_summary["benchmark_release_readiness"]
        self.assertFalse(readiness["ready"])
        self.assertIn("regression-clear", readiness["failed_gate_ids"])
        self.assertIn("baseline-candidate", readiness["failed_gate_ids"])

    def test_direct_helper_blocks_low_score(self) -> None:
        readiness = build_benchmark_release_readiness(
            release_readiness={"ready": True},
            outcome_scorecard={"scorecard_ready": True, "score_percent": 70},
            benchmark_baseline_snapshot={
                "baseline_recordable": True,
                "trend_bucket": "baseline-candidate",
            },
            benchmark_runner_report={"ready_to_execute": True},
            telemetry_regression={"regression_detected": False},
        )

        self.assertFalse(readiness["ready"])
        self.assertIn("outcome-score-threshold", readiness["failed_gate_ids"])


if __name__ == "__main__":
    unittest.main()
