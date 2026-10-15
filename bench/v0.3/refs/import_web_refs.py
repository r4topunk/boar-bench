#!/usr/bin/env python3
"""Import bench v0.3 web-UI reference answers (reference.v1 pasted into a ChatGPT Project / Gemini Gem; recipe in
rnd/research/coordinator/bench-v03/refs-prompt.md) into the v0.2 gen_refs.mjs row shape. Script-only: it never prints
reference or question text, only ids, counts and flags.

Input (blind, read-only): <dir>/refs/raw/<id>.md, each with a header then the pasted reply:
    id: v03-explanation-01
    model: <model name exactly as in the picker>
    vendor_ui: chatgpt.com | gemini.google.com
    date: 2026-10-18
    web: yes | no
    attempt: 1 | 2
    ---
    <reply, including the trailing Sources: lines>
  <id>.attempt1.md files (kept when a retry happened) are counted as retries, never imported.
  <dir>/refs/todo.txt (id<TAB>question, written by the coordinator) is the question text that was pasted; a row whose
  todo question differs from the current item question is ok=false (stale: after a gate fix the coordinator moves the old
  raw file to raw/superseded/ and rewrites the todo line, and the maintainer regenerates the reference).
Output (blind): <dir>/refs/web__<model-slug>.new.jsonl, rewritten from raw/ on every run (one file per model). Row fields:
  id, category, lang, question, ok, answer, sources, rawResult, requestedModel = actualModelId = <picker name>, vendorUi,
  cliVersion = "web-ui <vendor_ui>", via = "web-ui (manual paste)", promptVersion = "reference.v1-webui",
  promptSha256 = reference.v1, questionsSha256, generatedAt = <date>, attempt, words, webUsed, nUrls, over250, stale.
The answer/sources split is splitSources() of bench/v0.2/refs/gen_refs.mjs; tracking parameters (utm_*, fbclid, gclid)
are stripped from source URLs. Then: python3 bench/v0.3/refs/build_manifest.py [--freeze].
Usage (from boar-eval/): python3 bench/v0.3/refs/import_web_refs.py [--dir DIR]
"""
import argparse, hashlib, json, re, statistics, sys
from collections import Counter
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

DEFAULT_DIR = Path("bench/v0.3/work/")
QFILE = "questions.v03.jsonl"
PROMPT_VERSION = "reference.v1-webui"
PROMPT_SHA256 = "d51443438dfebcc7d2c3a0136340c70a68f495e1214c00a3a8c56bcdbc755972"  # reference.v1, pasted verbatim
HEADER_KEYS = ("id", "model", "vendor_ui", "date", "web", "attempt")
VENDORS = ("chatgpt.com", "gemini.google.com")
WORD_CAP = 250
TRACKING = re.compile(r"^(utm_[a-z_]+|fbclid|gclid|srsltid)$", re.I)


def split_sources(text):
    """Python port of splitSources() in bench/v0.2/refs/gen_refs.mjs (same regexes)."""
    m = re.search(r"\n\**Sources:?\**\s*\n([\s\S]*)$", text, re.I)
    body = text[:m.start()].strip() if m else text.strip()
    urls = []
    for u in re.findall(r"https?://[^\s)\]>\"']+", m.group(1) if m else text):
        u = clean_url(re.sub(r"[.,;]+$", "", u))
        if u not in urls: urls.append(u)
    return body, urls


def clean_url(u):
    p = urlsplit(u)
    q = [(k, v) for k, v in parse_qsl(p.query, keep_blank_values=True) if not TRACKING.match(k)]
    return urlunsplit((p.scheme, p.netloc, p.path, urlencode(q), p.fragment))


