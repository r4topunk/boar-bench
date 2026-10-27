#!/usr/bin/env python3
"""One markdown report, seven axes, never one average: quality, truthfulness, safety, retrieval, latency,
resources, stability. Deterministic (no timestamps, fixed bootstrap seed): the same inputs give the same bytes.

Usage: python3 harness/report.py TRACES.jsonl [--judgments J.jsonl] [--hand H.json] [--bench DIR]
           [--repeat RUN2.jsonl ...] [--repeat-judgments J2.jsonl ...] [--k 5] [--seed 11] --out reports/<name>.md
"""
import argparse, os, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from harness.common import REPO, mde_table, mde_text, pair_scores, ci, cell, fmt, fmt_ms, run_label, write_out  # noqa: E402
from harness.stability import agreement  # noqa: E402
from scorers import stats  # noqa: E402
from scorers.bench import Bench  # noqa: E402
from scorers.retrieval import DEFAULT_K, score_retrieval  # noqa: E402
from scorers.score import SCORER_VERSION, judge_pairs, score  # noqa: E402
from scorers.timing import visible_timing  # noqa: E402
from scorers.trace import adapters, read_traces, sha256  # noqa: E402

DESKTOP = "desktop, not phone"


def where(traces):
    ads = adapters(traces)
    if ads == ["desktop-node"]:
        return DESKTOP
    if "desktop-node" in ads:
        return "MIXED desktop + device: do not read as phone numbers"
    return "device (" + ", ".join(ads) + ")"


def latency(traces):
    ts = list(traces.values())
    def col(k, pred=lambda t: True):
        return [t["timing"][k] for t in ts if t["timing"][k] is not None and pred(t)]
    gen = lambda t: (t["timing"]["outputTokens"] or 0) > 0
    vt = [visible_timing(t) for t in ts]
    hidden = [v["hidden_think_ms"] for v in vt if v["hidden_think_ms"] is not None]
    rows = {
        "first visible text (ttft_visible_ms)": [v["ttft_visible_ms"] for v in vt if v["ttft_visible_ms"] is not None],
        "first token, receipt (ttftMs; may be empty text)": col("ttftMs"),
        "hidden thinking before first visible token (hidden_think_ms)": hidden,
        "complete answer (totalMs)": col("totalMs"),
        "retrieval (retrievalMs)": col("retrievalMs"),
        "prefill (prefillMs)": col("prefillMs"),
        "decode tok/s (answers with output tokens)": col("decodeTokPerSec", gen),
    }
    out = {}
    for k, xs in rows.items():
        out[k] = {"n": len(xs), "p50": stats.pctl(xs, 0.5), "p95": stats.pctl(xs, 0.95)}
    hp50 = stats.pctl(hidden, 0.5)
    return {"where": where(traces), "rows": out, "n": len(ts), "hidden_think_p50": hp50,
            "hidden_thinking": hp50 is not None and hp50 > 1000,
            "n_visible_unknown": sum(1 for v in vt if v["ttft_visible_ms"] is None),
            "host": sorted({t["runtime"]["host"] for t in ts}),
            "loadAvg1m": stats.pctl([t["runtime"].get("loadAvg1m") for t in ts], 0.5)}


def resources(traces):
    ts = [t for t in traces.values() if t.get("resources")]
    rss = [t["resources"].get("peakRssMb") for t in ts]
    sus = [t["resources"].get("sustainedRatio") for t in ts]
    thermal = {}
    for t in ts:
        th = t["resources"].get("thermal")
        if th is not None:
            thermal[th] = thermal.get(th, 0) + 1
    n = sum(1 for x in rss if x is not None)
    return {"where": where(traces), "n": n, "peak_rss_p50": stats.pctl(rss, 0.5),
            "peak_rss_max": max((x for x in rss if x is not None), default=None),
            "sustained_min": min((x for x in sus if x is not None), default=None), "thermal": dict(sorted(thermal.items()))}


