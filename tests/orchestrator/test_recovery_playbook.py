from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from nixvibe.orchestrator.recovery import build_recovery_playbook
from nixvibe.orchestrator.types import Mode


class TestRecoveryPlaybook(unittest.TestCase):
    def test_advisory_checkpoint_path(self) -> None:
        playbook = build_recovery_playbook(
            escalation={
                "tier": "advisory",
                "reason": "apply_dirty_workspace",
            },
            mode=Mode.APPLY,
            next_action="Review changes and checkpoint.",
            ledger_summary={"dirty": True},
        )

        self.assertFalse(playbook["required"])
        self.assertEqual(playbook["stage"], "advisory-checkpoint")
        self.assertEqual(playbook["strategy"], "checkpoint-intentional-changes")
        self.assertTrue(playbook["checkpoint_required"])
        self.assertEqual(playbook["source_tier"], "advisory")

    def test_no_escalation_path(self) -> None:
        playbook = build_recovery_playbook(
            escalation={
                "tier": "none",
                "reason": "no_escalation",
            },
            mode=Mode.PROPOSE,
            next_action="Continue normally.",
            ledger_summary={"dirty": False},
        )

        self.assertFalse(playbook["required"])
        self.assertEqual(playbook["stage"], "none")
        self.assertEqual(playbook["strategy"], "none")
        self.assertEqual(playbook["action_count"], 0)
        self.assertEqual(playbook["source_reason"], "no_escalation")


if __name__ == "__main__":
    unittest.main()
