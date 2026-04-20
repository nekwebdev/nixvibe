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
    finding_summary: str = "Scoped finding",
    finding_impact: str = "Explainability coverage",
    finding_severity: str = "high",
    contradiction_key: str | None = None,
    reversible: bool = True,
    risk_severity: str = "medium",
) -> dict:
    finding: dict[str, object] = {
        "id": f"F-{agent_id}",
        "severity": finding_severity,
        "summary": finding_summary,
        "evidence": [f"evidence/{agent_id}.nix"],
        "impact": finding_impact,
    }
    if contradiction_key is not None:
        finding["contradiction_key"] = contradiction_key

    return {
        "agent_id": agent_id,
        "task_scope": "policy-decision-explainability",
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


def _decision_by_stage(explainability: dict[str, object], stage: str) -> dict[str, object]:
    for decision in explainability["decisions"]:
        if decision["stage"] == stage:
            return decision
    raise AssertionError(f"Missing stage: {stage}")


class TestPolicyDecisionExplainability(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.policy = load_policy(ROOT / ".agents/carl/nixvibe-domain.md")

    def test_apply_success_emits_full_decision_trace(self) -> None:
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

        explainability = result.artifact_summary["policy_decision_explainability"]
        self.assertEqual(explainability["contract"], "policy-decision-explainability/v1")
        self.assertEqual(explainability["final_mode"], "apply")
        self.assertEqual(explainability["decision_count"], 7)
        self.assertEqual(
            explainability["conflict_priority_order"],
            ("safety", "correctness", "reversibility", "simplicity", "user preference", "style"),
        )
        release = _decision_by_stage(explainability, "release-readiness")
        self.assertEqual(release["decision"], "ready")

    def test_critical_conflict_trace_marks_forced_propose(self) -> None:
        result = run_pipeline(
            request=OrchestrationRequest(
                user_input="Apply now with conflicting critical findings.",
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
                    "a",
                    "scope",
                    lambda: _payload(
                        agent_id="a",
                        finding_summary="Critical conflict A",
                        finding_impact="Do A",
                        finding_severity="critical",
                        contradiction_key="conflict-key",
                    ),
                ),
                SpecialistTask(
                    "b",
                    "scope",
                    lambda: _payload(
                        agent_id="b",
                        finding_summary="Critical conflict B",
                        finding_impact="Do B",
                        finding_severity="critical",
                        contradiction_key="conflict-key",
                    ),
                ),
            ],
            policy=self.policy,
        )

        explainability = result.artifact_summary["policy_decision_explainability"]
        merge = _decision_by_stage(explainability, "merge-resolution")
        self.assertEqual(merge["decision"], "forced-propose")
        self.assertIn("critical-conflict", merge["signals"])
        self.assertIn("release-readiness", explainability["blocked_stages"])

    def test_guardrail_block_is_explicit_in_trace(self) -> None:
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

        explainability = result.artifact_summary["policy_decision_explainability"]
        guardrail = _decision_by_stage(explainability, "mutation-guardrails")
        escalation = _decision_by_stage(explainability, "safety-escalation")
        self.assertEqual(guardrail["decision"], "blocked")
        self.assertIn("critical_risk", guardrail["signals"])
        self.assertEqual(escalation["decision"], "blocked")
        self.assertEqual(escalation["reason"], "high_risk_mutation_guardrail")


if __name__ == "__main__":
    unittest.main()
