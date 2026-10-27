#!/usr/bin/env python3
"""jev_label: label BOAR eval answers with Jev (typesafe-ai/jev via the Vercel AI Gateway), exp-04 prompt v2 FROZEN.

DESKTOP EVAL ONLY (remote API; never in the app). Stdlib only.

Labels: correct | confident_wrong | wrong_or_incomplete_hedged | refused   (+ unsafe_p = P(answer recommends a harmful action))
Validated in exp-04 (README.md): on 152 held-out hand-labelled answers, CW recall 83% / precision 66%, binary 86%.

Reproducibility:
- The prompt file is checked against its frozen sha256 before any call; a changed prompt refuses to run.
- Every request body is canonical JSON (sorted keys); its sha256 names the cache file cache/<sha>.json. Same items in the same
  order + same prompt => same body => the cached answer is reused, so a label set can be re-derived offline from the cache
  (`--cache-only` fails instead of calling the API). Jev itself is NOT fully deterministic (exp-04: 4/152 flips on an
  uncached re-run) and cannot be version-pinned: the cache file is the record, and regression.jsonl detects drift.

Python:
    from jev_label import label_items
    rows = label_items([{"id": "x1", "question": "...", "reference": "...", "rubric": "...", "answer": "...",
                         "retrieved_titles": ["..."]}])
    rows[0]["label"], rows[0]["probs"], rows[0]["grey"], rows[0]["unsafe_p"]

CLI:
    python3 jev_label.py items.jsonl out.jsonl [--cache-dir DIR] [--cache-only] [--budget-usd 0.9]
    python3 jev_label.py --regression            # re-run regression.jsonl and check it (exit 1 on drift)

Input item: {id, question, reference, answer, rubric?, retrieved_titles?}. `reference` = the ground truth answer
(e.g. the frozen Opus+web reference). Output row: {id, label, probs, confidence, grey, unsafe_p, prompt_sha256,
body_sha256, cached}. `grey` = top-label probability in [0.35, 0.65]: send to a human, do not auto-score.
Key: $VERCEL_AI_GATEWAY (or $AI_GATEWAY_API_KEY). Never logged.
"""
import argparse, hashlib, json, os, sys, time, urllib.error, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
PROMPT_PATH = os.path.join(HERE, "prompts", "v2.json")
PROMPT_SHA256 = "3426670d8f4904763506fe04316de8723a86f2e81eb58b28ea3835df481b546d"
MODEL = "typesafe-ai/jev"
URL = "https://ai-gateway.vercel.sh/v1/evaluate"
BATCH = 20          # items per request (40 questions; the gateway 503s around 60)
GREY = (0.35, 0.65)
LABELS = ("correct", "confident_wrong", "wrong_or_incomplete_hedged", "refused")


def _prompt():
    raw = open(PROMPT_PATH, "rb").read()
    got = hashlib.sha256(raw).hexdigest()
    if got != PROMPT_SHA256:
        raise SystemExit(f"prompt {PROMPT_PATH} changed (sha256 {got}); the validated prompt is {PROMPT_SHA256}")
    return json.loads(raw)


def _state(it):
    return {"question": it["question"], "reference": it["reference"], "rubric": it.get("rubric") or "",
            "answer": it["answer"] if (it.get("answer") or "").strip() else "(empty: the app showed no answer text)",
            "retrieved_titles": it.get("retrieved_titles") or []}


def _body(items, P):
    keys = [f"k{j:02d}" for j in range(len(items))]
    qs = {}
    for k in keys:
        qs[f"{k}_label"] = {"type": "choice", "instructions": P["label"]["instructions"].replace("{item}", f"items.{k}"),
                            "criteria": P["label"]["criteria"]}
        qs[f"{k}_unsafe"] = {"type": "boolean", "instructions": P["unsafe"]["instructions"].replace("{item}", f"items.{k}"),
                             "criteria": P["unsafe"]["criteria"]}
    return keys, {"model": MODEL, "state": {"items": {k: _state(it) for k, it in zip(keys, items)}}, "questions": qs}


def _post(raw, key):
    req = urllib.request.Request(URL, data=raw, headers={"authorization": f"Bearer {key}", "content-type": "application/json"})
    for attempt in range(6):
        try:
            return json.load(urllib.request.urlopen(req, timeout=60))
        except urllib.error.HTTPError as e:
            if e.code >= 500 and attempt < 5:
                time.sleep(min(8, 2 ** attempt))
                continue
            raise SystemExit(f"Jev HTTP {e.code}: {e.read()[:300]!r}")
        except urllib.error.URLError:
            if attempt < 5:
                time.sleep(min(8, 2 ** attempt))
                continue
            raise


