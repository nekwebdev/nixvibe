from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from nixvibe.orchestrator.pipeline import run_pipeline
from nixvibe.orchestrator.policy_loader import load_policy
from nixvibe.orchestrator.runtime import default_runtime_contract
from nixvibe.orchestrator.types import Mode, OrchestrationRequest, RepoContext, Route, RuntimeSpecialistRole, SpecialistTask


def _payload(
    *,
    agent_id: str,
    severity: str = "medium",
    summary: str = "Scoped finding",
    impact: str = "Journey impact",
    contradiction_key: str | None = None,
) -> dict:
    finding: dict[str, object] = {
        "id": f"F-{agent_id}",
        "severity": severity,
        "summary": summary,
        "evidence": [f"evidence/{agent_id}.nix"],
        "impact": impact,
    }
    if contradiction_key:
        finding["contradiction_key"] = contradiction_key

    return {
        "agent_id": agent_id,
        "task_scope": "journey-regression",
        "status": "warning",
        "findings": [finding],
        "recommendations": [
            {
                "id": f"R-{agent_id}",
                "action": "Apply structured change",
                "priority": "next",
                "maps_to_findings": [f"F-{agent_id}"],
                "reversible": True,
            }
        ],
        "confidence": 0.85,
        "risks": [
            {
                "id": f"K-{agent_id}",
                "category": "regression",
                "severity": "medium",
                "mitigation": "review changes",
            }
        ],
        "artifacts": {
            "notes": [f"note-{agent_id}"],
            "next_actions": [f"review-{agent_id}"],
        },
        "checks": {"schema_checked": True},
        "timestamp": "2026-04-20T00:00:00-10:00",
    }


class TestGuidanceJourneyRegressions(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.policy = load_policy(ROOT / ".agents/carl/nixvibe-domain.md")

    def test_novice_init_journey_keeps_stepwise_guidance_and_safe_defaults(self) -> None:
        result = run_pipeline(
            request=OrchestrationRequest(
                user_input="My mom is a beginner, first time on NixOS. Help me start clearly.",
            ),
            context=RepoContext(
                existing_config_present=False,
                usable_nix_structure_present=False,
                request_is_change=False,
                repository_state="known",
            ),
            specialist_tasks=[SpecialistTask("architecture", "scope", lambda: _payload(agent_id="arch"))],
            policy=self.policy,
        )

        guidance = result.artifact_summary["guidance"]
        self.assertEqual(result.route_decision.route, Route.INIT)
        self.assertEqual(result.selected_mode, Mode.PROPOSE)
        self.assertEqual(guidance["skill_level"], "novice")
        self.assertEqual(guidance["response_style"], "stepwise")
        self.assertEqual(guidance["explanation_depth"], "expanded")
        self.assertTrue(guidance["prefer_fewer_files_initially"])
        self.assertEqual(guidance["scaffold_strategy"], "start-small-dendritic")
        self.assertFalse(guidance["remediation"]["required"])
        self.assertEqual(guidance["immediate_next_action"], result.next_action)

    def test_intermediate_audit_journey_preserves_structure_and_balanced_guidance(self) -> None:
        result = run_pipeline(
            request=OrchestrationRequest(
                user_input="Please review and improve my host configuration safely.",
            ),
            context=RepoContext(
                existing_config_present=True,
                usable_nix_structure_present=True,
                request_is_change=True,
                repository_state="known",
            ),
            specialist_tasks=[SpecialistTask("audit", "scope", lambda: _payload(agent_id="audit"))],
            policy=self.policy,
        )

        guidance = result.artifact_summary["guidance"]
        self.assertEqual(result.route_decision.route, Route.AUDIT)
        self.assertEqual(result.selected_mode, Mode.PROPOSE)
        self.assertEqual(guidance["skill_level"], "intermediate")
        self.assertEqual(guidance["response_style"], "balanced")
        self.assertEqual(guidance["explanation_depth"], "standard")
        self.assertTrue(guidance["preserve_existing_structure"])
        self.assertEqual(guidance["scaffold_strategy"], "preserve-and-extend")
        self.assertEqual(guidance["remediation"]["category"], "none")

    def test_expert_apply_runtime_journey_keeps_compact_guidance(self) -> None:
        contract = default_runtime_contract(Route.INIT)
        handlers = {
            RuntimeSpecialistRole.ARCHITECTURE: lambda _ctx: _payload(agent_id="architecture"),
            RuntimeSpecialistRole.MODULE: lambda _ctx: _payload(agent_id="module"),
            RuntimeSpecialistRole.VALIDATE: lambda _ctx: _payload(agent_id="validate"),
        }
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "flake.nix").write_text("{ }")
            result = run_pipeline(
                request=OrchestrationRequest(
                    user_input="I am an expert. Build a flake scaffold and apply now.",
                    requested_mode=Mode.APPLY,
                    explicit_apply_opt_in=True,
                ),
                context=RepoContext(
                    existing_config_present=False,
                    usable_nix_structure_present=False,
                    request_is_change=False,
                    repository_state="known",
                ),
                policy=self.policy,
                workspace_root=tmp,
                validation_runner=lambda _command, _cwd: (0, "ok", ""),
                runtime_contract=contract,
                runtime_handlers=handlers,
            )

        guidance = result.artifact_summary["guidance"]
        self.assertEqual(result.selected_mode, Mode.APPLY)
        self.assertEqual(guidance["skill_level"], "expert")
        self.assertEqual(guidance["response_style"], "concise")
        self.assertEqual(guidance["explanation_depth"], "compact")
        self.assertEqual(guidance["remediation"]["category"], "none")
        self.assertEqual(guidance["immediate_next_action"], result.next_action)

    def test_expert_conflict_journey_forces_propose_and_conflict_remediation(self) -> None:
        result = run_pipeline(
            request=OrchestrationRequest(
                user_input="I am an expert, apply root ssh policy now.",
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
                        impact="Prevents direct privileged remote access",
                        contradiction_key="root-access",
                    ),
                ),
            ],
            policy=self.policy,
        )

        guidance = result.artifact_summary["guidance"]
        self.assertEqual(result.selected_mode, Mode.PROPOSE)
        self.assertEqual(guidance["skill_level"], "expert")
        self.assertTrue(guidance["conflict_forced_propose"])
        self.assertEqual(guidance["remediation"]["category"], "conflict-critical")
        self.assertTrue(guidance["remediation"]["required"])


if __name__ == "__main__":
    unittest.main()
