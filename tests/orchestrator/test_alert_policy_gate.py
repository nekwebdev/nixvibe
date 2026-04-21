from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from nixvibe.orchestrator.alert_policy_gate import build_alert_policy_gate
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
        "task_scope": "alert-policy-gate",
        "status": "warning",
        "findings": [
            {
                "id": f"F-{agent_id}",
                "severity": "high",
                "summary": "Scoped finding",
                "evidence": [f"evidence/{agent_id}.nix"],
                "impact": "Alert policy gate coverage",
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


class TestAlertPolicyGate(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.policy = load_policy(ROOT / ".agents/carl/nixvibe-domain.md")

    def test_helper_open_gate_when_alert_clear(self) -> None:
        gate = build_alert_policy_gate(
            outcome_alert={"contract": "outcome-alert/v1", "alert_status": "none"},
            release_readiness={"contract": "release-readiness/v1", "ready": True},
            apply_safety_escalation={"tier": "none"},
        )

        self.assertEqual(gate["gate_status"], "open")
        self.assertEqual(gate["apply_gate"], "allow")
        self.assertEqual(gate["release_gate"], "allow")
        self.assertFalse(gate["requires_acknowledgement"])

    def test_helper_warn_gate_for_warning_alert(self) -> None:
        gate = build_alert_policy_gate(
            outcome_alert={"contract": "outcome-alert/v1", "alert_status": "warning"},
            release_readiness={"contract": "release-readiness/v1", "ready": True},
            apply_safety_escalation={"tier": "none"},
        )

        self.assertEqual(gate["gate_status"], "warn")
        self.assertEqual(gate["apply_gate"], "allow_with_warning")
        self.assertEqual(gate["release_gate"], "deny")
        self.assertIn("track-warning-alert", gate["policy_actions"])

    def test_helper_blocks_critical_alert(self) -> None:
        gate = build_alert_policy_gate(
            outcome_alert={"contract": "outcome-alert/v1", "alert_status": "critical"},
            release_readiness={"contract": "release-readiness/v1", "ready": True},
            apply_safety_escalation={"tier": "none"},
        )

        self.assertEqual(gate["gate_status"], "blocked")
        self.assertEqual(gate["apply_gate"], "deny")
        self.assertEqual(gate["release_gate"], "deny")

    def test_helper_blocks_when_contracts_missing(self) -> None:
        gate = build_alert_policy_gate(
            outcome_alert={"contract": "missing"},
            release_readiness={"contract": "missing"},
            apply_safety_escalation={},
        )

        self.assertEqual(gate["gate_status"], "blocked")
        self.assertFalse(gate["gate_ready"])
        self.assertIn("outcome-alert-contract", gate["failed_check_ids"])

    def test_pipeline_emits_alert_policy_gate_contract(self) -> None:
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

        gate = result.artifact_summary["alert_policy_gate"]
        self.assertEqual(gate["contract"], "alert-policy-gate/v1")
        self.assertEqual(gate["gate_status"], "warn")
        self.assertEqual(gate["apply_gate"], "allow_with_warning")
        self.assertEqual(gate["release_gate"], "deny")


if __name__ == "__main__":
    unittest.main()
