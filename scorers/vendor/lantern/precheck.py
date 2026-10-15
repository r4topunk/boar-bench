#!/usr/bin/env python3
"""precheck v2: deterministic pre-check of BOAR answers against vitalik-evalset grading.

Statuses (one per answer):
  pass             must_any / must_k satisfied, nothing forbidden
  refused          the app declined (row.declined, or BOAR's refusal strings EN/PT, or a generic refusal);
                   counts as pass only where the item has refuse_ok=true
  confident-wrong  a forbid term matched (checked before refusal and must_any)
  fail-missing     answered, but the required facts are absent
  empty / missing  no answer text / no row

Grading fields (per item, `grading`):
  must_any  [[term, ...], ...]  every group needs >=1 hit
  must_k    {"k": n, "terms": [...]}  >= n distinct terms must hit (for "Tell me about X")
  forbid    [[term, ...], ...]  any hit -> confident-wrong
  refuse_ok bool
Terms: case-insensitive; plain terms need a word boundary at the start, and at the end only when they are
<=4 chars or end in a digit (so stems/plurals like "sampl", "inclusion list" still match);
"re:<regex>" is a Python regex (re.I | re.M). Plain must terms that appear in the question are ignored
(echo filter): repeating the question is not evidence. A group left empty by the echo filter never passes.

Usage:
  precheck.py <runs.jsonl> [--questions Q] [--subset S] [--json out.json]
  precheck.py --lint [--questions Q]
  precheck.py <runs.jsonl> --refusals   # + false-refusal audit (tools/refusal_audit.py, reads local pack copies)
Runs file: eval/ judge format, one row per question with queryId + answer (+ declined)."""
import argparse, json, re, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
DEFAULT_Q = HERE / "handoff" / "questions.vitalik-lantern.jsonl"

# Exact strings from boar-app src/routing/answer.ts (lines ~965-1243 at 14de107), EN and PT.
APP_REFUSALS = [
    "i didn't find this in this phone's library",
    "the passages found don't support this answer",
    "não encontrei isso no acervo deste celular",
    "os trechos encontrados não sustentam esta resposta",
]
GENERIC_REFUSAL = re.compile(
    r"(don't|do not|cannot|can't|couldn't|could not) (have|find|cover|answer)"
    r"|not (in|covered by) (my|the) (offline )?(sources|packs|library)"
    r"|no (offline )?sources? (cover|mention|say)"
    r"|não (encontrei|tenho|consigo)", re.I)

DETOK = [(re.compile(r"(\d)\. (\d)"), r"\1.\2"),      # "8. 3 billion" -> "8.3" (llama detokenizer spacing)
         (re.compile(r"(\d), (\d{3})\b"), r"\1,\2")]   # "4, 000" -> "4,000"

def norm(s):
    s = (s or "").replace("’", "'").replace("‘", "'").lower()
    for rx, rep in DETOK:
        s = rx.sub(rep, s)
    return s

def compile_term(t):
    if t.startswith("re:"):
        return re.compile(t[3:], re.I | re.M)
    t = norm(t)
    pre = r"\b" if t[:1].isalnum() else ""
    # trailing boundary only for short tokens and numbers ("yen", "300"); longer terms may be stems/plurals
    post = r"\b" if t[-1:].isalnum() and (len(t) <= 4 or t[-1:].isdigit()) else ""
    return re.compile(pre + re.escape(t) + post, re.I)

def hits(term, text):
    return bool(compile_term(term).search(text))

def is_echo(term, question):
    return not term.startswith("re:") and hits(term, question)

def refused(row, text):
    if row.get("declined"):
        return True
    head = text.strip()[:200]
    return any(s in head for s in APP_REFUSALS) or bool(GENERIC_REFUSAL.search(head))

def grade(q, row):
    g = q.get("grading", {})
    if row is None:
        return "missing", ""
    text = norm(row.get("answer"))
    question = norm(q.get("query") or q.get("question"))
    if not text.strip():
        return "empty", ""
    bad = [t for grp in g.get("forbid", []) for t in grp if hits(t, text)]
    if bad:
        return "confident-wrong", "; ".join(bad)
    if refused(row, text):
        return "refused", "ok" if g.get("refuse_ok") else "not-ok"
    missing = []
    for grp in g.get("must_any", []):
        live = [t for t in grp if not is_echo(t, question)]
        if not any(hits(t, text) for t in live):
            missing.append(live[0] if live else f"(echo-only group {grp})")
    mk = g.get("must_k")
    if mk:
        live = [t for t in mk["terms"] if not is_echo(t, question)]
        got = [t for t in live if hits(t, text)]
        if len(got) < mk["k"]:
            missing.append(f"must_k {len(got)}/{mk['k']} ({', '.join(got) or 'none'})")
    if missing:
        return "fail-missing", "; ".join(missing)
    return "pass", ""

