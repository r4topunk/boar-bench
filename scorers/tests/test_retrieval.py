"""Retrieval axis: recall@k on retrieval.raw and on-topic gold dropped, or 'no gold'."""
import json, tempfile, unittest
from pathlib import Path

from scorers.tests.helpers import BENCH_V0, load, synth
from scorers.bench import Bench
from scorers.retrieval import score_retrieval
from scorers.tests.helpers import FIXTURES_OK, FIXTURES_MSG
import unittest as _ut
if not FIXTURES_OK:
    raise _ut.SkipTest(FIXTURES_MSG)

ref = lambda t, s=None: {"title": t, "section": s, "source": None, "similarity": None}


class Retrieval(unittest.TestCase):
    def test_no_gold_on_bench_v0(self):
        r = score_retrieval(load("x8b-577912b6.traces.jsonl"), Bench(BENCH_V0).gold_sources())
        self.assertEqual(r["status"], "no gold")
        self.assertEqual(r["line"], "no gold: 0/54 traced items have gold source titles")
        self.assertEqual(r["descriptive"]["legacy_traces"], 54)

    def test_recall_and_dropped(self):
        a = synth("q1", "x")
        a["retrieval"] = {"raw": [ref("Snakebite"), ref("Thailand"), ref("Hiking")], "kept": [ref("Snakebite")], "dropped": [ref("Thailand"), ref("Hiking")]}
        b = synth("q2", "y")
        b["retrieval"] = {"raw": [ref("Andes"), ref("Altitude sickness", "Treatment")], "kept": [ref("Andes")], "dropped": [ref("Altitude sickness", "Treatment")]}
        c = synth("q3", "z")  # no gold for q3
        gold = {"q1": ["snakebite", "First aid"], "q2": ["Altitude sickness#Treatment"]}
        r = score_retrieval({"q1": a, "q2": b, "q3": c}, gold, k=5)
        self.assertEqual(r["status"], "ok")
        self.assertEqual(r["n_gold_items"], 2)
        self.assertAlmostEqual(r["recall_at_k"], (0.5 + 1.0) / 2)
        self.assertEqual(r["on_topic_gold_dropped"], [{"id": "q2", "gold_dropped": ["Altitude sickness#Treatment"]}])
        self.assertEqual(score_retrieval({"q2": b}, gold, k=1)["recall_at_k"], 0.0)  # gold is raw[1], outside k=1

    def test_gold_from_bench_item_field(self):
        with tempfile.TemporaryDirectory() as d:
            q = json.loads((BENCH_V0 / "questions.public.jsonl").read_text().splitlines()[0])
            q["gold_sources"] = ["Mozi"]
            q["frozen_label"] = True
            (Path(d) / "questions.public.jsonl").write_text(json.dumps(q) + "\n")
            b = Bench(d)
            self.assertEqual(b.gold_sources(), {q["id"]: ["Mozi"]})
            self.assertEqual(b.frozen_ids(), {q["id"]})


if __name__ == "__main__":
    unittest.main(verbosity=2)


class PreAnswerSources(unittest.TestCase):
    """QUEUE #10: drops are judged against the last `sources` event, not retrieval.kept (emptied on a decline)."""

    @staticmethod
    def trace(raw, kept, events, declined):
        t = synth("q", "I didn't find this.", declined=declined)
        t["retrieval"] = {"raw": [ref(x) for x in raw], "kept": [ref(x) for x in kept], "dropped": []}
        t["events"] = [{"tMs": n, "type": "sources", "sources": [ref(x) for x in ev]} for n, ev in enumerate(events)]
        return t

    def test_decline_artifact_is_not_a_drop(self):
        t = self.trace(["Wikivoyage: Montenegro", "Croatia"], [], [["Croatia"], ["Wikivoyage: Montenegro"]], declined=True)
        r = score_retrieval({"q": t}, {"q": ["Montenegro"]})
        self.assertEqual(r["n_on_topic_gold_dropped"], 0)
        self.assertEqual(r["declined_with_gold"], [{"id": "q", "gold_in_sources": ["Montenegro"]}])
        self.assertEqual(r["pre_answer_from"], {"sources-event": 1, "kept": 0})

    def test_real_drop_uses_last_sources_event(self):
        # gold was in an earlier sources event but not in the last one before the answer -> dropped
        t = self.trace(["Altitude sickness", "North Sikkim"], [], [["Altitude sickness"], ["North Sikkim"]], declined=False)
        r = score_retrieval({"q": t}, {"q": ["Altitude sickness"]})
        self.assertEqual(r["on_topic_gold_dropped"], [{"id": "q", "gold_dropped": ["Altitude sickness"]}])
        self.assertEqual(r["n_declined_with_gold"], 0)

    def test_fallback_to_kept_without_sources_event(self):
        t = self.trace(["A", "B"], ["B"], [], declined=False)
        r = score_retrieval({"q": t}, {"q": ["A", "B"]})
        self.assertEqual((r["on_topic_gold_dropped"], r["pre_answer_from"]), ([{"id": "q", "gold_dropped": ["A"]}], {"sources-event": 0, "kept": 1}))

    def test_gold_not_retrieved_is_not_a_drop(self):
        t = self.trace(["B"], ["B"], [["B"]], declined=False)
        self.assertEqual(score_retrieval({"q": t}, {"q": ["A"]})["n_on_topic_gold_dropped"], 0)
