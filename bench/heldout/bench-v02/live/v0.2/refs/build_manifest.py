#!/usr/bin/env python3
"""Build bench/v0.2/refs/{refs.jsonl, MANIFEST.jsonl, MANIFEST.json} from claude-code__opus.new.jsonl (gen_refs.mjs).
Mirrors section 5 of bench/v0.1/build.py. Only rows whose question text equals the current item's are used (the
latest such row per id). refs.jsonl (text) is gitignored; MANIFEST* hold hashes only.
Usage (from boar-eval/): python3 bench/v0.2/refs/build_manifest.py [--freeze]   (--freeze only when 110/110 ok)"""
import hashlib, json, sys
from pathlib import Path

REFS = Path(__file__).resolve().parent
BENCH = REFS.parent
Q = BENCH / "questions.v02-new.jsonl"
RAW = REFS / "claude-code__opus.new.jsonl"
PROMPT_SHA256 = "d51443438dfebcc7d2c3a0136340c70a68f495e1214c00a3a8c56bcdbc755972"  # reference.v1


def sha(b): return hashlib.sha256(b).hexdigest()
def jsonl(rows): return "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows).encode("utf-8")


def main():
    qb = Q.read_bytes()
    items = [json.loads(l) for l in qb.decode("utf-8").splitlines() if l.strip()]
    gen = {}
    for l in (RAW.read_text(encoding="utf-8").splitlines() if RAW.exists() else []):
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
                    "generated_at": r["generatedAt"], "web_search": True, "tools": r["tools"],
                    "source": "generated for v0.2-new"})
    if any(m["prompt_sha256"] != PROMPT_SHA256 for m in man): sys.exit("ABORT: a row was not generated with reference.v1")
    freeze = "--freeze" in sys.argv
    if freeze and missing: sys.exit(f"ABORT: cannot freeze, {len(missing)} missing")
    (REFS / "refs.jsonl").write_bytes(jsonl(rows))
    (REFS / "MANIFEST.jsonl").write_bytes(jsonl(man))
    qtext = {x["id"]: x["question"] for x in items}
    stale = sorted(i for i, rs in gen.items() if any(r["question"] != qtext.get(i) for r in rs))
    (REFS / "MANIFEST.json").write_text(json.dumps({
        "bench": "boar-eval bench v0.2-new, frontier+web references",
        "questions_file": Q.name, "questions_sha256": sha(qb),
        "promptVersion": "reference.v1", "promptSha256": PROMPT_SHA256,
        "frozen": freeze, "n_items": len(items), "n_ok": len(man), "n_missing": len(missing), "missing_ids": missing,
        "generator": "bench/v0.2/refs/gen_refs.mjs (recipe of bench/v0.1/refs/gen_refs.mjs)",
        "models": sorted({m["model_id"] for m in man}), "cli_versions": sorted({m["cli_version"] for m in man}),
        "first_generatedAt": min((m["generated_at"] for m in man), default=None),
        "last_generatedAt": max((m["generated_at"] for m in man), default=None),
        "raw_file_sha256": sha(RAW.read_bytes()) if RAW.exists() else None,
        "questions_sha256_at_generation": sorted({r["questionsSha256"] for r in rows}),
        "ids_with_superseded_rows": stale,
        "sum_wall_s": round(sum(r.get("wallMs", 0) for r in rows) / 1000),
        "refs_jsonl_sha256": sha(jsonl(rows)),
        "policy": "reference TEXT stays private (gitignored); only hashes are committed"}, indent=1, ensure_ascii=False) + "\n")
    print(f"refs {len(man)}/{len(items)} ok; missing {len(missing)}; frozen={freeze}")


if __name__ == "__main__":
    main()
