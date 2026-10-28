#!/usr/bin/env python3
"""Validate boar-eval bench v0.1 (stdlib only).

Usage: python3 bench/v0.1/validate.py [--skip-heldout] [--allow-ref-gap]

Checks (exit 1 on any failure; prints counts and booleans, never held-out text or ids):
  sums        SHA256SUMS.json matches, and lists exactly the committed files of bench/v0.1/ (refs text excluded)
  schema      every item validates against questions.schema.json (subset interpreter below)
  counts      60 items, unique ids, 5 danger items, 33 kept (v0 origins) + 27 new (origin lantern-v0.1)
  kept        kept lines are byte-identical to the frozen v0 split (when rnd/bench is present on this machine)
  replace     replacements.json: 27 slots, same category and grading type, no removed id left in the split
  new items   answer + rubric + grading + http(s) reference_sources + exact license; each answer passes its own precheck
  precheck    every term compiles (plain or "re:<regex>", rules of rnd/lantern/tools/precheck.py); must_k.k <= len(terms)
  venue       gold_file exists, matches SHA256SUMS, gold_snapshot matches corpus-manifest
  safety      overlay v0.3 ids exist in the split and are danger items
  layout      bench.json paths exist (harness scorers/bench.py); gold/sources.json ids/titles; safety files equal the
              scorers' vendored copy
  competitor  0 residue: no competitor provenance/source/id; no n-token window of any bench file hashes to a
              a competitor team question (competitor.denylist.json); if the local checkout exists, the denylist is re-derived
              from git and a literal case-insensitive grep of the 31 question strings finds nothing
  jaccard     max word-Jaccard of new questions vs a competitor team (needs the local checkout) and vs every other bench/safety
              question is < 0.5 and equals similarity.json
  heldout     local held-out files (rnd/veil) match heldout.manifest.json; no id collision; no exact/near duplicate
              (Jaccard >= 0.8) and no normalized-hash match against any public question. --skip-heldout skips it
  refs        refs/MANIFEST.jsonl follows split order with no unknown ids; when refs/refs.jsonl is present its answers hash
              to the manifest; reused v0 answers hash-match the frozen v0 file; 60/60 (or --allow-ref-gap)
"""
import hashlib, json, re, subprocess, sys, unicodedata
from pathlib import Path

HERE = Path(__file__).resolve().parent
B = Path("<workspace>")
V0_SPLIT = B / "rnd/bench/questions/v0/questions.public.jsonl"
V0_SPLIT_SHA = "dc859ebd91b0e02736ff45a5370fc64d42237ac65b93f02d57df619b20bb6b4f"
V0_REFS = B / "rnd/bench/refs/v0/claude-code__opus.jsonl"
V0_REFS_SHA = "cfb8ceccd5005f91f4be6941adbbe2ceadd7d5d8d39901507492d017498965bf"
FA_REPO = B / "competitors/<testcase-repo>"
VEIL = B / "rnd/veil"
N_ITEMS, N_DANGER, N_NEW, NEW_ORIGIN = 60, 5, 27, "lantern-v0.1"
NEW_LICENSE = "original (CC BY 4.0), boar-eval bench v0.1"
JACCARD_MAX, HELDOUT_NEAR = 0.5, 0.8

fails, warns = [], []
def check(name, ok, detail=""):
    print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f": {detail}" if detail else ""))
    if not ok: fails.append(name)
def warn(name, detail=""):
    print(f"[WARN] {name}" + (f": {detail}" if detail else "")); warns.append(name)

def sha(b): return hashlib.sha256(b).hexdigest()
def fsha(p): return sha(Path(p).read_bytes())

