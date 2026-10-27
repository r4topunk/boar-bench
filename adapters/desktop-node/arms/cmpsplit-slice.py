#!/usr/bin/env python3
"""Arm cmpsplit vs main on the card's frozen criterion (cmpsplit.README.md). Deterministic parts only:
  (a) both-sides-in-context on the comparison slice: the prompt's sources (the sources event = answer.shown; emitted
      before generation, so sampling doesn't move it; retrieval.kept empties on a decline) with >= 1 title per gold side;
      also reported for retrieval.raw (what the retriever returned, before the engine's gates);
  (b) citation-check declines (route codes grounding:all-citations-removed* / grounding:uncited-with-sources*) on the slice;
  (c) non-slice items whose retrieval.raw (title+section list) changed (splitter false fires);
  (e) retrievalMs p50 on the slice, main vs arm.
(d) needs the judge (confident-wrong) and the gate (safety): not computed here.
Usage: python3 cmpsplit-slice.py MAIN.traces.jsonl ARM.traces.jsonl
"""
import json, re, statistics, sys

# Gold sides, frozen in cmpsplit.README.md before any run (title regexes, case-insensitive).
GOLD = {
    "vit-hum-002": [r"mozi|mohis", r"confucian"],
    "lan-cmp-001": [r"brazil", r"russia"],
    "lan-cmp-002": [r"polar bear", r"grizzly|brown bear"],
    "vit-sci-002": [r"japan", r"german"],
    "lan-cmp-004": [r"moose", r"bison"],
    "lan-cmp-005": [r"saltwater crocodile", r"nile crocodile"],
    "vit-cry-005": [r"privacy pool", r"tornado"],
    "vit-fa-004": [r"japan", r"nigeria"],
    "vit-fa-005": [r"rhino", r"elephant"],
    "vit-fa-006": [r"blue whale", r"dinosaur|sauropod|argentinosaurus"],
    "vit-fa-021": [r"lion", r"tiger"],
    "vit-fa-022": [r"elephant", r"rhino"],
}
CITE_DECLINE = re.compile(r"^grounding:(all-citations-removed|uncited-with-sources)")


def read(p):
    return {t["itemId"]: t for t in (json.loads(l) for l in open(p) if l.strip())}


def sides_hit(srcs, gold):
    return [any(re.search(g, s["title"], re.I) for s in srcs) for g in gold]


def cite_declined(t):
    return t["answer"]["declined"] and any(CITE_DECLINE.match(c) for c in t["route"]["reasonCodes"])


def main(pm, pa):
    m, a = read(pm), read(pa)
    slice_ids = [i for i in GOLD if i in m and i in a]
    print(f"slice: {len(slice_ids)} items ({', '.join(slice_ids)})\n")
    print("| item | sides | raw main→arm | prompt main→arm | shown main→arm | declined main→arm | cite-decline main→arm | retrievalMs main→arm |")
    print("|---|---|---|---|---|---|---|---|")
    tot = {"raw": [0, 0], "kept": [0, 0], "both_kept": [0, 0], "cite": [0, 0]}
    rms = [[], []]
    for i in slice_ids:
        g = GOLD[i]
        row = []
        for k, t in enumerate((m[i], a[i])):
            # Prompt sources = the sources event (answer.shown): emitted before generation, so not moved by sampling.
            r, kp = sides_hit(t["retrieval"]["raw"], g), sides_hit([{"title": x} for x in t["answer"]["shown"]], g)
            tot["raw"][k] += sum(r)
            tot["kept"][k] += sum(kp)
            tot["both_kept"][k] += all(kp)
            tot["cite"][k] += cite_declined(t)
            if t["timing"]["retrievalMs"] is not None:
                rms[k].append(t["timing"]["retrievalMs"])
            row.append((r, kp, len(t["answer"]["shown"]), t["answer"]["declined"], cite_declined(t), t["timing"]["retrievalMs"]))
        f = lambda x: "".join("●" if y else "○" for y in x)
        (r0, k0, s0, d0, c0, t0), (r1, k1, s1, d1, c1, t1) = row
        print(f"| {i} | {' · '.join(g)} | {f(r0)}→{f(r1)} | {f(k0)}→{f(k1)} | {s0}→{s1} | {d0}→{d1} | {c0}→{c1} | {t0:.0f}→{t1:.0f} |")
    n = len(slice_ids)
    print(f"\nsides in raw:  {tot['raw'][0]}/{2*n} → {tot['raw'][1]}/{2*n}")
    print(f"sides in prompt: {tot['kept'][0]}/{2*n} → {tot['kept'][1]}/{2*n}")
    pp = lambda x: 100 * x / n
    print(f"(a) both-sides-in-context (prompt) items: {tot['both_kept'][0]}/{n} ({pp(tot['both_kept'][0]):.0f}%) → {tot['both_kept'][1]}/{n} ({pp(tot['both_kept'][1]):.0f}%), Δ {pp(tot['both_kept'][1]) - pp(tot['both_kept'][0]):+.0f} pp (bar: ≥ +30 pp)")
    print(f"(b) citation-check declines on the slice: {tot['cite'][0]} → {tot['cite'][1]} (bar: fall by ≥ 3)")
    key = lambda t: [(s["title"], s["section"]) for s in t["retrieval"]["raw"]]
    changed = [i for i in m if i in a and i not in GOLD and key(m[i]) != key(a[i])]
    print(f"(c) non-slice items with changed retrieval.raw: {len(changed)}/{len([i for i in m if i not in GOLD])} {changed} (bar: ≤ 1, hand-checked)")
    if rms[0] and rms[1]:
        p0, p1 = statistics.median(rms[0]), statistics.median(rms[1])
        print(f"(e) retrievalMs p50 on the slice: {p0:.0f} → {p1:.0f} ms (Δ {p1 - p0:+.0f}; bar: ≤ +50 ms)")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(*sys.argv[1:])
