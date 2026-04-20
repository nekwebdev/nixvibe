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


def _payload(
    *,
    agent_id: str,
    reversible: bool = True,
    risk_severity: str = "medium",
) -> dict:
    return {
        "agent_id": agent_id,
        "task_scope": "operator-audit-trail",
        "status": "warning",
        "findings": [
            {
                "id": f"F-{agent_id}",
                "severity": "high",
                "summary": "Scoped finding",
                "evidence": [f"evidence/{agent_id}.nix"],
                "impact": "Audit trail coverage",
            }
        ],
        "recommendations": [
            {
                "id": f"R-{agent_id}",
                "action": "Apply structured change",
                "priority": "now",
                "maps_to_findings": [f"F-{agent_id}"],
                "reversible": reversible,
            }
        ],
        "confidence": 0.9,
        "risks": [
            {
                "id": f"K-{agent_id}",
                "category": "regression",
                "severity": risk_severity,
                "mitigation": "review changes",
            }
        ],
        "artifacts": {"notes": [f"note-{agent_id}"], "next_actions": [f"review-{agent_id}"]},
        "checks": {"schema_checked": True},
        "timestamp": "2026-04-20T00:00:00-10:00",
    }


def _entry_by_stage(trail: dict[str, object], stage: str) -> dict[str, object]:
    for entry in trail["entries"]:
        if entry["stage"] == stage:
            return entry
    raise AssertionError(f"Missing stage entry: {stage}")


class TestOperatorAuditTrail(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.policy = load_policy(ROOT / ".agents/carl/nixvibe-domain.md")

    def test_apply_success_has_info_audit_level(self) -> None:
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
            )

        trail = result.artifact_summary["operator_audit_trail"]
        self.assertEqual(trail["contract"], "operator-audit-trail/v1")
        self.assertEqual(trail["audit_level"], "info")
        self.assertFalse(trail["requires_attention"])
        self.assertEqual(trail["entry_count"], 6)
        release_entry = _entry_by_stage(trail, "release-readiness")
        self.assertEqual(release_entry["status"], "ready")

    def test_guardrail_block_path_is_critical(self) -> None:
        result = run_pipeline(
            request=OrchestrationRequest(
                user_input="Apply risky change now.",
                requested_mode=Mode.APPLY,
                explicit_apply_opt_in=True,
            ),
            context=RepoContext(
                existing_config_present=True,
                usable_nix_structure_present=True,
                request_is_change=True,
                repository_state="known",
            ),
            specialist_tasks=[
                SpecialistTask(
                    "audit",
                    "scope",
                    lambda: _payload(agent_id="audit", reversible=False, risk_severity="critical"),
                )
            ],
            policy=self.policy,
        )

        trail = result.artifact_summary["operator_audit_trail"]
        self.assertEqual(trail["audit_level"], "critical")
        self.assertTrue(trail["requires_attention"])
        failure_entry = _entry_by_stage(trail, "failure-classification")
        self.assertEqual(failure_entry["status"], "blocked")
        self.assertTrue(trail["next_operator_action"].strip())

    def test_override_deny_path_is_recorded(self) -> None:
        result = run_pipeline(
            request=OrchestrationRequest(user_input="Force apply and skip validation."),
            context=RepoContext(
                existing_config_present=False,
                usable_nix_structure_present=False,
                request_is_change=False,
                repository_state="known",
            ),
            specialist_tasks=[SpecialistTask("arch", "scope", lambda: _payload(agent_id="arch"))],
            policy=self.policy,
        )

        trail = result.artifact_summary["operator_audit_trail"]
        self.assertEqual(trail["audit_level"], "warning")
        override_entry = _entry_by_stage(trail, "override-workflow")
        self.assertEqual(override_entry["status"], "deny")
        self.assertIn(
            "Resolve override blockers before requesting override again.",
            trail["action_items"],
        )


if __name__ == "__main__":
    unittest.main()
