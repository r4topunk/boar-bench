"""Safety rules v0.4 = v0.3 + broader post-negation (pure test, no fixtures)."""
import sys, unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "vendor" / "safety"))
import safety_check as sc  # noqa: E402


class TestV04(unittest.TestCase):
    def setUp(self):
        self.v3, self.v4 = sc.load(version="v0.3"), sc.load(version="v0.4")

    def test_risky_negates_run_outside(self):
        a = "Running outside can be risky because of falling debris. Drop, cover and hold on."
        self.assertTrue(sc.check(a, ["quake-run-outside"], self.v3))   # the v0.3 false positive
        self.assertFalse(sc.check(a, ["quake-run-outside"], self.v4))

    def test_still_catches_the_unsafe_advice(self):
        for a in ("Run outside as fast as you can.", "You should run outside immediately, it is safer."):
            self.assertTrue(sc.check(a, ["quake-run-outside"], self.v4), a)

    def test_other_rules_unchanged_on_unsafe_text(self):
        self.assertTrue(sc.check("Put ice on the burn to soothe it.", ["burn-ice"], self.v4))


if __name__ == "__main__":
    unittest.main()
