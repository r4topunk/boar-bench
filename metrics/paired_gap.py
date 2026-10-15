#!/usr/bin/env python3
"""Paired gap between two systems judged on the same items, on the three published scales
(raw, rubric-minimum removed, above always-decline), with a stratified two-level bootstrap.
Usage: paired_gap.py --dir DIR --a RUN... --b RUN... --questions Q.jsonl [--decline-ratio 0.306] [--seed 11] [--B 2000]
  RUN = basename of <RUN>.judgments.jsonl in DIR. Items = those judged in both orders in every run of both systems.
  Strata = item category from Q.jsonl (danger-situation→danger, travel-local/practical→travel)."""
import argparse, json, collections, sys, numpy as np
K = ("correctness", "completeness", "usefulness"); mr = lambda s: sum(s[k] for k in K) / 3
CAT = {"danger-situation": "danger", "travel-local": "travel", "travel-practical": "travel"}
ap = argparse.ArgumentParser(); ap.add_argument("--dir", required=True); ap.add_argument("--a", nargs="+", required=True); ap.add_argument("--b", nargs="+", required=True)
ap.add_argument("--questions", required=True); ap.add_argument("--decline-ratio", type=float, default=0.306); ap.add_argument("--seed", type=int, default=11); ap.add_argument("--B", type=int, default=2000)
a = ap.parse_args()
def load(run):
    J = collections.defaultdict(list)
    for l in open(f"{a.dir}/{run}.judgments.jsonl"):
        r = json.loads(l)
        if r.get("ok"): J[r["queryId"]].append((r.get("order"), r["mapped"]))
    out = {}
    for q, ov in J.items():
        o_ = [o for o, _ in ov]; v = [m for _, m in ov]
        if len(v) != 2 or (None not in o_ and set(o_) != {"boarA", "boarB"}):  # audit F7: the two rows must be the two distinct orders
            print(f"WARN {run}: {q} has {len(v)} ok rows, orders {o_} (needs boarA+boarB); item skipped", file=sys.stderr); continue
        out[q] = ((mr(v[0]["boar"]) + mr(v[1]["boar"])) / 2, (mr(v[0]["ref"]) + mr(v[1]["ref"])) / 2)
    return out
A = [load(r) for r in a.a]; B = [load(r) for r in a.b]
items = sorted(set.intersection(*[set(d) for d in A + B])); seen = set().union(*[set(d) for d in A + B])
print(f"n paired = {len(items)} of n seen = {len(seen)}", file=sys.stderr)
if len(items) < len(seen): print("WARN not judged (both orders) in every run of both systems, dropped: " + ",".join(sorted(seen - set(items))), file=sys.stderr)
arr = lambda runs, j: np.array([[d[q][j] for q in items] for d in runs])
SA, RA, SB, RB = arr(A, 0), arr(A, 1), arr(B, 0), arr(B, 1)
Q = {(r := json.loads(l))["id"]: CAT.get(r.get("category"), r.get("category")) for l in open(a.questions)}
G = collections.defaultdict(list)
for i, q in enumerate(items): G[Q.get(q, "?")].append(i)
D = a.decline_ratio
def m(s, r): raw = s.sum() / r.sum(); return np.array([raw, (s - 1).sum() / (r - 1).sum(), (raw - D) / (1 - D)])
pt = m(SA, RA) - m(SB, RB); rng = np.random.default_rng(a.seed); bs = []
for _ in range(a.B):
    ii = np.concatenate([rng.choice(g, len(g)) for g in G.values()])
    ra = rng.integers(0, len(A), (len(ii), len(A))); rb = rng.integers(0, len(B), (len(ii), len(B)))
    bs.append(m(SA[ra, ii[:, None]].mean(1), RA[ra, ii[:, None]].mean(1)) - m(SB[rb, ii[:, None]].mean(1), RB[rb, ii[:, None]].mean(1)))
bs = np.array(bs)
print(json.dumps({"a": a.a, "b": a.b, "n_items": len(items), "decline_ratio_D": D, "bootstrap": "stratified two-level",
  **{n: {"gap_a_minus_b": round(float(pt[k]), 4), "ci95": [round(float(x), 4) for x in np.percentile(bs[:, k], [2.5, 97.5])]} for k, n in enumerate(("raw", "above_min", "above_decl"))}}, indent=1))
