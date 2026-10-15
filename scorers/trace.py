"""EvalTrace jsonl reader (protocol 1.0.0, packages/protocol/src/index.ts) and the per-trace predicates every
scorer and harness command shares. Stdlib only: the structural check mirrors the Zod schema's required keys and
types; the Zod schema stays the contract (scorers/tests/test_convert.py validates fixtures against it with node)."""
import hashlib, json
from pathlib import Path

PROTOCOL_VERSION = "1.0.0"
NO_SOURCE_CARD = "grounding:health-no-source"
HEALTH_STRICT = "grounding:health-strict"

_REQUIRED = {
    "": ["protocol", "runId", "itemId", "question", "engine", "runtime", "config", "route", "retrieval", "answer", "timing", "createdAt"],
    "engine": ["commit", "arm"],
    "runtime": ["adapter", "host", "model", "sampler"],
    "config": ["commit", "modelId", "device"],
    "route": ["task", "tier", "outcome", "reasonCodes"],
    "retrieval": ["raw", "kept", "dropped"],
    "answer": ["text", "cited", "shown", "declined", "weakSources"],
    "timing": ["ttftMs", "totalMs", "retrievalMs", "prefillMs", "decodeTokPerSec", "promptTokens", "outputTokens"],
}
ADAPTERS = {"desktop-node", "ios-app", "android-app", "reference-cli"}  # reference-cli: anchors (harness/anchors.mjs)


class TraceError(ValueError):
    pass


def check_trace(t, where="trace"):
    """Raises TraceError on the first structural problem (missing key, wrong protocol, wrong basic type)."""
    if not isinstance(t, dict):
        raise TraceError(f"{where}: not an object")
    for sect, keys in _REQUIRED.items():
        obj = t if not sect else t.get(sect)
        if not isinstance(obj, dict):
            raise TraceError(f"{where}: '{sect}' missing or not an object")
        for k in keys:
            if k not in obj:
                raise TraceError(f"{where}: missing {sect + '.' if sect else ''}{k}")
    if t["protocol"] != PROTOCOL_VERSION:
        raise TraceError(f"{where}: protocol {t['protocol']!r} != {PROTOCOL_VERSION}")
    if t["runtime"]["adapter"] not in ADAPTERS:
        raise TraceError(f"{where}: runtime.adapter {t['runtime']['adapter']!r}")
    if not isinstance(t["answer"]["declined"], bool):
        raise TraceError(f"{where}: answer.declined must be a boolean")
    for k in ("raw", "kept", "dropped"):
        if not isinstance(t["retrieval"][k], list) or any(not isinstance(s, dict) or "title" not in s for s in t["retrieval"][k]):
            raise TraceError(f"{where}: retrieval.{k} must be a list of SourceRef")
    if not isinstance(t["answer"]["text"], str):
        raise TraceError(f"{where}: answer.text must be a string")
    return t


def read_traces(path):
    """One EvalTrace per line; the last trace per itemId wins (resumed runs). Returns {itemId: trace} in file order
    of first appearance."""
    out = {}
    for n, line in enumerate(Path(path).read_text().splitlines(), 1):
        if not line.strip():
            continue
        t = check_trace(json.loads(line), f"{path}:{n}")
        out[t["itemId"]] = t
    return out


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


# ------------------------------------------------------------------ predicates
def declined(t):
    return bool(t["answer"]["declined"])


def shown(t):
    return list(t["answer"]["shown"])


def codes(t):
    return list(t["route"]["reasonCodes"] or [])


def errored(t):
    return t.get("error") is not None


def card(t):
    """The health no-source card (exp-08c): a deliberate non-answer, not a memory answer."""
    return NO_SOURCE_CARD in codes(t)


def memory_answer(t):
    """Answered from the model's memory: not declined, no shown sources, not the no-source card, no error."""
    return not declined(t) and not shown(t) and not card(t) and not errored(t)


def state(t):
    if errored(t):
        return "ERROR"
    if card(t):
        return "CARD"
    if declined(t):
        return "declined"
    return f"answered+{len(shown(t))}src" if shown(t) else "MEMORY"


def adapters(traces):
    return sorted({t["runtime"]["adapter"] for t in traces.values()})


def is_desktop(traces):
    return adapters(traces) == ["desktop-node"]
