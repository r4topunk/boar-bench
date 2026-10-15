#!/usr/bin/env python3
"""Assemble boar-eval bench v0.3-ext from the maintainer's writer files (deterministic; byte-identical on re-run). Copy of
bench/v0.2/assemble.py pointed at private/bench-v03/ (one writer, no rewrite rounds: gate fixes replace the line in place).

Inputs (read-only, bench/v0.3/work/):
  <category>.jsonl   one file per category (10), items pasted from the writer chats after hand fact-check
  vstyle.ids         optional (D3 = fold): the writer's "V-STYLE IDS:" lines; only v03 ids are taken from it
Output: bench/v0.3/work/questions.v03.jsonl (category order below, then id), with safety_rules mapped to rules
v0.7; with --wave1 only ids 01..w1 (the pre-declared 60-item fallback). If vstyle.ids exists, bench/v0.3/plan/vstyle.ids
(ids only, sorted) is written for the freeze. Prints counts and hashes only, never item text.
Usage (from boar-eval/): python3 bench/v0.3/assemble.py [--wave1]
"""
import argparse, hashlib, json, re, sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = Path("bench/v0.3/work/")
OUT = Path("bench/v0.3/work/questions.v03.jsonl")
ORDER = ["explanation", "reasoning", "comparison", "crypto", "honesty-refusal", "health", "danger", "synthesis",
         "travel-practical", "travel-local"]
COUNTS = dict(zip(ORDER, [21, 21, 13, 13, 12, 8, 10, 6, 4, 2]))
WAVE1 = dict(zip(ORDER, [11, 11, 7, 7, 7, 4, 6, 3, 2, 2]))
ID_RX = re.compile(r"v03-[a-z-]+-[0-9]{2}")

# safety_rules -> ids in boar-eval/scorers/vendor/safety/rules.v0.7.json (matcher safety_check.v0.7.py, addendum 04).
# Same rule as v0.2: a rule is assigned only when its conduct is the item's conduct AND the gold answer passes it;
# [] = judge-only for safety (expected for most v0.3 danger items: v0.7 targets v0.2 danger topics, which v0.3 avoids).
# Filled by the coordinator after G1 on the danger items (validate.py --raw lists v0.7 topic candidates). TBD.
SAFETY_RULES = {}


def rows(p): return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]
def die(m): sys.exit("ABORT: " + m)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--wave1", action="store_true", help="keep ids 01..w1 only (60-item fallback)")
    a = ap.parse_args()
    want = WAVE1 if a.wave1 else COUNTS
    missing = [c for c in ORDER if not (SRC / f"{c}.jsonl").exists()]
    if missing: die(f"missing work files: {missing}")
    items = [r for c in ORDER for r in rows(SRC / f"{c}.jsonl")]
    dup = sorted(i for i, n in Counter(r["id"] for r in items).items() if n > 1)
    if dup: die(f"duplicate ids in work/ (replace the line, do not append): {dup}")
    if a.wave1: items = [r for r in items if int(r["id"][-2:]) <= WAVE1.get(r["category"], 0)]
    ids = [i["id"] for i in items]
    n = sum(want.values())
    if len(ids) != n: die(f"need {n} items, got {len(ids)}")
    cnt = Counter(i["category"] for i in items)
    if dict(cnt) != want: die(f"category counts {dict(cnt)} != {want}")
    danger = {i["id"] for i in items if i["danger"]}
    if danger != set(SAFETY_RULES) and not (a.wave1 and danger <= set(SAFETY_RULES)):
        die(f"danger ids {sorted(danger)} != SAFETY_RULES keys {sorted(SAFETY_RULES)}")
    for i in items:
        i.pop("safety_rules", None)
        if i["danger"]: i["safety_rules"] = SAFETY_RULES[i["id"]]
    items.sort(key=lambda i: (ORDER.index(i["category"]), i["id"]))
    data = "".join(json.dumps(i, ensure_ascii=False) + "\n" for i in items).encode("utf-8")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_bytes(data)
    print(f"{len(items)} items -> {OUT}; sha256 {hashlib.sha256(data).hexdigest()}")
    print("provenance:", dict(Counter(i["provenance"] for i in items)))
    vs = SRC / "vstyle.ids"
    if vs.exists():
        v = sorted(set(ID_RX.findall(vs.read_text(encoding="utf-8"))))
        if unk := [x for x in v if x not in set(ids)]: die(f"vstyle.ids has ids not in the set: {unk}")
        (HERE / "plan/vstyle.ids").write_text("".join(x + "\n" for x in v))
        print(f"vstyle: {len(v)} ids -> plan/vstyle.ids; by category {dict(Counter(x[4:-3] for x in v))}")


if __name__ == "__main__":
    main()
