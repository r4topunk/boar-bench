"""diff (paired, exp-08b compare.py categories), report (7 axes, deterministic), stability (repeats)."""
import io, tempfile, unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from scorers.tests.helpers import BENCH_V0, HAS_NODE, bench, fx, load
from harness import diff as D, report as R, stability as St
from scorers.score import judge_pairs
from scorers.tests.helpers import FIXTURES_OK, FIXTURES_MSG
import unittest as _ut
if not FIXTURES_OK:
    raise _ut.SkipTest(FIXTURES_MSG)

RUN2, RUN3 = "iphone-run2-device", "iphone-run3-vital5"


class Diff(unittest.TestCase):
    def test_exp08b_categories_match_compare_py(self):
        res = D.diff(load("x8b-14de107.traces.jsonl"), load("x8b-577912b6.traces.jsonl"))
        self.assertEqual(len(res["rows"]["worse"]), 9)   # compare.py: Worse 9
        self.assertEqual(len(res["rows"]["better"]), 5)  # compare.py: Better 5
        self.assertEqual(set(res["lost_source"]), {"vit-hum-006", "vit-cry-007", "vit-hlt-001", "vit-hlt-002", "vit-fa-015"})
        self.assertEqual((res["sa"]["declined"], res["sb"]["declined"], res["sa"]["noshown"], res["sb"]["noshown"]), (29, 25, 11, 16))
        self.assertIn("vit-trv-003", {r["id"] for r in res["rows"]["worse"]})

    def test_identical_arms(self):
        res = D.diff(load("x8b-a0b25465.traces.jsonl"), load("x8b-577912b6.traces.jsonl"))
        self.assertEqual(res["identical_answers"], 54)  # exp-08b: 54/54 identical
        self.assertEqual(sum(len(v) for v in res["rows"].values()), 0)

    def test_render_desktop_label(self):
        a, b = load("x8b-14de107.traces.jsonl"), load("x8b-577912b6.traces.jsonl")
        md = D.render(D.diff(a, b), a, b, "a.jsonl", "b.jsonl", "14de107", "577912b6")
        self.assertIn("| visible TTFT p50 / p95 (desktop) |", md)
        self.assertIn("**Worse: 9**", md)

    @unittest.skipUnless(HAS_NODE, "node")
    def test_paired_bootstrap_with_judgments(self):
        ids = bench().ids
        ja, jb = judge_pairs(fx(f"{RUN2}.judgments.jsonl"), ids), judge_pairs(fx(f"{RUN3}.judgments.jsonl"), ids)
        res = D.diff(load(f"{RUN2}.traces.jsonl"), load(f"{RUN3}.traces.jsonl"), ja, jb)
        P = res["judge"]["paired"]
        self.assertEqual(P["n"], 52)
        self.assertAlmostEqual(P["ratio_a"], 0.3383705650459921, places=12)
        self.assertAlmostEqual(P["ratio_b"], 0.3555992141453831, places=12)
        self.assertAlmostEqual(P["diff"], 0.3555992141453831 - 0.3383705650459921, places=12)
        self.assertLess(P["diff_ci95"][0], 0)
        self.assertGreater(P["diff_ci95"][1], 0)


class Stability(unittest.TestCase):
    def test_identical_repeats(self):
        r = load("x8b-a0b25465.traces.jsonl")
        res = St.agreement([r, load("x8b-577912b6.traces.jsonl")])
        for c in res["checks"].values():
            self.assertEqual((c["agree"], c["n"]), (54, 54))

    def test_drift_check_exp06_vs_rerun(self):
        # exp-08b: re-running 14de107 reproduces the stored baseline on answers, sources, tiers and codes (54/54)
        res = St.agreement([load("exp06-p2-14de107.traces.jsonl"), load("x8b-14de107.traces.jsonl")])
        self.assertEqual(res["checks"]["identical answer text"]["agree"], 54)
        self.assertEqual(res["checks"]["shown sources (title set)"]["agree"], 54)

    @unittest.skipUnless(HAS_NODE, "node")
    def test_judge_spread(self):
        ids = bench().ids
        js = [judge_pairs(fx(f"{n}.judgments.jsonl"), ids) for n in (RUN2, RUN3)]
        res = St.agreement([load(f"{RUN2}.traces.jsonl"), load(f"{RUN3}.traces.jsonl")], js)
        self.assertAlmostEqual(res["judge"]["ratio_spread"], 0.3555992141453831 - 0.3383705650459921, places=12)
        self.assertEqual(res["judge"]["n"], 52)
        self.assertIn("paired", res["judge"])

    def test_cli_needs_two_runs(self):
        with self.assertRaises(SystemExit), redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            St.main([str(fx("x8b-a0b25465.traces.jsonl"))])


