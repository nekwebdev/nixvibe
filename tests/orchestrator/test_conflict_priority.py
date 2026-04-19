from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from nixvibe.orchestrator.conflicts import resolve_conflict
from nixvibe.orchestrator.policy_loader import load_policy
from nixvibe.orchestrator.types import ConflictCandidate, Priority


class TestConflictPriority(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.policy = load_policy(ROOT / ".agents/carl/nixvibe-domain.md")

    def test_higher_priority_wins(self) -> None:
        winner = resolve_conflict(
            [
                ConflictCandidate(
                    candidate_id="style-fix",
                    priority=Priority.STYLE,
                    confidence=0.99,
                    reversible=True,
                ),
                ConflictCandidate(
                    candidate_id="safety-guard",
                    priority=Priority.SAFETY,
                    confidence=0.10,
                    reversible=False,
                ),
            ],
            self.policy,
        )
        self.assertEqual(winner.candidate_id, "safety-guard")

    def test_equal_priority_uses_confidence(self) -> None:
        winner = resolve_conflict(
            [
                ConflictCandidate(
                    candidate_id="option-a",
                    priority=Priority.CORRECTNESS,
                    confidence=0.60,
                    reversible=True,
                ),
                ConflictCandidate(
                    candidate_id="option-b",
                    priority=Priority.CORRECTNESS,
                    confidence=0.80,
                    reversible=False,
                ),
            ],
            self.policy,
        )
        self.assertEqual(winner.candidate_id, "option-b")

    def test_equal_priority_and_confidence_prefers_reversible(self) -> None:
        winner = resolve_conflict(
            [
                ConflictCandidate(
                    candidate_id="irreversible",
                    priority=Priority.REVERSIBILITY,
                    confidence=0.75,
                    reversible=False,
                ),
                ConflictCandidate(
                    candidate_id="reversible",
                    priority=Priority.REVERSIBILITY,
                    confidence=0.75,
                    reversible=True,
                ),
            ],
            self.policy,
        )
        self.assertEqual(winner.candidate_id, "reversible")

    def test_full_tie_is_deterministic_by_candidate_id(self) -> None:
        winner = resolve_conflict(
            [
                ConflictCandidate(
                    candidate_id="b-option",
                    priority=Priority.SIMPLICITY,
                    confidence=0.50,
                    reversible=True,
                ),
                ConflictCandidate(
                    candidate_id="a-option",
                    priority=Priority.SIMPLICITY,
                    confidence=0.50,
                    reversible=True,
                ),
            ],
            self.policy,
        )
        self.assertEqual(winner.candidate_id, "a-option")


if __name__ == "__main__":
    unittest.main()

