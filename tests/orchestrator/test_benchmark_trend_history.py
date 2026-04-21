from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from nixvibe.orchestrator.benchmark_trend_history import build_benchmark_trend_history


def _entry(*, trend_key: str, score: int, duration_ms: int) -> dict[str, object]:
    return {
        "contract": "benchmark-trend-entry/v1",
        "trend_key": trend_key,
        "trend_status": "stable_watch",
        "outcome_score_percent": score,
        "timing": {"total_duration_ms": duration_ms},
    }


class TestBenchmarkTrendHistory(unittest.TestCase):
    def test_seeded_history_without_previous(self) -> None:
        history = build_benchmark_trend_history(benchmark_trend_entry=_entry(trend_key="trend-1", score=80, duration_ms=1000))

        self.assertEqual(history["contract"], "benchmark-trend-history/v1")
        self.assertEqual(history["history_status"], "seeded")
        self.assertEqual(history["history_count"], 1)
        self.assertFalse(history["has_previous"])
        self.assertIsNone(history["previous_benchmark_trend_entry"])

    def test_advanced_history_uses_latest_previous_entry(self) -> None:
        history = build_benchmark_trend_history(
            benchmark_trend_entry=_entry(trend_key="trend-3", score=90, duration_ms=900),
            prior_history=(
                _entry(trend_key="trend-1", score=75, duration_ms=1500),
                _entry(trend_key="trend-2", score=82, duration_ms=1200),
            ),
        )

        self.assertEqual(history["history_status"], "advanced")
        self.assertTrue(history["has_previous"])
        self.assertEqual(history["previous_trend_key"], "trend-2")
        self.assertEqual(history["history_count"], 3)

    def test_history_limit_trims_old_entries(self) -> None:
        history = build_benchmark_trend_history(
            benchmark_trend_entry=_entry(trend_key="trend-4", score=91, duration_ms=800),
            prior_history=(
                _entry(trend_key="trend-1", score=70, duration_ms=1700),
                _entry(trend_key="trend-2", score=76, duration_ms=1500),
                _entry(trend_key="trend-3", score=85, duration_ms=1200),
            ),
            history_limit=2,
        )

        self.assertEqual(history["history_count"], 2)
        self.assertEqual(history["dropped_count"], 2)
        entries = history["history_entries"]
        self.assertEqual(entries[0]["trend_key"], "trend-3")
        self.assertEqual(entries[1]["trend_key"], "trend-4")

    def test_invalid_current_entry_blocks_history(self) -> None:
        history = build_benchmark_trend_history(
            benchmark_trend_entry={"contract": "missing"},
            prior_history=(_entry(trend_key="trend-1", score=70, duration_ms=1700),),
        )

        self.assertEqual(history["history_status"], "blocked")
        self.assertFalse(history["history_ready"])
        self.assertEqual(history["history_count"], 1)
        self.assertEqual(history["previous_trend_key"], "trend-1")


if __name__ == "__main__":
    unittest.main()