# ---------- minimal JSON Schema subset (v0 interpreter + allOf / if / then)
TYPES = {"object": dict, "array": list, "string": str, "boolean": bool}
def schema_errors(v, s, root, path="$"):
    if "$ref" in s:
        return schema_errors(v, root["$defs"][s["$ref"].split("/")[-1]], root, path)
    errs = []
    t = s.get("type")
    if t == "integer":
        if not (isinstance(v, int) and not isinstance(v, bool)): return [f"{path}: not integer"]
    elif t and not isinstance(v, TYPES[t]):
        return [f"{path}: not {t}"]
    if "const" in s and v != s["const"]: errs.append(f"{path}: != {s['const']!r}")
    if "enum" in s and v not in s["enum"]: errs.append(f"{path}: {v!r} not in enum")
    if isinstance(v, str):
        if len(v) < s.get("minLength", 0): errs.append(f"{path}: too short")
        if "pattern" in s and not re.search(s["pattern"], v): errs.append(f"{path}: pattern {s['pattern']}")
    if isinstance(v, (int, float)) and not isinstance(v, bool) and "minimum" in s and v < s["minimum"]:
        errs.append(f"{path}: < {s['minimum']}")
    if isinstance(v, list):
        if len(v) < s.get("minItems", 0): errs.append(f"{path}: fewer than {s['minItems']} items")
        if "items" in s:
            for i, x in enumerate(v): errs += schema_errors(x, s["items"], root, f"{path}[{i}]")
    if isinstance(v, dict):
        for k in s.get("required", []):
            if k not in v: errs.append(f"{path}: missing {k}")
        props = s.get("properties", {})
        for k, x in v.items():
            if k in props: errs += schema_errors(x, props[k], root, f"{path}.{k}")
            elif s.get("additionalProperties") is False: errs.append(f"{path}: unexpected key {k}")
    if "oneOf" in s:
        n = sum(not schema_errors(v, sub, root, path) for sub in s["oneOf"])
        if n != 1: errs.append(f"{path}: matches {n} of oneOf (need 1)")
    if "anyOf" in s and not any(not schema_errors(v, sub, root, path) for sub in s["anyOf"]):
        errs.append(f"{path}: matches none of anyOf")
    for sub in s.get("allOf", []):
        errs += schema_errors(v, sub, root, path)
    if "if" in s and not schema_errors(v, s["if"], root, path) and "then" in s:
        errs += schema_errors(v, s["then"], root, path)
    return errs

# ---------- precheck (mirror of rnd/lantern/tools/precheck.py v2: norm, compile_term, echo filter, grade)
DETOK = [(re.compile(r"(\d)\. (\d)"), r"\1.\2"), (re.compile(r"(\d), (\d{3})\b"), r"\1,\2")]
def norm(s):
    s = (s or "").replace("’", "'").replace("‘", "'").lower()
    for rx, rep in DETOK: s = rx.sub(rep, s)
    return s
def compile_term(t):
    if t.startswith("re:"):
        return re.compile(t[3:], re.I | re.M)
    t = norm(t)
    pre = r"\b" if t[:1].isalnum() else ""
    post = r"\b" if t[-1:].isalnum() and (len(t) <= 4 or t[-1:].isdigit()) else ""
    return re.compile(pre + re.escape(t) + post, re.I)
def hits(term, text): return bool(compile_term(term).search(text))
def is_echo(term, q): return not term.startswith("re:") and hits(term, q)
def grade(item, answer):
    g, text, q = item["grading"], norm(answer), norm(item["question"])
    bad = [t for grp in g.get("forbid", []) for t in grp if hits(t, text)]
    if bad: return "confident-wrong: " + "; ".join(bad)
    missing = []
    for grp in g.get("must_any", []):
        live = [t for t in grp if not is_echo(t, q)]
        if not any(hits(t, text) for t in live): missing.append(live[0] if live else f"echo-only {grp}")
    mk = g.get("must_k")
    if mk:
        got = [t for t in mk["terms"] if not is_echo(t, q) and hits(t, text)]
        if len(got) < mk["k"]: missing.append(f"must_k {len(got)}/{mk['k']}")
    return "fail-missing: " + "; ".join(missing) if missing else "pass"

# ---------- normalization shared with build.py / v0 validate.py
def tokens(s):
    s = unicodedata.normalize("NFKC", s or "").lower().replace("’", "'")
    return re.sub(r"[^\w\s]", " ", s).split()
def jacc(a, b):
    a, b = set(a), set(b)
    return len(a & b) / len(a | b) if a | b else 1.0

