from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from nixvibe.orchestrator.payloads import PayloadValidationError, validate_payload
from nixvibe.orchestrator.types import SpecialistStatus


def _base_payload() -> dict:
    return {
        "agent_id": "architecture",
        "task_scope": "Assess structure",
        "status": "warning",
        "findings": [
            {
                "id": "F-1",
                "severity": "high",
                "summary": "Duplicate option definitions",
                "evidence": ["hosts/lotus/configuration.nix"],
                "impact": "High drift risk",
            }
        ],
        "recommendations": [
            {
                "id": "R-1",
                "action": "Consolidate duplicate options in shared module",
                "priority": "now",
                "maps_to_findings": ["F-1"],
                "reversible": True,
            }
        ],
        "confidence": 0.88,
        "risks": [
            {
                "id": "K-1",
                "category": "regression",
                "severity": "medium",
                "mitigation": "Apply patch in propose mode and review diff",
            }
        ],
        "artifacts": {"notes": ["Preserve host identity settings"]},
        "checks": {"schema_checked": True},
        "timestamp": "2026-04-19T00:00:00-10:00",
    }


class TestSpecialistPayloads(unittest.TestCase):
    def test_valid_payload_is_accepted(self) -> None:
        payload = validate_payload(_base_payload())
        self.assertEqual(payload.agent_id, "architecture")
        self.assertEqual(payload.status, SpecialistStatus.WARNING)
        self.assertEqual(payload.confidence, 0.88)

    def test_missing_required_field_is_rejected(self) -> None:
        data = _base_payload()
        del data["task_scope"]
        with self.assertRaises(PayloadValidationError):
            validate_payload(data)

    def test_confidence_out_of_range_is_rejected(self) -> None:
        data = _base_payload()
        data["confidence"] = 1.2
        with self.assertRaises(PayloadValidationError):
            validate_payload(data)

    def test_ok_empty_findings_requires_checks_evidence(self) -> None:
        data = _base_payload()
        data["status"] = "ok"
        data["findings"] = []
        data["checks"] = {}
        with self.assertRaises(PayloadValidationError):
            validate_payload(data)


if __name__ == "__main__":
    unittest.main()

