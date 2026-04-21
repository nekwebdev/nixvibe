from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from nixvibe.orchestrator.benchmark_snapshot import build_benchmark_baseline_snapshot
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
        "task_scope": "benchmark-baseline-snapshot",
        "status": "warning",
        "findings": [
            {
                "id": f"F-{agent_id}",
                "severity": "high",
                "summary": "Scoped finding",
                "evidence": [f"evidence/{agent_id}.nix"],
                "impact": "Benchmark baseline snapshot coverage",
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


class TestBenchmarkBaselineSnapshot(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.policy = load_policy(ROOT / ".agents/carl/nixvibe-domain.md")

    def test_apply_fast_path_is_recordable_baseline_candidate(self) -> None:
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

        snapshot = result.artifact_summary["benchmark_baseline_snapshot"]
        self.assertEqual(snapshot["contract"], "benchmark-baseline-snapshot/v1")
        self.assertTrue(snapshot["snapshot_ready"])
        self.assertTrue(snapshot["baseline_recordable"])
        self.assertEqual(snapshot["trend_bucket"], "baseline-candidate")
        self.assertEqual(snapshot["failed_check_ids"], ())

    def test_propose_path_snapshots_recovery_bucket(self) -> None:
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

        snapshot = result.artifact_summary["benchmark_baseline_snapshot"]
        self.assertTrue(snapshot["snapshot_ready"])
        self.assertFalse(snapshot["baseline_recordable"])
        self.assertEqual(snapshot["run_mode"], "recovery")
        self.assertEqual(snapshot["trend_bucket"], "recovery-needed")

    def test_slow_path_snapshots_regression_bucket(self) -> None:
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

        snapshot = result.artifact_summary["benchmark_baseline_snapshot"]
        self.assertTrue(snapshot["snapshot_ready"])
        self.assertTrue(snapshot["regression_detected"])
        self.assertEqual(snapshot["run_mode"], "regression")
        self.assertEqual(snapshot["trend_bucket"], "regression-investigate")

    def test_direct_helper_flags_regression_check_mismatch(self) -> None:
        snapshot = build_benchmark_baseline_snapshot(
            run_manifest={"route": "init", "modes": {"selected": "apply"}},
            run_telemetry={"contract": "run-telemetry/v1", "route": "init", "total_duration_ms": 110},
            benchmark_baseline_report={
                "contract": "benchmark-baseline-report/v1",
                "benchmark_id": "bm-test",
                "baseline_eligible": True,
            },
            telemetry_regression={
                "contract": "telemetry-regression/v1",
                "status": "regression",
                "regression_detected": False,
            },
            benchmark_scenario_catalog={"contract": "benchmark-scenario-catalog/v1"},
            benchmark_runner_report={
                "contract": "benchmark-runner-report/v1",
                "run_mode": "baseline",
                "ready_to_execute": False,
                "planned_scenario_ids": (),
            },
        )

        self.assertFalse(snapshot["snapshot_ready"])
        self.assertIn("regression-status-consistency", snapshot["failed_check_ids"])
        self.assertIn("runner-ready", snapshot["failed_check_ids"])


if __name__ == "__main__":
    unittest.main()
