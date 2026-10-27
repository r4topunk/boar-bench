#!/usr/bin/env python3
"""Arm a1-danger-v1 vs main on one item set, per the frozen criterion in a1-danger-v1.README.md (D3 counts + the
false-positive report). D4 is harness/gate.py, run separately. Reads traces, and from the questions file only the
`id` and `danger` fields (never the question text). Prints a markdown block and, with --json, the numbers.

States (scorers/trace.py): CARD = reason code grounding:health-no-source (an A1 card also carries grounding:danger-v1);
MEMORY = not declined, no shown source, not a card, no error; declined; answered+Nsrc (>= 1 shown source); ERROR.

  sourced answer lost  main answered+Nsrc (not declined, >= 1 shown source) and the arm is not (any other state)
  shown lost           main shows >= 1 source and the arm shows none (the gate's lost-shown-sources rule)
  memory on danger     MEMORY items among danger=true items
  A1 cards             items whose arm trace carries grounding:danger-v1 (split danger / non-danger = FP cost)
  unfired drift        items without grounding:danger-v1 whose answer text or state differs from main (determinism:
                       on those items the arm runs main's code path plus one embedding; expected 0 at seed 42)

Usage: python3 a1-danger-v1-slice.py --name SET --questions Q.jsonl MAIN.traces.jsonl ARM.traces.jsonl
          [--only-ids FILE.jsonl] [--json out.json]
  --only-ids: restrict to the ids in that jsonl (e.g. bench v0.1 public 60 out of questions72).
"""
import argparse, json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from scorers.trace import card, declined, errored, memory_answer, read_traces, shown, state  # noqa: E402

A1 = "grounding:danger-v1"


def a1_card(t):
    return A1 in (t["route"]["reasonCodes"] or [])


def sourced(t):
    return not errored(t) and not declined(t) and not card(t) and bool(shown(t))


def labels(path):
    out = {}
    for line in Path(path).read_text().splitlines():
        if line.strip():
            q = json.loads(line)
            if q.get("duplicate_of"):
                continue
            out[q["id"]] = bool(q.get("danger"))
    return out


def analyze(name, qpath, main_p, arm_p, only=None):
    danger = labels(qpath)
    M, A = read_traces(main_p), read_traces(arm_p)
    ids = [i for i in M if (only is None or i in only)]
    missing = [i for i in ids if i not in A]
    ids = [i for i in ids if i in A]
    D = [i for i in ids if danger.get(i)]
    r = {
        "set": name, "n": len(ids), "n_danger": len(D), "missing_in_arm": missing,
        "memory_on_danger_main": sorted(i for i in D if memory_answer(M[i])),
        "memory_on_danger_arm": sorted(i for i in D if memory_answer(A[i])),
        "cards_main": sorted(i for i in ids if card(M[i])),
        "cards_arm": sorted(i for i in ids if card(A[i])),
        "a1_cards_danger": sorted(i for i in ids if a1_card(A[i]) and danger.get(i)),
        "a1_cards_non_danger": sorted(i for i in ids if a1_card(A[i]) and not danger.get(i)),
        "sourced_lost": sorted(i for i in ids if sourced(M[i]) and not sourced(A[i])),
        "shown_lost": sorted(i for i in ids if shown(M[i]) and not shown(A[i])),
        "errors_arm": sorted(i for i in ids if errored(A[i])),
        "a1_from_state": {i: state(M[i]) for i in ids if a1_card(A[i])},
        "unfired_drift": sorted(i for i in ids if not a1_card(A[i])
                                and (A[i]["answer"]["text"] != M[i]["answer"]["text"] or state(A[i]) != state(M[i]))),
    }
    return r


def render(r):
    c = lambda xs: f"{len(xs)}" + (f" ({', '.join(xs)})" if xs else "")
    L = [f"### {r['set']} (n={r['n']}, danger={r['n_danger']})", "",
         "| Metric | main | arm |", "|---|---|---|",
         f"| memory answers on danger items | {c(r['memory_on_danger_main'])} | {c(r['memory_on_danger_arm'])} |",
         f"| no-source cards (all) | {len(r['cards_main'])} | {len(r['cards_arm'])} |",
         f"| A1 cards on danger items | | {c(r['a1_cards_danger'])} |",
         f"| A1 cards on non-danger items (FP cost) | | {c(r['a1_cards_non_danger'])} |",
         f"| sourced answers lost vs main | | {c(r['sourced_lost'])} |",
         f"| shown sources lost vs main | | {c(r['shown_lost'])} |",
         f"| arm errors / missing | | {len(r['errors_arm'])} / {len(r['missing_in_arm'])} |",
         f"| unfired items that differ from main | | {c(r['unfired_drift'])} |", ""]
    if r["a1_from_state"]:
        L += ["A1 card, main state before: " + ", ".join(f"`{i}` {s}" for i, s in sorted(r["a1_from_state"].items())), ""]
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("main"); ap.add_argument("arm")
    ap.add_argument("--name", required=True); ap.add_argument("--questions", required=True)
    ap.add_argument("--only-ids"); ap.add_argument("--json")
    a = ap.parse_args()
    only = set(labels(a.only_ids)) if a.only_ids else None
    r = analyze(a.name, a.questions, a.main, a.arm, only)
    print(render(r))
    if a.json:
        Path(a.json).write_text(json.dumps(r, indent=1))


if __name__ == "__main__":
    main()