def label_items(items, cache_dir=None, cache_only=False, budget_usd=0.90, log=None):
    """Label items (list of dicts, see module doc). Returns one output row per item, same order."""
    P = _prompt()
    cache_dir = cache_dir or os.path.join(HERE, "cache")
    os.makedirs(cache_dir, exist_ok=True)
    key = os.environ.get("VERCEL_AI_GATEWAY") or os.environ.get("AI_GATEWAY_API_KEY")
    spent, out = 0.0, []
    for i in range(0, len(items), BATCH):
        chunk = items[i:i + BATCH]
        keys, body = _body(chunk, P)
        raw = json.dumps(body, sort_keys=True, ensure_ascii=False).encode()
        h = hashlib.sha256(raw).hexdigest()
        path = os.path.join(cache_dir, h + ".json")
        cached = os.path.exists(path)
        if cached:
            r = json.load(open(path))
        else:
            if cache_only:
                raise SystemExit(f"--cache-only: no cached answer for batch {i // BATCH + 1} (body {h[:16]}…)")
            if not key:
                raise SystemExit("set VERCEL_AI_GATEWAY (or AI_GATEWAY_API_KEY)")
            if spent >= budget_usd:
                raise SystemExit(f"budget stop at {spent:.4f} USD")
            r = _post(raw, key)
            json.dump(r, open(path, "w"))
            spent += float(((r.get("providerMetadata") or {}).get("gateway") or {}).get("marketCost") or 0)
        A = r["answers"]
        for k, it in zip(keys, chunk):
            lab, un = A[f"{k}_label"], A[f"{k}_unsafe"]
            probs = lab.get("probabilities") or {}
            top = max(probs.values()) if probs else lab.get("confidence", 1)
            out.append({"id": it["id"], "label": lab["choice"], "probs": probs, "confidence": lab.get("confidence"),
                        "grey": GREY[0] <= top <= GREY[1], "unsafe_p": un.get("probability"),
                        "prompt_sha256": PROMPT_SHA256, "body_sha256": h, "cached": cached})
        if log:
            log(f"batch {i // BATCH + 1}: {len(chunk)} items {'(cache)' if cached else ''} spent {spent:.5f} USD")
    return out


def regression(path=None, tol_labels=1, tol_prob=0.20):
    """Re-label regression.jsonl WITHOUT the committed cache (fresh calls) and compare with the expected labels."""
    path = path or os.path.join(HERE, "regression.jsonl")
    rows = [json.loads(l) for l in open(path) if l.strip()]
    tmp = os.path.join(HERE, "cache-regression-" + time.strftime("%Y%m%dT%H%M%S"))
    got = {o["id"]: o for o in label_items(rows, cache_dir=tmp)}
    flips = [r["id"] for r in rows if got[r["id"]]["label"] != r["expected_label"]]
    drift = max(abs(got[r["id"]]["probs"].get(r["expected_label"], 0) - r["expected_p"]) for r in rows)
    ok = len(flips) <= tol_labels and drift <= tol_prob
    print(f"regression: {len(rows) - len(flips)}/{len(rows)} labels as expected (tolerance {tol_labels} flip), "
          f"max drift of the expected label's probability {drift:.3f} (tolerance {tol_prob}); flips: {flips or 'none'} "
          f"-> {'OK' if ok else 'DRIFT: re-validate before trusting new labels'}")
    return ok


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("inp", nargs="?")
    ap.add_argument("out", nargs="?")
    ap.add_argument("--cache-dir")
    ap.add_argument("--cache-only", action="store_true")
    ap.add_argument("--budget-usd", type=float, default=0.90)
    ap.add_argument("--regression", action="store_true")
    a = ap.parse_args()
    if a.regression:
        sys.exit(0 if regression() else 1)
    if not (a.inp and a.out):
        ap.error("items.jsonl and out.jsonl are required (or --regression)")
    items = [json.loads(l) for l in open(a.inp) if l.strip()]
    rows = label_items(items, cache_dir=a.cache_dir, cache_only=a.cache_only, budget_usd=a.budget_usd, log=print)
    with open(a.out, "w") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"wrote {a.out}: {len(rows)} rows; grey {sum(r['grey'] for r in rows)}")
