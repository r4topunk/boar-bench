#!/usr/bin/env python3
"""Validate bench v0.3-ext (gate G1, plus the G4 refs check). Copy of bench/v0.2/validate.py with v0.3 paths, counts,
origin and rules. Reuses bench/v0.1/validate.py (schema subset interpreter, precheck) and
scorers/vendor/safety/safety_check.v0.7.py (rules v0.7, addendum 04). Exit 1 on any FAIL; WARN lines never fail.

Checks: item count + unique ids, category counts (spec section 2, or the wave-1 counts with --wave1), id = v03-<category>-NN
with NN in 01..n (01..w1 with --wave1); refuse_ok = 8 and danger = 10 (full set only); danger flag <=> category danger;
v0.3 schema (subset interpreter; also jsonschema 2020-12 if installed); each gold answer passes its own precheck; every
precheck term compiles, no echo-only group; origin v0.3-ext, lang en, gold answer, http(s) sources; danger items carry
safety_rules with known v0.7 ids and each danger gold passes its own rules (with --raw: writer files before assemble.py,
so safety_rules must be absent; v0.7 topic candidates are reported, never failed); refs/MANIFEST.jsonl (this folder, if
present) has known ids and matches <dir>/refs/refs.jsonl when that blind file is present (G4).
Item-spec format checks (question 8-40 words, answer 40-120 words, 1-2 "Penalize:" bullets, "Decline rule:" on
honesty items, 1-3 sources, provenance filled) are WARN only.
Output: ids, check names, counts and precheck terms; never question, answer or reference text.

Usage (from boar-eval/):
  python3 bench/v0.3/validate.py                                   # bench/v0.3/work/questions.v03.jsonl, 110 items
  python3 bench/v0.3/validate.py --wave1                           # the pre-declared 60-item fallback (ids 01..w1)
  python3 bench/v0.3/validate.py --raw --any-counts --file <f.jsonl> [--file ...]   # format check of writer drafts
"""
import argparse, hashlib, json, re, sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
DEFAULT_DIR = Path("bench/v0.3/work/")
QFILE = "questions.v03.jsonl"
sys.path.insert(0, str(HERE.parent / "v0.1"))
from validate import schema_errors, grade, compile_term, is_echo, norm  # noqa: E402
import importlib.util  # noqa: E402
SAFETY = ROOT / "scorers/vendor/safety"
RULES_VERSION = "v0.7"
_spec = importlib.util.spec_from_file_location("safety_check_v07", SAFETY / f"safety_check.{RULES_VERSION}.py")
sc = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(sc)

ORIGIN, LICENSE = "v0.3-ext", "CC-BY-4.0"
COUNTS = {"explanation": 21, "reasoning": 21, "comparison": 13, "crypto": 13, "honesty-refusal": 12, "health": 8,
          "danger": 10, "synthesis": 6, "travel-practical": 4, "travel-local": 2}
WAVE1 = {"explanation": 11, "reasoning": 11, "comparison": 7, "crypto": 7, "honesty-refusal": 7, "health": 4,
         "danger": 6, "synthesis": 3, "travel-practical": 2, "travel-local": 2}
N_REFUSE_OK = 8  # honesty-refusal: 4 unknowable + 4 time-pinned (refuse_ok true); 4 false premise (false)
ID_RX = re.compile(r"^v03-([a-z-]+)-([0-9]{2})$")
fails, warns = [], []


def check(name, ok, detail=""):
    print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f": {detail}" if detail else ""))
    if not ok: fails.append(name)


def warn(name, bad, detail=""):
    print(f"[{'WARN' if bad else 'ok  '}] {name}" + (f": {detail}" if detail else ""))
    if bad: warns.append(name)


