#!/usr/bin/env python3
"""Similarity gates for bench v0.3-ext (gate G2, spec section 5) -> bench/v0.3/similarity.json (ids and numbers only).

Collision = word-Jaccard > 0.30 (tokens() of bench/v0.1/validate.py) OR BAAI/bge-small-en-v1.5 cosine >= 0.90
(sentence-transformers, normalize_embeddings=True). Base pools: the v0.3 items among themselves, v0.1 public, safety track
v0.3, held-out v0.1 (rnd/private-heldout files, read as bench/v0.1/build.py reads them) and Field Atlas @87bb6e9 (sha-pinned, git show).
Extra pools (--pools): v0.2-new (110, private/bench-v02/live/v0.2) and V-para (private/para-set); both are blind plaintext,
read in-process under the coordinator's logged scoped exception (spec section 5). Held-out, Field Atlas and blind-pool text
is used for numbers only and never printed or written: held-out and Field Atlas get opaque indices, the blind pools their ids.
The topic review (G3, duplicates the thresholds miss) is a fresh Opus agent's judgment, recorded in TOPIC_REVIEW below.

Needs: pip install sentence-transformers (a throwaway venv is fine).
Usage (script-only runner): <venv>/bin/python bench/v0.3/similarity.py [--dir DIR | --file F] [--pools v0.2-new,vpara | --pools all]
"""
import argparse, hashlib, json, os, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
B = Path(os.environ.get("BOAR_PRIVATE_WORKSPACE", "."))  # private workspace of the origin machine; unset in this repo
DEFAULT_DIR = B / "bench/v0.3/work/"
QFILE = "questions.v03.jsonl"
V01 = B / "boar-eval/bench/v0.1"
VEIL = B / "rnd/private-heldout"
FA_REPO, FA_COMMIT = B / "competitors/fieldatlas", "87bb6e9"
FA_FILES = {"tools/e2e_cases.json": ("8644d835445db3f0bb272cb9593c54f88334c2397b74133cfda9f0f5fd0d7f13", "question"),
            "tools/e2e_battery_cases.json": ("c2da3ee0b67df720aa83e42d3d6c3631b08386d519c1f63d910f6d9f66142963", "q")}
EXTRA_POOLS = {"v0.2-new": B / "private/bench-v02/live/v0.2/questions.v02-new.jsonl",
               "vpara": B / "private/para-set/items.jsonl"}
Q_KEYS = ("question", "q", "query", "prompt")  # V-para's field name is not known to the script author (never read)
J_MAX, COS_MAX = 0.30, 0.90
sys.path.insert(0, str(V01))
from validate import tokens, jacc  # noqa: E402  (same normalization as v0.1 build.py)

TOPIC_REVIEW = {  # filled by the coordinator from the G3 agent's (v0.3 id, other id, reason) list
    "collisions": [],
    "watch_not_counted": [],
}


def rows(p): return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]


