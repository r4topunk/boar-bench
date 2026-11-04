"""The bounty bar is defined on the floor-adjusted U, not on the raw ratio (poidh bounty 1520, claim 9300). Needs no fixtures."""
import unittest

from scorers import score as S


def judge_res(pairs, raw):
    return {"summary": {"n": len(pairs), "qualityRatio": raw, "qualityRatioCI": [raw, raw], "boarWin": 0, "tie": 0, "refWin": 1,
                        "winScore": 0, "winScoreCI": [0, 0], "positionConsistency": 1, "rubricBoar": {}, "rubricRef": {}},
            "pairs": pairs, "correctRate": 0, "judgeMeta": [], "singleOrderDropped": []}


class BarOnFloorAdjusted(unittest.TestCase):
    def test_raw_half_is_below_the_bar(self):
        # raw 0.50 at a reference mean of 4.878 is U = (0.5 * 4.878 - 1) / (4.878 - 1) = 0.371
        pairs = [{"boarMean": 0.5 * 4.878, "refMean": 4.878} for _ in range(40)]
        q = S.quality_block(judge_res(pairs, 0.5), len(pairs))
        self.assertAlmostEqual(q["floor_adjusted_u"], 0.371, places=3)
        self.assertEqual(q["bounty_bar"]["metric"], "floor_adjusted_u")
        self.assertEqual(q["bounty_bar"]["verdict"][:5], "BELOW")
        self.assertEqual(S.bar_verdict(0.5, [0.5, 0.5])[:5], "MEETS")  # what the old raw path printed for this same system

    def test_meets_needs_u_ci_above_half(self):
        pairs = [{"boarMean": 4.0, "refMean": 4.5} for _ in range(40)]  # U = 3 / 3.5 = 0.857
        q = S.quality_block(judge_res(pairs, 4 / 4.5), len(pairs))
        self.assertEqual(q["bounty_bar"]["verdict"][:5], "MEETS")


if __name__ == "__main__":
    unittest.main()
