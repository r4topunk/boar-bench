#!/usr/bin/env python3
"""Verify every published hash pin in this repository.

Checks: SHA256SUMS / SHA256SUMS.addendum-* / COMBINED.sha256 / *.sha256 files (text format `hash  name`),
bench/v0.1/SHA256SUMS.json (JSON map), the `*_sha256` of every refs/MANIFEST.json against its refs.jsonl,
and that COMBINED.sha256 equals the sha256 of bench/v0.3/plan/SHA256SUMS.
Targets that are withheld on purpose (three arm patches that embed competitor test questions) are reported as WITHHELD, not as failures.
Since v1.1 the retired held-out sets ship in bench/heldout/ and bench/v0.4/; a few of their pin files were written for the private
lab layout or pin files that were redacted on the way out. Those entries are reported as KNOWN with the reason (bench/heldout/HASHES.md).
Usage: python3 tools/verify-pins.py        (exit 0 = no mismatch)"""
import glob, hashlib, json, os, re, sys
from pathlib import Path

R = Path(__file__).resolve().parent.parent
WITHHELD = {"adapters/desktop-node/arms/cmpsplit.patch.sha256": {"cmpsplit.patch"},
            "adapters/desktop-node/arms/cmpsplit-v2.patch.sha256": {"cmpsplit-v2.patch"},
            "adapters/desktop-node/arms/cmpsplit-v21.patch.sha256": {"cmpsplit-v21.patch"}}

V02 = "bench/heldout/bench-v02/live/v0.2/"
XREPO = "lives in boar-research rnd/heldout/bench-v02/live/v0.2/ (redacted copy; original and released sha in bench/heldout/HASHES.md)"
LAYOUT = "path written for the private lab layout (scorers/vendor/safety/ of the old eval repo); the v1.0 re-issue of these rules dropped NHS wording, so they differ (bench/heldout/HASHES.md)"
KNOWN = {**{(V02 + "SHA256SUMS.items", f): XREPO for f in ("assemble.py", "validate.py", "similarity.py", "similarity.json")},
         (V02 + "plan/SHA256SUMS.addendum-01", "addendum-01-coverage-split.md"): "pre-existing: the coverage run record was appended after hashing, before any run (bench/heldout/HASHES.md)",
         **{(V02 + f"plan/SHA256SUMS.addendum-0{n}", f"../../../scorers/vendor/safety/{k}.v0.{n + 3}.{e}"): LAYOUT
            for n in (2, 3, 4) for k, e in (("rules", "json"), ("safety_check", "py"), ("tests", "json"))}}
known = []

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()

ok = bad = 0
bad_l, withheld = [], []

def check(base, name, h, src):
    global ok, bad
    p = base / name
    if (src, name) in KNOWN: known.append((src, name, KNOWN[(src, name)])); return
    if not p.is_file() and (base.parent / name).is_file(): p = base.parent / name   # pin file one level below the root it names
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
print(f"pins ok {ok}, bad {bad}, withheld {len(withheld)}, known {len(known)}")
for w in withheld: print("WITHHELD", *w)
for k in known: print("KNOWN", *k)
for b in bad_l: print("BAD", *b)
sys.exit(1 if bad else 0)
