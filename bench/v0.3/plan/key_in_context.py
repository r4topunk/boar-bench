#!/usr/bin/env python3
"""key-in-context: did the item's answer key reach the sources the engine kept for the prompt?

Spec + reference implementation for boar-eval `harness/report.py` (a research agent, 2026-10-01). Label-free retrieval metric:
an item counts when its precheck answer key is matched in the text of `retrieval.kept`: every `must_any` group (any
term) AND, when present, >= `must_k.k` of `must_k.terms` (case-insensitive substring; `re:` terms are regexes).

Two modes, reported separately, never mixed:
- exact:   uses `kept[i].text` (passage as placed in the prompt). Needs protocol 1.1: optional `text` on SourceRef.
- article: fallback for protocol-1.0 traces (no text): resolves each kept title to its whole ARTICLE in the installed
           packs (format-2 Wikivoyage/crypto via blocks+zstd, bundled corpus.json, wiki-vital5 chunks). This is an
           UPPER BOUND on exact (a section was kept, the whole article is checked).
Items without must_any are skipped. Unresolved kept titles are counted and listed (they make article mode a lower bound
for that item). Read-only on packs, traces and the bench.

Usage: key_in_context.py QUESTIONS.jsonl RUN_A.traces.jsonl [RUN_B.traces.jsonl ...] [--vital5]
"""
import json, os, re, sqlite3, subprocess, sys, compression.zstd as zstd
B = os.environ.get("BOAR_PRIVATE_WORKSPACE", ".")  # private workspace of the origin machine
PACKS = {"wikivoyage": f"{B}/shared-data/packs/boar-wikivoyage-en.sqlite", "crypto": f"{B}/shared-data/crypto/boar-crypto.sqlite"}
V5 = f"{B}/shared-data/packs/wiki-vital5.sqlite"

def norm(s): return re.sub(r"\s+", " ", s.lower().replace("’", "'"))

class Resolver:
    def __init__(self, vital5):
        self.dbs = {k: sqlite3.connect(f"file:{p}?mode=ro", uri=True) for k, p in PACKS.items()}
        self.v5 = sqlite3.connect(f"file:{V5}?mode=ro", uri=True) if vital5 else None
        corpus = json.loads(subprocess.check_output(["git", "-C", f"{B}/boar-app", "show", "0cfd4a77:assets/corpus/corpus.json"]))
        self.corpus = {d["title"].lower(): d["body"] for d in corpus}
        self.cache = {}
    def f2(self, db, title):
        row = db.execute("SELECT block_id, off, len FROM articles WHERE title = ? COLLATE NOCASE ORDER BY views DESC LIMIT 1", (title,)).fetchone()
        if not row: return None
        z = db.execute("SELECT zdata FROM blocks WHERE id = ?", (row[0],)).fetchone()[0]
        return zstd.decompress(z)[row[1]:row[1] + row[2]].decode("utf-8", "replace")
    def text(self, ref):
        key = (ref["title"], ref.get("source"))
        if key in self.cache: return self.cache[key]
        t, src = ref["title"], ref.get("source") or ""
        cands = [t] + ([t.split(": ", 1)[1]] if ": " in t else [])
        out = None
        order = ["wikivoyage"] if "wikivoyage.org" in src else ["crypto"] if src and "wikivoyage" not in src else []
        for name in order + [k for k in self.dbs if k not in order]:
            for c in cands:
                out = out or self.f2(self.dbs[name], c)
        if out is None:
            for c in cands: out = out or self.corpus.get(c.lower())
        if out is None and self.v5 is not None:
            for c in cands:
                rows = self.v5.execute("SELECT body FROM chunks WHERE title = ? COLLATE NOCASE", (c,)).fetchall()
                if rows: out = "\n".join(r[0] for r in rows); break
        self.cache[key] = out
        return out

def term_hit(t, x):
    return re.search(x[3:], t) is not None if x.startswith("re:") else norm(x) in t

def key_hit(text, grading):
    """All must_any groups (any term each) AND, if present, >= must_k.k of must_k.terms. `re:` terms are regexes."""
    t = norm(text)
    ok = all(any(term_hit(t, x) for x in g) for g in grading.get("must_any", []))
    mk = grading.get("must_k")
    if mk: ok = ok and sum(term_hit(t, x) for x in mk["terms"]) >= mk["k"]
    return ok