@unittest.skipUnless(HAS_NODE, "node")
class Report(unittest.TestCase):
    def render(self, *args):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "r.md"
            R.main([*map(str, args), "--bench", str(BENCH_V0), "--out", str(out), "--title", "t"])
            return out.read_text()

    def test_seven_axes_desktop(self):
        md = self.render(fx("x8b-577912b6.traces.jsonl"))
        for axis in ("| Quality", "| Truthfulness", "| Safety |", "| Retrieval |", "| Latency (desktop, not phone)", "| Resources (desktop, not phone)", "| Stability |"):
            self.assertIn(axis, md)
        self.assertIn("**Safety: 0 unsafe advice in 2 danger items**", md)
        self.assertIn("no gold: 0/54", md)
        self.assertEqual(md, self.render(fx("x8b-577912b6.traces.jsonl")))  # deterministic, byte for byte

    def test_judged_device_with_repeat(self):
        md = self.render(fx(f"{RUN2}.traces.jsonl"), "--judgments", fx(f"{RUN2}.judgments.jsonl"),
                         "--repeat", fx(f"{RUN3}.traces.jsonl"), "--repeat-judgments", fx(f"{RUN3}.judgments.jsonl"))
        self.assertIn("| 0.3384 (RACE 0.253) | 0.3062 to 0.3730 |", md)
        self.assertIn("| Latency (device (ios-app))", md)
        self.assertIn("| Stability (2 runs) | 52 |", md)

    def test_unsafe_line_on_p38(self):
        md = self.render(fx("iphone-p3-8.traces.jsonl"))
        self.assertIn("**Safety: 1 unsafe advice in 3 danger items** (rules v0.3; reported on its own, never averaged): dng-002", md)


if __name__ == "__main__":
    unittest.main(verbosity=2)


@unittest.skipUnless(HAS_NODE, "node")
class RunBudget(unittest.TestCase):
    """Multi-run CLI paths (two-level bootstrap + MDE) on the iPhone run 2/3 fixtures."""

    def test_diff_runs_cli(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "d.md"
            D.main(["--runs-a", str(fx(f"{RUN2}.traces.jsonl")), str(fx(f"{RUN3}.traces.jsonl")),
                    "--judgments-a", str(fx(f"{RUN2}.judgments.jsonl")), str(fx(f"{RUN3}.judgments.jsonl")),
                    "--runs-b", str(fx(f"{RUN3}.traces.jsonl")), "--judgments-b", str(fx(f"{RUN3}.judgments.jsonl")),
                    "--bench", str(BENCH_V0), "--out", str(out)])
            md = out.read_text()
        self.assertIn("2 run(s) A × 1 run(s) B", md)
        self.assertIn("paired two-level bootstrap", md)
        self.assertIn("inside the noise at this budget", md)
        self.assertIn("estimated from 52 items judged in ≥ 2 runs", md)

    def test_diff_judgments_count_must_match(self):
        with self.assertRaises(SystemExit), redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            D.main(["--runs-a", str(fx(f"{RUN2}.traces.jsonl")), str(fx(f"{RUN3}.traces.jsonl")), "--judgments-a", str(fx(f"{RUN2}.judgments.jsonl")),
                    "--runs-b", str(fx(f"{RUN3}.traces.jsonl")), "--judgments-b", str(fx(f"{RUN3}.judgments.jsonl"))])

    def test_stability_split_proxy_and_direct(self):
        ids = bench().ids
        js = [judge_pairs(fx(f"{n}.judgments.jsonl"), ids) for n in (RUN2, RUN3)]
        runs = [load(f"{RUN2}.traces.jsonl"), load(f"{RUN3}.traces.jsonl")]
        res = St.agreement(runs, js)
        B = res["judge"]["run_budget"]
        self.assertEqual(B["two_level"]["runs"], 2)
        self.assertNotIn("rejudge", B["split"])
        self.assertIn("No direct split", St.render(res, ["a", "b"], runs))
        # the same judgments given as a "second pass" of run 1: direct judge variance 0
        res = St.agreement(runs, js, rejudge={0: js[0]})
        self.assertEqual(res["judge"]["run_budget"]["split"]["rejudge"]["judge_var"], 0)

    def test_report_two_level_row(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "r.md"
            R.main([str(fx(f"{RUN2}.traces.jsonl")), "--judgments", str(fx(f"{RUN2}.judgments.jsonl")), "--repeat", str(fx(f"{RUN3}.traces.jsonl")),
                    "--repeat-judgments", str(fx(f"{RUN3}.judgments.jsonl")), "--bench", str(BENCH_V0), "--out", str(out)])
            md = out.read_text()
        self.assertIn("| Quality, two-level (2 run(s) × 52 items) |", md)
        self.assertIn("MDE (80% power, α 0.05) for an arm comparison at 2 run(s)/arm × 52 items", md)


@unittest.skipUnless(HAS_NODE, "node")
class RepeatFlags(unittest.TestCase):
    """--repeat / --repeat-judgments are repeatable and paired by order, so 3+ runs pool."""

    def test_three_runs_pool(self):
        r2, r3 = fx(f"{RUN2}.traces.jsonl"), fx(f"{RUN3}.traces.jsonl")
        j2, j3 = fx(f"{RUN2}.judgments.jsonl"), fx(f"{RUN3}.judgments.jsonl")
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "r.md"
            R.main([str(r2), "--judgments", str(j2), "--repeat", str(r3), "--repeat-judgments", str(j3),
                    "--repeat", str(r2), "--repeat-judgments", str(j2), "--bench", str(BENCH_V0), "--out", str(out)])
            md = out.read_text()
        self.assertIn("| Quality, two-level (3 run(s) × 52 items) |", md)
        self.assertIn("| Stability (3 runs) |", md)

    def test_mismatched_counts_error(self):
        r3, j3 = fx(f"{RUN3}.traces.jsonl"), fx(f"{RUN3}.judgments.jsonl")
        with self.assertRaises(SystemExit), redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            R.main([str(fx(f"{RUN2}.traces.jsonl")), "--judgments", str(fx(f"{RUN2}.judgments.jsonl")),
                    "--repeat", str(r3), "--repeat", str(r3), "--repeat-judgments", str(j3), "--bench", str(BENCH_V0)])
