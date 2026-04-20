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
    severity: str = "high",
    reversible: bool = True,
    risk_severity: str = "medium",
    contradiction_key: str | None = None,
    summary: str = "Scoped finding",
    impact: str = "Operational impact",
) -> dict:
    finding: dict[str, object] = {
        "id": f"F-{agent_id}",
        "severity": severity,
        "summary": summary,
        "evidence": [f"evidence/{agent_id}.nix"],
        "impact": impact,
    }
    if contradiction_key is not None:
        finding["contradiction_key"] = contradiction_key

    return {
        "agent_id": agent_id,
        "task_scope": "e2e-operational-acceptance",
        "status": "warning",
        "findings": [finding],
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


class TestE2EOperationalAcceptance(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.policy = load_policy(ROOT / ".agents/carl/nixvibe-domain.md")

    def test_apply_success_path_is_release_ready(self) -> None:
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

        run_manifest = result.artifact_summary["run_manifest"]
        readiness = result.artifact_summary["release_readiness"]
        self.assertEqual(result.selected_mode, Mode.APPLY)
        self.assertEqual(run_manifest["modes"]["selected"], "apply")
        self.assertTrue(readiness["ready"])
        self.assertEqual(readiness["failed_gate_ids"], ())

    def test_high_risk_apply_path_is_blocked_for_release(self) -> None:
        result = run_pipeline(
            request=OrchestrationRequest(
                user_input="Apply this risky change now.",
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

        escalation = result.artifact_summary["apply_safety_escalation"]
        run_manifest = result.artifact_summary["run_manifest"]
        readiness = result.artifact_summary["release_readiness"]
        self.assertEqual(result.selected_mode, Mode.PROPOSE)
        self.assertEqual(escalation["reason"], "high_risk_mutation_guardrail")
        self.assertTrue(run_manifest["safety"]["guardrail_blocked_apply"])
        self.assertFalse(readiness["ready"])
        self.assertIn("mode-apply", readiness["failed_gate_ids"])
        self.assertIn("safety-clear", readiness["failed_gate_ids"])

    def test_validation_failure_path_reports_recovery_and_release_hold(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "flake.nix").write_text("{ }")

            def _runner(command, _cwd):
                if command == ("nix", "flake", "check"):
                    return 1, "", "flake check failed"
                return 0, "", ""

            result = run_pipeline(
                request=OrchestrationRequest(
                    user_input="Apply this now.",
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
                validation_runner=_runner,
            )

        guidance = result.artifact_summary["guidance"]
        recovery = result.artifact_summary["recovery_playbook"]
        readiness = result.artifact_summary["release_readiness"]
        self.assertEqual(result.selected_mode, Mode.PROPOSE)
        self.assertEqual(recovery["stage"], "validation-pre-write")
        self.assertEqual(guidance["remediation"]["category"], "validation-pre-write")
        self.assertFalse(readiness["ready"])
        self.assertIn("safety-clear", readiness["failed_gate_ids"])

    def test_critical_conflict_path_reports_release_hold(self) -> None:
        result = run_pipeline(
            request=OrchestrationRequest(
                user_input="Apply root SSH policy now.",
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
                    "audit-a",
                    "scope",
                    lambda: _payload(
                        agent_id="audit-a",
                        severity="critical",
                        summary="Enable root SSH login",
                        impact="Broad remote attack surface",
                        contradiction_key="root-access",
                    ),
                ),
                SpecialistTask(
                    "audit-b",
                    "scope",
                    lambda: _payload(
                        agent_id="audit-b",
                        severity="critical",
                        summary="Disable root SSH login",
                        impact="Removes direct privileged access",
                        contradiction_key="root-access",
                    ),
                ),
            ],
            policy=self.policy,
        )

        escalation = result.artifact_summary["apply_safety_escalation"]
        readiness = result.artifact_summary["release_readiness"]
        self.assertEqual(result.selected_mode, Mode.PROPOSE)
        self.assertEqual(escalation["reason"], "critical_conflict_forced_propose")
        self.assertFalse(readiness["ready"])
        self.assertIn("safety-clear", readiness["failed_gate_ids"])


if __name__ == "__main__":
    unittest.main()
