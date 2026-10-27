#!/usr/bin/env python3
"""Arm leadgate vs main on the card's frozen criterion (leadgate.README.md), deterministic parts:
Sources = the last `sources` event (answer.shown): what reached the prompt, emitted before generation, so it does
not move with sampling (retrieval.kept is the post-generation result and empties on a decline).
  (a) Wikivoyage passages in the final sources of non-travel items: main -> arm (bar: fall >= 40%);
  (b) ON pairs of sonar/exp/02 pairs.json that main shows: how many disappear in the arm (bar: <= 1);
  (c) travel-category items (travel-*, local-*): final sources identical to main;
  (d) items whose sources lose only Wikivoyage guides and become newly declined (bar: none);
  (e) median prompt tokens on non-travel items that lost a guide: main -> arm (bar: down);
  coordinator (QUEUE #5): items answered with a removed guide in main -> declined / memory answer / answered otherwise.
New (item, guide) pairs not in pairs.json are listed for blind labelling, not used to pass/fail.
Usage: python3 leadgate-slice.py MAIN.traces.jsonl ARM.traces.jsonl QUESTIONS.jsonl PAIRS.json
"""
import json, statistics, sys

WV = "Wikivoyage: "


def read(p):
    return {t["itemId"]: t for t in (json.loads(l) for l in open(p) if l.strip())}


def titles(srcs):
    return [s if isinstance(s, str) else s["title"] for s in srcs]


def guides(srcs):
    return [t[len(WV):] for t in titles(srcs) if t.startswith(WV)]


def memory(t):
    return not t["answer"]["declined"] and not t["answer"]["shown"] and not t.get("error") and bool(t["answer"]["text"].strip())


def main(pm, pa, pq, pp):
    m, a = read(pm), read(pa)
    cat = {q["id"]: q.get("category", "") for q in (json.loads(l) for l in open(pq) if l.strip())}
    pairs = json.load(open(pp))
    ids = [i for i in m if i in a]
    travel = lambda i: cat.get(i, "").startswith(("travel", "local"))
    nt = [i for i in ids if not travel(i)]
    print(f"items: {len(ids)} paired ({len(nt)} non-travel, {len(ids) - len(nt)} travel/local)\n")

    wm = sum(len(guides(m[i]["answer"]["shown"])) for i in nt)
    wa = sum(len(guides(a[i]["answer"]["shown"])) for i in nt)
    rm = sum(len(guides(m[i]["retrieval"]["raw"])) for i in nt)
    ra = sum(len(guides(a[i]["retrieval"]["raw"])) for i in nt)
    drop = 100 * (wm - wa) / wm if wm else 0
    print(f"(a) Wikivoyage passages in the prompt's sources (sources event = answer.shown), non-travel: {wm} -> {wa} ({drop:.0f}% fewer; bar >= 40%) · in raw: {rm} -> {ra}")

    shows = lambda t, title: (WV + title) in t["answer"]["shown"]
    on = [p for p in pairs if p["on"] and not p["travel"] and p["id"] in m and p["id"] in a and shows(m[p["id"]], p["title"])]
    lost = [p for p in on if not shows(a[p["id"]], p["title"])]
    print(f"(b) ON pairs main shows: {len(on)}; lost in arm: {len(lost)} {[p['title'] + '@' + p['id'] for p in lost]} (bar <= 1)")

    key = lambda t: t["answer"]["shown"]
    tr_changed = [i for i in ids if travel(i) and key(m[i]) != key(a[i])]
    print(f"(c) travel/local items with changed prompt sources: {len(tr_changed)}/{len(ids) - len(nt)} {tr_changed} (bar 0)")

    lost_guide = {}
    for i in nt:
        gm, ga = guides(m[i]["answer"]["shown"]), guides(a[i]["answer"]["shown"])
        removed = [g for g in gm if g not in ga]
        if removed:
            lost_guide[i] = removed
    only_guides = []
    for i, removed in lost_guide.items():
        km, ka = m[i]["answer"]["shown"], a[i]["answer"]["shown"]
        if all(t in km for t in ka) and all(t.startswith(WV) for t in km if t not in ka):
            only_guides.append(i)
    new_decl = [i for i in only_guides if a[i]["answer"]["declined"] and not m[i]["answer"]["declined"]]
    print(f"(d) items losing only guides: {len(only_guides)}; newly declined among them: {len(new_decl)} {new_decl} (bar 0)")

    pt = [(m[i]["timing"]["promptTokens"], a[i]["timing"]["promptTokens"]) for i in lost_guide]
    pt = [(x, y) for x, y in pt if x is not None and y is not None]
    if pt:
        print(f"(e) median prompt tokens, non-travel items that lost a guide ({len(pt)} with a generation in both): "
              f"{statistics.median(x for x, _ in pt):.0f} -> {statistics.median(y for _, y in pt):.0f} (bar: down)")
    else:
        print("(e) no item that lost a guide had a generation in both runs")

    print("\nQUEUE #5: items answered (not declined) with a guide the arm removed, in main:")
    moved = {"declined": [], "memory": [], "answered with sources": [], "error": []}
    for i, removed in lost_guide.items():
        x, y = m[i], a[i]
        if x["answer"]["declined"] or not any(WV + g in x["answer"]["shown"] for g in removed):
            continue
        k = "error" if y.get("error") else "declined" if y["answer"]["declined"] else "memory" if memory(y) else "answered with sources"
        moved[k].append(i)
    for k, v in moved.items():
        print(f"  -> {k}: {len(v)} {v}")

    known = {(p["id"], p["title"]) for p in pairs}
    new = sorted({(i, g) for i, gs in lost_guide.items() for g in gs if (i, g) not in known})
    print(f"\nremoved (item, guide) pairs not in pairs.json, to label blind: {len(new)}")
    for i, g in new:
        print(f"  {i}\t{g}\t{m[i]['question'][:90]}")
    print("\nper item (non-travel, lost a guide): removed guides | main -> arm: declined, shown count, memory")
    for i, removed in lost_guide.items():
        print(f"  {i}: {', '.join(removed)} | {m[i]['answer']['declined']}->{a[i]['answer']['declined']}, "
              f"{len(m[i]['answer']['shown'])}->{len(a[i]['answer']['shown'])}, {memory(m[i])}->{memory(a[i])}")


if __name__ == "__main__":
    if len(sys.argv) != 5:
        sys.exit(__doc__)
    main(*sys.argv[1:])
