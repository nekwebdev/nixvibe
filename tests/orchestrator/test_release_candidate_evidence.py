from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from nixvibe.orchestrator.pipeline import run_pipeline
from nixvibe.orchestrator.policy_loader import load_policy
from nixvibe.orchestrator.release_candidate_evidence import build_release_candidate_evidence
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
        "task_scope": "release-candidate-evidence",
        "status": "warning",
        "findings": [
            {
                "id": f"F-{agent_id}",
                "severity": "high",
                "summary": "Scoped finding",
                "evidence": [f"evidence/{agent_id}.nix"],
                "impact": "Release candidate evidence coverage",
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


class TestReleaseCandidateEvidence(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.policy = load_policy(ROOT / ".agents/carl/nixvibe-domain.md")

    def test_helper_reports_ready_when_release_and_alert_policy_clear(self) -> None:
        evidence = build_release_candidate_evidence(
            release_readiness={"contract": "release-readiness/v1", "ready": True},
            outcome_alert={"contract": "outcome-alert/v1", "alert_status": "none"},
            alert_policy_gate={"contract": "alert-policy-gate/v1", "gate_status": "open"},
        )

        self.assertEqual(evidence["readiness_category"], "ready")
        self.assertEqual(evidence["failed_item_count"], 0)

    def test_helper_reports_hold_for_warning_gate(self) -> None:
        evidence = build_release_candidate_evidence(
            release_readiness={"contract": "release-readiness/v1", "ready": True},
            outcome_alert={"contract": "outcome-alert/v1", "alert_status": "warning"},
            alert_policy_gate={"contract": "alert-policy-gate/v1", "gate_status": "warn"},
        )

        self.assertEqual(evidence["readiness_category"], "hold")
        self.assertIn("alert-clear", evidence["failed_item_ids"])

    def test_helper_reports_blocked_for_critical_gate(self) -> None:
        evidence = build_release_candidate_evidence(
            release_readiness={"contract": "release-readiness/v1", "ready": False},
            outcome_alert={"contract": "outcome-alert/v1", "alert_status": "critical"},
            alert_policy_gate={"contract": "alert-policy-gate/v1", "gate_status": "blocked"},
        )

        self.assertEqual(evidence["readiness_category"], "blocked")

    def test_helper_reports_blocked_when_contracts_missing(self) -> None:
        evidence = build_release_candidate_evidence(
            release_readiness={"contract": "missing"},
            outcome_alert={"contract": "missing"},
            alert_policy_gate={"contract": "missing"},
        )

        self.assertFalse(evidence["evidence_ready"])
        self.assertEqual(evidence["readiness_category"], "blocked")
        self.assertIn("release-readiness-contract", evidence["failed_check_ids"])

    def test_pipeline_emits_release_candidate_evidence_contract(self) -> None:
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

        evidence = result.artifact_summary["release_candidate_evidence"]
        self.assertEqual(evidence["contract"], "release-candidate-evidence/v1")
        self.assertEqual(evidence["readiness_category"], "hold")
        self.assertGreaterEqual(evidence["failed_item_count"], 1)


if __name__ == "__main__":
    unittest.main()