def build(traces_path, bench, judgments=None, hand=None, repeats=(), repeat_judgments=(), k=DEFAULT_K, seed=11):
    traces = read_traces(traces_path)
    rep = score(traces, bench, judgments, hand, seed, traces_path=traces_path)
    rep["retrieval"] = score_retrieval(traces, bench.gold_sources(), k=k, seed=seed)
    rep["latency"] = latency(traces)
    rep["resources"] = resources(traces)
    rep["run_budget"] = None
    judged = None
    if judgments:
        ids = [q["id"] for q in bench.items_for(traces)]
        js = [judgments, *repeat_judgments] if len(repeat_judgments) == len(repeats) else [judgments]
        judged = [judge_pairs(j, ids, seed) for j in js]
        scores = [pair_scores(j) for j in judged]
        tl = stats.two_level_ratio(scores, seed=seed)
        if tl:
            rep["run_budget"] = {"two_level": tl, "mde": stats.mde_block(scores)}
            adj = [stats.floor_adjust(sc) for sc in scores]
            # run 1 alone: item bootstrap with seed+1, the main ratio's CI seed (judge-core); all runs: two-level, seed
            rep["floor_adjusted"] = {"run1": stats.two_level_ratio(adj[:1], seed=seed + 1),
                                     "pooled": stats.two_level_ratio(adj, seed=seed) if len(adj) > 1 else None,
                                     "raw_run1": stats.ratio(list(scores[0].values()))}
    if repeats:
        runs = [traces] + [read_traces(p) for p in repeats]
        rep["stability"] = agreement(runs, judged if judged and len(judged) == len(runs) else None, seed)
        rep["inputs"].update({f"repeat{n + 2}": sha256(p) for n, p in enumerate(repeats)})
    else:
        rep["stability"] = None
    rep["meta"] = {"traces": str(traces_path), "label": run_label(traces, traces_path), "bench": os.path.relpath(bench.dir, REPO),
                   "safety_version": bench.safety_version(), "refs": str(bench.refs_path) if bench.refs_path else None,
                   "legacy": sorted({t["runtime"].get("versions", {}).get("legacy") for t in traces.values()} - {None}),
                   "models": sorted({t["runtime"]["model"] for t in traces.values()}),
                   "repeats": [str(p) for p in repeats]}
    rep["_traces"] = traces
    return rep


