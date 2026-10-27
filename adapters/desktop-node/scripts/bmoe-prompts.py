#!/usr/bin/env python3
"""Pick the deep arm's real prompts for the bmoe memory probe (card deep-tier-streamed-moe §6b, criterion 6).

Input: the adapter's --dump-prompts jsonl ({itemId, messages, nPredict, ...}, one line per generate) for one deep run.
Rule (declared before the probe): the N prompts with the most characters, i.e. the ones closest to the deep contract's
400 context tokens, since the prefill peak grows with prompt length; ties broken by itemId. Each prompt is written as
the system content + a blank line + the user content (bmoe-cli --chatml wraps -p as the user turn).
Usage: bmoe-prompts.py prompts.jsonl OUT_DIR [N=10]
"""
import json, os, sys

src, out = sys.argv[1], sys.argv[2]
n = int(sys.argv[3]) if len(sys.argv) > 3 else 10
rows = [json.loads(l) for l in open(src) if l.strip()]
def text(r):
    if "messages" in r:
        sysm = "\n".join(m["content"] for m in r["messages"] if m["role"] == "system")
        rest = "\n\n".join(m["content"] for m in r["messages"] if m["role"] != "system")
        return f"{sysm}\n\n{rest}" if sysm else rest
    return r["prompt"]
seen, picked = set(), []
for r in sorted(rows, key=lambda r: (-len(text(r)), r["itemId"])):
    if r["itemId"] in seen:
        continue
    seen.add(r["itemId"])
    picked.append(r)
    if len(picked) == n:
        break
os.makedirs(out, exist_ok=True)
for i, r in enumerate(picked):
    with open(os.path.join(out, f"{i:02d}-{r['itemId']}.txt"), "w") as f:
        f.write(text(r))
    print(f"{i:02d} {r['itemId']} chars={len(text(r))}")
