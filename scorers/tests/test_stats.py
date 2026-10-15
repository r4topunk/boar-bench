"""The Python bootstrap is the JS one (judge-core mulberry32 + bootstrapCI), bit for bit."""
import json, unittest

from scorers.tests.helpers import HAS_NODE, node_json
from scorers import stats

LIB = "./scorers/vendor/eval-lib/judge-core.mjs"


@unittest.skipUnless(HAS_NODE, "node is required")
class SameAsJudgeCore(unittest.TestCase):
    def test_rng_sequence(self):
        js = node_json(f"import {{ rng }} from '{LIB}'; const r = rng(11); console.log(JSON.stringify(Array.from({{length: 50}}, r)));")
        r = stats.rng(11)
        self.assertEqual([r() for _ in range(50)], js)

    def test_bootstrap_ci_mean(self):
        xs = [1, 0, -1, 0, 1, 1, -9, 0, 1, 0, 0, 1]
        js = node_json(f"import {{ bootstrapCI }} from '{LIB}'; const xs = {json.dumps(xs)};"
                       "console.log(JSON.stringify(bootstrapCI(xs, (s) => s.reduce((a, x) => a + x, 0) / s.length, { seed: 11 })));")
        self.assertEqual(stats.bootstrap_ci(xs, stats.mean, seed=11), js)


class Paired(unittest.TestCase):
    def test_identical_arms_have_zero_difference(self):
        a = {str(i): (1 + i % 3, 4.5) for i in range(30)}
        p = stats.paired_ratio_diff(a, dict(a))
        self.assertEqual((p["diff"], p["diff_ci95"]), (0.0, [0.0, 0.0]))
        self.assertTrue(p["verdict"].startswith("no detectable"))

    def test_clear_improvement(self):
        a = {str(i): (1.0, 4.0) for i in range(30)}
        b = {str(i): (3.0 + (i % 2), 4.0) for i in range(30)}
        p = stats.paired_ratio_diff(a, b)
        self.assertGreater(p["diff_ci95"][0], 0)
        self.assertTrue(p["verdict"].startswith("B better"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
