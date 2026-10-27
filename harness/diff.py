#!/usr/bin/env python3
"""Paired per-item diff of two runs (A = before, B = after), generalizing rnd/kiln/exp-08b…/compare.py.

Per shared item it compares: declined, shown sources, kept/dropped sources, tier, route codes (context:* excluded),
answer text, error. Categories (compare.py rule):
  Worse   answered -> declined, or showed sources -> shows none, or a new error
  Better  declined -> answered, or no sources -> shows sources, or an error fixed
  Other   any other change (shown titles, kept/dropped, tier, route codes, answer text only)
With judgments for both sides: judge label changes per item (first run of each side), the paired two-level
(items × runs) bootstrap of ratio(B) - ratio(A) over every run given, and the minimum detectable effect (MDE) at the
current runs × items (Compass card judge-reliability-run-budget), so a Δ inside the noise is called out.

Usage: python3 harness/diff.py A.jsonl B.jsonl [--labels before after] [--judgments-a JA.jsonl --judgments-b JB.jsonl]
           [--bench DIR] [--seed 11] [--out reports/<name>.diff.md]
       python3 harness/diff.py --runs-a a1.jsonl a2.jsonl --judgments-a ja1 ja2 --runs-b b1.jsonl b2.jsonl --judgments-b jb1 jb2
       (per-item tables use the first run of each side; the quality block uses all runs)
"""
import argparse, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from harness.common import mde_table, mde_text, pair_scores, cell, declined, errored, fmt_ms, route_codes, run_label, short, shown, titles, write_out  # noqa: E402
from scorers import stats  # noqa: E402
from scorers.score import judge_label, judge_pairs  # noqa: E402
from scorers.timing import visible_timing  # noqa: E402
from scorers.trace import is_desktop, read_traces  # noqa: E402


def summary(ts):
    ts = list(ts)
    tiers = {}
    for t in ts:
        tiers[str(t["route"]["tier"])] = tiers.get(str(t["route"]["tier"]), 0) + 1
    tm = lambda k: [t["timing"][k] for t in ts]
    vt = [visible_timing(t) for t in ts]
    vis = [v["ttft_visible_ms"] for v in vt]
    hid = [v["hidden_think_ms"] for v in vt]
    return {"n": len(ts), "errors": sum(map(errored, ts)), "declined": sum(map(declined, ts)),
            "weak": sum(1 for t in ts if t["answer"]["weakSources"]), "noshown": sum(1 for t in ts if not shown(t)),
            "tiers": dict(sorted(tiers.items())),
            "ttft50": stats.pctl(vis, .5), "ttft95": stats.pctl(vis, .95),
            "rttft50": stats.pctl(tm("ttftMs"), .5), "rttft95": stats.pctl(tm("ttftMs"), .95), "hid50": stats.pctl(hid, .5),
            "tot50": stats.pctl(tm("totalMs"), .5), "tot95": stats.pctl(tm("totalMs"), .95), "ret50": stats.pctl(tm("retrievalMs"), .5)}


def item_changes(x, y):
    ch = []
    if errored(x) != errored(y):
        ch.append(f"error {bool(errored(x))}→{bool(errored(y))}")
    if declined(x) != declined(y):
        ch.append(f"declined {declined(x)}→{declined(y)}")
    if bool(shown(x)) != bool(shown(y)):
        ch.append(f"shown {len(shown(x))}→{len(shown(y))}")
    elif set(shown(x)) != set(shown(y)):
        ch.append(f"shown titles changed ({len(shown(x))}→{len(shown(y))})")
    for k in ("kept", "dropped"):
        a, b = titles(x["retrieval"][k]), titles(y["retrieval"][k])
        if sorted(a) != sorted(b):
            ch.append(f"{k} {len(a)}→{len(b)}")
    if x["route"]["tier"] != y["route"]["tier"]:
        ch.append(f"tier {x['route']['tier']}→{y['route']['tier']}")
    if route_codes(x) != route_codes(y):
        ch.append("route codes")
    if x["answer"]["text"] != y["answer"]["text"]:
        ch.append("answer text")
    return ch


def classify(x, y):
    worse = (not declined(x) and declined(y)) or (bool(shown(x)) and not shown(y)) or (not errored(x) and errored(y))
    better = (declined(x) and not declined(y)) or (not shown(x) and bool(shown(y))) or (errored(x) and not errored(y))
    return "worse" if worse else "better" if better else "other"


