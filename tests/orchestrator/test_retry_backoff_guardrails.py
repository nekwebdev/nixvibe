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
        "task_scope": "retry-backoff-guardrails",
        "status": "warning",
        "findings": [
            {
                "id": f"F-{agent_id}",
                "severity": "high",
                "summary": "Scoped finding",
                "evidence": [f"evidence/{agent_id}.nix"],
                "impact": "Retry guardrail coverage",
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


class TestRetryBackoffGuardrails(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.policy = load_policy(ROOT / ".agents/carl/nixvibe-domain.md")

    def test_apply_success_has_no_retry_policy(self) -> None:
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

        guardrails = result.artifact_summary["retry_backoff_guardrails"]
        self.assertEqual(guardrails["contract"], "retry-backoff-guardrails/v1")
        self.assertFalse(guardrails["automatic_retry_allowed"])
        self.assertFalse(guardrails["manual_retry_recommended"])
        self.assertEqual(guardrails["retry_mode"], "none")
        self.assertEqual(guardrails["max_attempts"], 0)
        self.assertEqual(guardrails["backoff_seconds"], ())

    def test_invalid_payload_enables_single_auto_retry(self) -> None:
        result = run_pipeline(
            request=OrchestrationRequest(user_input="Review config"),
            context=RepoContext(
                existing_config_present=True,
                usable_nix_structure_present=True,
                request_is_change=True,
                repository_state="known",
            ),
            specialist_tasks=[
                SpecialistTask("good", "scope", lambda: _payload(agent_id="good")),
                SpecialistTask(
                    "bad",
                    "scope",
                    lambda: {
                        "agent_id": "bad",
                        "task_scope": "retry-backoff-guardrails",
                        "status": "warning",
                        "findings": [],
                        "recommendations": [],
                        "confidence": 0.5,
                        "risks": [],
                        "artifacts": {},
                        "timestamp": "2026-04-20T00:00:00-10:00",
                    },
                ),
            ],
            policy=self.policy,
        )

        guardrails = result.artifact_summary["retry_backoff_guardrails"]
        self.assertTrue(guardrails["automatic_retry_allowed"])
        self.assertTrue(guardrails["manual_retry_recommended"])
        self.assertEqual(guardrails["retry_mode"], "propose")
        self.assertEqual(guardrails["max_attempts"], 1)
        self.assertEqual(guardrails["backoff_seconds"], (5,))
        self.assertEqual(guardrails["reason"], "degraded_auto_resume_window")

    def test_specialist_runtime_failure_uses_exponential_backoff(self) -> None:
        result = run_pipeline(
            request=OrchestrationRequest(user_input="Review config"),
            context=RepoContext(
                existing_config_present=True,
                usable_nix_structure_present=True,
                request_is_change=True,
                repository_state="known",
            ),
            specialist_tasks=[
                SpecialistTask("good", "scope", lambda: _payload(agent_id="good")),
                SpecialistTask(
                    "boom",
                    "scope",
                    lambda: (_ for _ in ()).throw(RuntimeError("runner crashed")),
                ),
            ],
            policy=self.policy,
        )

        guardrails = result.artifact_summary["retry_backoff_guardrails"]
        self.assertTrue(guardrails["automatic_retry_allowed"])
        self.assertEqual(guardrails["retry_mode"], "propose")
        self.assertEqual(guardrails["max_attempts"], 2)
        self.assertEqual(guardrails["backoff_seconds"], (5, 15))
        self.assertEqual(guardrails["backoff_strategy"], "exponential")
        self.assertEqual(guardrails["resume_stage"], "specialist-runtime")
        self.assertIn("specialist-runtime-persists", guardrails["stop_conditions"])

    def test_human_confirmation_blocks_auto_retry(self) -> None:
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

        guardrails = result.artifact_summary["retry_backoff_guardrails"]
        self.assertFalse(guardrails["automatic_retry_allowed"])
        self.assertTrue(guardrails["manual_retry_recommended"])
        self.assertEqual(guardrails["max_attempts"], 0)
        self.assertEqual(guardrails["reason"], "human_confirmation_required")
        self.assertEqual(guardrails["retry_mode"], "propose")


if __name__ == "__main__":
    unittest.main()
