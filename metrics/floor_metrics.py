#!/usr/bin/env python3
"""Floor-aware quality metrics for a boar-eval run set (reference implementation for the bench v0.2 analysis plan).
Usage: floor_metrics.py --runs RUN1 RUN2 ... [--dir DIR] [--decline-ratio D] [--ids ids.txt] [--seed 11] [--B 2000]
  RUN = basename of <RUN>.traces.jsonl / <RUN>.judgments.jsonl in DIR (same items across runs).
Outputs (each with a two-level bootstrap 95% CI: items, then runs within item):
  raw        = Σ mean-rubric(system) / Σ mean-rubric(ref)                  (the pre-registered primary)
  above_min  = Σ (S − 1) / Σ (R − 1)                                        (rubric minimum removed)
  above_decl = (raw − D) / (1 − D), D = always-decline ratio                (D from --decline-ratio, else measured
                                                                            on this run set's own declined answers)
Mean rubric = mean of correctness, completeness, usefulness; both A/B orders averaged (judge-core convention).
Fail-closed options (default output unchanged; the "n judged = X of n planned = Y" line goes to stderr):
  --floor-missing  items planned (--ids, else every item seen in a trace) but not judged in a run are scored at the rubric floor
                   (1 on each 1-5 dimension, FLOOR below) instead of being dropped; the reference side is imputed from the other runs'
                   judgments of the same item, else from the mean reference score. Errored/missing answers thus count against the arm.
  --strict         exit 1 (after printing) when n judged < n planned and --floor-missing is not given."""
import argparse, json, collections, sys, numpy as np
K = ("correctness", "completeness", "usefulness")
mr = lambda s: sum(s[k] for k in K) / 3
FLOOR = 1.0  # rubric minimum on the 1-5 scale (judge-core RUBRIC; same constant as the "above_min" metric's "- 1")
ap = argparse.ArgumentParser(); ap.add_argument("--runs", nargs="+", required=True); ap.add_argument("--dir", default=".")
ap.add_argument("--decline-ratio", type=float); ap.add_argument("--ids"); ap.add_argument("--seed", type=int, default=11); ap.add_argument("--B", type=int, default=2000); ap.add_argument("--floor-missing", action="store_true"); ap.add_argument("--strict", action="store_true"); ap.add_argument("--questions", help="questions jsonl with a category per id: enables the stratified bootstrap (plan default)")
a = ap.parse_args()
keep = set(open(a.ids).read().split()) if a.ids else None
per_run = []; decl_scores = []; ref_all = []; seen = set()
for run in a.runs:
    T = {json.loads(l)["itemId"]: json.loads(l) for l in open(f"{a.dir}/{run}.traces.jsonl")}; seen |= set(T)
    J = collections.defaultdict(list)
    for l in open(f"{a.dir}/{run}.judgments.jsonl"):
        r = json.loads(l)
        if r.get("ok"): J[r["queryId"]].append((r.get("order"), r["mapped"]))
    d = {}
    for q, ov in J.items():
        if keep and q not in keep: continue
        o_ = [o for o, _ in ov]; v = [m for _, m in ov]
        if len(v) != 2 or (None not in o_ and set(o_) != {"boarA", "boarB"}):  # audit F7: both orders, distinct (legacy rows without "order": count only)
            print(f"WARN {run}: {q} has {len(v)} ok rows, orders {o_} (needs boarA+boarB); item skipped in this run", file=sys.stderr); continue
        s = (mr(v[0]["boar"]) + mr(v[1]["boar"])) / 2; f = (mr(v[0]["ref"]) + mr(v[1]["ref"])) / 2
        d[q] = (s, f); ref_all.append(f)
        if q in T and T[q]["answer"].get("declined"): decl_scores.append(s)
    per_run.append(d)
items = sorted(set.intersection(*[set(d) for d in per_run]))
planned = sorted(keep) if keep else sorted(seen | set().union(*[set(d) for d in per_run]))
print(f"n judged = {len(items)} of n planned = {len(planned)}", file=sys.stderr)
if len(items) < len(planned):
    print("WARN not judged in every run (" + ("scored at the rubric floor" if a.floor_missing else "dropped") + "): " + ",".join(q for q in planned if q not in items), file=sys.stderr)
    if a.strict and not a.floor_missing: sys.exit(1)
if a.floor_missing and len(items) < len(planned):
    mref = float(np.mean(ref_all)) if ref_all else float("nan"); cells = 0
    for d in per_run:
        for q in planned:
            if q in d: continue
            oth = [e[q][1] for e in per_run if q in e]
            d[q] = (FLOOR, float(np.mean(oth)) if oth else mref); cells += 1
    print(f"floor-missing: {cells} run-item cells scored at floor {FLOOR}", file=sys.stderr)
    items = planned
S = np.array([[d[q][0] for q in items] for d in per_run]); R = np.array([[d[q][1] for q in items] for d in per_run])
D = a.decline_ratio if a.decline_ratio is not None else (np.mean(decl_scores) / np.mean(ref_all) if decl_scores else float("nan"))
def metrics(s, r):
    raw = s.sum() / r.sum(); return raw, (s - 1).sum() / (r - 1).sum(), (raw - D) / (1 - D)
point = metrics(S, R)
rng = np.random.default_rng(a.seed); n, k = len(items), len(per_run); boots = []
strata = None
if a.questions:
    CAT = {"danger-situation": "danger", "travel-local": "travel", "travel-practical": "travel"}
    qcat = {(r := json.loads(l))["id"]: CAT.get(r.get("category"), r.get("category")) for l in open(a.questions)}
    groups = collections.defaultdict(list)
    for i, q in enumerate(items): groups[qcat.get(q, "?")].append(i)
    strata = [np.array(g) for g in groups.values()]
for _ in range(a.B):
    ii = np.concatenate([rng.choice(g, len(g)) for g in strata]) if strata else rng.integers(0, n, n)
    rr = rng.integers(0, k, (n, k))
    boots.append(metrics(S[rr, ii[:, None]].mean(1), R[rr, ii[:, None]].mean(1)))
boots = np.array(boots)
print(json.dumps({"runs": a.runs, "n_items": n, "bootstrap": "stratified by category" if strata else "plain", "decline_ratio_D": round(float(D), 4), "D_source": "given" if a.decline_ratio is not None else f"measured on {len(decl_scores)} declined answers",
  **{name: {"point": round(float(point[i]), 4), "ci95": [round(float(x), 4) for x in np.percentile(boots[:, i], [2.5, 97.5])]} for i, name in enumerate(("raw", "above_min", "above_decl"))}}, indent=1))
