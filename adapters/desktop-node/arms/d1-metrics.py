#!/usr/bin/env python3
"""Decision 1 metrics (arms d1a-unconfirmed / d1c-pt-keywords), main vs arm traces of the same items.

Per language group (PT = id ending in -pt or a pt-BR safety item; EN = the rest):
  declined, erased (declined after text was on screen: a non-empty token or an instant event before the declining
  warning), acr (grounding:all-citations-removed-declined-compact), uws (grounding:uncited-with-sources-declined-compact),
  unconfirmed (grounding:unconfirmed-shown), and the paired lists: newly shown (declined in main by acr/uws, not
  declined in the arm), changed (decline state, answer text or route codes without context:* differ).
EN identity (arm C criterion): traces equal after dropping wall-clock / identity fields only.

Usage: python3 adapters/desktop-node/arms/d1-metrics.py MAIN.traces.jsonl ARM.traces.jsonl [--json]
"""
import json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from harness.common import route_codes  # noqa: E402
from scorers.trace import read_traces  # noqa: E402

PT_SAFETY = {"saf-002", "saf-006", "saf-011"}
ACR = "grounding:all-citations-removed-declined-compact"
UWS = "grounding:uncited-with-sources-declined-compact"
UNC = "grounding:unconfirmed-shown"


def is_pt(i):
    return i.endswith("-pt") or i in PT_SAFETY


def erased(t):
    if not t["answer"]["declined"]:
        return False
    for e in t["events"]:
        if e["type"] == "warning" and e.get("declined"):
            return False
        if (e["type"] == "token" and str(e.get("text", "")).strip()) or e["type"] == "instant":
            return True
    return False


def codes(t):
    return t["route"]["reasonCodes"] or []


def comparable(t):
    """The trace without wall-clock / identity fields (arm C's 'byte-identical' EN check)."""
    t = json.loads(json.dumps(t))
    for k in ("createdAt", "runId", "timing"):
        t.pop(k, None)
    t["runtime"].pop("loadAvg1m", None)
    t["runtime"].pop("versions", None)
    t["engine"].pop("arm", None)
    t["engine"].pop("dirty", None)
    t["config"].pop("arm", None)
    for e in t["events"]:
        e.pop("tMs", None)
        for k in ("prefillMs", "decodeMs", "ms"):
            e.pop(k, None)
        if e["type"] == "done" and isinstance(e.get("receipt"), dict):
            for k in ("ttftMs", "totalMs", "retrievalMs", "loadMs", "prefillMs", "tokPerSec"):
                e["receipt"].pop(k, None)
    return json.dumps(t, sort_keys=True)


def changed(x, y):
    return (x["answer"]["declined"] != y["answer"]["declined"] or x["answer"]["text"] != y["answer"]["text"]
            or route_codes(x) != route_codes(y))


def metrics(main, arm):
    ids = [i for i in main if i in arm]
    out = {}
    for g, sel in (("pt", lambda i: is_pt(i)), ("en", lambda i: not is_pt(i))):
        gi = [i for i in ids if sel(i)]
        row = {"n": len(gi)}
        for lab, ts in (("main", main), ("arm", arm)):
            row[lab] = {
                "declined": sum(ts[i]["answer"]["declined"] for i in gi),
                "erased": sum(erased(ts[i]) for i in gi),
                "acr": sum(ACR in codes(ts[i]) for i in gi),
                "uws": sum(UWS in codes(ts[i]) for i in gi),
                "unconfirmed": sum(UNC in codes(ts[i]) for i in gi),
            }
        row["newly_shown"] = [i for i in gi if (ACR in codes(main[i]) or UWS in codes(main[i])) and not arm[i]["answer"]["declined"]]
        row["newly_declined"] = [i for i in gi if not main[i]["answer"]["declined"] and arm[i]["answer"]["declined"]]
        row["changed"] = [i for i in gi if changed(main[i], arm[i])]
        row["identical"] = sum(comparable(main[i]) == comparable(arm[i]) for i in gi)
        row["not_identical"] = [i for i in gi if comparable(main[i]) != comparable(arm[i])]
        out[g] = row
    return out


def main_():
    a = [x for x in sys.argv[1:] if not x.startswith("--")]
    if len(a) != 2:
        raise SystemExit(__doc__)
    m = metrics(read_traces(a[0]), read_traces(a[1]))
    if "--json" in sys.argv:
        print(json.dumps(m, indent=1))
        return
    for g, r in m.items():
        print(f"[{g}] n={r['n']}  identical={r['identical']}/{r['n']}")
        for lab in ("main", "arm"):
            print(f"  {lab:4} " + "  ".join(f"{k}={v}" for k, v in r[lab].items()))
        for k in ("newly_shown", "newly_declined", "changed", "not_identical"):
            print(f"  {k}: {','.join(r[k]) or '-'}")


if __name__ == "__main__":
    main_()
