"""judge.mjs bench resolution (--dry-run, no judge calls): a bench without bench.json whose refs/MANIFEST.json names the
questions file and pins the frozen refs file's sha256 (bench v0.2 layout), next to the v0.1 layout (one refs file)."""
import hashlib, json, subprocess, tempfile, unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
JUDGE = REPO / "harness" / "judge.mjs"


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def write_jsonl(p, rows):
    Path(p).write_text("".join(json.dumps(r) + "\n" for r in rows))


def dry_run(bench, tmp):
    traces = Path(tmp) / "t.jsonl"
    traces.write_text("")
    out = subprocess.run(["node", str(JUDGE), "--bench", str(bench), "--traces", str(traces), "--out", str(Path(tmp) / "j.jsonl"), "--dry-run"],
                         capture_output=True, text=True, cwd=REPO)
    return out


class JudgeBenchResolve(unittest.TestCase):
    def make_v02(self, tmp, pin_frozen=True):
        b = Path(tmp) / "bench-v02"
        (b / "refs").mkdir(parents=True)
        q = b / "questions.v02-new.jsonl"
        write_jsonl(q, [{"id": "x-001", "question": "Q1", "category": "explanation"}])
        write_jsonl(b / "refs" / "raw.new.jsonl", [{"id": "x-001", "ok": True, "answer": "raw"}, {"id": "x-001", "ok": True, "answer": "raw2"}])
        write_jsonl(b / "refs" / "refs.jsonl", [{"id": "x-001", "ok": True, "answer": "frozen"}])
        man = {"questions_file": q.name, "questions_sha256": sha(q),
               "refs_jsonl_sha256": sha(b / "refs" / "refs.jsonl") if pin_frozen else "0" * 64}
        (b / "refs" / "MANIFEST.json").write_text(json.dumps(man))
        return b

    def test_v02_layout_uses_manifest_questions_and_pinned_refs(self):
        with tempfile.TemporaryDirectory() as tmp:
            b = self.make_v02(tmp)
            r = dry_run(b, tmp)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn(f"refs {sha(b / 'refs' / 'refs.jsonl')[:12]}", r.stdout)
            self.assertIn(f"questions {sha(b / 'questions.v02-new.jsonl')[:12]}", r.stdout)

    def test_v02_layout_without_a_matching_pin_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            b = self.make_v02(tmp, pin_frozen=False)
            r = dry_run(b, tmp)
            self.assertNotEqual(r.returncode, 0)
            self.assertIn("no references", r.stderr)

    def test_v01_layout_unchanged(self):
        with tempfile.TemporaryDirectory() as tmp:
            b = Path(tmp) / "bench-v01"
            (b / "refs").mkdir(parents=True)
            write_jsonl(b / "questions.public.jsonl", [{"id": "y-001", "question": "Q", "category": "explanation"}])
            write_jsonl(b / "refs" / "claude-code__opus.jsonl", [{"id": "y-001", "ok": True, "answer": "r"}])
            r = dry_run(b, tmp)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn(f"refs {sha(b / 'refs' / 'claude-code__opus.jsonl')[:12]}", r.stdout)


if __name__ == "__main__":
    unittest.main()
