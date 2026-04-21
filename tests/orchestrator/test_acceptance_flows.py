from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from nixvibe.orchestrator.pipeline import run_pipeline
from nixvibe.orchestrator.policy_loader import load_policy
from nixvibe.orchestrator.types import Mode, OrchestrationRequest, OrchestrationResult, RepoContext, Route, SpecialistTask


def _payload(
    *,
    agent_id: str,
    target_tree: dict | None = None,
    patch_path: str | None = None,
) -> dict:
    artifacts: dict = {
        "notes": [f"note-{agent_id}"],
        "next_actions": [f"review-{agent_id}"],
    }
    if target_tree is not None:
        artifacts["target_tree"] = target_tree
    if patch_path is not None:
        artifacts["patches"] = [{"id": f"P-{agent_id}", "path": patch_path}]

    return {
        "agent_id": agent_id,
        "task_scope": "acceptance",
        "status": "warning",
        "findings": [
            {
                "id": f"F-{agent_id}",
                "severity": "high",
                "summary": "Scoped finding",
                "evidence": [f"evidence/{agent_id}.nix"],
                "impact": "Acceptance impact",
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
                "mitigation": "review patch set",
            }
        ],
        "artifacts": artifacts,
        "checks": {"schema_checked": True},
        "timestamp": "2026-04-19T00:00:00-10:00",
    }


class TestAcceptanceFlows(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.policy = load_policy(ROOT / ".agents/carl/nixvibe-domain.md")

    def test_init_journey_is_propose_by_default_with_expected_outputs(self) -> None:
        result = run_pipeline(
            request=OrchestrationRequest(
                user_input="I want a clean new NixOS scaffold.",
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

        self.assertEqual(result.route_decision.route, Route.INIT)
        self.assertEqual(result.selected_mode, Mode.PROPOSE)
        generated = {artifact.path for artifact in result.generated_artifacts}
        self.assertTrue({"flake.nix", "ARCHITECTURE.md", "NEXT_STEPS.md"}.issubset(generated))
        self._assert_output_contract(result)

    def test_audit_journey_defaults_to_propose_with_plan_tree_and_patch(self) -> None:
        patch_path = "patches/042-acceptance-refactor.patch"
        result = run_pipeline(
            request=OrchestrationRequest(
                user_input="Please audit and refactor my existing NixOS setup.",
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
                    lambda: _payload(
                        agent_id="audit",
                        target_tree={"modules": {"services": ["default.nix"]}},
                        patch_path=patch_path,
                    ),
                )
            ],
            policy=self.policy,
        )

        self.assertEqual(result.route_decision.route, Route.AUDIT)
        self.assertEqual(result.selected_mode, Mode.PROPOSE)
        generated = {artifact.path for artifact in result.generated_artifacts}
        self.assertIn("REFACTOR_PLAN.md", generated)
        self.assertIn("TARGET_TREE.md", generated)
        self.assertIn(patch_path, generated)
        self.assertFalse(result.written_artifact_paths)
        self._assert_output_contract(result)

    def test_apply_with_validation_success_writes_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "flake.nix").write_text("{ }")
            result = run_pipeline(
                request=OrchestrationRequest(
                    user_input="Build this scaffold and apply.",
                    requested_mode=Mode.APPLY,
                    explicit_apply_opt_in=True,
                ),
                context=RepoContext(
                    existing_config_present=False,
                    usable_nix_structure_present=False,
                    request_is_change=False,
                    repository_state="known",
                ),
                specialist_tasks=[SpecialistTask("architecture", "scope", lambda: _payload(agent_id="arch"))],
                policy=self.policy,
                workspace_root=tmp,
                validation_runner=lambda _command, _cwd: (0, "ok", ""),
            )

            self.assertEqual(result.selected_mode, Mode.APPLY)
            self.assertTrue(result.written_artifact_paths)
            self.assertEqual(result.proposed_artifacts, ())
            self.assertTrue(result.artifact_summary["validation"]["success"])
            self._assert_output_contract(result)

    def test_apply_with_validation_failure_forces_safe_propose_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "flake.nix").write_text("{ }")

            def _runner(command, _cwd):
                if command == ("nix", "flake", "check"):
                    return 1, "", "flake check failed"
                return 0, "", ""

            result = run_pipeline(
                request=OrchestrationRequest(
                    user_input="Build this scaffold and apply.",
                    requested_mode=Mode.APPLY,
                    explicit_apply_opt_in=True,
                ),
                context=RepoContext(
                    existing_config_present=False,
                    usable_nix_structure_present=False,
                    request_is_change=False,
                    repository_state="known",
                ),
                specialist_tasks=[SpecialistTask("architecture", "scope", lambda: _payload(agent_id="arch"))],
                policy=self.policy,
                workspace_root=tmp,
                validation_runner=_runner,
            )

            self.assertEqual(result.selected_mode, Mode.PROPOSE)
            self.assertFalse(result.written_artifact_paths)
            self.assertTrue(result.proposed_artifacts)
            self.assertIn("Validation failed", result.next_action)
            self.assertFalse(result.artifact_summary["validation"]["success"])
            self._assert_output_contract(result)

    def _assert_output_contract(self, result: OrchestrationResult) -> None:
        self.assertIn("mode", result.artifact_summary)
        self.assertIn("route", result.artifact_summary)
        self.assertIn("generated_files", result.artifact_summary)
        self.assertIn("run_manifest", result.artifact_summary)
        self.assertIn("run_telemetry", result.artifact_summary)
        self.assertIn("run_failure_classification", result.artifact_summary)
        self.assertIn("benchmark_baseline_report", result.artifact_summary)
        self.assertIn("telemetry_regression", result.artifact_summary)
        self.assertIn("benchmark_scenario_catalog", result.artifact_summary)
        self.assertIn("benchmark_runner_report", result.artifact_summary)
        self.assertIn("benchmark_baseline_snapshot", result.artifact_summary)
        self.assertIn("outcome_scorecard", result.artifact_summary)
        self.assertIn("benchmark_release_readiness", result.artifact_summary)
        self.assertIn("benchmark_trend_entry", result.artifact_summary)
        self.assertIn("benchmark_trend_history", result.artifact_summary)
        self.assertIn("benchmark_trend_delta", result.artifact_summary)
        self.assertIn("release_readiness", result.artifact_summary)
        self.assertIn("resume_checkpoint", result.artifact_summary)
        self.assertIn("retry_backoff_guardrails", result.artifact_summary)
        self.assertIn("policy_decision_explainability", result.artifact_summary)
        self.assertIn("controlled_override_workflow", result.artifact_summary)
        self.assertIn("operator_audit_trail", result.artifact_summary)
        self.assertIn("release_artifact_manifest", result.artifact_summary)
        self.assertIn("release_check_command", result.artifact_summary)
        self.assertTrue(result.next_action.strip())


if __name__ == "__main__":
    unittest.main()
