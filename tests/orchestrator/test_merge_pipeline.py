from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from nixvibe.orchestrator.merge import merge_specialist_payloads
from nixvibe.orchestrator.pipeline import OrchestrationPipelineError, run_pipeline
from nixvibe.orchestrator.policy_loader import load_policy
from nixvibe.orchestrator.types import Mode, OrchestrationRequest, RepoContext, SpecialistTask


def _payload(
    *,
    agent_id: str,
    finding_id: str,
    severity: str,
    summary: str,
    impact: str,
    recommendation_id: str,
    action: str,
    policy_priority: str,
    conflict_group: str,
    confidence: float,
    contradiction_key: str | None = None,
) -> dict:
    finding = {
        "id": finding_id,
        "severity": severity,
        "summary": summary,
        "evidence": [f"evidence/{agent_id}.nix"],
        "impact": impact,
    }
    if contradiction_key:
        finding["contradiction_key"] = contradiction_key

    return {
        "agent_id": agent_id,
        "task_scope": "test",
        "status": "warning",
        "findings": [finding],
        "recommendations": [
            {
                "id": recommendation_id,
                "action": action,
                "priority": "now",
                "maps_to_findings": [finding_id],
                "reversible": True,
                "policy_priority": policy_priority,
                "conflict_group": conflict_group,
            }
        ],
        "confidence": confidence,
        "risks": [
            {
                "id": f"K-{agent_id}",
                "category": "regression",
                "severity": "medium",
                "mitigation": "review in propose mode",
            }
        ],
        "artifacts": {
            "notes": [f"note-{agent_id}"],
            "next_actions": [f"review-{agent_id}"],
        },
        "checks": {"schema_checked": True},
        "timestamp": "2026-04-19T00:00:00-10:00",
    }


class TestMergePipeline(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.policy = load_policy(ROOT / ".agents/carl/nixvibe-domain.md")

    def test_merge_conflict_prefers_higher_policy_priority(self) -> None:
        payloads = [
            _payload(
                agent_id="style",
                finding_id="F-style",
                severity="medium",
                summary="Minor formatting mismatch",
                impact="Style inconsistency",
                recommendation_id="R-style",
                action="Reformat module",
                policy_priority="style",
                conflict_group="module-choice",
                confidence=0.99,
            ),
            _payload(
                agent_id="safety",
                finding_id="F-safety",
                severity="high",
                summary="Unsafe service toggle",
                impact="Security exposure",
                recommendation_id="R-safety",
                action="Disable unsafe toggle",
                policy_priority="safety",
                conflict_group="module-choice",
                confidence=0.20,
            ),
        ]

        from nixvibe.orchestrator.payloads import validate_payload

        merged = merge_specialist_payloads([validate_payload(item) for item in payloads], self.policy)
        self.assertEqual(len(merged.recommendations), 1)
        self.assertEqual(merged.recommendations[0].id, "R-safety")

    def test_pipeline_forces_propose_on_contradictory_critical_findings(self) -> None:
        payload_a = _payload(
            agent_id="audit-a",
            finding_id="F-root-auth",
            severity="critical",
            summary="Enable root SSH login",
            impact="Broad remote attack surface",
            recommendation_id="R-a",
            action="Enable root ssh login",
            policy_priority="user preference",
            conflict_group="root-access",
            confidence=0.8,
            contradiction_key="root-auth",
        )
        payload_b = _payload(
            agent_id="audit-b",
            finding_id="F-root-auth",
            severity="critical",
            summary="Disable root SSH login",
            impact="Prevents direct privileged remote access",
            recommendation_id="R-b",
            action="Disable root ssh login",
            policy_priority="safety",
            conflict_group="root-access",
            confidence=0.7,
            contradiction_key="root-auth",
        )

        tasks = [
            SpecialistTask("audit-a", "scope-a", lambda: payload_a),
            SpecialistTask("audit-b", "scope-b", lambda: payload_b),
        ]
        result = run_pipeline(
            request=OrchestrationRequest(
                user_input="Please apply these changes now.",
                requested_mode=Mode.APPLY,
                explicit_apply_opt_in=True,
            ),
            context=RepoContext(existing_config_present=True, request_is_change=True),
            specialist_tasks=tasks,
            policy=self.policy,
        )

        self.assertEqual(result.selected_mode, Mode.PROPOSE)
        self.assertTrue(result.next_action)
        self.assertGreaterEqual(len(result.artifact_summary.get("notes", ())), 1)

    def test_pipeline_requires_at_least_one_valid_payload(self) -> None:
        tasks = [
            SpecialistTask("bad", "scope", lambda: {"agent_id": "bad"}),
        ]
        with self.assertRaises(OrchestrationPipelineError):
            run_pipeline(
                request=OrchestrationRequest(user_input="audit this"),
                context=RepoContext(existing_config_present=True, request_is_change=True),
                specialist_tasks=tasks,
                policy=self.policy,
            )


if __name__ == "__main__":
    unittest.main()

