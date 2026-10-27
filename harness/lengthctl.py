#!/usr/bin/env python3
"""Length-controlled quality-ratio gain (AlpacaEval-LC idea, paired and simplified): does an arm's judge-ratio gain
survive removing what the change in answer length explains? (Anvil card complete-paragraph-persona, criterion 5.)

Per judged item i and run (both A/B orders combined, as harness/diff.py): b = boarMean, r = refMean, w = answer words.
Runs of one side are averaged per item. Paired over the items judged on both sides (item difficulty and reference
length cancel):
  dy_i = mean(b - r)_arm - mean(b - r)_base      (judge preference change, score points)
  dx_i = log((w_arm + 1) / (w_base + 1))          (answer length change; mean over runs of each side first)
OLS dy = alpha + beta * dx. alpha is the preference change at unchanged length (the intercept).
  gain    = ratio(arm) - ratio(base)        ratio = sum b / sum r over every run (judge-core's ratio)
  LC gain = alpha / mean(r)                 the intercept in ratio units (a uniform shift d in b moves the ratio by d/mean r)
  also printed: mean(dy) / mean(r), the paired gain before length control, and beta.
If the gain is length bias, LC gain ~ 0; if not, LC gain ~ the paired gain. Criterion 5: LC gain >= +0.03.

Usage: python3 harness/lengthctl.py --base T1 J1 [T2 J2 ...] --arm T3 J3 [T4 J4 ...] [--min-gain 0.03]
(T = traces.jsonl, J = its judgments.jsonl, given as pairs.)
"""
import argparse, math, re, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

WORD = re.compile(r"\w+", re.U)


def words(text):
    return len(WORD.findall(text or ""))


def lc(base_runs, arm_runs):
    """base_runs/arm_runs: lists of runs; a run is {item: (boarMean, refMean, words)}. Returns a dict of results."""
    if not base_runs or not arm_runs:
        raise ValueError("need judged runs for both base and arm")
    ratio = lambda runs: sum(b for run in runs for b, _, _ in run.values()) / sum(r for run in runs for _, r, _ in run.values())

    def per_item(runs):
        out = {}
        for i in set().union(*runs):
            vs = [run[i] for run in runs if i in run]
            out[i] = (sum(b - r for b, r, _ in vs) / len(vs), sum(r for _, r, _ in vs) / len(vs), sum(math.log(w + 1) for *_, w in vs) / len(vs))
        return out

    B, A = per_item(base_runs), per_item(arm_runs)
    items = sorted(set(B) & set(A))
    if len(items) < 3:
        raise ValueError("need >= 3 items judged on both sides")
    dy = [A[i][0] - B[i][0] for i in items]
    dx = [A[i][2] - B[i][2] for i in items]
    rbar = sum((A[i][1] + B[i][1]) / 2 for i in items) / len(items)
    mx, my = sum(dx) / len(dx), sum(dy) / len(dy)
    sxx = sum((x - mx) ** 2 for x in dx)
    beta = sum((x - mx) * (y - my) for x, y in zip(dx, dy)) / sxx if sxx > 0 else 0.0
    alpha = my - beta * mx
    return {"n_items": len(items), "beta": beta, "alpha": alpha, "mean_dx": mx, "ratio_base": ratio(base_runs),
            "ratio_arm": ratio(arm_runs), "gain": ratio(arm_runs) - ratio(base_runs), "paired_gain": my / rbar, "lc_gain": alpha / rbar}


def load_run(traces, judgments):
    from harness.common import pair_scores
    from scorers.score import judge_pairs
    from scorers.trace import read_traces
    ts = read_traces(traces)
    pairs = pair_scores(judge_pairs(judgments, list(ts)))
    return {i: (b, r, words(ts[i]["answer"]["text"])) for i, (b, r) in pairs.items() if i in ts}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--base", nargs="+", required=True)
    ap.add_argument("--arm", nargs="+", required=True)
    ap.add_argument("--min-gain", type=float, default=0.03)
    a = ap.parse_args(argv)
    if len(a.base) % 2 or len(a.arm) % 2:
        ap.error("--base/--arm take TRACES JUDGMENTS pairs")
    runs = lambda xs: [load_run(xs[k], xs[k + 1]) for k in range(0, len(xs), 2)]
    res = lc(runs(a.base), runs(a.arm))
    print(f"paired items: {res['n_items']} · mean log word change arm/base {res['mean_dx']:+.2f} (×{math.exp(res['mean_dx']):.2f} words)")
    print(f"judge length slope beta {res['beta']:+.3f} points per unit log word change · intercept alpha {res['alpha']:+.3f} points")
    print(f"ratio: base {res['ratio_base']:.3f} -> arm {res['ratio_arm']:.3f} (gain {res['gain']:+.3f}); paired gain {res['paired_gain']:+.3f}")
    print(f"length-controlled gain (alpha / mean ref score): {res['lc_gain']:+.3f} ({'PASS' if res['lc_gain'] >= a.min_gain else 'FAIL'} vs >= {a.min_gain:+.2f})")
    return res


if __name__ == "__main__":
    main()
