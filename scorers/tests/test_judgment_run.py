import json
from pathlib import Path
import shutil
import tempfile
import unittest

from scorers.score import score


@unittest.skipUnless(shutil.which("node"), "score uses the Node judge bridge")
class JudgmentRun(unittest.TestCase):
    def run_score(self, orders):
        rubric = {"correctness": 4, "usefulness": 4, "completeness": 4}
        mapped = {"winner": "tie", "boar": rubric, "ref": rubric}
        trace = {"runId": "current", "answer": {"text": "Blue.", "declined": False}}
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "questions.jsonl").write_text(json.dumps({"id": "q", "category": "test", "question": "What color?"}))
            path = root / "judgments.jsonl"
            rows = [dict(queryId="q", order=order, ok=True, mapped=mapped, **fields) for order, fields in orders]
            path.write_text("\n".join(map(json.dumps, rows)))
            return score({"q": trace}, bench=root, judgments=path, safety=False)["quality"]

    def test_one_conflicting_order_fails(self):
        with self.assertRaisesRegex(RuntimeError, r"Judgment run mismatch for q \(boarB\).*old.*current"):
            self.run_score([("boarA", {"runId": "current"}), ("boarB", {"runId": "old"})])

    def test_superseded_and_legacy_rows(self):
        result = self.run_score([("boarA", {"runId": "old"}), ("boarA", {"runId": "current"}), ("boarB", {})])
        self.assertEqual(result["n_judged"], 1)
