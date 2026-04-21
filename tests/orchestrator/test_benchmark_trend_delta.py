from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from nixvibe.orchestrator.benchmark_trend_delta import build_benchmark_trend_delta
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
        "task_scope": "benchmark-trend-delta",
        "status": "warning",
        "findings": [
            {
                "id": f"F-{agent_id}",
                "severity": "high",
                "summary": "Scoped finding",
                "evidence": [f"evidence/{agent_id}.nix"],
                "impact": "Benchmark trend delta coverage",
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


class TestBenchmarkTrendDelta(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.policy = load_policy(ROOT / ".agents/carl/nixvibe-domain.md")

    def test_pipeline_without_previous_emits_no_baseline_delta(self) -> None:
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

        delta = result.artifact_summary["benchmark_trend_delta"]
        self.assertEqual(delta["contract"], "benchmark-trend-delta/v1")
        self.assertTrue(delta["delta_ready"])
        self.assertEqual(delta["delta_status"], "no_baseline")
        self.assertFalse(delta["has_previous"])

    def test_direct_helper_reports_improvement(self) -> None:
        delta = build_benchmark_trend_delta(
            benchmark_trend_entry={
                "contract": "benchmark-trend-entry/v1",
                "trend_key": "trend-current",
                "trend_status": "improving_candidate",
                "outcome_score_percent": 95,
                "timing": {"total_duration_ms": 900},
            },
            previous_benchmark_trend_entry={
                "contract": "benchmark-trend-entry/v1",
                "trend_key": "trend-previous",
                "trend_status": "stable_watch",
                "outcome_score_percent": 80,
                "timing": {"total_duration_ms": 1_500},
            },
        )
        self.assertEqual(delta["delta_status"], "improvement")
        self.assertEqual(delta["score_delta"], 15)
        self.assertEqual(delta["duration_delta_ms"], -600)

    def test_direct_helper_reports_regression(self) -> None:
        delta = build_benchmark_trend_delta(
            benchmark_trend_entry={
                "contract": "benchmark-trend-entry/v1",
                "trend_key": "trend-current",
                "trend_status": "degradation_alert",
                "outcome_score_percent": 60,
                "timing": {"total_duration_ms": 4_000},
            },
            previous_benchmark_trend_entry={
                "contract": "benchmark-trend-entry/v1",
                "trend_key": "trend-previous",
                "trend_status": "improving_candidate",
                "outcome_score_percent": 90,
                "timing": {"total_duration_ms": 1_000},
            },
        )
        self.assertEqual(delta["delta_status"], "regression")
        self.assertEqual(delta["score_delta"], -30)
        self.assertEqual(delta["duration_delta_ms"], 3000)

    def test_direct_helper_reports_blocked_when_contract_missing(self) -> None:
        delta = build_benchmark_trend_delta(
            benchmark_trend_entry={"contract": "missing"},
            previous_benchmark_trend_entry={"contract": "missing", "trend_key": "trend-previous"},
        )
        self.assertFalse(delta["delta_ready"])
        self.assertEqual(delta["delta_status"], "blocked")
        self.assertIn("current-trend-contract", delta["failed_check_ids"])


if __name__ == "__main__":
    unittest.main()
