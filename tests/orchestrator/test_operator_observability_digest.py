from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from nixvibe.orchestrator.operator_observability_digest import build_operator_observability_digest
from nixvibe.orchestrator.pipeline import run_pipeline
from nixvibe.orchestrator.policy_loader import load_policy
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
        "task_scope": "operator-observability-digest",
        "status": "warning",
        "findings": [
            {
                "id": f"F-{agent_id}",
                "severity": "high",
                "summary": "Scoped finding",
                "evidence": [f"evidence/{agent_id}.nix"],
                "impact": "Operator observability digest coverage",
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


class TestOperatorObservabilityDigest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.policy = load_policy(ROOT / ".agents/carl/nixvibe-domain.md")

    def test_helper_reports_healthy_when_signals_clear(self) -> None:
        digest = build_operator_observability_digest(
            run_manifest={"contract": "operator-run-manifest/v1", "route": "init", "modes": {"selected": "apply"}},
            operator_audit_trail={
                "contract": "operator-audit-trail/v1",
                "audit_level": "info",
                "entries": ({"severity": "info"},),
                "action_items": (),
            },
            run_telemetry={"contract": "run-telemetry/v1", "total_duration_ms": 100},
            release_policy_execution={"contract": "release-policy-execution/v1", "decision": "automated"},
        )

        self.assertEqual(digest["observability_band"], "healthy")
        self.assertFalse(digest["attention_required"])

    def test_helper_reports_attention_when_manual_ack_required(self) -> None:
        digest = build_operator_observability_digest(
            run_manifest={"contract": "operator-run-manifest/v1", "route": "init", "modes": {"selected": "apply"}},
            operator_audit_trail={
                "contract": "operator-audit-trail/v1",
                "audit_level": "info",
                "entries": ({"severity": "info"}, {"severity": "medium"}),
                "action_items": ("Review warning signal.",),
            },
            run_telemetry={"contract": "run-telemetry/v1", "total_duration_ms": 100},
            release_policy_execution={"contract": "release-policy-execution/v1", "decision": "manual-ack"},
        )

        self.assertEqual(digest["observability_band"], "attention")
        self.assertIn("Review warning signal.", digest["focus_items"])

    def test_helper_reports_critical_when_policy_blocked(self) -> None:
        digest = build_operator_observability_digest(
            run_manifest={"contract": "operator-run-manifest/v1", "route": "init", "modes": {"selected": "apply"}},
            operator_audit_trail={
                "contract": "operator-audit-trail/v1",
                "audit_level": "warning",
                "entries": ({"severity": "high"},),
                "action_items": (),
            },
            run_telemetry={"contract": "run-telemetry/v1", "total_duration_ms": 100},
            release_policy_execution={
                "contract": "release-policy-execution/v1",
                "decision": "blocked",
                "blockers": ("override-skip-validation",),
            },
        )

        self.assertEqual(digest["observability_band"], "critical")
        self.assertTrue(digest["escalation_recommended"])
        self.assertIn("Resolve release policy blocker: override-skip-validation.", digest["focus_items"])

    def test_helper_reports_degraded_when_contracts_missing(self) -> None:
        digest = build_operator_observability_digest(
            run_manifest={"contract": "missing"},
            operator_audit_trail={"contract": "missing"},
            run_telemetry={"contract": "missing"},
            release_policy_execution={"contract": "missing"},
        )

        self.assertFalse(digest["digest_ready"])
        self.assertEqual(digest["observability_band"], "degraded")
        self.assertIn("run-manifest-contract", digest["failed_check_ids"])

    def test_pipeline_emits_operator_observability_digest_contract(self) -> None:
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

        digest = result.artifact_summary["operator_observability_digest"]
        self.assertEqual(digest["contract"], "operator-observability-digest/v1")
        self.assertEqual(digest["observability_band"], "attention")
        self.assertTrue(digest["attention_required"])


if __name__ == "__main__":
    unittest.main()
