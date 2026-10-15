"""Bench resolution: one directory flag (`--bench DIR`) gives questions, gold files, references, the safety track
and frozen labels. Switching from bench v0 (rnd/bench/questions/v0) to v0.1 (bench/v0.1) is one flag or one line
in harness/config.json.

Lookup, first match wins (paths in bench.json are relative to the bench dir):
  questions      bench.json "questions" | questions.public.jsonl | questions.jsonl
  references     --refs | bench.json "refs" | refs/*.jsonl (one file) | v0 layout ../../refs/<dir name>/claude-code__opus.jsonl
  safety rules   bench.json "safety_dir" | safety/rules.<v>.json in the bench | scorers/vendor/safety (v0.3)
  safety track   bench.json "safety_track" | <safety dir>/track.<v>.jsonl
  frozen labels  item field frozen_label/frozen = true | frozen-labels.json {"ids": [...]} | bench.json "frozen"
  gold sources   item field gold_sources/gold_source_titles | gold/sources.json {id: [title, ...]}
"""
import importlib.util, json, os, warnings
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
CONFIG = REPO / "harness" / "config.json"
VENDOR_SAFETY = HERE / "vendor" / "safety"
DEFAULT_SAFETY_VERSION = "v0.3"
HEALTH_CATEGORIES = {"health", "danger", "danger-situation"}


def read_jsonl(path):
    return [json.loads(l) for l in Path(path).read_text().splitlines() if l.strip()]


def default_bench_dir():
    """--bench default: $BOAR_EVAL_BENCH, else harness/config.json "bench" (relative to the repo root)."""
    if os.environ.get("BOAR_EVAL_BENCH"):
        return Path(os.environ["BOAR_EVAL_BENCH"])
    cfg = json.loads(CONFIG.read_text()) if CONFIG.exists() else {}
    if not cfg.get("bench"):
        raise SystemExit("no bench: pass --bench DIR or set harness/config.json 'bench'")
    return (REPO / cfg["bench"]).resolve()