def lint(qs):
    problems = 0
    for q in qs.values():
        g = q.get("grading", {})
        if g.get("type") == "venue-list":
            continue
        question = norm(q.get("query") or q.get("question"))
        msgs = []
        if not g.get("must_any") and not g.get("must_k"):
            msgs.append("no positive requirement (any on-topic text passes)")
        for grp in g.get("must_any", []):
            if all(is_echo(t, question) for t in grp):
                msgs.append(f"echo-only group {grp}")
        for grp in g.get("forbid", []) + g.get("must_any", []) + [g.get("must_k", {}).get("terms", [])]:
            for t in grp:
                try:
                    compile_term(t)
                except re.error as e:
                    msgs.append(f"bad regex {t}: {e}")
        if msgs:
            problems += 1
            print(f"{q['id']}\t{' | '.join(msgs)}")
    print(f"lint: {problems} item(s) with problems")
    return problems

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("runs", nargs="?")
    ap.add_argument("--questions", default=str(DEFAULT_Q))
    ap.add_argument("--subset")
    ap.add_argument("--json")
    ap.add_argument("--lint", action="store_true")
    ap.add_argument("--installed-packs", default="boar-crypto,boar-wikivoyage-en",
                    help="packs installed on the device for this run (refusal audit), comma list")
    ap.add_argument("--hand", help="JSON {id: {kind, why}} of hand verdicts that override the auto refusal kind")
    ap.add_argument("--refusals", action="store_true", help="classify refused rows: false-refusal / possible-false-refusal / correct-refusal / unknown-dropped")
    a = ap.parse_args()
    qs = {q["id"]: q for q in map(json.loads, open(a.questions))}
    if a.lint:
        sys.exit(1 if lint(qs) else 0)
    if not a.runs:
        ap.error("runs file required")
    keep = set(json.load(open(a.subset))["ids"]) if a.subset else None
    rows = {r["queryId"]: r for r in map(json.loads, open(a.runs))}
    if a.refusals:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        import refusal_audit
        refusal_audit.configure([x.strip() for x in a.installed_packs.split(",") if x.strip()])
        packs = refusal_audit.Packs()
        hand = {k: v for k, v in json.load(open(a.hand)).items() if not k.startswith("_")} if a.hand else {}
    ids = sorted(keep if keep is not None else rows.keys())
    res = []
    for qid in ids:
        q = qs.get(qid)
        if q is None or q.get("grading", {}).get("type") == "venue-list":
            continue
        v, why = grade(q, rows.get(qid))
        x = {"id": qid, "category": q["category"], "status": v, "why": why,
             "counts_as_pass": v == "pass" or (v == "refused" and why == "ok")}
        if a.refusals and v == "refused":
            x.update(refusal_audit.audit(q, rows[qid], packs, hits, is_echo, norm))
            x["auto_kind"] = x["refusal_kind"]
            if hand.get(qid):
                x["refusal_kind"], x["evidence"] = hand[qid]["kind"], "hand: " + hand[qid]["why"]
        res.append(x)
    for x in res:
        print(f"{x['id']}\t{x['status']}\t{x['why']}")
    n = len(res)
    c = lambda s: sum(1 for x in res if x["status"] == s)
    passed = sum(1 for x in res if x["counts_as_pass"])
    ref, ref_ok = c("refused"), sum(1 for x in res if x["status"] == "refused" and x["why"] == "ok")
    pct = lambda k: f"{k/max(n,1):.0%}"
    print(f"\nn={n}  pass={passed} ({pct(passed)}, incl. {ref_ok} refused where refuse_ok)  "
          f"refused={ref} ({pct(ref)})  confident-wrong={c('confident-wrong')} ({pct(c('confident-wrong'))})  "
          f"fail-missing={c('fail-missing')}  empty={c('empty')}  missing={c('missing')}")
    if a.refusals:
        refs = [x for x in res if x["status"] == "refused"]
        fr = sum(1 for x in refs if x["refusal_kind"] == "false-refusal")
        print(f"\nrefusals by kind (n={len(refs)}; false-refusal rate = {fr}/{len(refs)} of refusals, {fr}/{n} of answers):")
        for kind in ("false-refusal", "possible-false-refusal", "correct-refusal", "unknown-dropped"):
            ids = [x for x in refs if x["refusal_kind"] == kind]
            print(f"  {kind}: {len(ids)}")
            for x in ids:
                extra = x["evidence"] or ", ".join(x["answer_in_installed_pack"]) or "-"
                print(f"    {x['id']}\t{x['mechanism']}\trefuse_ok={x['why'] == 'ok'}\t{extra}")
    if a.json:
        json.dump(res, open(a.json, "w"), indent=1)

if __name__ == "__main__":
    main()
