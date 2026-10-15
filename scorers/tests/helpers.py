"""Test helpers: fixture paths, the in-repo bench v0 copy, synthetic traces."""
import copy, json, shutil, subprocess, sys, unittest
from pathlib import Path

sys.dont_write_bytecode = True
FIX = Path(__file__).resolve().parent / "fixtures"
REPO = FIX.parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))
BENCH_V0 = FIX / "bench-v0"
HAS_NODE = shutil.which("node") is not None


# Fixtures are not shipped in the public repo (they were real local runs): fixture-bound tests skip.
FIXTURES_OK = (FIX / "bench-v0" / "questions.public.jsonl").exists()
FIXTURES_MSG = "fixtures are not shipped in the public repo"


def fx(name):
    p = FIX / name
    if not p.exists():
        raise unittest.SkipTest(FIXTURES_MSG)
    return p


def load(name):
    from scorers.trace import read_traces
    return read_traces(FIX / name)


def bench():
    from scorers.bench import Bench
    return Bench(BENCH_V0)


def write_traces(path, traces):
    Path(path).write_text("".join(json.dumps(t) + "\n" for t in (traces.values() if isinstance(traces, dict) else traces)))
    return path


def synth(item_id, text, declined=False, shown=(), adapter="desktop-node", **over):
    """A minimal valid EvalTrace built from a real fixture trace (keeps every required key)."""
    base = copy.deepcopy(next(iter(load("x8b-577912b6.traces.jsonl").values())))
    base.update(itemId=item_id, question=item_id, error=None)
    base["answer"].update(text=text, declined=declined, shown=list(shown), cited=[])
    base["runtime"]["adapter"] = adapter
    for k, v in over.items():
        base[k] = v
    return base


def node_json(script):
    p = subprocess.run(["node", "--input-type=module", "-e", script], capture_output=True, text=True, cwd=REPO)
    if p.returncode:
        raise RuntimeError(p.stderr)
    return json.loads(p.stdout)
