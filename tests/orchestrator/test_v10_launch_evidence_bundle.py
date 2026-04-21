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
from nixvibe.orchestrator.v10_launch_evidence_bundle import build_v10_launch_evidence_bundle


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
        "task_scope": "v10-launch-evidence-bundle",
        "status": "warning",
        "findings": [
            {
                "id": f"F-{agent_id}",
                "severity": "high",
                "summary": "Scoped finding",
                "evidence": [f"evidence/{agent_id}.nix"],
                "impact": "v1 launch evidence coverage",
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


class TestV10LaunchEvidenceBundle(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.policy = load_policy(ROOT / ".agents/carl/nixvibe-domain.md")

    def test_helper_reports_ready_for_stable_launch_context(self) -> None:
        evidence = build_v10_launch_evidence_bundle(
            governance_workflow_consolidation={
                "contract": "governance-workflow-consolidation/v1",
                "consolidation_status": "consolidated",
            },
            operator_control_plane_summary={
                "contract": "operator-control-plane-summary/v1",
                "control_plane_status": "aligned",
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

        self.assertEqual(evidence["evidence_status"], "ready")
        self.assertTrue(evidence["launch_ready"])
        self.assertEqual(evidence["blocker_count"], 0)

    def test_helper_reports_hold_for_guarded_launch_context(self) -> None:
        evidence = build_v10_launch_evidence_bundle(
            governance_workflow_consolidation={
                "contract": "governance-workflow-consolidation/v1",
                "consolidation_status": "review",
            },
            operator_control_plane_summary={
                "contract": "operator-control-plane-summary/v1",
                "control_plane_status": "attention",
            },
            benchmark_release_readiness={
                "contract": "benchmark-release-readiness/v1",
                "ready": True,
            },
            release_policy_execution={
                "contract": "release-policy-execution/v1",
                "decision": "manual-ack",
            },
        )

        self.assertEqual(evidence["evidence_status"], "hold")
        self.assertIn("consolidation:review", evidence["blockers"])
        self.assertIn("release-policy:manual-ack", evidence["blockers"])

    def test_helper_reports_blocked_for_critical_launch_context(self) -> None:
        evidence = build_v10_launch_evidence_bundle(
            governance_workflow_consolidation={
                "contract": "governance-workflow-consolidation/v1",
                "consolidation_status": "blocked",
            },
            operator_control_plane_summary={
                "contract": "operator-control-plane-summary/v1",
                "control_plane_status": "blocked",
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

        self.assertEqual(evidence["evidence_status"], "blocked")
        self.assertFalse(evidence["launch_ready"])
        self.assertIn("benchmark-ready:false", evidence["blockers"])

    def test_helper_reports_blocked_when_contracts_missing(self) -> None:
        evidence = build_v10_launch_evidence_bundle(
            governance_workflow_consolidation={"contract": "missing"},
            operator_control_plane_summary={"contract": "missing"},
            benchmark_release_readiness={"contract": "missing"},
            release_policy_execution={"contract": "missing"},
        )

        self.assertFalse(evidence["evidence_ready"])
        self.assertEqual(evidence["evidence_status"], "blocked")
        self.assertIn("governance-workflow-consolidation-contract", evidence["failed_check_ids"])

    def test_pipeline_emits_v10_launch_evidence_bundle_contract(self) -> None:
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

        evidence = result.artifact_summary["v10_launch_evidence_bundle"]
        self.assertEqual(evidence["contract"], "v10-launch-evidence-bundle/v1")
        self.assertEqual(evidence["evidence_status"], "hold")
        self.assertGreaterEqual(evidence["blocker_count"], 1)


if __name__ == "__main__":
    unittest.main()