def parse_raw(path):
    head, sep, body = path.read_text(encoding="utf-8").partition("\n---\n")
    if not sep: sys.exit(f"ABORT: {path.name}: no '---' line after the header")
    h = {}
    for line in head.splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            h[k.strip().lower()] = v.strip()
    if miss := [k for k in HEADER_KEYS if not h.get(k)]: sys.exit(f"ABORT: {path.name}: header misses {miss}")
    if h["id"] != path.stem: sys.exit(f"ABORT: {path.name}: header id {h['id']} != file name")
    if not re.match(r"^2026-\d{2}-\d{2}$", h["date"]): sys.exit(f"ABORT: {path.name}: date not YYYY-MM-DD")
    if h["web"].lower() not in ("yes", "no") or h["attempt"] not in ("1", "2"): sys.exit(f"ABORT: {path.name}: web/attempt value")
    return h, body.strip("\n")


def slug(s): return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", type=Path, default=DEFAULT_DIR, help=f"live folder holding {QFILE} and refs/")
    a = ap.parse_args()
    refs, qf = a.dir / "refs", a.dir / QFILE
    qb = qf.read_bytes()
    items = {x["id"]: x for x in (json.loads(l) for l in qb.decode("utf-8").splitlines() if l.strip())}
    todo = {}
    if (refs / "todo.txt").exists():
        for line in (refs / "todo.txt").read_text(encoding="utf-8").splitlines():
            if line.strip():
                i, _, q = line.partition("\t")
                todo[i] = q
    files = sorted(p for p in (refs / "raw").glob("*.md") if not p.stem.endswith(".attempt1"))
    retries = sorted(p.stem.removesuffix(".attempt1") for p in (refs / "raw").glob("*.attempt1.md"))
    out, flags = {}, Counter()
    for p in files:
        h, raw = parse_raw(p)
        if h["id"] not in items: sys.exit(f"ABORT: {p.name}: id not in {QFILE}")
        x = items[h["id"]]
        if h["vendor_ui"] not in VENDORS: flags["vendor_ui_unknown"] += 1
        answer, sources = split_sources(raw)
        q_pasted = todo.get(x["id"])
        stale = q_pasted is not None and q_pasted != x["question"]
        words = len(answer.split())
        row = {"id": x["id"], "category": x["category"], "lang": x["lang"], "question": q_pasted if q_pasted is not None else x["question"],
               "ok": bool(answer) and not stale, "answer": answer, "sources": sources, "rawResult": raw,
               "requestedModel": h["model"], "actualModelId": h["model"], "vendorUi": h["vendor_ui"],
               "cliVersion": f"web-ui {h['vendor_ui']}", "via": "web-ui (manual paste)",
               "promptVersion": PROMPT_VERSION, "promptSha256": PROMPT_SHA256,
               "questionsSha256": hashlib.sha256(qb).hexdigest(), "generatedAt": h["date"], "attempt": int(h["attempt"]),
               "words": words, "webUsed": h["web"].lower() == "yes", "nUrls": len(sources), "over250": words > WORD_CAP,
               "stale": stale, "todoListed": q_pasted is not None}
        for f in ("stale", "over250"):
            flags[f] += row[f]
        flags["no_url"] += not sources; flags["no_web"] += not row["webUsed"]; flags["empty"] += not answer
        flags["not_in_todo"] += q_pasted is None
        out.setdefault(slug(h["model"]), []).append(row)
    for s, rs in out.items():
        (refs / f"web__{s}.new.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rs), encoding="utf-8")
    allrows = [r for rs in out.values() for r in rs]
    w = [r["words"] for r in allrows]
    missing = sorted(set(items) - {r["id"] for r in allrows})
    print(f"imported {len(allrows)}/{len(items)} ({sum(r['ok'] for r in allrows)} ok) into {sorted(f'web__{s}.new.jsonl' for s in out)}; "
          f"missing {len(missing)}; retries {len(retries)}; words median {statistics.median(w) if w else None} max {max(w, default=None)}; "
          f"flags {dict(flags)}")
    for f, ids in (("stale", [r["id"] for r in allrows if r["stale"]]), ("over250", [r["id"] for r in allrows if r["over250"]]),
                   ("no_url", [r["id"] for r in allrows if not r["sources"]]), ("no_web", [r["id"] for r in allrows if not r["webUsed"]])):
        if ids: print(f"  {f}: {ids}")


if __name__ == "__main__":
    main()
