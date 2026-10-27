#!/usr/bin/env python3
"""Calibration ladder: BOAR quality ratios next to Claude anchors answering from memory (harness/anchors.mjs, no tools,
no web), all judged the same way (harness/judge.mjs, judge.v1, frozen Opus+web references, both A/B orders).
Deterministic (fixed bootstrap seed, no timestamps). Anchors whose judgments are missing or incomplete show as pending.

Usage: python3 harness/ladder.py [--anchors runs/anchors-2026-10-02] [--bench bench/v0.1] [--seed 11]
           --out reports/anchors-2026-10-02/ladder.md
"""
import argparse, json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from harness.common import REPO, pair_scores, write_out  # noqa: E402
from scorers import stats  # noqa: E402
from scorers.score import judge_pairs  # noqa: E402
from scorers.trace import read_traces  # noqa: E402

DECLINE = 0.306  # always-decline system, raw (rnd/research/QUEUE.md: 79 judged declines score 1.50/5; analysis plan: D fixed)
ANCHORS = ["haiku", "sonnet", "opus", "fable"]
NIGHT = "runs/night-2026-10-01"
# Existing BOAR rows: the judgments behind the cited reports, recomputed here with the same code as the anchors.
BOAR = [
    {"name": "iPhone Qwen2.5-1.5B, device (q15)", "short": "iPhone 1.5B dev", "runs": ["runs/devices/2026-10-02/ios-q15-r1.judgments.jsonl", "runs/devices/2026-10-02/ios-q15-r2.judgments.jsonl"],
     "cite": "reports/devices-2026-10-02/ios-q15.md", "cited": 0.394},
    {"name": "iPhone Qwen2.5-1.5B, desktop proxy (v5)", "short": "iPhone 1.5B v5", "runs": [f"{NIGHT}/ios-main-v5-s42.judgments.jsonl", f"{NIGHT}/ios-main-v5-s43.judgments.jsonl"],
     "cite": "reports/night-2026-10-01/ios-main-v5.md", "cited": 0.395},
    {"name": "Android Qwen3-4B, kit A (desktop proxy)", "short": "Android 4B", "runs": [f"{NIGHT}/and-qwen-s42.judgments.jsonl", f"{NIGHT}/and-qwen-s43.judgments.jsonl"],
     "cite": "reports/night-2026-10-01/and-qwen.md", "cited": 0.512},
    {"name": "Android Gemma 4 E4B (desktop proxy, not adopted)", "short": "Gemma E4B", "runs": [f"{NIGHT}/and-gemma-s42.judgments.jsonl", f"{NIGHT}/and-gemma-s43.judgments.jsonl"],
     "cite": "reports/night-2026-10-01/and-gemma-s42.md", "cited": 0.496},
]


def above(r):
    return (r - DECLINE) / (1 - DECLINE)


def f3(x):
    return "—" if x is None else f"{x:.3f}"


def ci(c):
    return f"{c[0]:.3f}–{c[1]:.3f}"


def load_runs(paths, ids, seed):
    res = [judge_pairs(REPO / p, ids, seed) for p in paths]
    return res, [pair_scores(r) for r in res]


def system_row(runs, seed):
    raw = stats.two_level_ratio(runs, seed=seed)
    fl = stats.two_level_ratio([stats.floor_adjust(r) for r in runs], seed=seed)
    return {"raw": raw, "floor": fl}