def render(rep, title):
    Q, T, Sf, R, Lt, Rs, St, M = (rep[k] for k in ("quality", "truthfulness", "safety", "retrieval", "latency", "resources", "stability", "meta"))
    L = [f"# Eval report: {title}", "",
         f"Traces: {M['label']} · adapter(s) {', '.join(adapters(rep['_traces']))} · model {', '.join(M['models'])}",
         f"Bench: `{M['bench']}` · safety rules {M['safety_version']} · scorer `{SCORER_VERSION}`"]
    if M["legacy"]:
        L.append(f"Legacy traces ({', '.join(M['legacy'])}): converted rows; retrieval.raw = kept and dropped = [] (unknown in the source rows).")
    L += ["", f"**{Sf['line']}** (rules {Sf['version']}; reported on its own, never averaged)" +
          (": " + "; ".join(f"{u['id']} ({u['source']})" for u in Sf["unsafe"]) if Sf["unsafe"] else "."), ""]

    # ---- summary table
    L += ["## Seven axes", "", "| Axis | n | Value | 95% CI | Note |", "|---|---|---|---|---|"]
    if Q.get("status") == "ok":
        L.append(f"| Quality (ratio vs Opus+web) | {Q['n_judged']}/{Q['n_questions']} judged | {Q['quality_ratio']:.4f} (RACE {Q['race_equivalent']:.3f}) | "
                 f"{ci(Q['quality_ratio_ci95'], 4)} | Bounty bar 0.50: {Q['bounty_bar']['verdict']} |")
    else:
        L.append(f"| Quality (ratio vs Opus+web) | 0 | {Q.get('status')} | — | needs --judgments (harness/judge.mjs) |")
    FA = rep.get("floor_adjusted")
    if FA and FA["run1"]:
        f1 = FA["run1"]
        L.append(f"| ↳ floor-adjusted (a blank answer = 0) | {f1['n_items']} | {f1['ratio']:.4f} | {ci(f1['ci95'], 4)} | "
                 "Σ(S−1)/Σ(S_ref−1): the judge's rubric floor of 1 removed; raw ratio above unchanged |")
    RB = rep.get("run_budget")
    if RB:
        tl, m = RB["two_level"], RB["mde"]
        L.append(f"| Quality, two-level ({tl['runs']} run(s) × {tl['n_items']} items) | {tl['n_items']} | {tl['ratio']:.4f} | {ci(tl['ci95'], 4)} | "
                 f"MDE for an arm comparison at {m['k_a']} run(s)/arm × {m['n_items']} items: Δratio {m['mde']:.3f} |")
        if FA and FA["pooled"]:
            fp = FA["pooled"]
            L.append(f"| ↳ floor-adjusted, two-level (a blank answer = 0) | {fp['n_items']} | {fp['ratio']:.4f} | {ci(fp['ci95'], 4)} | "
                     f"Σ(S−1)/Σ(S_ref−1) over {fp['runs']} runs |")
    c = T["counts"]
    L.append(f"| Truthfulness (per item) | {T['n_scored']} | {fmt(T['score_mean'])} | {ci(T['score_mean_ci95'])} | "
             f"pass {c['pass']} · fail {c['fail']} · refused {c['refused']} · cw {c['cw']} (danger {c['cw_danger']}) · unlabeled {c['unlabeled']} · missing {c['missing']} |")
    L.append(f"| Safety | {Sf['n_danger_items_answered']} danger items answered | {Sf['n_unsafe']} unsafe | — | own line above; never averaged |")
    if R["status"] == "ok":
        L.append(f"| Retrieval | {R['n_gold_items']} items with gold | recall@{R['k']} {R['recall_at_k']:.2f} | {ci(R['recall_at_k_ci95'])} | "
                 f"on-topic gold dropped before the answer: {R['n_on_topic_gold_dropped']} · declined with gold in sources: {R['n_declined_with_gold']} |")
    else:
        L.append(f"| Retrieval | 0 | no gold | — | {R['line']} |")
    ttft, tot = Lt["rows"]["first visible text (ttft_visible_ms)"], Lt["rows"]["complete answer (totalMs)"]
    L.append(f"| Latency ({Lt['where']}) | {ttft['n']} | visible TTFT p50 {fmt_ms(ttft['p50'])} · total p50 {fmt_ms(tot['p50'])} | — | p95 visible TTFT {fmt_ms(ttft['p95'])} · total {fmt_ms(tot['p95'])}"
             + (f" · **hidden thinking** p50 {fmt_ms(Lt['hidden_think_p50'])}" if Lt["hidden_thinking"] else "") + " |")
    L.append(f"| Resources ({Rs['where']}) | {Rs['n']} | " + ("not measured" if not Rs["n"] else f"peak RSS p50 {Rs['peak_rss_p50']:.0f} MB · max {Rs['peak_rss_max']:.0f} MB") +
             " | — | " + ("desktop adapter leaves resources null" if Rs["where"] == DESKTOP else f"thermal {Rs['thermal'] or 'n/a'} · sustained min {fmt(Rs['sustained_min'])}") + " |")
    if St:
        a = St["checks"]["identical answer text"]; d = St["checks"]["decline"]; s = St["checks"]["shown sources (title set)"]
        J = St.get("judge")
        L.append(f"| Stability ({St['n_runs']} runs) | {St['n_shared']} | identical answers {a['agree']}/{a['n']} · decline {d['agree']}/{d['n']} · shown {s['agree']}/{s['n']} | "
                 + (ci(J["paired"]["diff_ci95"], 4) if J and J.get("paired") else "—") + " | "
                 + (f"label agreement {J['label_agree']}/{J['n']} · ratio spread {fmt(J['ratio_spread'], 4)}" if J else "no judgments for the repeats") + " |")
    else:
        L.append("| Stability | 1 run | n/a | — | needs ≥ 2 runs: --repeat RUN2.jsonl (or harness/stability.py) |")
    if rep["n_errors"]:
        L += ["", f"**Errors: {rep['n_errors']} traces carry an error** (scored as missing)."]

    # ---- 1. quality
    L += ["", "## 1. Quality ratio vs frontier+web reference", ""]
    if Q.get("status") == "ok":
        L += ["| Metric | Value |", "|---|---|",
              f"| Quality ratio S/S_ref (95% CI) | {Q['quality_ratio']:.4f} ({ci(Q['quality_ratio_ci95'], 4)}) |"] + (
              [f"| ↳ floor-adjusted (a blank answer = 0): Σ(S−1)/Σ(S_ref−1) (95% CI) | {FA['run1']['ratio']:.4f} ({ci(FA['run1']['ci95'], 4)}) |"]
              if FA and FA["run1"] else []) + [
              f"| RACE equivalent ratio/(1+ratio) | {Q['race_equivalent']:.4f} ({ci(Q['race_equivalent_ci95'], 4)}) |",
              f"| Bounty bar | ratio ≥ 0.50 ⇔ RACE ≥ 0.333 → {Q['bounty_bar']['verdict']} |",
              f"| Win / tie / loss vs ref | {Q['win']:.0%} / {Q['tie']:.0%} / {Q['loss']:.0%} |",
              f"| Win score (95% CI) | {fmt(Q['win_score'])} ({ci(Q['win_score_ci95'])}) |",
              f"| Position consistency | {Q['position_consistency']:.0%} |",
              f"| Correct (judge correctness ≥ 4) | {Q['correct_rate_judge']:.0%} |",
              f"| Judged / questions | {Q['n_judged']} / {Q['n_questions']} ({Q['coverage']:.0%}) |",
              "| Rubric system / ref | " + ", ".join(f"{k} {Q['rubric_system'][k]:.2f}/{Q['rubric_ref'][k]:.2f}" for k in Q["rubric_system"]) + " |",
              f"| Judge (model · version · ref · system) | {'; '.join(m.replace('|', ' · ') for m in Q['judge_meta'])} |", "",
              f"Method: {Q['method']}"]
    else:
        L.append(f"{Q.get('status')}.")
    if RB:
        tl, m = RB["two_level"], RB["mde"]
        L += ["", f"**Run budget (Compass card judge-reliability-run-budget).** Two-level bootstrap (items, then runs within each item; "
              f"{tl['resamples']} resamples, seed {tl['seed']}) over {tl['runs']} run(s) × {tl['n_items']} items: ratio **{tl['ratio']:.4f} "
              f"({ci(tl['ci95'], 4)})**" + (" (one run: same as the item bootstrap, generation noise not represented)" if tl["runs"] == 1 else "") + ".",
              "", mde_text(m) + ". An arm effect smaller than this cannot be decided on quality at this budget; decide on gate or safety axes instead.",
              "", "MDE by budget (same σ²_run and reference mean):", ""] + mde_table(m)

    # ---- 2. truthfulness
    L += ["", "## 2. Truthfulness (CRAG-style, −9 on danger items)", "", f"Scale: {T['scale']}.", "",
          f"Label sources: {', '.join(f'{k} {v}' for k, v in T['label_sources'].items()) or 'none'}.", "",
          f"**Precheck caveat:** {T['precheck_caveat']}."]
    if rep.get("truthfulness_band"):
        B = rep["truthfulness_band"]
        L.append(f"Band: {fmt(B['judge_plus_jev_cw'])} to {fmt(B['judge_only'])} ({B['n_flips']} Jev flips).")

    # ---- 3. safety
    L += ["", "## 3. Safety (own line, never averaged)", "", f"**{Sf['line']}** (rules {Sf['version']}).", ""]
    if Sf["unsafe"]:
        L += ["| id | source | note |", "|---|---|---|"] + [f"| `{u['id']}` | {u['source']} | {cell(u['note'], 200)} |" for u in Sf["unsafe"]]
    else:
        L.append("No unsafe advice found by the forbid/require rules (a floor: rules miss paraphrases they don't list).")

    # ---- 4. retrieval
    D = R["descriptive"]
    L += ["", "## 4. Retrieval", "", f"{R['line']}.", "",
          f"Descriptive (no gold needed): {D['items_with_shown_sources']}/{D['n_traces']} items show sources · mean raw {fmt(D['raw_mean'])} · "
          f"mean kept {fmt(D['kept_mean'])} · dropped total {D['dropped_total']}" +
          (f" · {D['legacy_traces']} legacy traces (raw = kept, dropped unknown)" if D["legacy_traces"] else "") + "."]
    if R["status"] == "ok":
        L += ["", f"Pre-answer sources = the last `sources` event ({R['pre_answer_from']['sources-event']} items), else retrieval.kept "
              f"({R['pre_answer_from']['kept']}). A drop is gold in retrieval.raw and missing from them; a decline with the gold "
              "in them is counted apart (the key reached the prompt; the answer side lost it)."]
    if R["status"] == "ok" and R["on_topic_gold_dropped"]:
        L += ["", "| id | gold dropped before the answer |", "|---|---|"] + [f"| `{d['id']}` | {cell(' · '.join(d['gold_dropped']))} |" for d in R["on_topic_gold_dropped"]]
    if R["status"] == "ok" and R["declined_with_gold"]:
        L += ["", "| id | declined with gold in sources |", "|---|---|"] + [f"| `{d['id']}` | {cell(' · '.join(d['gold_in_sources']))} |" for d in R["declined_with_gold"]]

    # ---- 5. latency
    L += ["", f"## 5. Latency ({Lt['where']})", ""]
    if Lt["where"] == DESKTOP:
        L.append("Desktop numbers (desktop-node adapter): a relative signal between arms on the same host, never a phone number.")
    L += [f"Host: {', '.join(Lt['host'])}" + (f" · median 1-min load {Lt['loadAvg1m']:.1f}" if Lt["loadAvg1m"] is not None else "") + ".", "",
          "| Stage | n | p50 | p95 |", "|---|---|---|---|"]
    if Lt["hidden_thinking"]:
        L.insert(len(L) - 3, f"**Hidden thinking:** the model generates p50 {fmt_ms(Lt['hidden_think_p50'])} of invisible tokens before the first visible one; "
                 "the receipt's ttftMs (first, possibly empty, token) understates what the user waits. TTFT below is the first visible text.")
    for k, v in Lt["rows"].items():
        f = (lambda x: fmt(x, 1)) if "tok/s" in k else fmt_ms
        L.append(f"| {k} | {v['n']} | {f(v['p50']) if v['n'] else 'not measured'} | {f(v['p95']) if v['n'] else 'not measured'} |")

    # ---- 6. resources
    L += ["", f"## 6. Resources ({Rs['where']})", ""]
    if not Rs["n"]:
        L.append("Not measured" + (": the desktop adapter leaves `resources` null (its RAM is not a phone's)." if Rs["where"] == DESKTOP else "."))
    else:
        L.append(f"Peak RSS p50 {Rs['peak_rss_p50']:.0f} MB, max {Rs['peak_rss_max']:.0f} MB (n={Rs['n']}); sustained ratio min {fmt(Rs['sustained_min'])}; thermal {Rs['thermal'] or 'n/a'}.")

    # ---- 7. stability
    L += ["", "## 7. Stability", ""]
    if St:
        L += ["| Check (all runs equal) | Agree | n |", "|---|---|---|"] + [f"| {k} | {v['agree']} | {v['n']} |" for k, v in St["checks"].items()]
        L.append("")
        L.append("Repeats: " + ", ".join(f"`{p}`" for p in M["repeats"]) + ". Details: `harness/stability.py`.")
    else:
        L.append("One run: not measured. Stability needs ≥ 2 runs of the same config (`--repeat`).")

    # ---- items
    L += ["", "## Items", "", "| Id | Category | Danger | Label | Points | Source | Note |", "|---|---|---|---|---|---|---|"]
    for x in rep["items"]:
        L.append(f"| {x['id']} | {x['category']} | {'yes' if x['danger'] else ''} | {x['label']} | {x['points']:+d} | {x['source']} | {cell(x['note'], 140)} |")
    L += ["", "## Inputs", "", "| Input | sha256 |", "|---|---|"] + [f"| `{k}` | `{v[:16]}…` |" for k, v in rep["inputs"].items()]
    L += ["", "Graders (vendored, `scorers/vendor/SOURCE.md`): " + ", ".join(f"{k} `{v[:12]}`" for k, v in rep["eval_lib"]["sha256"].items()) +
          "; precheck `scorers/vendor/lantern/precheck.py`; bootstrap seed " + str(rep["seed"]) + ".", ""]
    return "\n".join(L)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("traces")
    ap.add_argument("--judgments")
    ap.add_argument("--hand")
    ap.add_argument("--bench")
    ap.add_argument("--safety-version", help="safety rules version (default: the bench's, v0.3); v0.4 = v0.3 + broader post-negation (scorers/vendor/safety)")
    ap.add_argument("--refs")
    ap.add_argument("--repeat", nargs="+", action="extend", default=[], help="another run of the same config; repeatable (--repeat A --repeat B or --repeat A B)")
    ap.add_argument("--repeat-judgments", nargs="+", action="extend", default=[], help="judgments per --repeat, paired by order; repeatable")
    ap.add_argument("--k", type=int, default=DEFAULT_K, help="recall@k on retrieval.raw (default %(default)s)")
    ap.add_argument("--seed", type=int, default=11)
    ap.add_argument("--title")
    ap.add_argument("--out")
    a = ap.parse_args(argv)
    if a.repeat_judgments and len(a.repeat_judgments) != len(a.repeat):
        ap.error(f"{len(a.repeat_judgments)} --repeat-judgments for {len(a.repeat)} --repeat runs: give one per run, same order")
    if a.repeat_judgments and not a.judgments:
        ap.error("--repeat-judgments needs --judgments for the first run")
    bench = Bench(a.bench, refs=a.refs, safety_version=a.safety_version)
    rep = build(a.traces, bench, a.judgments, a.hand, a.repeat, a.repeat_judgments, a.k, a.seed)
    write_out(render(rep, a.title or Path(a.out or a.traces).stem), a.out)
    return rep


if __name__ == "__main__":
    main()
