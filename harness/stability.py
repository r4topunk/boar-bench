#!/usr/bin/env python3
"""Stability across repeats of the same configuration: do ≥ 2 runs agree?

Per item shared by every run: identical answer text, same decline, same shown-source titles (as a set), same tier,
same route codes (context:* excluded). With one judgments file per run: judge label agreement (pass/fail/cw from
judge correctness, as in scorers/score.py) on items judged in every run, each run's quality ratio and their spread
(max - min); with exactly 2 runs, also the paired bootstrap of ratio(run 2) - ratio(run 1). Run budget (Compass card
judge-reliability-run-budget): the two-level (items × runs) CI of the pooled ratio, the minimum detectable effect at
this runs × items, and the judge-vs-generation split of the per-item per-run variance:
  direct  needs a second judge pass on the SAME traces (--rejudge N=PATH: judgments of run N's traces, judged again)
  proxy   items whose answer text is identical across runs (any score change there is the judge), and the fixed
          reference answer re-scored across runs (judge noise on a substantive text)

Usage: python3 harness/stability.py run1.jsonl run2.jsonl [run3.jsonl ...] [--judgments j1.jsonl j2.jsonl ...]
           [--rejudge 1=j1b.jsonl] [--bench DIR] [--seed 11] [--out reports/x.stability.md]
"""
import argparse, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from harness.common import mde_table, mde_text, pair_scores, cell, ci, declined, errored, fmt, route_codes, run_label, shown, write_out  # noqa: E402
from scorers import stats  # noqa: E402
from scorers.score import judge_label, judge_pairs  # noqa: E402
from scorers.trace import read_traces  # noqa: E402

CHECKS = {
    "identical answer text": lambda t: t["answer"]["text"],
    "decline": declined,
    "shown sources (title set)": lambda t: tuple(sorted(set(shown(t)))),
    "tier": lambda t: t["route"]["tier"],
    "route codes": lambda t: tuple(route_codes(t)),
}


def run_budget(runs, judged, rejudge=None, seed=11):
    """runs: [{item: trace}]; judged: [bridge judge result per run]; rejudge: {run index (0-based): bridge result of a
    second judge pass on that run's traces}."""
    scores = [pair_scores(j) for j in judged]
    out = {"two_level": stats.two_level_ratio(scores, seed=seed), "mde": stats.mde_block(scores)}
    boar = [{i: v[0] for i, v in sc.items()} for sc in scores]
    ident = []
    for x in range(len(runs)):
        for y in range(x + 1, len(runs)):
            for i in scores[x]:
                if i in scores[y] and i in runs[x] and i in runs[y] and runs[x][i]["answer"]["text"] == runs[y][i]["answer"]["text"]:
                    ident.append((scores[x][i][0], scores[y][i][0]))
    n_ident_decl = sum(1 for x in range(len(runs)) for y in range(x + 1, len(runs)) for i in scores[x]
                       if i in scores[y] and i in runs[x] and i in runs[y] and runs[x][i]["answer"]["text"] == runs[y][i]["answer"]["text"]
                       and runs[x][i]["answer"]["declined"])
    rj = []
    for k, res in (rejudge or {}).items():
        second = pair_scores(res)
        rj += [(scores[k][i][0], second[i][0]) for i in scores[k] if i in second]
    split = stats.variance_split(boar, rejudge=rj or None, identical=ident or None)
    ref = stats.run_variance([{i: (v[1], 0.0) for i, v in sc.items()} for sc in scores])
    if split is not None:
        split["identical_declined"] = n_ident_decl
        split["ref_rescore"] = ({"judge_var": ref["var"], "n": ref["n_items"], "judge_share": ref["var"] / split["total_var"] if split["total_var"] else None}
                                if ref else None)
    out["split"] = split
    return out