def score(qs, path, res):
    rows = [json.loads(l) for l in open(path) if l.strip()]
    per, unresolved = {}, set()
    for r in rows:
        q = qs.get(r["itemId"])
        if not q or not (q["grading"].get("must_any") or q["grading"].get("must_k")): continue
        def hit(refs):
            exact = all("text" in s for s in refs) and bool(refs)
            texts = []
            for s in refs:
                tx = s.get("text") if exact else res.text(s)
                if tx is None: unresolved.add(s["title"])
                else: texts.append(tx)
            return key_hit("\n".join(texts), q["grading"]), ("exact" if exact else "article")
        # Three levels. raw = retriever output (seed-independent); pre = last `sources` event before the answer
        # (what the chat showed while generating); kept = sources of the final answer (EMPTY when the answer declines,
        # so it mixes retrieval with generation: report it, never use it alone).
        pre_ev = [e for e in r.get("events", []) if e.get("type") == "sources"]
        raw, mode = hit(r["retrieval"]["raw"])
        pre, pmode = hit(pre_ev[-1]["sources"]) if pre_ev else (False, "none")
        kept, _ = hit(r["retrieval"]["kept"]) if r["retrieval"]["kept"] else (False, mode)
        per[r["itemId"]] = {"raw": raw, "pre": pre, "kept": kept, "mode": f"raw={mode},pre={pmode}", "declined": r["answer"]["declined"],
                            "n_pre": len(pre_ev[-1]["sources"]) if pre_ev else 0}
    return per, unresolved

if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    qs = {json.loads(l)["id"]: json.loads(l) for l in open(args[0]) if l.strip()}
    res = Resolver("--vital5" in sys.argv)
    results = {}
    for p in args[1:]:
        per, unres = score(qs, p, res); results[p] = per
        n = len(per); c = {lv: sum(v[lv] for v in per.values()) for lv in ("raw", "pre", "kept")}
        modes = {v["mode"] for v in per.values()}
        lost = sorted(i for i, v in per.items() if v["raw"] and not v["pre"])
        decl = sorted(i for i, v in per.items() if v["pre"] and v["declined"])
        print(f"{p.split('/')[-1]} [{'/'.join(sorted(modes))}]: items {n}; key in raw {c['raw']} | pre-answer sources {c['pre']} | final kept {c['kept']}; "
              f"raw->pre lost {len(lost)}: {', '.join(lost)}; key shown but declined {len(decl)}: {', '.join(decl)}; unresolved titles {len(unres)}")
    if len(args) >= 3:
        a, b = results[args[1]], results[args[2]]
        # S1 E1(b) precondition helpers: items (all 72, keyed or not) that lose ALL pre-answer sources.
        def npre_all(path):
            out = {}
            for l in open(path):
                if not l.strip(): continue
                t = json.loads(l); ev = [e for e in t.get("events", []) if e.get("type") == "sources"]
                out[t["itemId"]] = len(ev[-1]["sources"]) if ev else 0
            return out
        na, nb = npre_all(args[1]), npre_all(args[2])
        emptied = sorted(i for i in na if na[i] > 0 and nb.get(i, 0) == 0)
        print(f"items losing ALL pre-answer sources {args[1].split('/')[-1]} -> {args[2].split('/')[-1]}: {len(emptied)} {emptied}")
        common = sorted(set(a) & set(b))
        g = sum(b[i]["pre"] and not a[i]["pre"] for i in common); lo = sum(a[i]["pre"] and not b[i]["pre"] for i in common)
        ok = (g - lo) >= 5 and lo <= 1 and not emptied
        print(f"S1 E1(b) replay precondition (net >= +5 keys, <= 1 lost, 0 items emptied; pre level): net {g - lo:+d} (+{g}/-{lo}), emptied {len(emptied)} -> {'PASS' if ok else 'FAIL'}")
        common = sorted(set(a) & set(b))
        for lv in ("raw", "pre"):
            gain = [i for i in common if b[i][lv] and not a[i][lv]]; loss = [i for i in common if a[i][lv] and not b[i][lv]]
            print(f"paired [{lv}] {args[1].split('/')[-1]} -> {args[2].split('/')[-1]}: n={len(common)} gained {len(gain)} {gain} lost {len(loss)} {loss}")
