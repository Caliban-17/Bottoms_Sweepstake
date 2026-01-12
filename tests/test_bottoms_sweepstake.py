import unittest
import pandas as pd
import sys
import os

# Add parent directory to path so we can import the main module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bottoms_sweepstake import (  # noqa: E402
    _normalize_comp_id,
    season_start_year_from_label,
    get_player_picks,
)


class TestBottomsSweepstakeHelpers(unittest.TestCase):

    def test_normalize_comp_id(self):
        self.assertEqual(_normalize_comp_id(123), 123)
        self.assertEqual(_normalize_comp_id(123.0), 123)
        self.assertEqual(_normalize_comp_id("123"), 123)
        self.assertEqual(_normalize_comp_id("123.0"), 123)
        self.assertEqual(_normalize_comp_id("  123  "), 123)
        # Should return original if indeterminate
        self.assertEqual(_normalize_comp_id("abc"), "abc")

    def test_season_start_year_from_label(self):
        self.assertEqual(season_start_year_from_label("2025/26"), 2025)
        self.assertEqual(season_start_year_from_label("2024/25"), 2024)
        self.assertIsNone(season_start_year_from_label("random_string"))
        self.assertEqual(season_start_year_from_label(123), 123)

    def test_get_player_picks_structure(self):
        df = get_player_picks()
        self.assertIsInstance(df, pd.DataFrame)
        self.assertListEqual(list(df.columns), ["Player", "Team"])
        self.assertFalse(df.empty)


if __name__ == "__main__":
    unittest.main()
