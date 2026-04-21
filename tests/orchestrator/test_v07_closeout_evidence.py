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
from nixvibe.orchestrator.v07_closeout_evidence import build_v07_closeout_evidence


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
        "task_scope": "v07-closeout-evidence",
        "status": "warning",
        "findings": [
            {
                "id": f"F-{agent_id}",
                "severity": "high",
                "summary": "Scoped finding",
                "evidence": [f"evidence/{agent_id}.nix"],
                "impact": "v0.7 closeout evidence coverage",
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


class TestV07CloseoutEvidence(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.policy = load_policy(ROOT / ".agents/carl/nixvibe-domain.md")

    def test_helper_reports_ready_for_stable_governance(self) -> None:
        evidence = build_v07_closeout_evidence(
            governance_hardening_escalation={
                "contract": "governance-hardening-escalation/v1",
                "escalation_level": "none",
                "blockers": (),
            },
            operator_observability_digest={
                "contract": "operator-observability-digest/v1",
                "observability_band": "healthy",
            },
            release_policy_execution={
                "contract": "release-policy-execution/v1",
                "decision": "automated",
                "blockers": (),
            },
        )

        self.assertEqual(evidence["closeout_category"], "ready")
        self.assertEqual(evidence["blocker_count"], 0)

    def test_helper_reports_hold_for_attention_governance(self) -> None:
        evidence = build_v07_closeout_evidence(
            governance_hardening_escalation={
                "contract": "governance-hardening-escalation/v1",
                "escalation_level": "escalate",
                "blockers": ("Review warning signal.",),
            },
            operator_observability_digest={
                "contract": "operator-observability-digest/v1",
                "observability_band": "attention",
            },
            release_policy_execution={
                "contract": "release-policy-execution/v1",
                "decision": "manual-ack",
                "blockers": ("readiness-hold",),
            },
        )

        self.assertEqual(evidence["closeout_category"], "hold")
        self.assertIn("observability:attention", evidence["blockers"])

    def test_helper_reports_blocked_for_critical_governance(self) -> None:
        evidence = build_v07_closeout_evidence(
            governance_hardening_escalation={
                "contract": "governance-hardening-escalation/v1",
                "escalation_level": "critical",
                "blockers": ("Critical blocker",),
            },
            operator_observability_digest={
                "contract": "operator-observability-digest/v1",
                "observability_band": "critical",
            },
            release_policy_execution={
                "contract": "release-policy-execution/v1",
                "decision": "blocked",
                "blockers": ("override-skip-validation",),
            },
        )

        self.assertEqual(evidence["closeout_category"], "blocked")
        self.assertGreater(evidence["blocker_count"], 0)

    def test_helper_reports_blocked_when_contracts_missing(self) -> None:
        evidence = build_v07_closeout_evidence(
            governance_hardening_escalation={"contract": "missing"},
            operator_observability_digest={"contract": "missing"},
            release_policy_execution={"contract": "missing"},
        )

        self.assertFalse(evidence["evidence_ready"])
        self.assertEqual(evidence["closeout_category"], "blocked")
        self.assertIn("governance-hardening-escalation-contract", evidence["failed_check_ids"])

    def test_pipeline_emits_v07_closeout_evidence_contract(self) -> None:
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

        evidence = result.artifact_summary["v07_closeout_evidence"]
        self.assertEqual(evidence["contract"], "v07-closeout-evidence/v1")
        self.assertEqual(evidence["closeout_category"], "hold")
        self.assertGreaterEqual(evidence["blocker_count"], 1)


if __name__ == "__main__":
    unittest.main()
