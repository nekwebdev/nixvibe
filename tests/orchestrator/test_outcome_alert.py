from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from nixvibe.orchestrator.outcome_alert import build_outcome_alert
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


def _payload(*, agent_id: str) -> dict[str, object]:
    return {
        "agent_id": agent_id,
        "task_scope": "outcome-alert",
        "status": "warning",
        "findings": [
            {
                "id": f"F-{agent_id}",
                "severity": "high",
                "summary": "Scoped finding",
                "evidence": [f"evidence/{agent_id}.nix"],
                "impact": "Outcome alert coverage",
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
        "timestamp": "2026-04-21T00:00:00-10:00",
    }


class TestOutcomeAlert(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.policy = load_policy(ROOT / ".agents/carl/nixvibe-domain.md")

    def test_helper_reports_none_for_healthy_signals(self) -> None:
        alert = build_outcome_alert(
            benchmark_trend_entry={
                "contract": "benchmark-trend-entry/v1",
                "trend_status": "improving_candidate",
                "benchmark_release_ready": True,
            },
            benchmark_trend_history={"contract": "benchmark-trend-history/v1", "history_status": "advanced"},
            benchmark_trend_delta={"contract": "benchmark-trend-delta/v1", "delta_status": "improvement"},
        )

        self.assertEqual(alert["alert_status"], "none")
        self.assertEqual(alert["severity"], "info")
        self.assertFalse(alert["requires_operator_attention"])

    def test_helper_reports_warning_for_no_baseline(self) -> None:
        alert = build_outcome_alert(
            benchmark_trend_entry={
                "contract": "benchmark-trend-entry/v1",
                "trend_status": "stable_watch",
                "benchmark_release_ready": False,
            },
            benchmark_trend_history={"contract": "benchmark-trend-history/v1", "history_status": "seeded"},
            benchmark_trend_delta={"contract": "benchmark-trend-delta/v1", "delta_status": "no_baseline"},
        )

        self.assertEqual(alert["alert_status"], "warning")
        self.assertEqual(alert["severity"], "warning")
        self.assertIn("warning:no-baseline", alert["trigger_ids"])

    def test_helper_reports_critical_for_regression(self) -> None:
        alert = build_outcome_alert(
            benchmark_trend_entry={
                "contract": "benchmark-trend-entry/v1",
                "trend_status": "degradation_alert",
                "benchmark_release_ready": False,
            },
            benchmark_trend_history={"contract": "benchmark-trend-history/v1", "history_status": "advanced"},
            benchmark_trend_delta={"contract": "benchmark-trend-delta/v1", "delta_status": "regression"},
        )

        self.assertEqual(alert["alert_status"], "critical")
        self.assertEqual(alert["severity"], "critical")
        self.assertIn("critical:delta-regression", alert["trigger_ids"])

    def test_helper_reports_blocked_when_contracts_missing(self) -> None:
        alert = build_outcome_alert(
            benchmark_trend_entry={"contract": "missing"},
            benchmark_trend_history={"contract": "missing"},
            benchmark_trend_delta={"contract": "missing"},
        )

        self.assertEqual(alert["alert_status"], "blocked")
        self.assertFalse(alert["alert_ready"])
        self.assertIn("trend-entry-contract", alert["failed_check_ids"])

    def test_pipeline_emits_outcome_alert_contract(self) -> None:
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

        alert = result.artifact_summary["outcome_alert"]
        self.assertEqual(alert["contract"], "outcome-alert/v1")
        self.assertEqual(alert["alert_status"], "warning")
        self.assertTrue(alert["requires_operator_attention"])


if __name__ == "__main__":
    unittest.main()