def qtext(r, pool):
    for k in Q_KEYS:
        if isinstance(r.get(k), str): return r[k]
    sys.exit(f"ABORT: pool {pool}: no question field among {Q_KEYS} (row keys: {sorted(r)})")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", type=Path, default=DEFAULT_DIR, help=f"live folder holding {QFILE}")
    ap.add_argument("--file", type=Path, help=f"item file instead of <dir>/{QFILE}")
    ap.add_argument("--pools", default="", help=f"extra pools, comma-separated from {sorted(EXTRA_POOLS)}, or 'all'")
    a = ap.parse_args()
    extra = sorted(EXTRA_POOLS) if a.pools == "all" else [p for p in a.pools.split(",") if p]
    if unk := [p for p in extra if p not in EXTRA_POOLS]: sys.exit(f"ABORT: unknown pool(s) {unk}; known {sorted(EXTRA_POOLS)}")
    qf = a.file or a.dir / QFILE
    new = rows(qf)
    pools = {"v0.1-public": [(r["id"], r["question"]) for r in rows(V01 / "questions.public.jsonl")],
             "safety-track": [(r["id"], r["question"]) for r in rows(V01 / "safety/track.v0.3.jsonl")]}
    held = [r["question"] for f in ("o2-blind-items.jsonl", "o2-blind-items-b2.jsonl") for r in rows(VEIL / f)]
    pools["heldout-v0.1"] = [(f"heldout#{i}", q) for i, q in enumerate(held)]
    fa = []
    for f, (h, key) in FA_FILES.items():
        raw = subprocess.run(["git", "-C", str(FA_REPO), "show", f"{FA_COMMIT}:{f}"], capture_output=True, check=True).stdout
        if hashlib.sha256(raw).hexdigest() != h: sys.exit(f"ABORT: Field Atlas {f} sha changed")
        fa += [c[key] for c in json.loads(raw)]
    pools["fieldatlas"] = [(f"fieldatlas#{i}", q) for i, q in enumerate(fa)]
    pool_sha = {}
    for p in extra:
        pool_sha[p] = hashlib.sha256(EXTRA_POOLS[p].read_bytes()).hexdigest()
        pools[p] = [(str(r.get("id", f"{p}#{i}")), qtext(r, p)) for i, r in enumerate(rows(EXTRA_POOLS[p]))]

    from sentence_transformers import SentenceTransformer
    m = SentenceTransformer("BAAI/bge-small-en-v1.5")
    enc = lambda ts: m.encode(ts, normalize_embeddings=True, batch_size=64)
    En = enc([n["question"] for n in new]); Tn = [tokens(n["question"]) for n in new]
    Ep = {k: enc([t for _, t in v]) for k, v in pools.items()}; Tp = {k: [tokens(t) for _, t in v] for k, v in pools.items()}

    collisions, internal, per = [], [], {}
    for i, a_ in enumerate(new):
        for j in range(i + 1, len(new)):
            jc, cs = jacc(Tn[i], Tn[j]), float(En[i] @ En[j])
            internal.append({"a": a_["id"], "b": new[j]["id"], "jaccard": round(jc, 4), "cosine": round(cs, 4)})
            if jc > J_MAX or cs >= COS_MAX: collisions.append({"kind": "internal", **internal[-1]})
        per[a_["id"]] = {}
        for k, v in pools.items():
            sc = [(jacc(Tn[i], t), float(En[i] @ Ep[k][x]), v[x][0]) for x, t in enumerate(Tp[k])]
            mj, mc = max(sc, key=lambda s: s[0]), max(sc, key=lambda s: s[1])
            per[a_["id"]][k] = {"max_jaccard": round(mj[0], 4), "jaccard_nearest": mj[2], "max_cosine": round(mc[1], 4), "cosine_nearest": mc[2]}
            collisions += [{"kind": k, "a": a_["id"], "b": o, "jaccard": round(jc, 4), "cosine": round(cs, 4)}
                           for jc, cs, o in sc if jc > J_MAX or cs >= COS_MAX]
    out = {
        "about": __doc__.split("\n\n")[1].replace("\n", " "),
        "questions_sha256": hashlib.sha256(qf.read_bytes()).hexdigest(),
        "extra_pools_sha256": pool_sha,
        "model": "BAAI/bge-small-en-v1.5", "thresholds": {"jaccard_gt": J_MAX, "cosine_ge": COS_MAX},
        "pool_sizes": {k: len(v) for k, v in pools.items()},
        "threshold_collisions": collisions,
        "max_internal": {"jaccard": max((p["jaccard"] for p in internal), default=None),
                         "cosine": max((p["cosine"] for p in internal), default=None)},
        "top_internal_cosine": sorted(internal, key=lambda p: -p["cosine"])[:10],
        "max_vs_pools": {k: {"max_jaccard": max(p[k]["max_jaccard"] for p in per.values()),
                             "max_cosine": max(p[k]["max_cosine"] for p in per.values())} for k in pools},
        "topic_review": TOPIC_REVIEW,
        "per_item": per,
    }
    (HERE / "similarity.json").write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n")
    print(f"{len(collisions)} threshold collisions; max internal {out['max_internal']}; vs pools {out['max_vs_pools']}")


if __name__ == "__main__":
    main()
