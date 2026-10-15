"""Two-level (items × runs) bootstrap, MDE and the judge/generation split (a research agent card judge-reliability-run-budget).
Pure: synthetic judgments only."""
import unittest

from scorers import stats


def run(scores, ref=4.5):
    return {f"q{i}": (b, ref) for i, b in enumerate(scores)}


BASE = [1 + (i * 7) % 5 * 0.5 for i in range(40)]  # deterministic spread of item difficulty, 1.0..3.0


class TwoLevel(unittest.TestCase):
    def test_one_run_equals_item_bootstrap(self):
        a, b = run(BASE), run([x + 0.3 * (i % 2) for i, x in enumerate(BASE)])
        self.assertEqual(stats.two_level_diff([a], [b])["diff_ci95"], stats.paired_ratio_diff(a, b)["diff_ci95"])
        tl = stats.two_level_ratio([a])
        self.assertEqual(tl["ci95"], stats.bootstrap_ci(list(a.values()), stats.ratio, seed=11))
        self.assertEqual(tl["ratio"], stats.ratio(list(a.values())))

    def test_run_noise_widens_the_ci(self):
        noisy = [run([x + (0.8 if (i + k) % 2 else -0.8) for i, x in enumerate(BASE)]) for k in range(2)]
        mean_run = run(BASE)  # what a plain item bootstrap on the per-item run mean sees
        w2 = stats.two_level_ratio(noisy)["ci95"]
        w1 = stats.two_level_ratio([mean_run])["ci95"]
        self.assertAlmostEqual(stats.two_level_ratio(noisy)["ratio"], stats.ratio(list(mean_run.values())))
        self.assertGreater(w2[1] - w2[0], (w1[1] - w1[0]) * 1.2)

    def test_deterministic_and_seeded(self):
        rs = [run(BASE), run([x + 0.5 for x in BASE])]
        self.assertEqual(stats.two_level_ratio(rs, seed=3), stats.two_level_ratio(rs, seed=3))
        self.assertNotEqual(stats.two_level_ratio(rs, seed=3)["ci95"], stats.two_level_ratio(rs, seed=4)["ci95"])

    def test_paired_shift_detected(self):
        a = [run([x + d for x in BASE]) for d in (-0.2, 0.2)]
        b = [run([x + 1.0 + d for x in BASE]) for d in (-0.2, 0.2)]
        p = stats.two_level_diff(a, b)
        self.assertAlmostEqual(p["diff"], 1.0 / 4.5)
        self.assertGreater(p["diff_ci95"][0], 0)
        self.assertEqual((p["runs_a"], p["runs_b"], p["n"]), (2, 2, 40))

    def test_unbalanced_items(self):
        r1, r2 = run(BASE), run(BASE[:10])  # run 2 judged only 10 items
        tl = stats.two_level_ratio([r1, r2])
        self.assertEqual((tl["n_items"], tl["runs_per_item_min"]), (40, 1))


class Mde(unittest.TestCase):
    def test_card_table(self):
        # card: σ² 0.255 (s42/s43), mean ref score 4.87 -> 0.053 / 0.038 / 0.031 / 0.024 at 60 items; 0.037 / 0.026 at 120
        card = {60: [0.053, 0.037, 0.031, 0.024], 120: [0.037, 0.026, 0.022, 0.017]}  # a research agent results.txt
        for n, row in card.items():
            for k, want in zip((1, 2, 3, 5), row):
                self.assertAlmostEqual(stats.mde(0.255, n, k, refm=4.87)["mde"], want, delta=0.001)

    def test_run_variance(self):
        self.assertEqual(stats.run_variance([{"a": (1, 4)}, {"a": (3, 4)}]), {"var": 2.0, "n_items": 1})
        self.assertIsNone(stats.run_variance([{"a": (1, 4)}]))

    def test_block_estimates_or_falls_back(self):
        one = stats.mde_block([run(BASE)])
        self.assertEqual(one["var_run"], stats.PRIOR_RUN_VARIANCE)
        self.assertIn("prior", one["source"])
        two = stats.mde_block([run(BASE), run([x + 1 for x in BASE])])
        self.assertAlmostEqual(two["var_run"], 0.5)
        self.assertIn("estimated from 40 items", two["source"])
        self.assertLess(stats.mde_block([run(BASE)] * 3)["mde"], stats.mde_block([run(BASE)] * 3, [run(BASE)])["mde"] + 1)


class Split(unittest.TestCase):
    def test_direct_and_proxy(self):
        r1 = {"a": 1.0, "b": 2.0, "c": 3.0}
        r2 = {"a": 2.0, "b": 2.0, "c": 1.0}  # total var: (0.5 + 0 + 2) / 3
        sp = stats.variance_split([r1, r2], rejudge=[(1.0, 1.2), (2.0, 2.0), (3.0, 2.8)], identical=[(2.0, 2.0)])
        self.assertAlmostEqual(sp["total_var"], 2.5 / 3)
        self.assertAlmostEqual(sp["rejudge"]["judge_var"], (0.04 + 0 + 0.04) / 6)
        self.assertAlmostEqual(sp["rejudge"]["judge_share"] + sp["rejudge"]["generation_share"], 1)
        self.assertEqual(sp["identical_text"]["judge_var"], 0)

    def test_needs_two_runs(self):
        self.assertIsNone(stats.variance_split([{"a": 1.0}]))


if __name__ == "__main__":
    unittest.main(verbosity=2)


class FloorAdjusted(unittest.TestCase):
    """a research agent S1: rubric scores are >= 1, so a blank system reads ~0.2 raw; floor-adjusted it is 0."""

    def test_blank_system(self):
        blank = {f"q{i}": (1.0, 4.9) for i in range(40)}  # every rubric at the floor vs a strong reference
        self.assertAlmostEqual(stats.ratio(list(blank.values())), 1 / 4.9)  # ~0.20 raw
        adj = stats.two_level_ratio([stats.floor_adjust(blank)])
        self.assertEqual((adj["ratio"], adj["ci95"]), (0.0, [0.0, 0.0]))

    def test_declines_read_higher_raw_than_adjusted(self):
        run = {f"q{i}": ((1.5, 4.9) if i % 2 else (4.0, 4.9)) for i in range(40)}  # half declines (~1.5), half decent answers
        raw, adj = stats.ratio(list(run.values())), stats.ratio(list(stats.floor_adjust(run).values()))
        self.assertAlmostEqual(raw, (1.5 + 4.0) / (2 * 4.9))
        self.assertAlmostEqual(adj, (0.5 + 3.0) / (2 * 3.9))
        self.assertLess(adj, raw)

    def test_perfect_system_is_one_both_ways(self):
        run = {f"q{i}": (4.9, 4.9) for i in range(10)}
        self.assertEqual(stats.ratio(list(stats.floor_adjust(run).values())), 1.0)
