"""harness/lengthctl.py: a gain made of length alone vanishes after length control; a gain unrelated to length stays."""
import math, random, unittest

from harness.lengthctl import lc, words

ITEMS = [f"q{i}" for i in range(80)]


def run(words_mult, slope, bonus, seed):
    """Per item: a fixed difficulty, base length ~60 words x words_mult; judge adds slope * log(words / 60) + bonus."""
    rnd, item = random.Random(seed), random.Random(0)
    out = {}
    for i in ITEMS:
        hard = item.gauss(0, 0.8)
        w = max(1, int(60 * words_mult * math.exp(rnd.gauss(0, 0.3))))
        out[i] = (2.5 - hard + slope * math.log(w / 60) + bonus + rnd.gauss(0, 0.15), 4.8 + rnd.gauss(0, 0.1), w)
    return out


class LengthControl(unittest.TestCase):
    def test_pure_length_bias_vanishes(self):
        # The judge likes length (+1 point per unit log words); the arm is only 2.7x longer.
        res = lc([run(1, 1.0, 0, 1), run(1, 1.0, 0, 2)], [run(math.e, 1.0, 0, 3), run(math.e, 1.0, 0, 4)])
        self.assertGreater(res["gain"], 0.15)
        self.assertAlmostEqual(res["beta"], 1.0, delta=0.15)
        self.assertLess(abs(res["lc_gain"]), 0.03)

    def test_real_gain_survives(self):
        # Same length, the arm is better by 0.5 points per item.
        res = lc([run(1, 1.0, 0, 5)], [run(1, 1.0, 0.5, 6)])
        self.assertAlmostEqual(res["paired_gain"], 0.5 / 4.8, delta=0.03)
        self.assertAlmostEqual(res["lc_gain"], res["paired_gain"], delta=0.03)

    def test_inputs(self):
        with self.assertRaises(ValueError):
            lc([], [run(1, 0, 0, 7)])
        self.assertEqual(words("Mozi (c. 470–391 BCE) argued"), 6)
        self.assertEqual(words(""), 0)


if __name__ == "__main__":
    unittest.main()
