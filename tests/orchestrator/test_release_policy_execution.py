from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from nixvibe.orchestrator.pipeline import run_pipeline
from nixvibe.orchestrator.policy_loader import load_policy
from nixvibe.orchestrator.release_policy_execution import build_release_policy_execution
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
        "task_scope": "release-policy-execution",
        "status": "warning",
        "findings": [
            {
                "id": f"F-{agent_id}",
                "severity": "high",
                "summary": "Scoped finding",
                "evidence": [f"evidence/{agent_id}.nix"],
                "impact": "Release policy execution coverage",
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


class TestReleasePolicyExecution(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.policy = load_policy(ROOT / ".agents/carl/nixvibe-domain.md")

    def test_helper_enables_automated_when_gate_allow_and_no_override(self) -> None:
        policy_execution = build_release_policy_execution(
            release_execution_gate={
                "contract": "release-execution-gate/v1",
                "decision": "allow",
            },
            controlled_override_workflow={
                "contract": "controlled-override-workflow/v1",
                "override_requested": False,
                "decision": "none",
                "allowed_overrides": (),
                "blocked_overrides": (),
            },
            release_check_command={"contract": "release-check-command/v1", "status": "passed"},
        )

        self.assertEqual(policy_execution["decision"], "automated")
        self.assertTrue(policy_execution["automated_release_enabled"])

    def test_helper_requires_manual_ack_when_gate_hold(self) -> None:
        policy_execution = build_release_policy_execution(
            release_execution_gate={
                "contract": "release-execution-gate/v1",
                "decision": "hold",
                "blockers": ("readiness-hold",),
            },
            controlled_override_workflow={
                "contract": "controlled-override-workflow/v1",
                "override_requested": False,
                "decision": "none",
                "allowed_overrides": (),
                "blocked_overrides": (),
            },
            release_check_command={"contract": "release-check-command/v1", "status": "pending"},
        )

        self.assertEqual(policy_execution["decision"], "manual-ack")
        self.assertTrue(policy_execution["requires_human_acknowledgement"])
        self.assertIn("release-check-pending", policy_execution["blockers"])

    def test_helper_requires_manual_ack_when_override_needs_confirmation(self) -> None:
        policy_execution = build_release_policy_execution(
            release_execution_gate={
                "contract": "release-execution-gate/v1",
                "decision": "allow",
                "blockers": (),
            },
            controlled_override_workflow={
                "contract": "controlled-override-workflow/v1",
                "override_requested": True,
                "decision": "allow-with-confirmation",
                "allowed_overrides": ("force-apply",),
                "blocked_overrides": (),
            },
            release_check_command={"contract": "release-check-command/v1", "status": "passed"},
        )

        self.assertEqual(policy_execution["decision"], "manual-ack")
        self.assertIn("require-human-acknowledgement", policy_execution["execution_actions"])

    def test_helper_blocks_when_gate_denies(self) -> None:
        policy_execution = build_release_policy_execution(
            release_execution_gate={
                "contract": "release-execution-gate/v1",
                "decision": "deny",
                "blockers": ("release-check-failed",),
            },
            controlled_override_workflow={
                "contract": "controlled-override-workflow/v1",
                "override_requested": False,
                "decision": "none",
                "allowed_overrides": (),
                "blocked_overrides": (),
            },
            release_check_command={"contract": "release-check-command/v1", "status": "failed"},
        )

        self.assertEqual(policy_execution["decision"], "blocked")
        self.assertIn("release-check-failed", policy_execution["blockers"])

    def test_helper_blocks_when_requested_override_is_denied(self) -> None:
        policy_execution = build_release_policy_execution(
            release_execution_gate={
                "contract": "release-execution-gate/v1",
                "decision": "allow",
                "blockers": (),
            },
            controlled_override_workflow={
                "contract": "controlled-override-workflow/v1",
                "override_requested": True,
                "decision": "deny",
                "allowed_overrides": (),
                "blocked_overrides": (
                    {
                        "id": "skip-validation",
                        "severity": "critical",
                        "reason": "Validation gates cannot be bypassed.",
                    },
                ),
            },
            release_check_command={"contract": "release-check-command/v1", "status": "passed"},
        )

        self.assertEqual(policy_execution["decision"], "blocked")
        self.assertIn("override-skip-validation", policy_execution["blockers"])

    def test_helper_blocks_when_contracts_missing(self) -> None:
        policy_execution = build_release_policy_execution(
            release_execution_gate={"contract": "missing"},
            controlled_override_workflow={"contract": "missing"},
            release_check_command={"contract": "missing"},
        )

        self.assertFalse(policy_execution["policy_ready"])
        self.assertEqual(policy_execution["decision"], "blocked")
        self.assertIn("release-execution-gate-contract", policy_execution["failed_check_ids"])

    def test_pipeline_emits_release_policy_execution_contract(self) -> None:
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

        policy_execution = result.artifact_summary["release_policy_execution"]
        self.assertEqual(policy_execution["contract"], "release-policy-execution/v1")
        self.assertEqual(policy_execution["decision"], "manual-ack")
        self.assertFalse(policy_execution["automated_release_enabled"])


if __name__ == "__main__":
    unittest.main()