def by_category(runs, cats):
    obs = stats._obs(runs)
    out = {}
    for i, v in obs.items():
        b, r = stats._item_mean(v)
        c = out.setdefault(cats[i], [0.0, 0.0, 0])
        c[0] += b; c[1] += r; c[2] += 1
    return {k: (num / den, n) for k, (num, den, n) in out.items()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--anchors", default="runs/anchors-2026-10-02")
    ap.add_argument("--bench", default="bench/v0.1")
    ap.add_argument("--seed", type=int, default=11)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    qs = [json.loads(l) for l in (REPO / a.bench / "questions.public.jsonl").read_text().splitlines() if l.strip()]
    ids = [q["id"] for q in qs if (q.get("grading") or {}).get("type") != "venue-list"]
    cats = {q["id"]: q["category"] for q in qs}

    systems = []  # (name, short, kind, runs, row, extra)
    for m in ANCHORS:
        jp, tp = REPO / a.anchors / f"{m}.judgments.jsonl", REPO / a.anchors / f"{m}.traces.jsonl"
        if not jp.exists() or not tp.exists():
            systems.append({"name": f"Claude {m}, no web (anchor)", "short": m, "kind": "anchor", "pending": "not judged yet"})
            continue
        res, runs = load_runs([jp.relative_to(REPO)], ids, a.seed)
        traces = read_traces(tp)
        n_pairs = len(runs[0])
        model = sorted({t["runtime"]["model"] for t in traces.values()})
        words = sorted(len(t["answer"]["text"].split()) for t in traces.values())
        s = res[0]["summary"]
        systems.append({"name": f"Claude {m}, no web (anchor) · `{', '.join(model)}`", "short": m, "kind": "anchor", "runs": runs,
                        "row": system_row(runs, a.seed), "n_pairs": n_pairs, "n_traces": len(traces),
                        "declined": sorted(i for i, t in traces.items() if t["answer"]["declined"]),
                        "words_p50": words[len(words) // 2], "rubric": s["rubricBoar"], "rubric_ref": s["rubricRef"],
                        "winTieLoss": (s["boarWin"], s["tie"], s["refWin"]), "pc": s["positionConsistency"],
                        "judge": res[0]["judgeMeta"], "cite": f"`{jp.relative_to(REPO)}`"})
    for b in BOAR:
        res, runs = load_runs(b["runs"], ids, a.seed)
        s = res[0]["summary"]
        systems.append({**b, "kind": "boar", "runs": runs, "row": system_row(runs, a.seed), "n_pairs": len(stats._obs(runs))})

    done = [s for s in systems if "row" in s]
    done.sort(key=lambda s: -s["row"]["raw"]["ratio"])
    ref4b = next(s for s in systems if s["short"] == "Android 4B")

    L = ["# Calibration ladder: BOAR vs Claude answering from memory (bench v0.1)", "",
         "Every row is judged the same way: `harness/judge.mjs` (judge.v1, judge = Opus, pairwise, both A/B orders, blind) against the "
         "frozen **Opus + web** references of bench v0.1, over the 57 non-venue items. Anchors are Claude models run by "
         "`harness/anchors.mjs`: `claude -p`, **no tools, no web**, system prompt `anchor.v1` = the reference prompt `reference.v1` "
         "minus its web lines, user prompt = the bare question. The only differences vs the reference are web access and the model.", "",
         f"- **raw** = Σ S / Σ S_ref (judge-core ratio). Reference itself (Opus + web) = 1.000 by construction.",
         f"- **floor-adj** = Σ(S−1)/Σ(S_ref−1): removes the judge's rubric floor of 1 (a blank answer = 0).",
         f"- **above decline** = (raw − {DECLINE})/(1 − {DECLINE}): share of the gap between an always-decline system "
         f"(raw {DECLINE}, `../rnd/research/QUEUE.md`, 79 judged declines at 1.50/5) and the reference. CI = the raw CI mapped through the same line.",
         f"- 95% CI: two-level bootstrap (items, then runs within item; 2,000 resamples, seed {a.seed}). "
         "**Anchors: one run each**, so their CI is an item bootstrap only (generation noise not represented; BOAR's σ²_run ≈ 0.25 suggests ±0.02–0.03 more).", "",
         "## Ladder (ordered by raw ratio)", "",
         "| # | System | runs × items | raw (95% CI) | floor-adj (95% CI) | above decline (95% CI) | source |", "|---|---|---|---|---|---|---|",
         "| — | **Opus + web (the reference)** | — | 1.000 (by construction) | 1.000 | 1.000 | `bench/v0.1/refs/` |"]
    rows = done + [{"name": "Always-decline (every answer a decline)", "kind": "floor"}]
    rows.sort(key=lambda s: -(s["row"]["raw"]["ratio"] if "row" in s else DECLINE))
    for n, s in enumerate(rows, 1):
        if s["kind"] == "floor":
            L.append(f"| {n} | Always-decline (every answer a decline) | 79 declines | {DECLINE:.3f} (fixed) | 0.000 | 0.000 | `../rnd/research/QUEUE.md` |")
            continue
        raw, fl = s["row"]["raw"], s["row"]["floor"]
        lab = f"**{s['name']}**" if s["kind"] == "anchor" else s["name"]
        cited = f"; cited {s['cited']:.3f}" if s.get("cited") else ""
        src = s["cite"] if s["kind"] == "anchor" else f"`{s['cite']}`{cited}"
        L.append(f"| {n} | {lab} | {raw['runs']} × {raw['n_items']} | {raw['ratio']:.3f} ({ci(raw['ci95'])}) | {fl['ratio']:.3f} ({ci(fl['ci95'])}) | "
                 f"{above(raw['ratio']):.3f} ({above(raw['ci95'][0]):.3f}–{above(raw['ci95'][1]):.3f}) | {src} |")
    for s in systems:
        if "pending" in s:
            L.append(f"| — | Claude {s['short']}, no web (anchor) | — | pending | — | — | {s['pending']} |")
    L += ["", "BOAR rows are recomputed from their judgment files with the same code as the anchors and match the cited reports. Gemma: its report covers s42 alone (0.487); 0.496 is the 2-seed pool cited in `../rnd/research/summit/S1-dossier.md`. Always-decline 0.306 and above-decline 0.297 for the 4B: `../rnd/research/QUEUE.md` (F3, floor refined).", ""]

    anchors = [s for s in systems if s["kind"] == "anchor" and "row" in s]
    if anchors:
        L += ["## Each anchor vs Android 4B (paired, same 57 items)", "",
              "| Anchor | raw | Android 4B (2 runs) | Δ anchor − 4B (95% CI) | reading |", "|---|---|---|---|---|"]
        for s in anchors:
            d = stats.two_level_diff(ref4b["runs"], s["runs"], seed=a.seed)
            L.append(f"| {s['short']} | {d['ratio_b']:.3f} | {d['ratio_a']:.3f} | {d['diff']:+.3f} ({d['diff_ci95'][0]:+.3f} to {d['diff_ci95'][1]:+.3f}) | {d['verdict'].replace('B ', 'anchor ')} |")
        op = next((s for s in anchors if s["short"] == "opus"), None)
        if op:
            r = op["row"]["raw"]
            gap, fgap = 1 - r["ratio"], 1 - op["row"]["floor"]["ratio"]
            if r["ci95"][0] > 1:
                verdict = ("**the web adds nothing this judge can see: Opus from memory scores above Opus + web** "
                           f"(Δ {-gap:+.3f}, 95% CI {r['ci95'][0] - 1:+.3f} to {r['ci95'][1] - 1:+.3f}; win/tie/loss {op['winTieLoss'][0]:.0%} / {op['winTieLoss'][1]:.0%} / {op['winTieLoss'][2]:.0%}, "
                           f"position consistency {op['pc']:.0%}: the judge mostly cannot tell them apart)")
            elif r["ci95"][1] < 1:
                verdict = f"the web is worth **{gap:.3f}** of the reference score ({fgap:.3f} floor-adjusted)"
            else:
                verdict = f"no detectable web effect (CI contains 1.000; point {gap:+.3f})"
            L += ["", f"**What web adds (Opus):** Opus without web scores **{r['ratio']:.3f}** ({ci(r['ci95'])}) of Opus with web; floor-adjusted "
                  f"{op['row']['floor']['ratio']:.3f}. Same model id as the reference (`claude-opus-5-5`, all 60 refs), same prompt minus the web lines, "
                  f"similar length, same judge: {verdict}. Likely why: the judge (Opus) has no web either, so it scores against its own memory and cannot "
                  "reward freshness or verified sources; the 'Sources:' block is stripped before judging; and searching costs the reference answer "
                  "some breadth. This is a property of the judge, not proof that retrieval is useless: items whose truth moved after the training "
                  "cutoff are rare in v0.1."]
        L += ["", "## Anchor details", "", "| Anchor | pairs judged | win / tie / loss vs ref | position consistency | rubric correctness / completeness / usefulness (ref) | answer words p50 | flagged declines |",
              "|---|---|---|---|---|---|---|"]
        for s in anchors:
            rb, rr = s["rubric"], s["rubric_ref"]
            w, t, l = s["winTieLoss"]
            L.append(f"| {s['short']} | {s['n_pairs']}/{s['n_traces']} | {w:.0%} / {t:.0%} / {l:.0%} | {s['pc']:.0%} | "
                     f"{rb['correctness']:.2f} / {rb['completeness']:.2f} / {rb['usefulness']:.2f} ({rr['correctness']:.2f} / {rr['completeness']:.2f} / {rr['usefulness']:.2f}) | "
                     f"{s['words_p50']} | {len(s['declined'])}{': ' + ', '.join(s['declined']) if s['declined'] else ''} |")

        # per category
        catn = {}
        for i in ids:
            catn[cats[i]] = catn.get(cats[i], 0) + 1
        bc4 = by_category(ref4b["runs"], cats)
        bca = {s["short"]: by_category(s["runs"], cats) for s in anchors}
        L += ["", "## Per-category raw ratio: anchors vs Android 4B", "",
              "Small cells (n = items per category): read direction, not size. No CIs at this n.", "",
              "| Category | n | Android 4B | " + " | ".join(f"{s['short']} (Δ vs 4B)" for s in anchors) + " |",
              "|---|---|---|" + "---|" * len(anchors)]
        for c in sorted(bc4, key=lambda c: (-bc4[c][1], c)):
            cells = []
            for s in anchors:
                v = bca[s["short"]].get(c)
                cells.append("—" if v is None else f"{v[0]:.3f} ({v[0] - bc4[c][0]:+.3f})")
            L.append(f"| {c} | {bc4[c][1]} | {bc4[c][0]:.3f} | " + " | ".join(cells) + " |")

    if anchors:
        L += ["", "## Reading", "",
              "- **The scale saturates at frontier size.** Sonnet, Opus and Fable from memory all land at or above ~0.95; under judge.v1 a ratio near 1.0 means "
              "\"as good as a frontier model\", with or without web. The useful span of the bench is always-decline (0.306) → frontier (~1.0).",
              "- **Where BOAR sits on that span:** Android 4B is ~0.30 of the way from always-decline to the reference (above-decline column), "
              "Haiku from memory ~0.50, iPhone 1.5B ~0.13. The 0.50 raw bar the project uses is below Haiku-from-memory (0.653).",
              "- **The gap this judge measures is knowledge + length (it does not reward web):** completeness and usefulness are where BOAR loses most (Android 4B ~2.2 vs ref ~4.9; "
              "anchors answer at ~200–250 words, the 4B at ~51)."]
    L += ["", "## Caveats", "",
          "- **Claude judges Claude.** The judge is Opus; the anchors are Claude models and the reference is Opus + web. Self-preference "
          "(the Opus anchor is literally the judge's own model, answering from the judge's own memory) "
          "and shared style/structure with the reference likely inflate the anchors relative to BOAR's Qwen/Gemma answers. "
          "Read the gap BOAR → anchors as an upper bound until a cross-family judge (the held GPT-5.5 pilot) re-scores it.",
          "- **One run per anchor.** CIs are item-bootstrap only; BOAR rows pool 2 runs. A second anchor run would add generation noise "
          "(BOAR σ²_run ≈ 0.25 → roughly ±0.02–0.03 on the ratio).",
          "- **No web ≠ offline phone.** Anchors have no retrieval, no packs, no latency or memory budget, and run at frontier size in the cloud. "
          "They calibrate *what a frontier model knows from memory*, not what a phone could do; BOAR has local packs the anchors lack.",
          "- **Prompt parity, not format parity.** Anchors get `anchor.v1` (the reference prompt minus web lines: ≤ 250 words, lead with the answer); "
          "BOAR answers are much shorter (Android 4B ~51 words). Completeness/usefulness rubric gaps partly reflect length.",
          "- **Declines.** `answer.declined` on anchors is a regex flag (gives up on the question); it does not affect the quality ratio.",
          "- **Fable / Opus aliases** are resolved model ids recorded per trace (`runtime.model`); the alias may move between runs.", "",
          "## Inputs", "", f"- Anchors: `{a.anchors}/<model>.traces.jsonl` (EvalTrace v1, adapter `reference-cli`) and `<model>.judgments.jsonl`; spend `{a.anchors}/spend.jsonl`, judge spend `runs/judge-spend.jsonl`.",
          "- BOAR rows: " + "; ".join(f"{s['short']}: " + ", ".join(f"`{p}`" for p in s["runs_paths"]) for s in [{"short": b["short"], "runs_paths": b["runs"]} for b in BOAR]),
          f"- Generated by `python3 harness/ladder.py --out {a.out}` (seed {a.seed}).", ""]
    write_out("\n".join(L), REPO / a.out)
    print("\n".join(L[:40]))


if __name__ == "__main__":
    main()
