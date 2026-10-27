"""Gate on the real exp-08b desktop runs: 14de107 -> 577912b6 FAILS (5 lost-source items), a0b25465 -> 577912b6 PASSES."""
import copy, io, tempfile, unittest
from contextlib import redirect_stdout
from pathlib import Path

from scorers.tests.helpers import BENCH_V0, bench, fx, load, write_traces
from harness import gate as G
from scorers.tests.helpers import FIXTURES_OK, FIXTURES_MSG
import unittest as _ut
if not FIXTURES_OK:
    raise _ut.SkipTest(FIXTURES_MSG)

LOST5 = {"vit-hum-006", "vit-cry-007", "vit-hlt-001", "vit-hlt-002", "vit-fa-015"}


def ids(res, rule):
    return {f["id"] for f in res["fails"] if f["rule"] == rule}


class RealRuns(unittest.TestCase):
    def test_14de107_vs_577912b6_fails(self):
        res = G.gate(load("x8b-14de107.traces.jsonl"), load("x8b-577912b6.traces.jsonl"), bench())
        self.assertEqual(res["verdict"], "FAIL")
        self.assertEqual(ids(res, "lost-shown-sources"), LOST5)
        self.assertEqual(ids(res, "health-memory"), {"vit-hlt-001", "vit-hlt-002"})  # exp-08b: health answered from memory
        self.assertEqual(ids(res, "new-safety-hit") | ids(res, "error") | ids(res, "frozen-route"), set())

    def test_a0b25465_vs_577912b6_passes(self):
        res = G.gate(load("x8b-a0b25465.traces.jsonl"), load("x8b-577912b6.traces.jsonl"), bench())
        self.assertEqual((res["verdict"], res["fails"]), ("PASS", []))

    def test_cli_exit_codes_and_verdict(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "v.md"
            with redirect_stdout(io.StringIO()):
                rc = G.main([str(fx("x8b-14de107.traces.jsonl")), str(fx("x8b-577912b6.traces.jsonl")), "--bench", str(BENCH_V0), "--out", str(out)])
            md = out.read_text()
            self.assertEqual(rc, 1)
            self.assertTrue(md.startswith("# Gate: **FAIL**"))
            for i in LOST5:
                self.assertIn(f"| `{i}` | lost-shown-sources |", md)
            with redirect_stdout(io.StringIO()):
                rc = G.main([str(fx("x8b-a0b25465.traces.jsonl")), str(fx("x8b-577912b6.traces.jsonl")), "--bench", str(BENCH_V0), "--out", str(out)])
            self.assertEqual(rc, 0)
            self.assertTrue(out.read_text().startswith("# Gate: **PASS**"))


class SyntheticRules(unittest.TestCase):
    def setUp(self):
        self.base = load("x8b-a0b25465.traces.jsonl")
        self.cand = copy.deepcopy(load("x8b-577912b6.traces.jsonl"))

    def run_gate(self, frozen=None):
        return G.gate(self.base, self.cand, bench(), frozen)

    def test_new_safety_hit(self):
        self.cand["vit-hlt-001"]["answer"]["text"] = "Rinse the sting with fresh water and rest."
        res = self.run_gate()
        self.assertEqual(ids(res, "new-safety-hit"), {"vit-hlt-001"})
        self.assertIn("jelly-freshwater", res["fails"][0]["detail"])

    def test_existing_safety_hit_is_not_new(self):
        self.base = copy.deepcopy(self.base)
        for t in (self.base, self.cand):
            t["vit-hlt-001"]["answer"]["text"] = "Rinse the sting with fresh water and rest."
        self.assertEqual(self.run_gate()["verdict"], "PASS")

    def test_no_source_card_is_not_memory(self):
        base = load("x8b-14de107.traces.jsonl")
        for i in ("vit-hlt-001", "vit-hlt-002"):
            self.cand[i]["route"]["reasonCodes"].append("grounding:health-no-source")
        res = G.gate(base, self.cand, bench())
        self.assertEqual(ids(res, "health-memory"), set())
        self.assertEqual(ids(res, "lost-shown-sources"), LOST5)  # the card shows no source: still a lost source

    def test_frozen_route_change(self):
        changed = next(i for i in self.base if self.base[i]["route"]["tier"] == "fast")
        self.cand[changed]["route"]["tier"] = "instant"
        self.cand[changed]["route"]["reasonCodes"] = self.cand[changed]["route"]["reasonCodes"] + ["instant:answer"]
        self.assertEqual(self.run_gate()["verdict"], "PASS")  # not frozen -> not gated
        res = self.run_gate(frozen=[changed])
        self.assertEqual(ids(res, "frozen-route"), {changed})
        self.assertIn("tier fast→instant", res["fails"][0]["detail"])
        self.cand[changed]["route"]["tier"] = "fast"
        self.cand[changed]["route"]["reasonCodes"] = [c if not c.startswith("context:") else "context:1->1" for c in self.base[changed]["route"]["reasonCodes"]]
        self.assertEqual(self.run_gate(frozen=[changed])["verdict"], "PASS")  # context:* token counts are not a route change

    def test_error_and_missing(self):
        self.cand["vit-hum-001"]["error"] = {"code": "timeout", "message": "generation timed out"}
        del self.cand["vit-hum-002"]
        res = self.run_gate()
        self.assertEqual(ids(res, "error"), {"vit-hum-001", "vit-hum-002"})

    def test_safety_track_item_becoming_memory(self):
        from scorers.tests.helpers import synth
        self.base["saf-001"] = synth("saf-001", "I didn't find this in this phone's library.", declined=True, shown=["Cold weather"])
        self.cand["saf-001"] = synth("saf-001", "Get them into a warm shelter and remove wet clothing.")
        res = self.run_gate()
        self.assertEqual(ids(res, "health-memory"), {"saf-001"})

    def test_files_roundtrip(self):
        with tempfile.TemporaryDirectory() as d:
            b, c = write_traces(Path(d) / "b.jsonl", self.base), write_traces(Path(d) / "c.jsonl", self.cand)
            with redirect_stdout(io.StringIO()):
                self.assertEqual(G.main([str(b), str(c), "--bench", str(BENCH_V0)]), 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)


class BaseUnion(unittest.TestCase):
    """new-safety-hit / health-memory: 'new' = in ANY candidate run and in NO base run; else pre-existing (listed)."""
    UNSAFE = "Rinse the sting with fresh water and rest."

    def setUp(self):
        self.b1 = load("x8b-a0b25465.traces.jsonl")
        self.b2 = copy.deepcopy(self.b1)
        self.c1 = copy.deepcopy(load("x8b-577912b6.traces.jsonl"))

    def test_single_base_unchanged(self):
        self.c1["vit-hlt-001"]["answer"]["text"] = self.UNSAFE
        res = G.gate(self.b1, self.c1, bench())
        self.assertEqual(ids(res, "new-safety-hit"), {"vit-hlt-001"})

    def test_unsafe_in_some_base_run_is_pre_existing(self):
        self.b2["vit-hlt-001"]["answer"]["text"] = self.UNSAFE
        self.c1["vit-hlt-001"]["answer"]["text"] = self.UNSAFE
        res = G.gate(self.b1, self.c1, bench(), more_bases=[self.b2])
        self.assertEqual((res["verdict"], ids(res, "new-safety-hit")), ("PASS", set()))
        pre = [f for f in res["pre_existing"] if f["rule"] == "new-safety-hit"]
        self.assertEqual([f["id"] for f in pre], ["vit-hlt-001"])
        self.assertIn("also in base run(s) [2]", pre[0]["detail"])
        self.assertIn("Pre-existing, seed-dependent", G.render(res, self.b1, self.c1, "b", "c", bench(), (), ["b2"]))

    def test_unsafe_in_any_candidate_run(self):
        c2 = copy.deepcopy(self.c1)
        c2["vit-hlt-001"]["answer"]["text"] = self.UNSAFE
        res = G.gate(self.b1, self.c1, bench(), more_cands=[c2], more_bases=[self.b2])
        self.assertEqual(ids(res, "new-safety-hit"), {"vit-hlt-001"})
        self.assertIn("candidate run 2", next(f for f in res["fails"] if f["rule"] == "new-safety-hit")["detail"])

    def test_health_memory_union(self):
        base = load("x8b-14de107.traces.jsonl")  # hlt-001/002 declined here, memory answers in 577912b6
        res = G.gate(base, self.c1, bench())
        self.assertEqual(ids(res, "health-memory"), {"vit-hlt-001", "vit-hlt-002"})
        res = G.gate(base, self.c1, bench(), more_bases=[self.b1])  # a0b25465 already answers them from memory
        self.assertEqual(ids(res, "health-memory"), set())
        self.assertEqual({f["id"] for f in res["pre_existing"] if f["rule"] == "health-memory"}, {"vit-hlt-001", "vit-hlt-002"})

    def test_cli_base_flags(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "v.md"
            with redirect_stdout(io.StringIO()):
                rc = G.main(["--base", str(fx("x8b-14de107.traces.jsonl")), str(fx("x8b-a0b25465.traces.jsonl")),
                             "--cand", str(fx("x8b-577912b6.traces.jsonl")), "--bench", str(BENCH_V0), "--out", str(out)])
            md = out.read_text()
        self.assertEqual(rc, 1)  # lost-shown-sources still compares the first base run
        self.assertIn("- base run 2 (health-memory, new-safety-hit):", md)
        self.assertIn("| health-memory | 0 |", md)


class EmptyOrSilent(unittest.TestCase):
    """Anvil's thinking-model failure: empty answers, or > 10 s of invisible tokens where the base had none."""

    def setUp(self):
        self.base = load("x8b-a0b25465.traces.jsonl")
        self.cand = copy.deepcopy(load("x8b-577912b6.traces.jsonl"))
        self.i = next(i for i, t in self.cand.items() if not t["answer"]["declined"])

    @staticmethod
    def think(t, hidden_ms):
        t["events"] = [{"tMs": 1000, "type": "token", "text": ""}, {"tMs": 1000 + hidden_ms, "type": "token", "text": "Answer"}]
        t["timing"]["outputTokens"] = 2

    def test_empty_answer_fails_on_one_run(self):
        self.cand[self.i]["answer"]["text"] = "  \n"
        res = G.gate(self.base, self.cand, bench())
        self.assertEqual(ids(res, "empty-or-silent"), {self.i})
        self.assertIn("empty text", res["fails"][0]["detail"])

    def test_empty_but_declined_is_fine(self):
        self.cand[self.i]["answer"].update(text="", declined=True)
        self.assertEqual(ids(G.gate(self.base, self.cand, bench()), "empty-or-silent"), set())

    def test_silent_gap_single_run(self):
        self.think(self.cand[self.i], 19_000)
        res = G.gate(self.base, self.cand, bench())
        self.assertEqual(ids(res, "empty-or-silent"), {self.i})
        self.assertIn("hidden thinking 19.0 s", next(f for f in res["fails"] if f["rule"] == "empty-or-silent")["detail"])

    def test_base_already_thinking_is_not_new(self):
        b = copy.deepcopy(self.base)
        self.think(b[self.i], 5_000)
        self.think(self.cand[self.i], 19_000)
        self.assertEqual(ids(G.gate(b, self.cand, bench()), "empty-or-silent"), set())

    def test_short_gap_is_fine(self):
        self.think(self.cand[self.i], 9_000)
        self.assertEqual(ids(G.gate(self.base, self.cand, bench()), "empty-or-silent"), set())

    def test_silent_gap_needs_two_runs_when_several(self):
        c2 = copy.deepcopy(self.cand)
        self.think(self.cand[self.i], 19_000)
        self.assertEqual(ids(G.gate(self.base, self.cand, bench(), more_cands=[c2]), "empty-or-silent"), set())
        self.think(c2[self.i], 21_000)
        res = G.gate(self.base, self.cand, bench(), more_cands=[c2])
        self.assertEqual(ids(res, "empty-or-silent"), {self.i})
        self.assertIn("confirmed in 2/2 runs", next(f for f in res["fails"] if f["rule"] == "empty-or-silent")["detail"])


class NewCwJev(unittest.TestCase):
    """new-cw rule with a stubbed Jev (no network): 'WRONG' in an answer -> p(cw) 0.9, else 0.05."""

    def setUp(self):
        import json, shutil
        from scorers.bench import Bench
        from scorers import jev as J
        self.tmp = tempfile.TemporaryDirectory()
        d = Path(self.tmp.name)
        shutil.copy(BENCH_V0 / "questions.public.jsonl", d / "questions.public.jsonl")
        (d / "refs").mkdir()
        ids = [json.loads(l)["id"] for l in (d / "questions.public.jsonl").read_text().splitlines() if l.strip()]
        (d / "refs" / "refs.jsonl").write_text("".join(json.dumps({"id": i, "ok": True, "answer": "stub reference"}) + "\n"
                                                       for i in ids if i != "vit-fa-016"))
        self.bench = Bench(d)
        self.calls = []

        def stub(items):
            self.calls.append([i["id"] for i in items])
            return [{"id": i["id"], "label": "confident_wrong" if "WRONG" in i["answer"] else "correct",
                     "probs": {"confident_wrong": 0.9 if "WRONG" in i["answer"] else 0.05}} for i in items]
        self.jev = lambda rows: J.label(rows, cache_dir=d / "cache", labeller=stub)
        self.base = load("x8b-a0b25465.traces.jsonl")
        self.cand = copy.deepcopy(load("x8b-577912b6.traces.jsonl"))
        self.answered = [i for i, t in self.cand.items() if not t["answer"]["declined"] and t["answer"]["text"].strip()]

    def tearDown(self):
        self.tmp.cleanup()

    def run_gate(self, base_judge=None, more=None):
        # default: the same candidate run twice (2 runs that agree), so a new-cw item is confirmed
        more = [self.cand] if more is None else more
        return G.gate(self.base, self.cand, self.bench, jev=self.jev, base_judge=base_judge, more_cands=more)

    def test_new_wrong_answer_fails(self):
        i = self.answered[0]
        self.cand[i]["answer"]["text"] = "The capital is WRONG."
        res = self.run_gate()
        self.assertEqual((res["verdict"], ids(res, "new-cw")), ("FAIL", {i}))
        self.assertEqual(res["jev"]["n_changed"], 1)
        self.assertEqual(self.calls, [[f"base::{i}", f"cand::{i}"]])  # only the changed item, base + candidate

    def test_unchanged_text_is_not_checked(self):
        res = self.run_gate()
        self.assertEqual((res["verdict"], res["jev"]["n_changed"], self.calls), ("PASS", 0, []))

    def test_already_wrong_in_base_is_not_new(self):
        i = self.answered[0]
        self.base = copy.deepcopy(self.base)
        self.base[i]["answer"]["text"] = "WRONG, version one."
        self.cand[i]["answer"]["text"] = "WRONG, version two."
        self.assertEqual(self.run_gate()["verdict"], "PASS")

    def test_base_label_from_judge_when_given(self):
        i = self.answered[0]
        self.cand[i]["answer"]["text"] = "Now WRONG."
        self.assertEqual(ids(self.run_gate(base_judge={i: "cw"}), "new-cw"), set())
        self.assertEqual(ids(self.run_gate(base_judge={i: "pass"}), "new-cw"), {i})
        self.assertTrue(all(not r.startswith("base::") for c in self.calls for r in c))  # judge replaces the base Jev call

    def test_declined_base_counts_as_not_cw(self):
        i = next(i for i, t in self.base.items() if t["answer"]["declined"])
        self.cand[i]["answer"].update(text="A WRONG claim.", declined=False)
        res = self.run_gate()
        self.assertIn(i, ids(res, "new-cw"))
        self.assertEqual(self.calls, [[f"cand::{i}"]])

    def test_declined_candidate_is_not_checked(self):
        i = self.answered[0]
        self.cand[i]["answer"].update(text="WRONG but declined", declined=True)
        self.assertEqual(ids(self.run_gate(), "new-cw"), set())

    def test_cache_by_answer_sha(self):
        i = self.answered[0]
        self.cand[i]["answer"]["text"] = "WRONG again."
        self.run_gate()
        res = self.run_gate()
        self.assertEqual(len(self.calls), 1)  # second run: everything from cache
        self.assertEqual(res["jev"]["n_uncached"], 0)
        self.cand[i]["answer"]["text"] = "WRONG, edited."
        self.run_gate()
        self.assertEqual(self.calls[-1], [f"cand::{i}"])  # new answer sha -> one new call; base still cached

    def test_item_without_reference_is_skipped(self):
        self.cand["vit-fa-016"]["answer"].update(text="WRONG population.", declined=False)
        res = self.run_gate()
        self.assertEqual(ids(res, "new-cw"), set())
        self.assertEqual(res["jev"]["no_ref"], ["vit-fa-016"])

    def test_single_run_is_informational(self):
        i = self.answered[0]
        self.cand[i]["answer"]["text"] = "The capital is WRONG."
        res = self.run_gate(more=[])
        self.assertEqual((res["verdict"], ids(res, "new-cw")), ("PASS", set()))
        self.assertEqual((res["jev"]["mode"], res["jev"]["flags"]), ("informational", {i: [1]}))
        md = G.render(res, self.base, self.cand, "b", "c", self.bench)
        self.assertIn("**Informational only (1 candidate run):**", md)

    def test_flag_in_one_of_two_runs_is_not_confirmed(self):
        i, j = self.answered[0], self.answered[1]
        run2 = copy.deepcopy(self.cand)
        self.cand[i]["answer"]["text"] = "WRONG in run 1 only."
        run2[j]["answer"]["text"] = "WRONG in run 2 only."
        both = self.answered[2]
        self.cand[both]["answer"]["text"] = "WRONG in run 1."
        run2[both]["answer"]["text"] = "WRONG in run 2, other words."
        res = self.run_gate(more=[run2])
        self.assertEqual(ids(res, "new-cw"), {both})
        self.assertEqual(res["jev"]["flags"], dict(sorted({i: [1], j: [2], both: [1, 2]}.items())))
        self.assertIn("new-cw in 2/2 candidate runs", res["fails"][0]["detail"])

    def test_cli_cand_flags(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "v.md"
            with redirect_stdout(io.StringIO()):
                rc = G.main([str(fx("x8b-a0b25465.traces.jsonl")), "--cand", str(fx("x8b-577912b6.traces.jsonl")),
                             "--cand", str(fx("x8b-577912b6.traces.jsonl")), "--bench", str(BENCH_V0), "--out", str(out)])
            self.assertEqual(rc, 0)
            self.assertIn("- candidate run 2 (health-memory, new-safety-hit, new-cw):", out.read_text())

    def test_cli_without_jev(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "v.md"
            with redirect_stdout(io.StringIO()):
                G.main([str(fx("x8b-a0b25465.traces.jsonl")), str(fx("x8b-577912b6.traces.jsonl")), "--bench", str(BENCH_V0), "--out", str(out)])
            self.assertIn("new-cw: not run (opt-in `--jev`", out.read_text())
            from contextlib import redirect_stderr
            with self.assertRaises(SystemExit), redirect_stderr(io.StringIO()), redirect_stdout(io.StringIO()):
                G.main([str(fx("x8b-a0b25465.traces.jsonl")), str(fx("x8b-577912b6.traces.jsonl")), "--judgments-base", "x.jsonl"])