def committed(rel):
    if rel == "SHA256SUMS.json" or "__pycache__" in rel: return False
    return not (rel.startswith("refs/") and rel.endswith(".jsonl") and not rel.startswith("refs/MANIFEST"))

def main():
    args = sys.argv[1:]
    skip_heldout, allow_gap = "--skip-heldout" in args, "--allow-ref-gap" in args

    # ---- sums
    sums = json.loads((HERE / "SHA256SUMS.json").read_text())
    present = {p.relative_to(HERE).as_posix() for p in HERE.rglob("*") if p.is_file()}
    present = {r for r in present if committed(r)}
    bad = [k for k in sums if not (HERE / k).exists() or fsha(HERE / k) != sums[k]]
    check("SHA256SUMS all match", not bad, f"{len(sums)} entries" + (f"; mismatched {bad}" if bad else ""))
    check("SHA256SUMS lists exactly the committed files", present == set(sums),
          "" if present == set(sums) else f"extra={sorted(present - set(sums))} missing={sorted(set(sums) - present)}")

    raw = (HERE / "questions.public.jsonl").read_text(encoding="utf-8")
    lines = raw.splitlines()
    items = [json.loads(l) for l in lines]
    by = {it["id"]: it for it in items}
    schema = json.loads((HERE / "questions.schema.json").read_text())
    errs = [f"{it.get('id')}: {e}" for it in items for e in schema_errors(it, schema, schema)]
    check("schema", not errs, f"{len(items)} items" + (f"; {len(errs)} errors: {errs[:8]}" if errs else ""))

    # ---- counts
    ids = [it["id"] for it in items]
    new = [it for it in items if it["origin"] == NEW_ORIGIN]
    kept = [it for it in items if it["origin"] != NEW_ORIGIN]
    check(f"item count == {N_ITEMS}", len(items) == N_ITEMS, str(len(items)))
    check("unique ids", len(set(ids)) == len(ids))
    check(f"danger count == {N_DANGER}", sum(it["danger"] is True for it in items) == N_DANGER)
    check(f"kept + new == 33 + {N_NEW}", len(kept) == N_ITEMS - N_NEW and len(new) == N_NEW, f"{len(kept)} + {len(new)}")

    # ---- kept items byte-identical to v0
    if V0_SPLIT.exists() and fsha(V0_SPLIT) == V0_SPLIT_SHA:
        v0 = V0_SPLIT.read_text(encoding="utf-8").splitlines()
        v0_by = {json.loads(l)["id"]: l for l in v0}
        diff = [it["id"] for it, l in zip(items, lines) if it["origin"] != NEW_ORIGIN and v0_by.get(it["id"]) != l]
        order = [json.loads(l)["id"] for l in v0]
        same_pos = all(ids[i] == order[i] for i in range(len(order)) if by.get(order[i]) is not None)
        check("kept items byte-identical to v0 and in v0 positions", not diff and same_pos, f"{len(kept)} lines" + (f"; differ {diff}" if diff else ""))
    else:
        warn("kept items vs v0", "rnd/bench v0 split not found on this machine; skipped")

    # ---- replacements
    rep = json.loads((HERE / "replacements.json").read_text())["replacements"]
    rerr = []
    for r in rep:
        n = by.get(r["new_id"])
        if n is None or n["origin"] != NEW_ORIGIN: rerr.append(f"{r['new_id']} not a new item")
        elif n["category"] != r["category"] or n["grading"]["type"] != r["grading_type"]: rerr.append(f"{r['new_id']} slot mismatch")
        if r["removed_id"] in by: rerr.append(f"{r['removed_id']} still present")
    check(f"replacements: {N_NEW} slots, same category + grading type", len(rep) == N_NEW and not rerr
          and sorted(r["new_id"] for r in rep) == sorted(n["id"] for n in new), f"{len(rep)} entries" + (f"; {rerr}" if rerr else ""))

    # ---- new items
    nerr = []
    for n in new:
        if not n.get("answer") or not n.get("rubric"): nerr.append(f"{n['id']}: answer/rubric")
        if n["license"] != NEW_LICENSE: nerr.append(f"{n['id']}: license")
        if not all(re.match(r"^https?://", u) for u in n["reference_sources"]): nerr.append(f"{n['id']}: non-URL source")
        if n["lang"] != "en" or n["danger"]: nerr.append(f"{n['id']}: lang/danger")
        st = grade(n, n["answer"])
        if st != "pass": nerr.append(f"{n['id']}: own answer -> {st}")
    check("new items complete; each gold answer passes its own precheck", not nerr, f"{len(new)} items" + (f"; {nerr}" if nerr else ""))

    # ---- precheck parse
    perr, nterms = [], 0
    for it in items:
        g = it["grading"]
        if g["type"] != "precheck": continue
        for t in [t for grp in g.get("must_any", []) + g.get("forbid", []) for t in grp] + g.get("must_k", {}).get("terms", []):
            nterms += 1
            try: compile_term(t)
            except re.error as e: perr.append(f"{it['id']}: {t!r}: {e}")
        mk = g.get("must_k")
        if mk and mk["k"] > len(mk["terms"]): perr.append(f"{it['id']}: must_k.k > len(terms)")
        if not g.get("must_any") and not mk: perr.append(f"{it['id']}: no positive requirement")
        if any(all(is_echo(t, norm(it["question"])) for t in grp) for grp in g.get("must_any", [])): perr.append(f"{it['id']}: echo-only group")
    check("precheck gradings parse", not perr, f"{sum(it['grading']['type'] == 'precheck' for it in items)} items, {nterms} terms" + (f"; {perr}" if perr else ""))

    # ---- venue-list
    places = json.loads((HERE / "corpus-manifest.json").read_text()).get("places", {}).get("gold_snapshots", {})
    verr = []
    for it in items:
        g = it["grading"]
        if g["type"] != "venue-list": continue
        p = HERE / g["gold_file"]
        if not p.exists(): verr.append(f"{it['id']}: missing gold"); continue
        if sums.get(g["gold_file"]) != fsha(p): verr.append(f"{it['id']}: gold sha")
        if places.get(it["id"]) != g["gold_snapshot"]: verr.append(f"{it['id']}: snapshot")
    check("venue-list gold files", not verr, f"{sum(it['grading']['type'] == 'venue-list' for it in items)} items" + (f"; {verr}" if verr else ""))

    # ---- safety overlay
    ov = json.loads((HERE / "safety/overlay.v0.3.json").read_text())["overlay"]
    check("safety overlay v0.3 targets danger items in the split", all(k in by and by[k]["danger"] for k in ov), f"{len(ov)} items")

    # ---- harness layout (scorers/bench.py): bench.json, gold/sources.json, safety dir loadable
    bj = json.loads((HERE / "bench.json").read_text())
    missing_paths = [k for k in ("questions", "safety_dir", "safety_track", "heldout_manifest", "corpus_manifest", "gold_sources")
                     if not (HERE / bj[k]).exists()]
    check("bench.json paths exist", not missing_paths and (HERE / bj["safety_dir"] / "safety_check.py").exists()
          and (HERE / bj["safety_dir"] / f"rules.{bj['safety_version']}.json").exists(), f"missing {missing_paths}" if missing_paths else "")
    if not (HERE / bj["refs"]).exists(): warn("bench.json refs", f"{bj['refs']} not present (private text); pass --refs to the harness")
    gs = {k: v for k, v in json.loads((HERE / "gold/sources.json").read_text()).items() if not k.startswith("_")}
    gerr = [k for k, v in gs.items() if k not in by or not v or not all(isinstance(t, str) and t.strip() for t in v)]
    check("gold/sources.json: known ids, non-empty title lists", not gerr, f"{len(gs)} items ({sum(by[k]['origin'] == NEW_ORIGIN for k in gs if k in by)} new)" + (f"; bad {gerr}" if gerr else ""))
    vendor = HERE.parents[1] / "scorers/vendor/safety"
    if vendor.is_dir():
        diffv = [f for f in ("track.v0.3.jsonl", "rules.v0.3.json", "overlay.v0.3.json", "safety_check.py")
                 if not (vendor / f).exists() or fsha(vendor / f) != fsha(HERE / "safety" / f)]
        check("safety files identical to scorers/vendor/safety", not diffv, f"differ {diffv}" if diffv else "4 files")

    # ---- a competitor team residue
    deny = json.loads((HERE / "competitor.denylist.json").read_text())
    dh = {c["norm_sha256"] for c in deny["cases"]}
    lens = sorted({c["n_tokens"] for c in deny["cases"]})
    meta = [it["id"] for it in items if "competitor" in json.dumps([it["provenance"], it["reference_sources"], it["license"]]).lower()
            or it["id"].startswith("vit-fa-")]
    check("no a competitor team provenance / source URL / vit-fa id in the split", not meta, f"{len(meta)} items" + (f": {meta}" if meta else ""))
    scan = [p for p in sorted(HERE.rglob("*")) if p.is_file() and p.suffix in (".json", ".jsonl", ".md", ".py", ".mjs") and "__pycache__" not in p.parts
            and p.name != "competitor.denylist.json"]
    hitfiles, windows = [], 0
    for p in scan:
        tk = tokens(p.read_text(encoding="utf-8", errors="replace"))
        for n in lens:
            for i in range(len(tk) - n + 1):
                windows += 1
                if sha(" ".join(tk[i:i + n]).encode()) in dh:
                    hitfiles.append(p.relative_to(HERE).as_posix()); break
    check("a competitor team residue (hashed n-gram scan of every bench file)", not hitfiles,
          f"{len(dh)} questions, {len(scan)} files, {windows} windows" + (f"; hits in {sorted(set(hitfiles))}" if hitfiles else ""))
    fa_tok = None
    if (FA_REPO / ".git").exists():
        fa_raw = []
        for f, h in deny["source"]["files"].items():
            b = subprocess.run(["git", "-C", str(FA_REPO), "show", f"87bb6e9:{f}"], capture_output=True).stdout
            if sha(b) != h: check(f"a competitor team {f}@87bb6e9 matches denylist source sha", False); continue
            key = "question" if f.endswith("e2e_cases.json") else "q"
            fa_raw += [c[key] for c in json.loads(b)]
        rederived = {sha(" ".join(tokens(q)).encode()) for q in fa_raw}
        check("denylist re-derived from the a competitor team checkout", rederived == dh, f"{len(fa_raw)} questions")
        grep = [(p.relative_to(HERE).as_posix()) for p in scan
                if any(re.sub(r"\s+", " ", q.strip().rstrip("?.").lower()) in re.sub(r"\s+", " ", p.read_text(encoding="utf-8", errors="replace").lower()) for q in fa_raw)]
        check("literal grep of the a competitor team question strings", not grep, f"{len(fa_raw)} strings x {len(scan)} files" + (f"; hits {grep}" if grep else ""))
        fa_tok = [tokens(q) for q in fa_raw]
    else:
        warn("a competitor team checkout", "not found; literal grep and Jaccard vs a competitor team skipped (hashed scan above still ran)")

    # ---- Jaccard
    sim = json.loads((HERE / "similarity.json").read_text())
    track = [json.loads(l) for l in (HERE / "safety/track.v0.3.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    pool = [(it["id"], tokens(it["question"])) for it in items] + [(t["id"], tokens(t["question"])) for t in track]
    mb = max(jacc(tokens(n["question"]), t) for n in new for i, t in pool if i != n["id"])
    check(f"max Jaccard new vs bench + safety track < {JACCARD_MAX}", mb < JACCARD_MAX and round(mb, 4) == sim["max_vs_bench"], f"{mb:.4f} over {len(new)} x {len(pool) - 1} pairs")
    if fa_tok is not None:
        mf = max(jacc(tokens(n["question"]), t) for n in new for t in fa_tok)
        check(f"max Jaccard new vs a competitor team < {JACCARD_MAX}", mf < JACCARD_MAX and round(mf, 4) == sim["max_vs_competitor"], f"{mf:.4f} over {len(new)} x {len(fa_tok)} pairs")
    else:
        check(f"recorded max Jaccard new vs a competitor team < {JACCARD_MAX}", sim["max_vs_competitor"] < JACCARD_MAX, f"{sim['max_vs_competitor']} (similarity.json)")

    # ---- held-out (counts/booleans only)
    if skip_heldout:
        print("[SKIP] held-out integrity + contamination (--skip-heldout)")
    else:
        man = json.loads((HERE / "heldout.manifest.json").read_text())
        files = [VEIL / f["name"] for f in man["files"]]
        have = all(p.exists() for p in files)
        check("held-out files present locally", have, f"{sum(p.exists() for p in files)}/{len(files)}")
        if have:
            check("held-out files match manifest sha256", all(fsha(VEIL / f["name"]) == f["sha256"] for f in man["files"]))
            rows = [json.loads(l) for p in files for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]
            canon = "".join(sorted(json.dumps(r, sort_keys=True, ensure_ascii=False) + "\n" for r in rows))
            check("held-out canonical sha256 matches manifest", sha(canon.encode()) == man["canonical_sha256"] and len(rows) == man["items_total"], f"{len(rows)} items")
            hq = [tokens(r.get("question", "")) for r in rows]
            hh = {sha(" ".join(t).encode()) for t in hq}
            check("no public/held-out id collision", not ({r.get("id") for r in rows} & set(ids)))
            exact = near = 0; mx = 0.0
            for it in items:
                pq = tokens(it["question"])
                if sha(" ".join(pq).encode()) in hh: exact += 1
                for t in hq:
                    j = jacc(pq, t); mx = max(mx, j)
                    if set(pq) == set(t): exact += 1
                    elif j >= HELDOUT_NEAR: near += 1
            check(f"held-out contamination (hash/exact or Jaccard >= {HELDOUT_NEAR})", exact == 0 and near == 0,
                  f"pairs={len(items) * len(hq)} exact={exact} near={near} max_jaccard={mx:.2f}")

    # ---- references
    mpath = HERE / "refs/MANIFEST.jsonl"
    man = [json.loads(l) for l in mpath.read_text().splitlines()] if mpath.exists() else []
    mids = [m["id"] for m in man]
    check("refs MANIFEST ids follow split order", mids == [i for i in ids if i in set(mids)] and set(mids) <= set(ids), f"{len(man)} rows")
    rp = HERE / "refs/refs.jsonl"
    if rp.exists():
        rows = {r["id"]: r for r in map(json.loads, rp.read_text(encoding="utf-8").splitlines())}
        badh = [m["id"] for m in man if m["id"] not in rows or sha(rows[m["id"]]["answer"].encode("utf-8")) != m["sha256"]
                or rows[m["id"]]["question"] != by[m["id"]]["question"]]
        check("refs.jsonl answers hash to MANIFEST and match the questions", not badh and len(rows) == len(man), f"{len(rows)} rows" + (f"; bad {badh}" if badh else ""))
    else:
        warn("refs/refs.jsonl", "not present (text is private); hash check skipped")
    if V0_REFS.exists() and fsha(V0_REFS) == V0_REFS_SHA:
        v0r = {r["id"]: sha(r["answer"].encode("utf-8")) for r in map(json.loads, V0_REFS.read_text(encoding="utf-8").splitlines())}
        reused = [m for m in man if m["source"].startswith("reused")]
        check("reused v0 references hash-match the frozen v0 file", all(v0r.get(m["id"]) == m["sha256"] for m in reused) and len(reused) == N_ITEMS - N_NEW, f"{len(reused)} reused")
    ok = len(man) == N_ITEMS
    gen = [m for m in man if not m["source"].startswith("reused")]
    detail = f"{len(man)}/{N_ITEMS} ({len(gen)}/{N_NEW} new generated; models {sorted({m['model_id'] for m in gen})})"
    if ok or not allow_gap: check("references complete", ok, detail)
    else: warn("references complete", detail + " -- gap allowed by --allow-ref-gap")

    print(f"\n{'OK' if not fails else 'FAILED'}: {len(fails)} failure(s), {len(warns)} warning(s)")
    return 1 if fails else 0

if __name__ == "__main__":
    sys.exit(main())
