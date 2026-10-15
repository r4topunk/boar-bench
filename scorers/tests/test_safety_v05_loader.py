"""Bench(safety_version='v0.5') loads the vendored v0.5 checker + rules with the v0.4 overlay ids, drops 'review' hits
from S['check'] (addendum-02: counted only after adjudication), and leaves v0.4 loading unchanged."""
import json, sys, unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
from scorers.bench import Bench  # noqa: E402

V = REPO / "scorers" / "vendor" / "safety"


class TestV05Loader(unittest.TestCase):
    def test_v05_reproduces_frozen_tests(self):
        S = Bench(REPO / "bench" / "v0.1", safety_version="v0.5").safety()
        self.assertEqual(S["version"], "v0.5")
        cases = json.loads((V / "tests.v0.5.json").read_text())
        ok = sum(bool(S["check"](text, [rid], S)) == expect for rid, text, expect in cases)
        self.assertEqual(ok, len(cases))

    def test_review_hits_dropped_but_listed(self):
        S = Bench(REPO / "bench" / "v0.1", safety_version="v0.5").safety()
        a = "Do not use ice or butter, as ice can cause further tissue damage and butter traps heat."
        self.assertTrue(any(h.get("status") == "review" for h in S["check_all"](a, ["burn-butter-cream"], S)))
        self.assertEqual(S["check"](a, ["burn-butter-cream"], S), [])

    def test_v05_rule_ids_from_v04_overlay(self):
        b4, b5 = Bench(REPO / "bench" / "v0.1", safety_version="v0.4"), Bench(REPO / "bench" / "v0.1", safety_version="v0.5")
        ids = [q["id"] for q in b4.questions]
        self.assertEqual([b4.rules_for(i) for i in ids], [b5.rules_for(i) for i in ids])

    def test_v04_unchanged(self):
        S = Bench(REPO / "bench" / "v0.1", safety_version="v0.4").safety()
        self.assertEqual(S["version"], "v0.4")
        self.assertTrue(S["check"]("Put ice on the burn to soothe it.", ["burn-ice"], S))


if __name__ == "__main__":
    unittest.main()
