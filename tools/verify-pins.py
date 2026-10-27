#!/usr/bin/env python3
"""Verify every published hash pin in this repository.

Checks: SHA256SUMS / SHA256SUMS.addendum-* / COMBINED.sha256 / *.sha256 files (text format `hash  name`),
bench/v0.1/SHA256SUMS.json (JSON map), the `*_sha256` of every refs/MANIFEST.json against its refs.jsonl,
and that COMBINED.sha256 equals the sha256 of bench/v0.3/plan/SHA256SUMS.
Targets that are withheld on purpose (the held-out v0.4 items; three arm patches that embed competitor test questions) are reported as WITHHELD, not as failures.
Usage: python3 tools/verify-pins.py        (exit 0 = no mismatch)"""
import glob, hashlib, json, os, re, sys
from pathlib import Path

R = Path(__file__).resolve().parent.parent
WITHHELD = {"bench/v0.4/SHA256SUMS": {"items.jsonl", "items.candidate.jsonl"},
            "adapters/desktop-node/arms/cmpsplit.patch.sha256": {"cmpsplit.patch"},
            "adapters/desktop-node/arms/cmpsplit-v2.patch.sha256": {"cmpsplit-v2.patch"},
            "adapters/desktop-node/arms/cmpsplit-v21.patch.sha256": {"cmpsplit-v21.patch"}}

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()

ok = bad = 0
bad_l, withheld = [], []

def check(base, name, h, src):
    global ok, bad
    p = base / name
    if not p.is_file():
        if name in WITHHELD.get(src, ()): withheld.append((src, name))
        else: bad += 1; bad_l.append((src, name, "missing"))
        return
    if sha(p) == h: ok += 1
    else: bad += 1; bad_l.append((src, name, "mismatch"))

for p in sorted(R.rglob("*")):
    if not p.is_file() or "node_modules" in p.parts or ".git" in p.parts: continue
    rel = str(p.relative_to(R))
    if p.name == "SHA256SUMS.json":
        for k, h in json.loads(p.read_text()).items(): check(p.parent, k, h, rel)
    elif p.name.startswith("SHA256SUMS") or p.name.endswith(".sha256"):
        for line in p.read_text(encoding="utf-8").splitlines():
            m = re.match(r"^([0-9a-f]{64})\s+\*?(.+?)\s*$", line)
            if m: check(p.parent, m.group(2), m.group(1), rel)

comb = R / "bench/v0.3/plan/COMBINED.sha256"
if comb.is_file():
    good = comb.read_text().split()[0] == sha(R / "bench/v0.3/plan/SHA256SUMS")
    print("COMBINED.sha256 == sha256(plan/SHA256SUMS):", good)
    if not good: bad += 1
for m in sorted(glob.glob(str(R / "bench/**/refs/MANIFEST.json"), recursive=True)):
    j = json.loads(Path(m).read_text()); refs = Path(m).parent / "refs.jsonl"
    for k in ("refs_jsonl_sha256", "jsonl_sha256"):
        if k in j and refs.is_file():
            if sha(refs) == j[k]: ok += 1
            else: bad += 1; bad_l.append((str(Path(m).relative_to(R)), "refs.jsonl", "mismatch"))
print(f"pins ok {ok}, bad {bad}, withheld {len(withheld)}")
for w in withheld: print("WITHHELD", *w)
for b in bad_l: print("BAD", *b)
sys.exit(1 if bad else 0)
