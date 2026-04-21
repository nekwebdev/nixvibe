from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from nixvibe.orchestrator.outcome_scorecard import build_outcome_scorecard
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
        "task_scope": "outcome-scorecard",
        "status": "warning",
        "findings": [
            {
                "id": f"F-{agent_id}",
                "severity": "high",
                "summary": "Scoped finding",
                "evidence": [f"evidence/{agent_id}.nix"],
                "impact": "Outcome scorecard coverage",
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


class TestOutcomeScorecard(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.policy = load_policy(ROOT / ".agents/carl/nixvibe-domain.md")

    def test_apply_fast_path_is_on_track(self) -> None:
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

        scorecard = result.artifact_summary["outcome_scorecard"]
        self.assertEqual(scorecard["contract"], "outcome-scorecard/v1")
        self.assertEqual(scorecard["overall_status"], "on_track")
        self.assertEqual(scorecard["achieved_score"], 100)
        self.assertEqual(scorecard["failed_metric_ids"], ())

    def test_propose_path_is_at_risk(self) -> None:
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

        scorecard = result.artifact_summary["outcome_scorecard"]
        self.assertEqual(scorecard["overall_status"], "at_risk")
        self.assertIn("existing-config-modularization", scorecard["failed_metric_ids"])
        self.assertIn("service-add-without-core-edits", scorecard["failed_metric_ids"])

    def test_slow_regression_path_is_at_risk(self) -> None:
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

        scorecard = result.artifact_summary["outcome_scorecard"]
        self.assertTrue(scorecard["regression_detected"])
        self.assertEqual(scorecard["overall_status"], "at_risk")

    def test_direct_helper_yields_watch_when_mid_score_without_regression(self) -> None:
        scorecard = build_outcome_scorecard(
            benchmark_scenario_catalog={
                "contract": "benchmark-scenario-catalog/v1",
                "scenarios": (
                    {"id": "init-apply-scaffold", "estimated_runtime_ms": 90_000},
                    {"id": "audit-apply-refactor", "estimated_runtime_ms": 120_000},
                ),
            },
            benchmark_runner_report={
                "contract": "benchmark-runner-report/v1",
                "ready_to_execute": True,
            },
            benchmark_baseline_snapshot={
                "contract": "benchmark-baseline-snapshot/v1",
                "baseline_recordable": False,
                "trend_bucket": "recovery-needed",
            },
            release_readiness={"contract": "release-readiness/v1", "ready": True},
            telemetry_regression={"contract": "telemetry-regression/v1", "regression_detected": False},
        )

        self.assertEqual(scorecard["overall_status"], "watch")
        self.assertEqual(scorecard["achieved_score"], 70)


if __name__ == "__main__":
    unittest.main()
