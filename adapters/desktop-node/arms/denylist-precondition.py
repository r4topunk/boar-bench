#!/usr/bin/env python3
"""QUEUE #11 step 1 (card unsafe-passage-denylist, criterion 1): on a run, count safety-rule hits (rules v0.4, forbid
rules, the bench checker's negation logic) whose answer comes from a denylisted sentence. Prints item ids only.

Every forbid rule of the version is checked on every answered item (not declined, non-empty; blind items carry no rule
overlay). A hit is TRACEABLE when the item's pre-answer sources (the `sources` event = answer.shown) include an article
whose title (display prefix "<Source>: " removed, case-insensitive, exact) is a denylist entry's title AND that entry's
rule is the hit's rule (match-rule.md: title match, pack not required). Word overlap between the answer's hit sentence
and the entry's sentence is printed as a sanity check (traces carry no passage text, protocol 1.0).
Usage: python3 denylist-precondition.py DENYLIST.json RUN1.traces.jsonl [RUN2 ...] [--safety-version v0.4]
"""
import json, re, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from scorers.bench import Bench  # noqa: E402

PREFIX = re.compile(r"^(Wikipedia|Wikibooks|Wikivoyage|US government|Appropedia|ethereum\.org|Ethereum EIPs/ERCs|Ethereum specs|Bitcoin BIPs):\s*")
words = lambda s: set(re.findall(r"[a-zà-ú]+", s.lower()))


def main(argv):
    ver = "v0.4"
    if "--safety-version" in argv:
        ver = argv[argv.index("--safety-version") + 1]
        argv = [a for i, a in enumerate(argv) if a != "--safety-version" and (i == 0 or argv[i - 1] != "--safety-version")]
    deny = json.load(open(argv[0]))["items"]
    S = Bench(Path(__file__).resolve().parents[3] / "bench" / "v0.1", safety_version=ver).safety()
    forbid = [rid for rid, m in S["meta"].items() if m.get("type", "forbid") == "forbid"]
    total = 0
    for run in argv[1:]:
        ts = [json.loads(l) for l in open(run) if l.strip()]
        n_hit, trace = [], []
        for t in ts:
            a = t["answer"]
            if a["declined"] or not a["text"].strip() or t.get("error"):
                continue
            hits = S["check"](a["text"], forbid, S)
            if not hits:
                continue
            n_hit.append(f"{t['itemId']}:{'+'.join(sorted({h['rule'] for h in hits}))}")
            shown = {PREFIX.sub("", s).lower() for s in a["shown"]}
            for h in hits:
                for e in deny:
                    if e["rule"] == h["rule"] and e["title"].lower() in shown:
                        ov = len(words(h["sentence"]) & words(e["sentence"])) / max(1, len(words(e["sentence"])))
                        k = f"{t['itemId']}:{h['rule']}<-{e['title']}"
                        # one hit per (item, rule, article): "Cold weather" is listed for both packs
                        if not any(x.startswith(k + " ") for x in trace):
                            trace.append(f"{k} (word overlap {ov:.2f})")
        total += len(trace)
        print(f"{Path(run).name}: answered items with a v0.4 forbid hit: {len(n_hit)} {n_hit}")
        print(f"  traceable to a denylisted sentence: {len(trace)} {trace}")
    print(f"TOTAL traceable hits over {len(argv) - 1} run(s): {total} (card criterion 1: >= 2 to proceed)")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    main(sys.argv[1:])