def words(s): return len((s or "").split())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", type=Path, default=DEFAULT_DIR, help=f"live folder holding {QFILE} and refs/")
    ap.add_argument("--file", type=Path, action="append", help=f"item file(s) to check instead of <dir>/{QFILE}")
    ap.add_argument("--wave1", action="store_true", help="expect the wave-1 counts and ids 01..w1")
    ap.add_argument("--any-counts", action="store_true", help="dev: skip count, id-range and total checks (report only)")
    ap.add_argument("--raw", action="store_true", help="writer drafts before assemble.py: no safety_rules expected")
    a = ap.parse_args()
    files = a.file or [a.dir / QFILE]
    if missing := [str(f) for f in files if not f.exists()]: sys.exit(f"ABORT: not found: {missing}")
    items = [json.loads(l) for f in files for l in f.read_text(encoding="utf-8").splitlines() if l.strip()]
    want = WAVE1 if a.wave1 else COUNTS
    mode = "any counts (dev)" if a.any_counts else ("wave 1" if a.wave1 else "full")
    print(f"bench v0.3 validate: {len(items)} items from {len(files)} file(s); mode {mode}{'; raw drafts' if a.raw else ''}")

    ids = [i.get("id") for i in items]
    cnt = dict(Counter(i.get("category") for i in items))
    if a.any_counts:
        check("unique ids", len(set(ids)) == len(ids), f"{len(items)} / {len(set(ids))}")
        print(f"[info] category counts: {cnt}")
    else:
        n = sum(want.values())
        check(f"{n} items, unique ids", len(items) == n and len(set(ids)) == n, f"{len(items)} / {len(set(ids))}")
        check("category counts", cnt == want, str(cnt))
    ierr = []
    for i in items:
        m = ID_RX.match(i.get("id") or "")
        if not m or m.group(1) != i.get("category"): ierr.append(f"{i.get('id')}: id/category mismatch"); continue
        if not a.any_counts and not 1 <= int(m.group(2)) <= want.get(i["category"], 0): ierr.append(f"{i['id']}: outside 01..{want.get(i['category'], 0):02d}")
    check("ids v03-<category>-NN" + ("" if a.any_counts else " in the declared range"), not ierr, "; ".join(ierr))
    nref, ndng = sum(bool(i.get("grading", {}).get("refuse_ok")) for i in items), sum(bool(i.get("danger")) for i in items)
    if a.any_counts or a.wave1:
        print(f"[info] refuse_ok true: {nref}; danger true: {ndng}")
    else:
        check(f"refuse_ok = {N_REFUSE_OK}, danger = {COUNTS['danger']}", nref == N_REFUSE_OK and ndng == COUNTS["danger"], f"{nref} / {ndng}")
    derr = [i["id"] for i in items if bool(i.get("danger")) != (i.get("category") == "danger")]
    check("danger flag <=> category danger", not derr, str(derr))

    S = json.loads((HERE / "questions.schema.json").read_text())
    errs = [f"{i.get('id')}: {e}" for i in items for e in schema_errors(i, S, S)]
    try:
        import jsonschema
        errs += [f"{i.get('id')}: {e.message[:120]}" for i in items for e in jsonschema.Draft202012Validator(S).iter_errors(i)]
        how = "subset + jsonschema"
    except ImportError:
        how = "subset only (jsonschema not installed)"
    check(f"schema v0.3 ({how})", not errs, "; ".join(errs[:6]) + (f" (+{len(errs) - 6})" if len(errs) > 6 else ""))
    st = [f"{i['id']}: {grade(i, i['answer'])}" for i in items if i.get("answer") and grade(i, i["answer"]) != "pass"]
    check("each gold answer passes its own precheck", not st, "; ".join(st))
    perr = []
    for it in items:
        g = it["grading"]
        if g["type"] != "precheck": perr.append(f"{it['id']}: {g['type']}"); continue
        for t in [t for grp in g.get("must_any", []) + g.get("forbid", []) for t in grp] + g.get("must_k", {}).get("terms", []):
            try: compile_term(t)
            except re.error as e: perr.append(f"{it['id']}: {t!r}: {e}")
        if any(all(is_echo(t, norm(it["question"])) for t in grp) for grp in g.get("must_any", [])): perr.append(f"{it['id']}: echo-only")
    check("precheck on every item, terms compile, no echo-only group", not perr, "; ".join(perr))
    oerr = [i.get("id") for i in items if i.get("origin") != ORIGIN or i.get("lang") != "en" or not i.get("answer")
            or i.get("license") != LICENSE or not i.get("reference_sources")
            or not all(re.match(r"^https?://", u) for u in i.get("reference_sources", []))]
    check(f"origin {ORIGIN}, lang en, gold answer, license {LICENSE}, URL sources", not oerr, str(oerr))

    SS = sc.load(rules_path=SAFETY / f"rules.{RULES_VERSION}.json", overlay_path=SAFETY / "overlay.v0.4.json")  # overlay unused
    serr, cand = [], []
    for it in items:
        if it.get("danger") and not a.raw:
            if "safety_rules" not in it: serr.append(f"{it['id']}: missing"); continue
            unk = [r for r in it["safety_rules"] if r not in SS["meta"]]
            if unk: serr.append(f"{it['id']}: unknown {unk}")
            hit = sc.check(it["answer"], it["safety_rules"], SS)
            if hit: serr.append(f"{it['id']}: gold trips {[h['rule'] for h in hit]}")
        elif "safety_rules" in it:
            serr.append(f"{it['id']}: safety_rules " + ("in a writer draft (assemble.py maps them)" if a.raw else "on a non-danger item"))
        if it.get("danger") and a.raw:
            tr = sc.rules_by_topic(it["question"], SS)
            cand.append(f"{it['id']}: {tr or '-'}" + (f" gold trips {[h['rule'] for h in sc.check(it['answer'], tr, SS)]}" if tr and sc.check(it["answer"], tr, SS) else ""))
    nd = [i for i in items if i.get("danger")]
    if a.raw:
        check(f"no safety_rules in writer drafts (rules {RULES_VERSION} mapped later)", not serr, "; ".join(serr))
        print(f"[info] {len(nd)} danger items; v0.7 topic candidates for the assemble.py mapping: " + ("; ".join(cand) or "-"))
    else:
        check(f"safety_rules (rules {RULES_VERSION}): known ids, golds pass", not serr,
              f"{len(nd)} danger items, {sum(bool(i.get('safety_rules')) for i in nd)} mapped, {sum(not i.get('safety_rules') for i in nd)} judge-only"
              + (f"; {serr}" if serr else ""))

    # item-spec format checks (WARN only; the writer prompts' FIELD RULES)
    pen = [i["id"] for i in items if not 1 <= sum(r.strip().startswith("Penalize:") for r in i.get("rubric", [])) <= 2]
    warn("question 8-40 words", bad := [i["id"] for i in items if not 8 <= words(i.get("question")) <= 40], str(bad) if bad else "")
    warn("answer 40-120 words", bad := [f"{i['id']}={words(i.get('answer'))}" for i in items if not 40 <= words(i.get("answer")) <= 120], str(bad) if bad else "")
    warn("rubric has 1-2 'Penalize:' bullets", pen, str(pen) if pen else "")
    dec = [i["id"] for i in items if i.get("category") == "honesty-refusal" and not any("Decline rule:" in r for r in i.get("rubric", []))]
    warn("honesty items carry a 'Decline rule:' bullet", dec, str(dec) if dec else "")
    warn("1-3 reference_sources", bad := [i["id"] for i in items if not 1 <= len(i.get("reference_sources", [])) <= 3], str(bad) if bad else "")
    prov = [i["id"] for i in items if not re.match(r"^writer-human\+\S.* 2026-\d{2}-\d{2}$", i.get("provenance", ""))]
    warn("provenance = 'writer-human+<model> 2026-MM-DD'", prov, str(prov) if prov else "")

    mp = HERE / "refs/MANIFEST.jsonl"
    if mp.exists() and not a.file:
        man = [json.loads(l) for l in mp.read_text().splitlines() if l.strip()]
        check("refs MANIFEST ids known", {m["id"] for m in man} <= set(ids), f"{len(man)}/{len(items)} rows")
        rp = a.dir / "refs/refs.jsonl"
        if rp.exists():
            rows = {r["id"]: r for r in map(json.loads, filter(str.strip, rp.read_text(encoding="utf-8").splitlines()))}
            q = {i["id"]: i["question"] for i in items}
            bad = [m["id"] for m in man if m["id"] not in rows or hashlib.sha256(rows[m["id"]]["answer"].encode()).hexdigest() != m["sha256"]
                   or rows[m["id"]]["question"] != q.get(m["id"])]
            check("refs.jsonl hashes match MANIFEST and questions (G4)", not bad, str(bad))
    print(f"\n{'OK' if not fails else 'FAILED'}: {len(fails)} failure(s), {len(warns)} warning(s)")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
