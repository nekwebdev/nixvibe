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


def _payload(*, agent_id: str) -> dict:
    return {
        "agent_id": agent_id,
        "task_scope": "run-telemetry-contract",
        "status": "warning",
        "findings": [
            {
                "id": f"F-{agent_id}",
                "severity": "high",
                "summary": "Scoped finding",
                "evidence": [f"evidence/{agent_id}.nix"],
                "impact": "Telemetry contract coverage",
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


class TestRunTelemetryContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.policy = load_policy(ROOT / ".agents/carl/nixvibe-domain.md")

    def test_apply_success_emits_deterministic_timing_fields(self) -> None:
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

        telemetry = result.artifact_summary["run_telemetry"]
        manifest_timing = result.artifact_summary["run_manifest"]["timing"]

        self.assertEqual(telemetry["contract"], "run-telemetry/v1")
        self.assertEqual(telemetry["route"], "init")
        self.assertEqual(telemetry["mode"], "apply")
        self.assertEqual(telemetry["specialist_count"], 1)
        self.assertEqual(telemetry["validation_checkpoint_count"], 2)
        self.assertEqual(telemetry["specialist_execution_ms"], 10)
        self.assertEqual(telemetry["artifact_materialization_ms"], 10)
        self.assertEqual(telemetry["validation_pre_write_ms"], 10)
        self.assertEqual(telemetry["validation_post_write_ms"], 10)
        self.assertEqual(telemetry["validation_total_ms"], 20)
        self.assertEqual(telemetry["ledger_inspection_ms"], 10)
        self.assertEqual(telemetry["total_duration_ms"], 110)

        self.assertEqual(manifest_timing["total_duration_ms"], telemetry["total_duration_ms"])
        self.assertEqual(
            manifest_timing["specialist_execution_ms"],
            telemetry["specialist_execution_ms"],
        )
        self.assertEqual(manifest_timing["validation_total_ms"], telemetry["validation_total_ms"])

    def test_propose_path_reports_zero_validation_timing(self) -> None:
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

        telemetry = result.artifact_summary["run_telemetry"]
        self.assertEqual(result.selected_mode, Mode.PROPOSE)
        self.assertEqual(telemetry["validation_checkpoint_count"], 0)
        self.assertEqual(telemetry["validation_pre_write_ms"], 0)
        self.assertEqual(telemetry["validation_post_write_ms"], 0)
        self.assertEqual(telemetry["validation_total_ms"], 0)
        self.assertEqual(telemetry["total_duration_ms"], 70)


if __name__ == "__main__":
    unittest.main()
