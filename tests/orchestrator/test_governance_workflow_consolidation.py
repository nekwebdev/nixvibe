from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from nixvibe.orchestrator.governance_workflow_consolidation import (
    build_governance_workflow_consolidation,
)
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
        "task_scope": "governance-workflow-consolidation",
        "status": "warning",
        "findings": [
            {
                "id": f"F-{agent_id}",
                "severity": "high",
                "summary": "Scoped finding",
                "evidence": [f"evidence/{agent_id}.nix"],
                "impact": "governance workflow consolidation coverage",
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


class TestGovernanceWorkflowConsolidation(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.policy = load_policy(ROOT / ".agents/carl/nixvibe-domain.md")

    def test_helper_reports_consolidated_for_stable_signals(self) -> None:
        consolidation = build_governance_workflow_consolidation(
            operator_control_plane_summary={
                "contract": "operator-control-plane-summary/v1",
                "control_plane_status": "aligned",
            },
            governance_hardening_escalation={
                "contract": "governance-hardening-escalation/v1",
                "escalation_level": "none",
            },
            controlled_override_workflow={
                "contract": "controlled-override-workflow/v1",
                "decision": "none",
            },
            release_policy_execution={
                "contract": "release-policy-execution/v1",
                "decision": "automated",
            },
        )

        self.assertEqual(consolidation["consolidation_status"], "consolidated")
        self.assertTrue(consolidation["workflow_ready"])
        self.assertEqual(consolidation["blocker_count"], 0)

    def test_helper_reports_review_for_guarded_signals(self) -> None:
        consolidation = build_governance_workflow_consolidation(
            operator_control_plane_summary={
                "contract": "operator-control-plane-summary/v1",
                "control_plane_status": "attention",
            },
            governance_hardening_escalation={
                "contract": "governance-hardening-escalation/v1",
                "escalation_level": "escalate",
            },
            controlled_override_workflow={
                "contract": "controlled-override-workflow/v1",
                "decision": "allow-with-confirmation",
            },
            release_policy_execution={
                "contract": "release-policy-execution/v1",
                "decision": "manual-ack",
            },
        )

        self.assertEqual(consolidation["consolidation_status"], "review")
        self.assertIn("control-plane:attention", consolidation["blockers"])
        self.assertIn("release-policy:manual-ack", consolidation["blockers"])

    def test_helper_reports_blocked_for_critical_signals(self) -> None:
        consolidation = build_governance_workflow_consolidation(
            operator_control_plane_summary={
                "contract": "operator-control-plane-summary/v1",
                "control_plane_status": "blocked",
            },
            governance_hardening_escalation={
                "contract": "governance-hardening-escalation/v1",
                "escalation_level": "critical",
            },
            controlled_override_workflow={
                "contract": "controlled-override-workflow/v1",
                "decision": "deny",
            },
            release_policy_execution={
                "contract": "release-policy-execution/v1",
                "decision": "blocked",
            },
        )

        self.assertEqual(consolidation["consolidation_status"], "blocked")
        self.assertFalse(consolidation["workflow_ready"])
        self.assertIn("override:deny", consolidation["blockers"])

    def test_helper_reports_blocked_when_contracts_missing(self) -> None:
        consolidation = build_governance_workflow_consolidation(
            operator_control_plane_summary={"contract": "missing"},
            governance_hardening_escalation={"contract": "missing"},
            controlled_override_workflow={"contract": "missing"},
            release_policy_execution={"contract": "missing"},
        )

        self.assertFalse(consolidation["consolidation_ready"])
        self.assertEqual(consolidation["consolidation_status"], "blocked")
        self.assertIn("operator-control-plane-summary-contract", consolidation["failed_check_ids"])

    def test_pipeline_emits_governance_workflow_consolidation_contract(self) -> None:
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

        consolidation = result.artifact_summary["governance_workflow_consolidation"]
        self.assertEqual(consolidation["contract"], "governance-workflow-consolidation/v1")
        self.assertEqual(consolidation["consolidation_status"], "review")
        self.assertGreaterEqual(consolidation["blocker_count"], 1)


if __name__ == "__main__":
    unittest.main()
