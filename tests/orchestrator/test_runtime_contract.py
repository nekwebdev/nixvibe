from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from nixvibe.orchestrator.pipeline import OrchestrationPipelineError, run_pipeline
from nixvibe.orchestrator.policy_loader import load_policy
from nixvibe.orchestrator.runtime import (
    RuntimeSpecialistContractError,
    default_runtime_contract,
    plan_runtime_specialists,
)
from nixvibe.orchestrator.types import (
    Mode,
    OrchestrationRequest,
    RepoContext,
    Route,
    RuntimeSpecialistContract,
    RuntimeSpecialistRole,
    RuntimeSpecialistSpec,
    SpecialistDispatchContext,
)


def _payload(agent_id: str) -> dict:
    return {
        "agent_id": agent_id,
        "task_scope": "runtime-contract",
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
        "artifacts": {"notes": [f"note-{agent_id}"], "next_actions": [f"review-{agent_id}"]},
        "checks": {"schema_checked": True},
        "timestamp": "2026-04-19T00:00:00-10:00",
    }


def _dispatch_context(route: Route = Route.AUDIT) -> SpecialistDispatchContext:
    return SpecialistDispatchContext(
        requested_mode=None,
        resolved_route=route,
        resolved_mode=Mode.PROPOSE,
        repository_state="known",
        existing_config_present=True if route is Route.AUDIT else False,
        usable_nix_structure_present=True if route is Route.AUDIT else False,
        request_is_change=True if route is Route.AUDIT else False,
    )


class TestRuntimeContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.policy = load_policy(ROOT / ".agents/carl/nixvibe-domain.md")

    def test_default_runtime_contract_has_deterministic_roles(self) -> None:
        contract = default_runtime_contract(Route.AUDIT)
        self.assertEqual(contract.name, "audit-default")
        self.assertEqual(
            tuple(spec.role for spec in contract.specialists),
            (
                RuntimeSpecialistRole.ARCHITECTURE,
                RuntimeSpecialistRole.AUDIT,
                RuntimeSpecialistRole.VALIDATE,
                RuntimeSpecialistRole.EXPLAIN,
            ),
        )

    def test_plan_runtime_specialists_enforces_required_handlers(self) -> None:
        contract = RuntimeSpecialistContract(
            name="required-check",
            route=Route.AUDIT,
            specialists=(
                RuntimeSpecialistSpec(
                    role=RuntimeSpecialistRole.AUDIT,
                    agent_id="audit",
                    task_scope="audit",
                    required=True,
                ),
            ),
        )
        with self.assertRaises(RuntimeSpecialistContractError):
            plan_runtime_specialists(
                contract=contract,
                handlers={},
                dispatch_context=_dispatch_context(Route.AUDIT),
            )

    def test_plan_runtime_specialists_skips_missing_optional_roles(self) -> None:
        contract = RuntimeSpecialistContract(
            name="optional-check",
            route=Route.AUDIT,
            specialists=(
                RuntimeSpecialistSpec(
                    role=RuntimeSpecialistRole.AUDIT,
                    agent_id="audit",
                    task_scope="audit",
                    required=True,
                ),
                RuntimeSpecialistSpec(
                    role=RuntimeSpecialistRole.EXPLAIN,
                    agent_id="explain",
                    task_scope="explain",
                    required=False,
                ),
            ),
        )
        tasks = plan_runtime_specialists(
            contract=contract,
            handlers={
                RuntimeSpecialistRole.AUDIT: lambda _ctx: _payload("audit"),
            },
            dispatch_context=_dispatch_context(Route.AUDIT),
        )
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0].agent_id, "audit")

    def test_pipeline_can_execute_via_runtime_contract_path(self) -> None:
        contract = default_runtime_contract(Route.INIT)
        handlers = {
            RuntimeSpecialistRole.ARCHITECTURE: lambda _ctx: _payload("architecture"),
            RuntimeSpecialistRole.MODULE: lambda _ctx: _payload("module"),
            RuntimeSpecialistRole.VALIDATE: lambda _ctx: _payload("validate"),
        }
        result = run_pipeline(
            request=OrchestrationRequest(user_input="Create a new scaffold."),
            context=RepoContext(
                existing_config_present=False,
                usable_nix_structure_present=False,
                request_is_change=False,
                repository_state="known",
            ),
            policy=self.policy,
            runtime_contract=contract,
            runtime_handlers=handlers,
        )
        self.assertEqual(result.selected_mode, Mode.PROPOSE)
        self.assertEqual(len(result.included_payloads), 3)
        dispatch_summary = result.artifact_summary["specialist_dispatch"]
        self.assertEqual(dispatch_summary["runtime_contract_name"], "init-default")
        self.assertEqual(dispatch_summary["runtime_contract_route"], "init")
        self.assertEqual(dispatch_summary["task_count"], 3)
        self.assertEqual(dispatch_summary["agent_ids"], ("architecture", "module", "validate"))

    def test_pipeline_requires_contract_and_handlers_together(self) -> None:
        with self.assertRaises(OrchestrationPipelineError):
            run_pipeline(
                request=OrchestrationRequest(user_input="scaffold"),
                context=RepoContext(existing_config_present=False),
                policy=self.policy,
                runtime_contract=default_runtime_contract(Route.INIT),
            )

    def test_runtime_contract_apply_mode_executes_validation_checkpoints(self) -> None:
        contract = default_runtime_contract(Route.INIT)
        handlers = {
            RuntimeSpecialistRole.ARCHITECTURE: lambda _ctx: _payload("architecture"),
            RuntimeSpecialistRole.MODULE: lambda _ctx: _payload("module"),
            RuntimeSpecialistRole.VALIDATE: lambda _ctx: _payload("validate"),
        }
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "flake.nix").write_text("{ }")
            call_count = {"value": 0}

            def _runner(_command, _cwd):
                call_count["value"] += 1
                return 0, "ok", ""

            result = run_pipeline(
                request=OrchestrationRequest(
                    user_input="Create a new scaffold and apply.",
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
                validation_runner=_runner,
                runtime_contract=contract,
                runtime_handlers=handlers,
            )

        self.assertEqual(result.selected_mode, Mode.APPLY)
        self.assertEqual(call_count["value"], 4)
        validation = result.artifact_summary["validation"]
        self.assertEqual(
            tuple(checkpoint["stage"] for checkpoint in validation["checkpoints"]),
            ("pre_write", "post_write"),
        )
        self.assertEqual(validation["final_checkpoint"], "post_write")
        self.assertTrue(validation["final_success"])


if __name__ == "__main__":
    unittest.main()
