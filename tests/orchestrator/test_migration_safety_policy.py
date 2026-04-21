from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from nixvibe.orchestrator.migration_safety_policy import build_migration_safety_policy
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
        "task_scope": "migration-safety-policy",
        "status": "warning",
        "findings": [
            {
                "id": f"F-{agent_id}",
                "severity": "high",
                "summary": "Scoped finding",
                "evidence": [f"evidence/{agent_id}.nix"],
                "impact": "migration safety policy coverage",
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


class TestMigrationSafetyPolicy(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.policy = load_policy(ROOT / ".agents/carl/nixvibe-domain.md")

    def test_helper_reports_allow_for_safe_context(self) -> None:
        policy = build_migration_safety_policy(
            v10_compatibility_baseline={
                "contract": "v10-compatibility-baseline/v1",
                "compatibility_status": "ready",
            },
            apply_safety_escalation={"tier": "none"},
            controlled_override_workflow={
                "contract": "controlled-override-workflow/v1",
                "decision": "none",
            },
            release_policy_execution={
                "contract": "release-policy-execution/v1",
                "decision": "automated",
            },
        )

        self.assertEqual(policy["policy_decision"], "allow")
        self.assertTrue(policy["migration_ready"])

    def test_helper_reports_review_for_guarded_context(self) -> None:
        policy = build_migration_safety_policy(
            v10_compatibility_baseline={
                "contract": "v10-compatibility-baseline/v1",
                "compatibility_status": "hold",
            },
            apply_safety_escalation={"tier": "advisory"},
            controlled_override_workflow={
                "contract": "controlled-override-workflow/v1",
                "decision": "allow-with-confirmation",
            },
            release_policy_execution={
                "contract": "release-policy-execution/v1",
                "decision": "manual-ack",
            },
        )

        self.assertEqual(policy["policy_decision"], "review")
        self.assertIn("compatibility:hold", policy["blockers"])

    def test_helper_reports_block_for_blocked_context(self) -> None:
        policy = build_migration_safety_policy(
            v10_compatibility_baseline={
                "contract": "v10-compatibility-baseline/v1",
                "compatibility_status": "blocked",
            },
            apply_safety_escalation={"tier": "blocked"},
            controlled_override_workflow={
                "contract": "controlled-override-workflow/v1",
                "decision": "deny",
            },
            release_policy_execution={
                "contract": "release-policy-execution/v1",
                "decision": "blocked",
            },
        )

        self.assertEqual(policy["policy_decision"], "block")
        self.assertFalse(policy["migration_ready"])

    def test_helper_reports_block_when_contracts_missing(self) -> None:
        policy = build_migration_safety_policy(
            v10_compatibility_baseline={"contract": "missing"},
            apply_safety_escalation={"tier": "none"},
            controlled_override_workflow={"contract": "missing"},
            release_policy_execution={"contract": "missing"},
        )

        self.assertFalse(policy["policy_ready"])
        self.assertEqual(policy["policy_decision"], "block")
        self.assertIn("v10-compatibility-baseline-contract", policy["failed_check_ids"])

    def test_pipeline_emits_migration_safety_policy_contract(self) -> None:
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

        policy = result.artifact_summary["migration_safety_policy"]
        self.assertEqual(policy["contract"], "migration-safety-policy/v1")
        self.assertEqual(policy["policy_decision"], "review")
        self.assertGreaterEqual(policy["blocker_count"], 1)


if __name__ == "__main__":
    unittest.main()