def agreement(runs, judged=None, seed=11, rejudge=None):
    """runs: [{itemId: trace}, ...] (≥ 2); judged: optional [bridge judge result per run]."""
    ids = [i for i in runs[0] if all(i in r for r in runs[1:])]
    ok_ids = [i for i in ids if not any(errored(r[i]) for r in runs)]
    out = {"n_runs": len(runs), "n_shared": len(ids), "n_errored": len(ids) - len(ok_ids), "checks": {}, "disagree": {}}
    for name, key in CHECKS.items():
        dis = [i for i in ok_ids if len({key(r[i]) for r in runs}) > 1]
        out["checks"][name] = {"agree": len(ok_ids) - len(dis), "n": len(ok_ids),
                               "rate": (len(ok_ids) - len(dis)) / len(ok_ids) if ok_ids else None}
        out["disagree"][name] = dis
    if judged:
        pair_maps = [{p["queryId"]: p for p in j["pairs"]} for j in judged]
        jids = [i for i in ok_ids if all(i in pm for pm in pair_maps)]
        labels = {i: [judge_label(pm[i])[0] for pm in pair_maps] for i in jids}
        dis = [i for i in jids if len(set(labels[i])) > 1]
        ratios = [j["summary"]["qualityRatio"] if j["summary"] else None for j in judged]
        valid = [r for r in ratios if r is not None]
        out["judge"] = {
            "label_agree": len(jids) - len(dis), "n": len(jids), "rate": (len(jids) - len(dis)) / len(jids) if jids else None,
            "label_disagree": [{"id": i, "labels": labels[i]} for i in dis],
            "ratios": ratios, "ratio_cis": [j["summary"]["qualityRatioCI"] if j["summary"] else None for j in judged],
            "ratio_spread": (max(valid) - min(valid)) if len(valid) >= 2 else None,
        }
        if len(judged) == 2:
            a = {i: (p["boarMean"], p["refMean"]) for i, p in pair_maps[0].items()}
            b = {i: (p["boarMean"], p["refMean"]) for i, p in pair_maps[1].items()}
            out["judge"]["paired"] = stats.paired_ratio_diff(a, b, seed=seed)
        out["judge"]["run_budget"] = run_budget(runs, judged, rejudge, seed)
    return out


def render_budget(B):
    tl, m, sp = B["two_level"], B["mde"], B["split"]
    L = ["", "## Run budget (Compass card judge-reliability-run-budget)", "",
         f"- Pooled quality ratio, two-level bootstrap (items, then runs within item; {tl['resamples']} resamples, seed {tl['seed']}) "
         f"over {tl['runs']} runs × {tl['n_items']} items: **{tl['ratio']:.4f} ({ci(tl['ci95'], 4)})**.",
         f"- {mde_text(m)}.", "", "MDE by budget:", ""] + mde_table(m)
    L += ["", "### Judge vs generation variance", ""]
    if not sp:
        L.append("Not computable: no item judged in ≥ 2 runs.")
        return L
    L.append(f"Per-item per-run variance of BOAR's mean rubric (total = generation + judge): **{sp['total_var']:.3f}** over {sp['n_items']} items.")
    L += ["", "| Estimate of the judge's part | n | judge σ² | judge share | generation share |", "|---|---|---|---|---|"]
    if sp.get("rejudge"):
        r = sp["rejudge"]
        L.append(f"| **direct: same traces judged twice** | {r['n']} | {r['judge_var']:.3f} | {r['judge_share']:.0%} | {r['generation_share']:.0%} |")
    else:
        L.append("| direct: same traces judged twice | 0 | — | — | — |")
    if sp.get("identical_text"):
        r = sp["identical_text"]
        L.append(f"| proxy: identical answer text across runs ({sp['identical_declined']} of them declines) | {r['n']} | {r['judge_var']:.3f} | {r['judge_share']:.0%} | {r['generation_share']:.0%} |")
    if sp.get("ref_rescore"):
        r = sp["ref_rescore"]
        L.append(f"| proxy: fixed reference text re-scored across runs | {r['n']} | {r['judge_var']:.3f} | {r['judge_share']:.0%} | {1 - r['judge_share']:.0%} |")
    if not sp.get("rejudge"):
        L += ["", "No direct split: there is no second judge pass on the same traces. The proxies lean on declines and on the "
              "reference text, so judge noise on long substantive BOAR answers is not measured. To measure it: "
              "`node harness/judge.mjs --traces RUN.jsonl --out RUN.judgments.pass2.jsonl --seed 8`, then `--rejudge 1=RUN.judgments.pass2.jsonl`."]
    return L


