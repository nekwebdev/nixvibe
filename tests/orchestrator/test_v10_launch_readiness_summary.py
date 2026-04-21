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
from nixvibe.orchestrator.v10_launch_readiness_summary import build_v10_launch_readiness_summary


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
        "task_scope": "v10-launch-readiness-summary",
        "status": "warning",
        "findings": [
            {
                "id": f"F-{agent_id}",
                "severity": "high",
                "summary": "Scoped finding",
                "evidence": [f"evidence/{agent_id}.nix"],
                "impact": "v1 launch readiness summary coverage",
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


class TestV10LaunchReadinessSummary(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.policy = load_policy(ROOT / ".agents/carl/nixvibe-domain.md")

    def test_helper_reports_ready_for_stable_launch_context(self) -> None:
        summary = build_v10_launch_readiness_summary(
            v10_launch_evidence_bundle={
                "contract": "v10-launch-evidence-bundle/v1",
                "evidence_status": "ready",
            },
            release_readiness={
                "contract": "release-readiness/v1",
                "ready": True,
            },
            benchmark_release_readiness={
                "contract": "benchmark-release-readiness/v1",
                "ready": True,
            },
            migration_safety_policy={
                "contract": "migration-safety-policy/v1",
                "policy_decision": "allow",
            },
        )

        self.assertEqual(summary["readiness_status"], "ready")
        self.assertTrue(summary["ga_ready"])
        self.assertEqual(summary["blocker_count"], 0)

    def test_helper_reports_hold_for_guarded_launch_context(self) -> None:
        summary = build_v10_launch_readiness_summary(
            v10_launch_evidence_bundle={
                "contract": "v10-launch-evidence-bundle/v1",
                "evidence_status": "hold",
            },
            release_readiness={
                "contract": "release-readiness/v1",
                "ready": True,
            },
            benchmark_release_readiness={
                "contract": "benchmark-release-readiness/v1",
                "ready": True,
            },
            migration_safety_policy={
                "contract": "migration-safety-policy/v1",
                "policy_decision": "review",
            },
        )

        self.assertEqual(summary["readiness_status"], "hold")
        self.assertIn("evidence:hold", summary["blockers"])
        self.assertIn("migration:review", summary["blockers"])

    def test_helper_reports_blocked_for_critical_launch_context(self) -> None:
        summary = build_v10_launch_readiness_summary(
            v10_launch_evidence_bundle={
                "contract": "v10-launch-evidence-bundle/v1",
                "evidence_status": "blocked",
            },
            release_readiness={
                "contract": "release-readiness/v1",
                "ready": False,
            },
            benchmark_release_readiness={
                "contract": "benchmark-release-readiness/v1",
                "ready": False,
            },
            migration_safety_policy={
                "contract": "migration-safety-policy/v1",
                "policy_decision": "block",
            },
        )

        self.assertEqual(summary["readiness_status"], "blocked")
        self.assertFalse(summary["ga_ready"])
        self.assertIn("release-ready:false", summary["blockers"])

    def test_helper_reports_blocked_when_contracts_missing(self) -> None:
        summary = build_v10_launch_readiness_summary(
            v10_launch_evidence_bundle={"contract": "missing"},
            release_readiness={"contract": "missing"},
            benchmark_release_readiness={"contract": "missing"},
            migration_safety_policy={"contract": "missing"},
        )

        self.assertFalse(summary["summary_ready"])
        self.assertEqual(summary["readiness_status"], "blocked")
        self.assertIn("v10-launch-evidence-bundle-contract", summary["failed_check_ids"])

    def test_pipeline_emits_v10_launch_readiness_summary_contract(self) -> None:
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

        summary = result.artifact_summary["v10_launch_readiness_summary"]
        self.assertEqual(summary["contract"], "v10-launch-readiness-summary/v1")
        self.assertEqual(summary["readiness_status"], "hold")
        self.assertGreaterEqual(summary["blocker_count"], 1)


if __name__ == "__main__":
    unittest.main()
