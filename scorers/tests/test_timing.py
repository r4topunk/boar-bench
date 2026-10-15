"""Visible TTFT from events (a research agent: thinking models emit empty first tokens). Pure, synthetic events."""
import unittest

from scorers.timing import visible_timing


def tr(events, ttft=None, out_tokens=None):
    return {"events": events, "timing": {"ttftMs": ttft, "outputTokens": out_tokens}}


tok = lambda t, s: {"tMs": t, "type": "token", "text": s}


class Visible(unittest.TestCase):
    def test_thinking_model_empty_first_tokens(self):
        v = visible_timing(tr([tok(3097, ""), tok(3147, " "), tok(3195, "\n"), tok(21259, "Mill"), tok(21306, "'s")], ttft=3097, out_tokens=5))
        self.assertEqual((v["ttft_visible_ms"], v["ttft_receipt_ms"], v["hidden_think_ms"]), (21259, 3097, 21259 - 3097))

    def test_plain_model_no_hidden_time(self):
        v = visible_timing(tr([tok(5197, "Mo"), tok(5240, "zi")], ttft=5197, out_tokens=2))
        self.assertEqual((v["ttft_visible_ms"], v["hidden_think_ms"]), (5197, 0.0))

    def test_instant_snippet_counts_first(self):
        ev = [{"tMs": 248, "type": "instant", "snippet": {"text": "- Bears: temperate forest", "sourceIndex": 1}}, tok(4000, ""), tok(9000, "Bears")]
        v = visible_timing(tr(ev, ttft=248, out_tokens=2))
        self.assertEqual((v["ttft_visible_ms"], v["hidden_think_ms"]), (248, 5000))

    def test_decline_without_tokens_uses_done(self):
        v = visible_timing(tr([{"tMs": 186.5, "type": "done", "finalText": "I didn't find this in this phone's library."}], ttft=186.4, out_tokens=0))
        self.assertEqual((v["ttft_visible_ms"], v["visible_from"], v["hidden_think_ms"]), (186.5, "done", None))

    def test_fixed_route_text_without_final_text(self):
        t = tr([{"tMs": 40.0, "type": "done", "finalText": ""}], ttft=None, out_tokens=0)
        t["answer"] = {"text": "The offline places pack is not installed."}
        self.assertEqual(visible_timing(t)["ttft_visible_ms"], 40.0)

    def test_truncated_invisible_tokens_are_unknown(self):
        ev = [tok(100 + n, "") for n in range(32)] + [{"tMs": 30000, "type": "done", "finalText": "Answer."}]
        v = visible_timing(tr(ev, ttft=100, out_tokens=200))
        self.assertIsNone(v["ttft_visible_ms"])
        self.assertIsNone(v["hidden_think_ms"])

    def test_empty_events(self):
        self.assertIsNone(visible_timing(tr([], ttft=50))["ttft_visible_ms"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
