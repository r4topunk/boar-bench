#!/usr/bin/env python3
"""Builds the device request files in devices/requests/ from one questions file (default: the night 2026-10-01
72-item set = bench v0.1 public 60 + safety track v0.3 12). Deterministic: same input, same bytes.

Writes:
  questions72.device.jsonl            {id, query, category} per line: input of scripts/eval-iphone.mjs --questions
  <config>.request.json               the in-app request (src/eval/deviceEvalRequest.pure.ts @ 0cfd4a77, pipeline
                                      "answer"), one per config; the rep is the requestId suffix (-r1, -r2 ...)
  p3-speed9x3.device.jsonl            P3 probe: 9 items that generate >= 60 tokens on desktop, asked 3 times
  and-*-p3speed.request.json          the same probe as an Android request
  and-*-smoke.request.json            3-question smoke per Android config (first install / pickup check)
  MANIFEST.json                       sha256 of every file above and of the source questions file

Usage: python3 devices/make_requests.py [--questions runs/night-2026-10-01/questions72.jsonl]
"""
import argparse, hashlib, json
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
OUT = HERE / "requests"
EVAL_SET_VERSION = "dataset-bench-v0.1-72"  # = what eval-iphone.mjs --dataset bench-v0.1-72 records
QUICK = {"quickFirst": True, "alwaysComplete": False}  # = desktop config settings (p2-iphone13-0cfd4a77.json)
KIT = ["boar-crypto", "boar-wikivoyage-en"]  # = desktop config kit; the bundled corpus is always there
# Items that generated >= 60 tokens on desktop ios-main-s42 (night 2026-10-01): the P3 speed probe asks them 3 times.
SPEED_IDS = ["lan-rsn-002", "vit-cry-001", "vit-cry-004", "vit-cry-005", "vit-cry-006", "vit-cry-009", "vit-hlt-003",
             "lan-exp-005", "lan-cmp-005"]

CONFIGS = {
    # name: (model id in the app catalog @ 0cfd4a77, confirmLargeModels)
    "ios-q15-quick": ("qwen2.5-1.5b-instruct-q4km", False),
    "and-qwen3-4b-quick": ("qwen3-4b-instruct-2507-q4km", True),
    "and-gemma4-e4b-quick": ("gemma-4-e4b-it-q4_0", True),
    # added 2026-10-02: the 4B is LMK-killed on load on an 8 GB phone (moto g75); the 1.5B is the Android fallback
    "and-q15-quick": ("qwen2.5-1.5b-instruct-q4km", False),
}
SMOKE_IDS = ["vit-cry-001", "lan-exp-005", "saf-001"]  # one generated crypto answer, one explanation, one danger card


def device_questions(path):
    out = []
    for line in Path(path).read_text().splitlines():
        if not line.strip():
            continue
        q = json.loads(line)
        if q.get("duplicate_of"):
            continue
        out.append({"id": q["id"], "query": q["question"].strip(), "category": q.get("category") or "custom"})
    ids = [q["id"] for q in out]
    assert len(ids) == len(set(ids)), "duplicate ids"
    return out


def request(name, questions, rep=1, tag=None):
    model, confirm = CONFIGS[name]
    r = {
        "requestId": f"be-{name}{'-' + tag if tag else ''}-r{rep}",
        "pipeline": "answer",
        "models": [model],
        "questions": questions,
        "evalSetVersion": EVAL_SET_VERSION,
        "answerSettings": QUICK,
        # A no-op when present (no network needed); it also registers the Wikivoyage catalog entry for this session.
        "install": {"assets": [model, *KIT]},
    }
    if confirm:
        r["confirmLargeModels"] = True
    return r


def jsonl(rows):
    return "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--questions", default=str(REPO / "runs/night-2026-10-01/questions72.jsonl"))
    a = ap.parse_args()
    qs = device_questions(a.questions)
    OUT.mkdir(parents=True, exist_ok=True)
    files = {"questions72.device.jsonl": jsonl(qs)}
    by_id = {q["id"]: q for q in qs}
    speed = [{**by_id[i], "id": f"{i}__k{k}"} for k in (1, 2, 3) for i in SPEED_IDS]
    files["p3-speed9x3.device.jsonl"] = jsonl(speed)
    for name in CONFIGS:
        files[f"{name}.request.json"] = json.dumps(request(name, qs), ensure_ascii=False, indent=1) + "\n"
        if name.startswith("and-"):  # the iPhone takes the .jsonl directly (eval-iphone.mjs --questions)
            files[f"{name}-p3speed.request.json"] = json.dumps(request(name, speed, tag="p3speed"), ensure_ascii=False, indent=1) + "\n"
            smoke = [by_id[i] for i in SMOKE_IDS]
            files[f"{name}-smoke.request.json"] = json.dumps(request(name, smoke, tag="smoke"), ensure_ascii=False, indent=1) + "\n"
    for f, text in files.items():
        (OUT / f).write_text(text)
    manifest = {"source": {"path": str(Path(a.questions).resolve().relative_to(REPO)) if str(Path(a.questions).resolve()).startswith(str(REPO)) else a.questions,
                           "sha256": hashlib.sha256(Path(a.questions).read_bytes()).hexdigest(), "items": len(qs)},
                "evalSetVersion": EVAL_SET_VERSION,
                "files": {f: hashlib.sha256(t.encode()).hexdigest() for f, t in sorted(files.items())}}
    (OUT / "MANIFEST.json").write_text(json.dumps(manifest, indent=1) + "\n")
    print(f"{len(qs)} questions -> {OUT} ({', '.join(sorted(files))})")


if __name__ == "__main__":
    main()
