"""Retrieval axis (deterministic). With gold source titles for an item:
  recall@k        |gold ∩ titles(retrieval.raw[:k])| / |gold|  (raw = what the retriever returned, before the gates)
  on-topic drop   a gold title present in retrieval.raw and absent from the pre-answer sources: the LAST `sources`
                  event in trace.events (fallback: retrieval.kept when the trace has no sources event). The engine's
                  gates threw the right source away before the answer.
  declined with gold in sources
                  the answer declined although a gold title was in the pre-answer sources (Decision-1 loss: the key
                  reached the prompt; generation/citation side). Counted on its own, never as a drop.
  Why not retrieval.kept: kept is emptied when the answer declines, so "raw - kept" counted declines as drops
  (in the first diagnosis, 5 of 6 night drops were that artifact).
Items without gold are counted as "no gold" and never scored. The descriptive part (raw/kept/dropped sizes,
items with shown sources) is reported for every item: it needs no gold.
Titles match case-insensitively after trimming; a gold entry "Title#Section" also requires the section."""
import re
from scorers import stats

DEFAULT_K = 5


def _norm(s):
    return " ".join(str(s or "").split()).casefold()


# Pack titles carry their library as a prefix ("Wikivoyage: Singapore", "ethereum.org: Gas", "Ethereum EIPs/ERCs:
# EIP-1559"); built-in corpus and Wikipedia titles don't. A bare gold title matches the article in any library; a
# prefixed gold title ("Wikivoyage: Singapore") requires that library.
_LIB = re.compile(r"^[^:]{2,40}:\s+")


def _bare(t):
    return _LIB.sub("", str(t or ""), count=1)


def _match(gold, ref):
    title, _, section = gold.partition("#")
    ref_title = ref.get("title")
    if _norm(title) != _norm(ref_title) and (_LIB.match(title) or _norm(title) != _norm(_bare(ref_title))):
        return False
    return not section or _norm(section) == _norm(ref.get("section"))


def _hit(gold, refs):
    return any(_match(gold, r) for r in refs)


def pre_answer_sources(t):
    """(refs, origin): the last `sources` event's list, else retrieval.kept."""
    for e in reversed(t.get("events") or []):
        if e.get("type") == "sources" and isinstance(e.get("sources"), list):
            return [s if isinstance(s, dict) else {"title": s} for s in e["sources"]], "sources-event"
    return t["retrieval"]["kept"], "kept"


def score_retrieval(traces, gold, k=DEFAULT_K, seed=11):
    """traces: {itemId: EvalTrace}; gold: {itemId: [title, ...]}."""
    per_item, recalls, dropped_gold, declined_gold = [], [], [], []
    origins = {"sources-event": 0, "kept": 0}
    for qid, t in traces.items():
        g = gold.get(qid)
        if not g:
            continue
        raw = t["retrieval"]["raw"]
        pre, origin = pre_answer_sources(t)
        origins[origin] += 1
        found = [x for x in g if _hit(x, raw[:k])]
        lost = [x for x in g if _hit(x, raw) and not _hit(x, pre)]
        in_pre = [x for x in g if _hit(x, pre)]
        rec = len(found) / len(g)
        recalls.append(rec)
        if lost:
            dropped_gold.append({"id": qid, "gold_dropped": lost})
        if in_pre and t["answer"]["declined"]:
            declined_gold.append({"id": qid, "gold_in_sources": in_pre})
        per_item.append({"id": qid, "recall": rec, "found": found, "gold": g, "gold_dropped": lost, "gold_in_pre": in_pre,
                         "pre_from": origin})
    n_traces = len(traces)
    legacy = sum(1 for t in traces.values() if t["runtime"].get("versions", {}).get("legacy"))
    desc = {
        "n_traces": n_traces,
        "items_with_shown_sources": sum(1 for t in traces.values() if t["answer"]["shown"]),
        "raw_mean": stats.mean(len(t["retrieval"]["raw"]) for t in traces.values()) if n_traces else None,
        "kept_mean": stats.mean(len(t["retrieval"]["kept"]) for t in traces.values()) if n_traces else None,
        "dropped_total": sum(len(t["retrieval"]["dropped"]) for t in traces.values()),
        "legacy_traces": legacy,
    }
    if not recalls:
        return {"status": "no gold", "k": k, "n_gold_items": 0, "n_traces": n_traces, "descriptive": desc,
                "line": f"no gold: 0/{n_traces} traced items have gold source titles"}
    return {
        "status": "ok", "k": k, "n_gold_items": len(recalls), "n_traces": n_traces,
        "recall_at_k": stats.mean(recalls), "recall_at_k_ci95": stats.bootstrap_ci(recalls, stats.mean, seed=seed),
        "n_on_topic_gold_dropped": len(dropped_gold), "on_topic_gold_dropped": dropped_gold,
        "n_declined_with_gold": len(declined_gold), "declined_with_gold": declined_gold, "pre_answer_from": origins,
        "items": per_item, "descriptive": desc,
        "line": f"recall@{k} {stats.mean(recalls):.2f} over {len(recalls)} items with gold; "
                f"on-topic gold dropped before the answer in {len(dropped_gold)}; declined with gold in sources {len(declined_gold)}",
    }