def render(res, paths, runs):
    L = ["# Stability across repeats", "", "Runs:"] + [f"- run {k + 1}: {run_label(r, p)}" for k, (r, p) in enumerate(zip(runs, paths))]
    L += ["", f"Items in every run: {res['n_shared']}; errored in at least one run (excluded): {res['n_errored']}.", "",
          "| Check (all runs equal) | Agree | n | Rate |", "|---|---|---|---|"]
    for name, c in res["checks"].items():
        L.append(f"| {name} | {c['agree']} | {c['n']} | {fmt(c['rate'])} |")
    J = res.get("judge")
    if J:
        L += ["", "## Judge", "", f"- Label agreement (pass/fail/cw from judge correctness): **{J['label_agree']}/{J['n']}** ({fmt(J['rate'])}).",
              "- Quality ratio per run: " + ", ".join(f"run {k + 1} {fmt(r, 4)} ({ci(c)})" for k, (r, c) in enumerate(zip(J["ratios"], J["ratio_cis"]))) + ".",
              f"- Ratio spread (max − min): **{fmt(J['ratio_spread'], 4)}**."]
        P = J.get("paired")
        if P:
            L.append(f"- Paired bootstrap, run 2 − run 1 over {P['n']} items judged in both: **{P['diff']:+.4f}** "
                     f"(95% CI {P['diff_ci95'][0]:+.4f} to {P['diff_ci95'][1]:+.4f}; seed {P['seed']}, {P['resamples']} resamples): {P['verdict']}.")
        if J["label_disagree"]:
            L += ["", "| id | labels per run |", "|---|---|"] + [f"| `{d['id']}` | {' → '.join(d['labels'])} |" for d in J["label_disagree"]]
    else:
        L += ["", "Judge: no judgments given (label agreement and ratio spread need one judgments file per run)."]
    if J and res["judge"].get("run_budget"):
        L += render_budget(res["judge"]["run_budget"])
    L += ["", "## Disagreeing items", ""]
    for name, ids in res["disagree"].items():
        if name == "identical answer text":
            L.append(f"- {name}: {len(ids)} items differ" + (f" ({', '.join(ids[:30])}{' …' if len(ids) > 30 else ''})" if ids else ""))
        else:
            L.append(f"- {name}: " + (", ".join(f"`{i}`" for i in ids) if ids else "none"))
    for name in ("decline", "shown sources (title set)"):
        ids = res["disagree"][name]
        if ids:
            L += ["", f"### {name}", "", "| id | " + " | ".join(f"run {k + 1}" for k in range(len(runs))) + " |",
                  "|---|" + "---|" * len(runs)]
            for i in ids:
                vals = [("declined" if declined(r[i]) else "answered") if name == "decline" else (" · ".join(shown(r[i])) or "—") for r in runs]
                L.append(f"| `{i}` | " + " | ".join(cell(v, 120) for v in vals) + " |")
    return "\n".join(L) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("runs", nargs="+")
    ap.add_argument("--judgments", nargs="*")
    ap.add_argument("--bench", help="restrict judged items to the bench ids (default: every judged item)")
    ap.add_argument("--rejudge", nargs="*", default=[], metavar="N=PATH",
                    help="second judge pass on run N's traces (1-based), for the direct judge-vs-generation split")
    ap.add_argument("--seed", type=int, default=11)
    ap.add_argument("--out")
    a = ap.parse_args(argv)
    if len(a.runs) < 2:
        ap.error("need at least 2 runs")
    if a.judgments and len(a.judgments) != len(a.runs):
        ap.error("give one judgments file per run, in the same order")
    runs = [read_traces(p) for p in a.runs]
    judged = None
    if a.judgments:
        ids = None
        if a.bench:
            from scorers.bench import Bench
            b = Bench(a.bench)
            ids = [q["id"] for q in b.items_for(set().union(*runs))]
        judged = [judge_pairs(j, ids, a.seed) for j in a.judgments]
    rejudge = {}
    for spec in a.rejudge:
        n, _, path = spec.partition("=")
        if not judged or not path or not n.isdigit() or not 1 <= int(n) <= len(runs):
            ap.error(f"--rejudge {spec!r}: expected N=PATH with 1 <= N <= {len(runs)}, and --judgments")
        rejudge[int(n) - 1] = judge_pairs(path, ids, a.seed)
    res = agreement(runs, judged, a.seed, rejudge)
    write_out(render(res, a.runs, runs), a.out)
    return res


if __name__ == "__main__":
    main()
