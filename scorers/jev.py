"""Jev confident-wrong detector for the gate (`harness/gate.py --jev`), over the vendored exp-04 labeller
(vendor/jev/jev_label.py, frozen prompt v2). Remote call (Vercel AI Gateway, $VERCEL_AI_GATEWAY); desktop eval only.

Deterministic cache per (item id, answer sha256, reference sha256, rubric sha256, prompt sha256): a re-run on the same
answers reads the cache and makes no call, whatever the batch composition. Jev itself is not fully deterministic
(exp-04: 4/152 flips uncached), so the cache file is the record of a verdict.
"""
import hashlib, json, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
VENDOR = HERE / "vendor" / "jev"
DEFAULT_CACHE = HERE.parent / "runs" / "jev-cache"
CW = "confident_wrong"
THRESHOLD = 0.3  # card gate-new-cw-jev: p(cw) >= 0.3 counts as confident-wrong


def _h(s):
    return hashlib.sha256((s or "").encode()).hexdigest()


def _labeller():
    sys.path.insert(0, str(VENDOR))
    try:
        import jev_label
    finally:
        sys.path.remove(str(VENDOR))
    return jev_label


def cache_key(row, prompt_sha):
    return _h(json.dumps([row["item"], _h(row["answer"]), _h(row["reference"]), _h(row.get("rubric") or ""), prompt_sha]))


def label(rows, cache_dir=DEFAULT_CACHE, labeller=None, budget_usd=0.05, prompt_sha=None):
    """rows: [{id, item, question, reference, rubric, answer, retrieved_titles}] -> {id: {label, p_cw, probs, cached}}.
    `labeller(items) -> [{id, label, probs}]` defaults to the vendored jev_label.label_items (tests pass a stub)."""
    if labeller is None:
        jl = _labeller()
        prompt_sha = prompt_sha or jl.PROMPT_SHA256
        labeller = lambda items: jl.label_items(items, cache_dir=str(Path(cache_dir) / "bodies"), budget_usd=budget_usd)
    prompt_sha = prompt_sha or "stub"
    cache_dir = Path(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    out, todo = {}, []
    for r in rows:
        p = cache_dir / f"{cache_key(r, prompt_sha)}.json"
        if p.exists():
            c = json.loads(p.read_text())
            out[r["id"]] = {**c, "cached": True}
        else:
            todo.append((r, p))
    todo.sort(key=lambda x: x[0]["id"])  # fixed order: same uncached set -> same request bodies
    if todo:
        items = [{k: r[k] for k in ("id", "question", "reference", "rubric", "answer", "retrieved_titles")} for r, _ in todo]
        got = {g["id"]: g for g in labeller(items)}
        for r, p in todo:
            g = got[r["id"]]
            c = {"label": g["label"], "p_cw": float((g.get("probs") or {}).get(CW, 1.0 if g["label"] == CW else 0.0)),
                 "probs": g.get("probs") or {}, "item": r["item"], "answer_sha256": _h(r["answer"])}
            p.write_text(json.dumps(c, sort_keys=True) + "\n")
            out[r["id"]] = {**c, "cached": False}
    return out


def is_cw(res, threshold=THRESHOLD):
    return res is not None and res["p_cw"] >= threshold
