#!/usr/bin/env python3
"""Desktop <-> device agreement, per key, on the items both runs share (EvalTrace only).

The engine decides route and retrieval before it generates, so those keys should agree across runtimes; everything
after the first token (answer text, citation checks, the decline that follows from them, timing) should not. The
expected level is the desktop's own seed-to-seed agreement (e.g. ios-main-s42 vs ios-main-s43): a device run that
agrees with desktop about as well as two desktop seeds agree with each other is consistent.

Keys: task (task:* code), tier, retrieve (retrieve:* codes), instant (instant:* codes), kept (retrieval.kept title
set), shown (answer.shown title set), declined, route (all codes minus context:*, citations:*, grounding:*),
text (identical answer text).
Not comparable desktop <-> device: kept. Device rows only carry the final source list (retrievedTitles), so a
device trace has kept = shown, while desktop kept is the AnswerResult's sources (empty on a decline). Read shown.

Usage: python3 devices/agreement.py A.traces.jsonl B.traces.jsonl [--labels desktop device] [--list KEY]
"""
import argparse, sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scorers.trace import read_traces  # noqa: E402

POST_GEN = ("context:", "citations:", "grounding:")


def codes(t, prefix=None):
    cs = t["route"]["reasonCodes"] or []
    return tuple(sorted(c for c in cs if (c.startswith(prefix) if prefix else not c.startswith(POST_GEN))))


KEYS = {
    "task": lambda t: t["route"]["task"],
    "tier": lambda t: t["route"]["tier"],
    "retrieve": lambda t: codes(t, "retrieve:"),
    "instant": lambda t: codes(t, "instant:"),
    "kept": lambda t: tuple(sorted({s["title"] for s in t["retrieval"]["kept"]})),
    "shown": lambda t: tuple(sorted(set(t["answer"]["shown"]))),
    "declined": lambda t: bool(t["answer"]["declined"]),
    "route": codes,
    "text": lambda t: t["answer"]["text"],
}


def agreement(a, b):
    ids = [i for i in a if i in b and a[i].get("error") is None and b[i].get("error") is None]
    return ids, {k: [i for i in ids if f(a[i]) != f(b[i])] for k, f in KEYS.items()}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("a")
    ap.add_argument("b")
    ap.add_argument("--labels", nargs=2, default=["A", "B"])
    ap.add_argument("--list", choices=sorted(KEYS), help="print the disagreeing items of one key")
    x = ap.parse_args()
    a, b = read_traces(x.a), read_traces(x.b)
    ids, diff = agreement(a, b)
    print(f"{x.labels[0]} vs {x.labels[1]}: {len(ids)} shared items without errors "
          f"(only {x.labels[0]}: {len([i for i in a if i not in b])}, only {x.labels[1]}: {len([i for i in b if i not in a])})")
    print("| key | agree | disagree |\n|---|---|---|")
    for k in KEYS:
        print(f"| {k} | {len(ids) - len(diff[k])}/{len(ids)} | {', '.join(diff[k][:6])}{' …' if len(diff[k]) > 6 else ''} |")
    if x.list:
        f = KEYS[x.list]
        for i in diff[x.list]:
            print(f"\n{i}\n  {x.labels[0]}: {f(a[i])}\n  {x.labels[1]}: {f(b[i])}")


if __name__ == "__main__":
    main()
