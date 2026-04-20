from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from nixvibe.orchestrator.pipeline import run_pipeline
from nixvibe.orchestrator.policy_loader import load_policy
from nixvibe.orchestrator.specialists import run_specialists
from nixvibe.orchestrator.types import (
    Mode,
    OrchestrationRequest,
    SpecialistDispatchContext,
    SpecialistExecutionOutcome,
    SpecialistTask,
    Route,
)
from nixvibe.orchestrator.workspace import build_repo_context


def _payload(*, agent_id: str) -> dict:
    return {
        "agent_id": agent_id,
        "task_scope": "dispatch-context",
        "status": "warning",
        "findings": [
            {
                "id": f"F-{agent_id}",
                "severity": "high",
                "summary": "Scoped finding",
                "evidence": [f"evidence/{agent_id}.nix"],
                "impact": "Test impact",
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
        "artifacts": {
            "notes": [f"note-{agent_id}"],
            "next_actions": [f"review-{agent_id}"],
        },
        "checks": {"schema_checked": True},
        "timestamp": "2026-04-19T00:00:00-10:00",
    }


def _dispatch_context() -> SpecialistDispatchContext:
    return SpecialistDispatchContext(
        requested_mode=None,
        resolved_route=Route.AUDIT,
        resolved_mode=Mode.PROPOSE,
        repository_state="known",
        existing_config_present=True,
        usable_nix_structure_present=True,
        request_is_change=True,
    )


class TestSpecialistDispatchContext(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.policy = load_policy(ROOT / ".agents/carl/nixvibe-domain.md")

    def test_run_specialists_passes_dispatch_context_to_context_runner(self) -> None:
        captured: dict[str, str] = {}

        def _runner(dispatch_context):
            captured["route"] = dispatch_context.resolved_route.value
            return {"agent_id": "audit"}

        tasks = [
            SpecialistTask(
                "audit",
                "scope",
                _runner,
                dispatch_context=_dispatch_context(),
            )
        ]
        results = run_specialists(tasks)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].outcome, SpecialistExecutionOutcome.OK)
        self.assertEqual(captured["route"], "audit")

    def test_run_specialists_keeps_backward_compat_for_zero_arg_runner(self) -> None:
        tasks = [
            SpecialistTask(
                "audit",
                "scope",
                lambda: {"agent_id": "audit"},
                dispatch_context=_dispatch_context(),
            )
        ]
        results = run_specialists(tasks)
        self.assertEqual(results[0].outcome, SpecialistExecutionOutcome.OK)

    def test_pipeline_wires_dispatch_context_and_summary(self) -> None:
        with tempfile.TemporaryDirectory() as workspace_tmp, tempfile.TemporaryDirectory() as reference_tmp:
            workspace_root = Path(workspace_tmp)
            reference_root = Path(reference_tmp)
            (workspace_root / "flake.nix").write_text("{ }")
            (workspace_root / "modules/services").mkdir(parents=True)
            (workspace_root / "modules/services/default.nix").write_text("{ ... }: { }")
            (reference_root / "flake.nix").write_text("# nix flake check\n")

            context = build_repo_context(
                workspace_root=workspace_root,
                reference_root=reference_root,
                max_entries=100,
            )
            captured: dict[str, object] = {}

            def _context_runner(dispatch_context):
                captured["route"] = dispatch_context.resolved_route.value
                captured["mode"] = dispatch_context.resolved_mode.value
                captured["has_adaptation"] = dispatch_context.reference_adaptation is not None
                return _payload(agent_id="audit")

            result = run_pipeline(
                request=OrchestrationRequest(user_input="Need help."),
                context=context,
                specialist_tasks=[SpecialistTask("audit", "scope", _context_runner)],
                policy=self.policy,
            )

            self.assertEqual(captured["route"], "audit")
            self.assertEqual(captured["mode"], "propose")
            self.assertTrue(captured["has_adaptation"])

            dispatch_summary = result.artifact_summary["specialist_dispatch"]
            self.assertEqual(dispatch_summary["route"], "audit")
            self.assertEqual(dispatch_summary["mode"], "propose")
            self.assertEqual(dispatch_summary["task_count"], 1)
            self.assertTrue(dispatch_summary["has_workspace_snapshot"])
            self.assertTrue(dispatch_summary["has_reference_adaptation"])


if __name__ == "__main__":
    unittest.main()