def diff(a, b, ja=None, jb=None, seed=11):
    """a, b: first run of each side ({item: trace}); ja, jb: one bridge judge result or a list (one per run)."""
    ja = ja if ja is None or isinstance(ja, list) else [ja]
    jb = jb if jb is None or isinstance(jb, list) else [jb]
    ids = [i for i in a if i in b]
    rows = {"worse": [], "better": [], "other": []}
    for i in ids:
        ch = item_changes(a[i], b[i])
        if ch:
            rows[classify(a[i], b[i])].append({"id": i, "changes": ch})
    res = {"ids": ids, "only_a": [i for i in a if i not in b], "only_b": [i for i in b if i not in a],
           "sa": summary(a[i] for i in ids), "sb": summary(b[i] for i in ids), "rows": rows,
           "identical_answers": sum(1 for i in ids if a[i]["answer"]["text"] == b[i]["answer"]["text"]),
           "lost_source": [i for i in ids if shown(a[i]) and not shown(b[i])]}
    if ja and jb:
        pa = {p["queryId"]: p for p in ja[0]["pairs"]}
        pb = {p["queryId"]: p for p in jb[0]["pairs"]}
        changed = []
        for i in ids:
            if i in pa and i in pb:
                la, lb = judge_label(pa[i])[0], judge_label(pb[i])[0]
                if la != lb:
                    changed.append({"id": i, "a": la, "b": lb, "ca": pa[i]["boar"]["correctness"], "cb": pb[i]["boar"]["correctness"]})
        keep = set(ids)
        sa_ = [{i: v for i, v in pair_scores(j).items() if i in keep} for j in ja]
        sb_ = [{i: v for i, v in pair_scores(j).items() if i in keep} for j in jb]
        two = stats.two_level_diff(sa_, sb_, seed=seed)
        fa = stats.two_level_diff([stats.floor_adjust(x) for x in sa_], [stats.floor_adjust(x) for x in sb_], seed=seed)
        res["judge"] = {
            "floor_adjusted": fa,
            "label_changes": changed,
            "paired": two,  # with 1 run per side this equals the plain paired item bootstrap
            "mde": stats.mde_block(sa_, sb_, n_items=two["n"]) if two else None,
        }
    return res


