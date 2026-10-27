#!/usr/bin/env python3
"""Build <dir>/refs/refs.jsonl (blind) and bench/v0.3/refs/{MANIFEST.jsonl, MANIFEST.json} (git, hashes only) from the
web__*.new.jsonl rows written by import_web_refs.py. Copy of bench/v0.2/refs/build_manifest.py: the RAW source, the
account terms, cli_version ("web-ui <vendor_ui>"), prompt version (reference.v1-webui) and output folders changed; word
counts, the >250-word count and the retry count added. Only rows whose question text equals the current item's are used
(the latest such row per id). Reference text never leaves private/; MANIFEST* hold hashes and numbers only.
Usage (from boar-eval/): python3 bench/v0.3/refs/build_manifest.py [--dir DIR] [--freeze]   (--freeze only at n/n ok)"""
import argparse, hashlib, json, statistics, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent          # bench/v0.3/refs (git): MANIFEST.jsonl, MANIFEST.json
DEFAULT_DIR = Path("bench/v0.3/work/")
QFILE = "questions.v03.jsonl"
PROMPT_VERSION = "reference.v1-webui"
PROMPT_SHA256 = "d51443438dfebcc7d2c3a0136340c70a68f495e1214c00a3a8c56bcdbc755972"  # reference.v1
ACCOUNT_TERMS = "consumer web UI, training opt-out on"
WORD_CAP = 250


def sha(b): return hashlib.sha256(b).hexdigest()
def jsonl(rows): return "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows).encode("utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", type=Path, default=DEFAULT_DIR, help=f"live folder holding {QFILE} and refs/")
    ap.add_argument("--freeze", action="store_true")
    a = ap.parse_args()
    Q, REFS = a.dir / QFILE, a.dir / "refs"
    RAW = sorted(REFS.glob("web__*.new.jsonl"))
    qb = Q.read_bytes()
    items = [json.loads(l) for l in qb.decode("utf-8").splitlines() if l.strip()]
    gen = {}
    for f in RAW:
        for l in f.read_text(encoding="utf-8").splitlines():
            if l.strip():
                r = json.loads(l)
                gen.setdefault(r["id"], []).append(r)
    rows, man, missing = [], [], []
    for x in items:
        ok = [r for r in gen.get(x["id"], []) if r.get("ok") and r["question"] == x["question"]]
        if not ok:
            missing.append(x["id"]); continue
        r = ok[-1]
        rows.append(r)
        man.append({"id": x["id"], "sha256": sha(r["answer"].encode("utf-8")), "model_id": r["actualModelId"],
                    "cli_version": r["cliVersion"], "prompt_version": r["promptVersion"], "prompt_sha256": r["promptSha256"],
                    "generated_at": r["generatedAt"], "web_search": r["webUsed"], "tools": ["web-ui search"],
                    "account_terms": ACCOUNT_TERMS, "source": "generated for v0.3-ext (manual paste)",
                    "attempt": r["attempt"], "words": r["words"]})
    if any(m["prompt_sha256"] != PROMPT_SHA256 or m["prompt_version"] != PROMPT_VERSION for m in man):
        sys.exit("ABORT: a row was not generated with reference.v1 (web UI)")
    if a.freeze and missing: sys.exit(f"ABORT: cannot freeze, {len(missing)} missing")
    (REFS / "refs.jsonl").write_bytes(jsonl(rows))
    (HERE / "MANIFEST.jsonl").write_bytes(jsonl(man))
    qtext = {x["id"]: x["question"] for x in items}
    stale = sorted(i for i, rs in gen.items() if any(r["question"] != qtext.get(i) for r in rs))
    w = [m["words"] for m in man]
    (HERE / "MANIFEST.json").write_text(json.dumps({
        "bench": "boar-eval bench v0.3-ext, frontier+web references (non-Claude web UI)",
        "questions_file": Q.name, "questions_sha256": sha(qb),
        "promptVersion": PROMPT_VERSION, "promptSha256": PROMPT_SHA256,
        "frozen": a.freeze, "n_items": len(items), "n_ok": len(man), "n_missing": len(missing), "missing_ids": missing,
        "generator": "manual paste in a vendor web UI (rnd/research/coordinator/bench-v03/refs-prompt.md) -> bench/v0.3/refs/import_web_refs.py",
        "models": sorted({m["model_id"] for m in man}), "cli_versions": sorted({m["cli_version"] for m in man}),
        "first_generatedAt": min((m["generated_at"] for m in man), default=None),
        "last_generatedAt": max((m["generated_at"] for m in man), default=None),
        "raw_files_sha256": {f.name: sha(f.read_bytes()) for f in RAW},
        "questions_sha256_at_generation": sorted({r["questionsSha256"] for r in rows}),
        "ids_with_superseded_rows": stale,
        "n_web_used": sum(m["web_search"] for m in man),
        "n_retried": sum(m["attempt"] > 1 for m in man),
        "words_median": statistics.median(w) if w else None, "words_max": max(w, default=None),
        "n_over_250_words": sum(x > WORD_CAP for x in w),
        "refs_jsonl_sha256": sha(jsonl(rows)),
        "policy": "reference TEXT stays in private/ (never in git); only hashes and numbers are committed"}, indent=1, ensure_ascii=False) + "\n")
    print(f"refs {len(man)}/{len(items)} ok; missing {len(missing)}; frozen={a.freeze}")


if __name__ == "__main__":
    main()
