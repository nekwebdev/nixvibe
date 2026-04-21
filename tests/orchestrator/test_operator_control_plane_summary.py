from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from nixvibe.orchestrator.operator_control_plane_summary import build_operator_control_plane_summary
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
        "task_scope": "operator-control-plane-summary",
        "status": "warning",
        "findings": [
            {
                "id": f"F-{agent_id}",
                "severity": "high",
                "summary": "Scoped finding",
                "evidence": [f"evidence/{agent_id}.nix"],
                "impact": "operator control-plane summary coverage",
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


class TestOperatorControlPlaneSummary(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.policy = load_policy(ROOT / ".agents/carl/nixvibe-domain.md")

    def test_helper_reports_aligned_for_open_governance_context(self) -> None:
        summary = build_operator_control_plane_summary(
            migration_safety_policy={
                "contract": "migration-safety-policy/v1",
                "policy_decision": "allow",
            },
            governance_hardening_escalation={
                "contract": "governance-hardening-escalation/v1",
                "escalation_level": "none",
            },
            operator_audit_trail={
                "contract": "operator-audit-trail/v1",
                "audit_level": "info",
            },
            policy_decision_explainability={
                "contract": "policy-decision-explainability/v1",
                "blocked_stages": (),
            },
        )

        self.assertTrue(summary["summary_ready"])
        self.assertEqual(summary["control_plane_status"], "aligned")
        self.assertEqual(summary["blocker_count"], 0)

    def test_helper_reports_attention_for_guarded_context(self) -> None:
        summary = build_operator_control_plane_summary(
            migration_safety_policy={
                "contract": "migration-safety-policy/v1",
                "policy_decision": "review",
            },
            governance_hardening_escalation={
                "contract": "governance-hardening-escalation/v1",
                "escalation_level": "escalate",
            },
            operator_audit_trail={
                "contract": "operator-audit-trail/v1",
                "audit_level": "warning",
            },
            policy_decision_explainability={
                "contract": "policy-decision-explainability/v1",
                "blocked_stages": ("mutation-guardrails",),
            },
        )

        self.assertEqual(summary["control_plane_status"], "attention")
        self.assertIn("migration:review", summary["blockers"])
        self.assertIn("governance:escalate", summary["blockers"])
        self.assertIn("audit:warning", summary["blockers"])

    def test_helper_reports_blocked_for_critical_context(self) -> None:
        summary = build_operator_control_plane_summary(
            migration_safety_policy={
                "contract": "migration-safety-policy/v1",
                "policy_decision": "block",
            },
            governance_hardening_escalation={
                "contract": "governance-hardening-escalation/v1",
                "escalation_level": "critical",
            },
            operator_audit_trail={
                "contract": "operator-audit-trail/v1",
                "audit_level": "critical",
            },
            policy_decision_explainability={
                "contract": "policy-decision-explainability/v1",
                "blocked_stages": ("release-readiness",),
            },
        )

        self.assertEqual(summary["control_plane_status"], "blocked")
        self.assertIn("migration:block", summary["blockers"])
        self.assertIn("governance:critical", summary["blockers"])

    def test_helper_reports_blocked_when_contracts_missing(self) -> None:
        summary = build_operator_control_plane_summary(
            migration_safety_policy={"contract": "missing"},
            governance_hardening_escalation={"contract": "missing"},
            operator_audit_trail={"contract": "missing"},
            policy_decision_explainability={"contract": "missing"},
        )

        self.assertFalse(summary["summary_ready"])
        self.assertEqual(summary["control_plane_status"], "blocked")
        self.assertIn("migration-safety-policy-contract", summary["failed_check_ids"])

    def test_pipeline_emits_operator_control_plane_summary_contract(self) -> None:
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

        summary = result.artifact_summary["operator_control_plane_summary"]
        self.assertEqual(summary["contract"], "operator-control-plane-summary/v1")
        self.assertEqual(summary["control_plane_status"], "attention")
        self.assertGreaterEqual(summary["blocker_count"], 1)


if __name__ == "__main__":
    unittest.main()
