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
from nixvibe.orchestrator.v10_pathway_scaffold import build_v10_pathway_scaffold


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
        "task_scope": "v10-pathway-scaffold",
        "status": "warning",
        "findings": [
            {
                "id": f"F-{agent_id}",
                "severity": "high",
                "summary": "Scoped finding",
                "evidence": [f"evidence/{agent_id}.nix"],
                "impact": "v1.0 pathway scaffold coverage",
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


class TestV10PathwayScaffold(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.policy = load_policy(ROOT / ".agents/carl/nixvibe-domain.md")

    def test_helper_reports_ready_for_clear_transition(self) -> None:
        scaffold = build_v10_pathway_scaffold(
            v07_closeout_evidence={
                "contract": "v07-closeout-evidence/v1",
                "closeout_category": "ready",
            },
            governance_hardening_escalation={
                "contract": "governance-hardening-escalation/v1",
                "escalation_level": "none",
            },
            benchmark_release_readiness={
                "contract": "benchmark-release-readiness/v1",
                "ready": True,
            },
            release_policy_execution={
                "contract": "release-policy-execution/v1",
                "decision": "automated",
            },
        )

        self.assertEqual(scaffold["pathway_status"], "ready")
        self.assertEqual(scaffold["transition_gate"], "open")
        self.assertEqual(scaffold["blocker_count"], 0)

    def test_helper_reports_hold_for_manual_ack_transition(self) -> None:
        scaffold = build_v10_pathway_scaffold(
            v07_closeout_evidence={
                "contract": "v07-closeout-evidence/v1",
                "closeout_category": "hold",
            },
            governance_hardening_escalation={
                "contract": "governance-hardening-escalation/v1",
                "escalation_level": "review",
            },
            benchmark_release_readiness={
                "contract": "benchmark-release-readiness/v1",
                "ready": False,
            },
            release_policy_execution={
                "contract": "release-policy-execution/v1",
                "decision": "manual-ack",
            },
        )

        self.assertEqual(scaffold["pathway_status"], "hold")
        self.assertIn("release-policy:manual-ack", scaffold["blockers"])

    def test_helper_reports_blocked_for_critical_signals(self) -> None:
        scaffold = build_v10_pathway_scaffold(
            v07_closeout_evidence={
                "contract": "v07-closeout-evidence/v1",
                "closeout_category": "blocked",
            },
            governance_hardening_escalation={
                "contract": "governance-hardening-escalation/v1",
                "escalation_level": "critical",
            },
            benchmark_release_readiness={
                "contract": "benchmark-release-readiness/v1",
                "ready": False,
            },
            release_policy_execution={
                "contract": "release-policy-execution/v1",
                "decision": "blocked",
            },
        )

        self.assertEqual(scaffold["pathway_status"], "blocked")
        self.assertGreater(scaffold["blocker_count"], 0)

    def test_helper_reports_blocked_when_contracts_missing(self) -> None:
        scaffold = build_v10_pathway_scaffold(
            v07_closeout_evidence={"contract": "missing"},
            governance_hardening_escalation={"contract": "missing"},
            benchmark_release_readiness={"contract": "missing"},
            release_policy_execution={"contract": "missing"},
        )

        self.assertFalse(scaffold["scaffold_ready"])
        self.assertEqual(scaffold["pathway_status"], "blocked")
        self.assertIn("v07-closeout-evidence-contract", scaffold["failed_check_ids"])

    def test_pipeline_emits_v10_pathway_scaffold_contract(self) -> None:
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

        scaffold = result.artifact_summary["v10_pathway_scaffold"]
        self.assertEqual(scaffold["contract"], "v10-pathway-scaffold/v1")
        self.assertEqual(scaffold["pathway_status"], "hold")
        self.assertGreaterEqual(scaffold["phase_count"], 3)


if __name__ == "__main__":
    unittest.main()
