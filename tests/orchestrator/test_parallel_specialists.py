from __future__ import annotations

import sys
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from nixvibe.orchestrator.specialists import run_specialists
from nixvibe.orchestrator.types import SpecialistExecutionOutcome, SpecialistTask


def _slow_runner(delay: float, result: dict):
    def _runner():
        time.sleep(delay)
        return result

    return _runner


class TestParallelSpecialists(unittest.TestCase):
    def test_dispatch_runs_in_parallel_with_stable_ordering(self) -> None:
        tasks = [
            SpecialistTask("architecture", "structure", _slow_runner(0.15, {"agent_id": "architecture"})),
            SpecialistTask("audit", "audit", _slow_runner(0.15, {"agent_id": "audit"})),
            SpecialistTask("validate", "checks", _slow_runner(0.15, {"agent_id": "validate"})),
        ]

        started = time.perf_counter()
        results = run_specialists(tasks)
        elapsed = time.perf_counter() - started

        self.assertLess(elapsed, 0.35)
        self.assertEqual([result.agent_id for result in results], ["architecture", "audit", "validate"])
        self.assertTrue(all(result.outcome is SpecialistExecutionOutcome.OK for result in results))

    def test_dispatch_captures_runner_errors(self) -> None:
        def _broken():
            raise RuntimeError("boom")

        tasks = [
            SpecialistTask("audit", "scope", _broken),
        ]
        results = run_specialists(tasks)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].outcome, SpecialistExecutionOutcome.ERROR)
        self.assertIn("boom", results[0].error or "")


if __name__ == "__main__":
    unittest.main()

