"""Shared helpers for the harness commands (report, diff, gate, stability). Every command reads EvalTrace only."""
import sys
from pathlib import Path

sys.dont_write_bytecode = True
REPO = Path(__file__).resolve().parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from scorers.trace import codes, declined, errored, shown  # noqa: E402

VOLATILE_CODE_PREFIXES = ("context:",)  # token counts: they move with any prompt change, not a route change


def route_codes(t):
    """Reason codes without the volatile ones, as a sorted list (route comparison key)."""
    return sorted({c for c in codes(t) if not c.startswith(VOLATILE_CODE_PREFIXES)})


def titles(refs):
    return [r["title"] + (f"#{r['section']}" if r.get("section") else "") for r in refs]


def run_label(traces, path):
    ts = list(traces.values())
    if not ts:
        return f"`{path}` (empty)"
    commits = sorted({t["engine"]["commit"] for t in ts})
    arms = sorted({t["engine"]["arm"] for t in ts})
    return f"`{path}` · commit {', '.join(commits)} · arm {', '.join(arms)} · n={len(ts)}"


def fmt(x, nd=2):
    return "n/a" if x is None else f"{x:.{nd}f}"


def fmt_ms(v):
    return "—" if v is None else f"{v / 1000:.2f} s"


def ci(c, nd=2):
    return "—" if not c or c[0] is None else f"{c[0]:.{nd}f} to {c[1]:.{nd}f}"


def cell(s, n=160):
    return str(s).replace("|", "/").replace("\n", " ")[:n]


def short(text, n=140):
    return cell(text, n) if text else "—"


def write_out(md, out):
    if out:
        Path(out).parent.mkdir(parents=True, exist_ok=True)
        Path(out).write_text(md)
    else:
        sys.stdout.write(md)


__all__ = ["REPO", "route_codes", "titles", "run_label", "fmt", "fmt_ms", "ci", "cell", "short", "write_out",
           "codes", "declined", "errored", "shown"]


def pair_scores(judge_result):
    """Bridge judge result -> {item: (boarMean, refMean)} (both A/B orders combined)."""
    return {p["queryId"]: (p["boarMean"], p["refMean"]) for p in judge_result["pairs"]}


def mde_text(m):
    return (f"MDE (80% power, α 0.05) for an arm comparison at {m['k_a']}"
            + (f" vs {m['k_b']}" if m["k_b"] != m["k_a"] else "") + f" run(s)/arm × {m['n_items']} items: **Δratio {m['mde']:.3f}** "
            f"(SE {m['se']:.3f}; σ²_run {m['var_run']:.3f}, {m['source']}; mean ref score {m['ref_mean']:.2f})")


def mde_table(m):
    t = m["table"]
    return ["| runs/arm | 60 items | 120 items |", "|---|---|---|"] + [
        f"| {k} | {t[f'{k}x60']:.3f} | {t[f'{k}x120']:.3f} |" for k in (1, 2, 3, 5)]