def render(res, a, b, pa, pb, la, lb):
    sa, sb = res["sa"], res["sb"]
    where = " (desktop)" if is_desktop(a) and is_desktop(b) else ""
    L = [f"# Diff: {la} → {lb}", "", f"- A ({la}): {run_label(a, pa)}", f"- B ({lb}): {run_label(b, pb)}", "",
         f"| | {la} | {lb} |", "|---|---|---|",
         f"| items (shared) | {sa['n']} | {sb['n']} |",
         f"| errors | {sa['errors']} | {sb['errors']} |",
         f"| declined | {sa['declined']}/{sa['n']} | {sb['declined']}/{sb['n']} |",
         f"| weak_sources | {sa['weak']}/{sa['n']} | {sb['weak']}/{sb['n']} |",
         f"| no shown sources | {sa['noshown']}/{sa['n']} | {sb['noshown']}/{sb['n']} |",
         f"| tier | {sa['tiers']} | {sb['tiers']} |",
         f"| visible TTFT p50 / p95{where} | {fmt_ms(sa['ttft50'])} / {fmt_ms(sa['ttft95'])} | {fmt_ms(sb['ttft50'])} / {fmt_ms(sb['ttft95'])} |",
         f"| receipt TTFT (first token, may be empty) p50 / p95{where} | {fmt_ms(sa['rttft50'])} / {fmt_ms(sa['rttft95'])} | {fmt_ms(sb['rttft50'])} / {fmt_ms(sb['rttft95'])} |",
         f"| hidden thinking p50{where} | {fmt_ms(sa['hid50'])}{' **(hidden thinking)**' if (sa['hid50'] or 0) > 1000 else ''} | {fmt_ms(sb['hid50'])}{' **(hidden thinking)**' if (sb['hid50'] or 0) > 1000 else ''} |",
         f"| total p50 / p95{where} | {fmt_ms(sa['tot50'])} / {fmt_ms(sa['tot95'])} | {fmt_ms(sb['tot50'])} / {fmt_ms(sb['tot95'])} |",
         f"| retrieval p50{where} | {fmt_ms(sa['ret50'])} | {fmt_ms(sb['ret50'])} |",
         "", f"Identical answer text: **{res['identical_answers']}/{len(res['ids'])}** · items that lost their shown sources: **{len(res['lost_source'])}**"
         + (f" ({', '.join(res['lost_source'])})" if res["lost_source"] else "") + "."]
    if where:
        L.append("Latency is desktop (desktop-node): relative between arms on the same host, not a phone number.")
    if res["only_a"] or res["only_b"]:
        L.append(f"Not paired: only in A {res['only_a'] or '—'}; only in B {res['only_b'] or '—'}.")
    J = res.get("judge")
    if J:
        P = J["paired"]
        L += ["", "## Quality (paired)", ""]
        if P:
            m = J["mde"]
            L.append(f"Quality ratio over {P['n']} items judged on both sides, {P['runs_a']} run(s) A × {P['runs_b']} run(s) B: "
                     f"A {P['ratio_a']:.4f} → B {P['ratio_b']:.4f}; **Δ {P['diff']:+.4f} (95% CI {P['diff_ci95'][0]:+.4f} to {P['diff_ci95'][1]:+.4f})**, "
                     f"paired two-level bootstrap (items, then runs within item; {P['resamples']} resamples, seed {P['seed']}): {P['verdict']}.")
            F = J.get("floor_adjusted")
            if F:
                L.append(f"↳ floor-adjusted (a blank answer = 0), Σ(S−1)/Σ(S_ref−1): A {F['ratio_a']:.4f} → B {F['ratio_b']:.4f}; "
                         f"**Δ {F['diff']:+.4f} (95% CI {F['diff_ci95'][0]:+.4f} to {F['diff_ci95'][1]:+.4f})**, same bootstrap: {F['verdict']}.")
            if P["runs_a"] == 1 and P["runs_b"] == 1:
                L.append("One run per side: the CI holds item noise only; generation (run-to-run) noise is not represented, so it is too narrow.")
            L += ["", mde_text(m) + ".",
                  "", (f"**|Δ| {abs(P['diff']):.3f} < MDE {m['mde']:.3f}: inside the noise at this budget; not decidable on quality.**"
                       if abs(P["diff"]) < m["mde"] else f"|Δ| {abs(P['diff']):.3f} ≥ MDE {m['mde']:.3f}: large enough to be detectable at this budget."),
                  "", "MDE by budget:", ""] + mde_table(m)
        else:
            L.append("No item judged in both runs.")
        if J["label_changes"]:
            L += ["", "| id | judge label A → B | correctness A → B |", "|---|---|---|"] + [
                f"| `{c['id']}` | {c['a']} → {c['b']} | {c['ca']:g} → {c['cb']:g} |" for c in J["label_changes"]]
    hdr = [f"| id | change | codes {la} | codes {lb} | shown {la} | shown {lb} |", "|---|---|---|---|---|---|"]
    for name, key in (("Worse", "worse"), ("Better", "better"), ("Other changes (same decline/source status)", "other")):
        rows = res["rows"][key]
        L += ["", f"**{name}: {len(rows)}**", ""]
        if rows:
            L += hdr
            for r in rows:
                x, y = a[r["id"]], b[r["id"]]
                L.append(f"| `{r['id']}` | {'; '.join(r['changes'])} | {cell(', '.join(route_codes(x)) or '—', 300)} | {cell(', '.join(route_codes(y)) or '—', 300)} | "
                         f"{cell(' · '.join(shown(x)) or '—', 200)} | {cell(' · '.join(shown(y)) or '—', 200)} |")
    changed_text = [r for k in ("worse", "better", "other") for r in res["rows"][k] if "answer text" in r["changes"]]
    if changed_text:
        L += ["", "## Answer text changes", "", f"| id | {la} | {lb} |", "|---|---|---|"]
        for r in changed_text:
            L.append(f"| `{r['id']}` | {short(a[r['id']]['answer']['text'])} | {short(b[r['id']]['answer']['text'])} |")
    return "\n".join(L) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("a", nargs="?")
    ap.add_argument("b", nargs="?")
    ap.add_argument("--runs-a", nargs="+", help="A runs (first = per-item tables); replaces the positional A")
    ap.add_argument("--runs-b", nargs="+", help="B runs; replaces the positional B")
    ap.add_argument("--labels", nargs=2, default=None)
    ap.add_argument("--judgments-a", nargs="+", help="one judgments file per A run, same order")
    ap.add_argument("--judgments-b", nargs="+", help="one judgments file per B run, same order")
    ap.add_argument("--bench", help="restrict judged items to the bench ids")
    ap.add_argument("--seed", type=int, default=11)
    ap.add_argument("--out")
    x = ap.parse_args(argv)
    runs_a = x.runs_a or ([x.a] if x.a else None)
    runs_b = x.runs_b or ([x.b] if x.b else None)
    if not runs_a or not runs_b:
        ap.error("give A and B (positional, or --runs-a / --runs-b)")
    a, b = read_traces(runs_a[0]), read_traces(runs_b[0])
    la, lb = x.labels or (Path(runs_a[0]).stem, Path(runs_b[0]).stem)
    ja = jb = None
    if x.judgments_a and x.judgments_b:
        if len(x.judgments_a) != len(runs_a) or len(x.judgments_b) != len(runs_b):
            ap.error("give one judgments file per run on each side, in the same order")
        ids = None
        if x.bench:
            from scorers.bench import Bench
            ids = [q["id"] for q in Bench(x.bench).items_for(set(a) | set(b))]
        ja = [judge_pairs(j, ids, x.seed) for j in x.judgments_a]
        jb = [judge_pairs(j, ids, x.seed) for j in x.judgments_b]
    elif x.judgments_a or x.judgments_b:
        ap.error("give judgments for both sides (--judgments-a and --judgments-b)")
    res = diff(a, b, ja, jb, x.seed)
    md = render(res, a, b, runs_a[0], runs_b[0], la, lb)
    if len(runs_a) > 1 or len(runs_b) > 1:
        md = md.replace("\n\n", "\n\n" + "Runs: A " + ", ".join(f"`{p}`" for p in runs_a) + " · B " + ", ".join(f"`{p}`" for p in runs_b) + "\n\n", 1)
    write_out(md, x.out)
    return res


if __name__ == "__main__":
    main()
