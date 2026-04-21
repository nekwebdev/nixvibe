from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from nixvibe.orchestrator.pipeline import run_pipeline
from nixvibe.orchestrator.policy_loader import load_policy
from nixvibe.orchestrator.release_execution_gate import build_release_execution_gate
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
        "task_scope": "release-execution-gate",
        "status": "warning",
        "findings": [
            {
                "id": f"F-{agent_id}",
                "severity": "high",
                "summary": "Scoped finding",
                "evidence": [f"evidence/{agent_id}.nix"],
                "impact": "Release execution gate coverage",
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


class TestReleaseExecutionGate(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.policy = load_policy(ROOT / ".agents/carl/nixvibe-domain.md")

    def test_helper_allows_execution_when_ready_and_passed(self) -> None:
        gate = build_release_execution_gate(
            v06_readiness_summary={"contract": "v06-readiness-summary/v1", "readiness_band": "ready"},
            release_check_command={"contract": "release-check-command/v1", "status": "passed"},
        )

        self.assertEqual(gate["decision"], "allow")
        self.assertTrue(gate["automated_execution_allowed"])

    def test_helper_holds_execution_when_readiness_hold(self) -> None:
        gate = build_release_execution_gate(
            v06_readiness_summary={"contract": "v06-readiness-summary/v1", "readiness_band": "hold"},
            release_check_command={"contract": "release-check-command/v1", "status": "pending"},
        )

        self.assertEqual(gate["decision"], "hold")
        self.assertIn("readiness-hold", gate["blockers"])

    def test_helper_denies_execution_when_blocked(self) -> None:
        gate = build_release_execution_gate(
            v06_readiness_summary={"contract": "v06-readiness-summary/v1", "readiness_band": "blocked"},
            release_check_command={"contract": "release-check-command/v1", "status": "failed"},
        )

        self.assertEqual(gate["decision"], "deny")
        self.assertIn("release-check-failed", gate["blockers"])

    def test_helper_denies_when_contracts_missing(self) -> None:
        gate = build_release_execution_gate(
            v06_readiness_summary={"contract": "missing"},
            release_check_command={"contract": "missing"},
        )

        self.assertFalse(gate["gate_ready"])
        self.assertEqual(gate["decision"], "deny")
        self.assertIn("v06-readiness-summary-contract", gate["failed_check_ids"])

    def test_pipeline_emits_release_execution_gate_contract(self) -> None:
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

        gate = result.artifact_summary["release_execution_gate"]
        self.assertEqual(gate["contract"], "release-execution-gate/v1")
        self.assertEqual(gate["decision"], "hold")
        self.assertFalse(gate["automated_execution_allowed"])


if __name__ == "__main__":
    unittest.main()
