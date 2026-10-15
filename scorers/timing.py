"""Visible time to first text, from the trace's event stream.

trace.timing.ttftMs is the receipt's first-token time. It counts an EMPTY first token, so for a thinking model (Gemma,
fast-tier thinking budget) it marks the start of hidden reasoning, not the first text the user sees (night 2026-10-01:
receipt 4.4 s vs first visible text 21-23 s; a research agent). Here:
  ttft_visible_ms  tMs of the first event that puts non-whitespace text on screen: a `token` with visible text, or an
                   `instant` snippet; else the `done` event when its finalText (or, with no token events, answer.text) is non-empty and no generated text was
                   lost to event truncation (declines, instant-only answers). None when unknowable.
  ttft_receipt_ms  trace.timing.ttftMs (kept for comparison)
  hidden_think_ms  first VISIBLE token tMs - first token tMs (any text), when > 0: generation time the user does not
                   see. 0 when the first token is already visible; None without token events.
"""


def _text(e):
    if e.get("type") == "token":
        return e.get("text") or ""
    if e.get("type") == "instant":
        s = e.get("snippet")
        return (s.get("text") if isinstance(s, dict) else s) or ""
    return ""


def visible_timing(t):
    ev = t.get("events") or []
    toks = [e for e in ev if e.get("type") == "token"]
    first_tok = toks[0]["tMs"] if toks else None
    vis_tok = next((e["tMs"] for e in toks if _text(e).strip()), None)
    vis = next((e["tMs"] for e in ev if e.get("type") in ("token", "instant") and _text(e).strip()), None)
    source = "event" if vis is not None else None
    if vis is None:
        out_toks = (t.get("timing") or {}).get("outputTokens") or 0
        truncated = bool(toks) and out_toks > len(toks)
        done = next((e for e in reversed(ev) if e.get("type") == "done"), None)
        shown_text = (done or {}).get("finalText") or ((t.get("answer") or {}).get("text") if not toks else "")
        if done and (shown_text or "").strip() and not truncated:
            vis, source = done["tMs"], "done"
    hidden = None
    if first_tok is not None:
        hidden = max(0.0, vis_tok - first_tok) if vis_tok is not None else None
    return {"ttft_visible_ms": vis, "ttft_receipt_ms": (t.get("timing") or {}).get("ttftMs"), "hidden_think_ms": hidden,
            "first_token_ms": first_tok, "visible_from": source}