class Bench:
    def __init__(self, path=None, refs=None, safety_version=None):
        self.dir = Path(path).resolve() if path else default_bench_dir()
        if not self.dir.is_dir():
            raise SystemExit(f"bench dir not found: {self.dir}")
        man = self.dir / "bench.json"
        self.manifest = json.loads(man.read_text()) if man.exists() else {}
        self.questions_path = self._first(self.manifest.get("questions"), "questions.public.jsonl", "questions.jsonl")
        if not self.questions_path:
            raise SystemExit(f"no questions file in {self.dir}")
        self.questions = read_jsonl(self.questions_path)
        self.ids = [q["id"] for q in self.questions]
        self.by_id = {q["id"]: q for q in self.questions}
        self.refs_path = Path(refs) if refs else self._refs()
        self._safety_version = safety_version
        self._safety = None
        self.track = self._track()
        self.track_by_id = {q["id"]: q for q in self.track}

    # ---------------------------------------------------------------- paths
    def _first(self, *names):
        for n in names:
            if n and (self.dir / n).exists():
                return self.dir / n
        return None

    def _refs(self):
        if self.manifest.get("refs"):
            return self.dir / self.manifest["refs"]
        cands = sorted((self.dir / "refs").glob("*.jsonl")) if (self.dir / "refs").is_dir() else []
        cands = [c for c in cands if not c.name.startswith("MANIFEST")]
        if len(cands) == 1:
            return cands[0]
        legacy = self.dir.parent.parent / "refs" / self.dir.name / "claude-code__opus.jsonl"
        return legacy if legacy.exists() else None

    def references(self):
        """{item id: reference answer text} (ok rows of the references file), {} when the bench has none."""
        if not self.refs_path or not Path(self.refs_path).exists():
            return {}
        return {r["id"]: r["answer"] for r in read_jsonl(self.refs_path) if r.get("ok", True) and r.get("answer")}

    def refs_manifest(self):
        if not self.refs_path:
            return None
        p = self.refs_path.parent / "MANIFEST.json"
        return json.loads(p.read_text()) if p.exists() else None

    def safety_dir(self):
        # An explicitly requested rules version the bench doesn't ship (e.g. v0.4, newer than the frozen bench) comes
        # from the vendored rules; the bench's own track and overlay ids are unchanged.
        if self._safety_version and not any((d / f"rules.{self._safety_version}.json").exists()
                                            for d in (self.dir / self.manifest.get("safety_dir", "safety"),)):
            return VENDOR_SAFETY
        if self.manifest.get("safety_dir"):
            return self.dir / self.manifest["safety_dir"]
        if (self.dir / "safety").is_dir() and list((self.dir / "safety").glob("rules.*.json")):
            return self.dir / "safety"
        return VENDOR_SAFETY

    def safety_version(self):
        if self._safety_version:
            return self._safety_version
        if self.manifest.get("safety_version"):
            return self.manifest["safety_version"]
        d = self.safety_dir()
        if (d / f"rules.{DEFAULT_SAFETY_VERSION}.json").exists():
            return DEFAULT_SAFETY_VERSION
        vs = sorted(p.name[len("rules."):-len(".json")] for p in d.glob("rules.*.json"))
        return vs[-1] if vs else None

    def _track(self):
        if self.manifest.get("safety_track"):
            return read_jsonl(self.dir / self.manifest["safety_track"])
        p = self.safety_dir() / f"track.{self.safety_version()}.jsonl"
        return read_jsonl(p) if p.exists() else []

    def gold_file(self, q):
        return self.dir / q["grading"]["gold_file"]

    # ---------------------------------------------------------------- items
    def items_for(self, trace_ids):
        """The public split plus every safety-track item that has a trace (the track never counts as missing)."""
        extra = [q for q in self.track if q["id"] in set(trace_ids) and q["id"] not in self.by_id]
        return self.questions + extra

    def item(self, qid):
        return self.by_id.get(qid) or self.track_by_id.get(qid)

    def safety(self):
        """safety_check state for the configured rules version (vendored v0.3 by default)."""
        if self._safety is None:
            d = self.safety_dir()
            v = self.safety_version()
            # v0.5+ ships its own checker (safety_check.v0.5.py) and no overlay of its own: its rules apply to the item ids
            # of the newest overlay at or below it (addendum-02). Older versions load exactly as before.
            checker = d / f"safety_check.{v}.py" if (d / f"safety_check.{v}.py").exists() else d / "safety_check.py"
            overlay = d / f"overlay.{v}.json"
            if not overlay.exists():
                older = sorted((o for o in d.glob("overlay.v*.json") if o.name[len("overlay."):-len(".json")] <= v),
                               key=lambda o: o.name)
                if older:
                    overlay = older[-1]
            spec = importlib.util.spec_from_file_location(f"safety_check_{abs(hash(str(checker)))}", checker)
            sc = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(sc)
            with warnings.catch_warnings():  # the vendored loader leaves its files to the GC (ResourceWarning noise)
                warnings.simplefilter("ignore", ResourceWarning)
                S = sc.load(rules_path=d / f"rules.{v}.json", overlay_path=overlay)
            # v0.5 'review' hits (warning sentences) count only after the coordinator's blind adjudication (addendum-02):
            # S["check"] (gate, scorer) drops them; S["check_all"] keeps them for listing. Pre-v0.5 hits carry no status.
            S["check"] = lambda answer, rule_ids, S_, _c=sc.check: [h for h in _c(answer, rule_ids, S_) if h.get("status") != "review"]
            S["check_all"], S["rules_for"], S["dir"] = sc.check, sc.rules_for, str(d)
            self._safety = S
        return self._safety

    def rules_for(self, qid):
        q = self.item(qid)
        return self.safety()["rules_for"](q, self.safety()) if q else []

    def is_health(self, qid):
        """Health/danger item: bench danger=true, a safety-track item, an item with safety rules (overlay), or a
        health/danger category."""
        q = self.item(qid)
        if q is None:
            return False
        return bool(q.get("danger")) or qid in self.track_by_id or bool(self.rules_for(qid)) or q.get("category") in HEALTH_CATEGORIES

    def frozen_ids(self):
        ids = {q["id"] for q in self.questions + self.track if q.get("frozen_label") or q.get("frozen") is True}
        p = self.dir / "frozen-labels.json"
        if p.exists():
            doc = json.loads(p.read_text())
            ids |= set(doc["ids"] if isinstance(doc, dict) else doc)
        ids |= set(self.manifest.get("frozen") or [])
        return ids

    def gold_sources(self):
        """{item id: [gold source title, ...]} for items that have them."""
        out = {}
        p = self.dir / "gold" / "sources.json"
        if p.exists():
            out.update({k: v for k, v in json.loads(p.read_text()).items() if not k.startswith("_") and v})
        for q in self.questions + self.track:
            g = q.get("gold_sources") or q.get("gold_source_titles")
            if g:
                out[q["id"]] = [x if isinstance(x, str) else x["title"] for x in g]
        return out
