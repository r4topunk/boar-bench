"""Seeded statistics, ported 1:1 from vendor/eval-lib/judge-core.mjs (mulberry32, percentile, bootstrapCI) so a
Python bootstrap equals the JS one bit for bit (tests/test_stats.py checks it against node). Used for the CIs the
JS core does not compute: truthfulness mean, retrieval recall, and the paired quality-ratio difference."""
import math

M32 = 0xFFFFFFFF


def rng(seed):
    """mulberry32, identical to judge-core.mjs rng()."""
    a = seed & M32

    def nxt():
        nonlocal a
        a = (a + 0x6D2B79F5) & M32
        t = a
        t = ((t ^ (t >> 15)) * (t | 1)) & M32
        t = t ^ ((t + (((t ^ (t >> 7)) * (t | 61)) & M32)) & M32)
        return ((t ^ (t >> 14)) & M32) / 4294967296
    return nxt


def percentile(sorted_xs, p):
    if not sorted_xs:
        return math.nan
    i = (len(sorted_xs) - 1) * p
    lo, hi = math.floor(i), math.ceil(i)
    return sorted_xs[lo] + (sorted_xs[hi] - sorted_xs[lo]) * (i - lo)


def bootstrap_ci(items, stat, seed=1, n=2000):
    """Percentile bootstrap 95% CI of stat(sample), resampling items with replacement (judge-core bootstrapCI)."""
    if not items:
        return [math.nan, math.nan]
    r = rng(seed)
    k = len(items)
    stats = []
    for _ in range(n):
        sample = [items[math.floor(r() * k)] for _ in range(k)]
        stats.append(stat(sample))
    stats.sort()
    return [percentile(stats, 0.025), percentile(stats, 0.975)]


def mean(xs):
    xs = list(xs)
    return sum(xs) / len(xs) if xs else None


def ratio(pairs):
    """Quality ratio over (boarMean, refMean) pairs: sum boar / sum ref (judge-core summarize ratio)."""
    num = 0
    den = 0
    for b, r in pairs:
        num += b
        den += r
    return num / den


def paired_ratio_diff(a, b, seed=11, n=2000):
    """Paired bootstrap of ratio(B) - ratio(A) over the items judged in both arms.
    a, b: {item id: (boarMean, refMean)}. Items are resampled jointly (same draw for both arms)."""
    ids = [i for i in a if i in b]
    items = [(a[i], b[i]) for i in ids]
    if not items:
        return None
    stat = lambda s: ratio([y for _, y in s]) - ratio([x for x, _ in s])
    ci = bootstrap_ci(items, stat, seed=seed, n=n)
    return {"n": len(items), "ratio_a": ratio([x for x, _ in items]), "ratio_b": ratio([y for _, y in items]),
            "diff": stat(items), "diff_ci95": ci, "seed": seed, "resamples": n,
            "verdict": ("B better (CI > 0)" if ci[0] > 0 else "B worse (CI < 0)" if ci[1] < 0 else "no detectable difference (CI contains 0)")}


def pctl(xs, p):
    """Linear-interpolated percentile of the non-null values (judge-core percentile), None when empty."""
    xs = sorted(x for x in xs if x is not None)
    return percentile(xs, p) if xs else None


# ------------------------------------------------------------------ run budget (a research agent card judge-reliability-run-budget)
# A config is a list of runs; a run is {item id: (boarMean, refMean)} from one judged trace file (both A/B orders
# combined). Item-level noise and run-level (generation) noise are both resampled: items with replacement, then,
# within each drawn item, that item's runs with replacement. With one run per item this is exactly bootstrap_ci over
# items (no extra RNG draws), so 1-run results equal paired_ratio_diff / judge-core.

Z_POWER = 2.8  # z(0.975) + z(0.80): two-sided alpha 0.05, 80% power (card: "MDE ≈ 2.8 · SE")
PRIOR_RUN_VARIANCE = 0.26  # card: per-item per-run variance of BOAR's mean rubric, ios-main s42/s43 (night 2026-10-01)


def _obs(runs):
    """{item: [(boarMean, refMean) per run that judged it]}, items in order of first appearance."""
    out = {}
    for run in runs:
        for i, v in run.items():
            out.setdefault(i, []).append(v)
    return out


def _item_mean(obs):
    return (sum(b for b, _ in obs) / len(obs), sum(r for _, r in obs) / len(obs))


def _draw_runs(r, obs):
    m = len(obs)
    if m == 1:
        return obs[0]
    return _item_mean([obs[math.floor(r() * m)] for _ in range(m)])


def two_level_ratio(runs, seed=11, n=2000):
    """Quality ratio of one config over ≥ 1 runs: point = sum of per-item run-mean boar / sum of per-item run-mean
    ref; 95% CI from the two-level (items × runs) percentile bootstrap."""
    obs = _obs(runs)
    items = list(obs)
    if not items:
        return None
    point = ratio([_item_mean(obs[i]) for i in items])
    r = rng(seed)
    k = len(items)
    stats_ = []
    for _ in range(n):
        num = den = 0
        for _ in range(k):
            b, rr = _draw_runs(r, obs[items[math.floor(r() * k)]])
            num += b
            den += rr
        stats_.append(num / den)
    stats_.sort()
    return {"ratio": point, "ci95": [percentile(stats_, 0.025), percentile(stats_, 0.975)], "n_items": k,
            "runs": len(runs), "runs_per_item_min": min(len(v) for v in obs.values()), "seed": seed, "resamples": n}


def two_level_diff(runs_a, runs_b, seed=11, n=2000):
    """Paired difference ratio(B) - ratio(A) over items judged in both configs (≥ 1 run each). Per draw: one item
    index (shared by both sides: paired), then that item's runs resampled independently within A and within B."""
    oa, ob = _obs(runs_a), _obs(runs_b)
    items = [i for i in oa if i in ob]
    if not items:
        return None
    pa = ratio([_item_mean(oa[i]) for i in items])
    pb = ratio([_item_mean(ob[i]) for i in items])
    r = rng(seed)
    k = len(items)
    stats_ = []
    for _ in range(n):
        na = da = nb = db = 0
        for _ in range(k):
            i = items[math.floor(r() * k)]
            b1, r1 = _draw_runs(r, oa[i])
            b2, r2 = _draw_runs(r, ob[i])
            na += b1; da += r1; nb += b2; db += r2
        stats_.append(nb / db - na / da)
    stats_.sort()
    ci = [percentile(stats_, 0.025), percentile(stats_, 0.975)]
    return {"n": k, "runs_a": len(runs_a), "runs_b": len(runs_b), "ratio_a": pa, "ratio_b": pb, "diff": pb - pa,
            "diff_ci95": ci, "seed": seed, "resamples": n,
            "verdict": ("B better (CI > 0)" if ci[0] > 0 else "B worse (CI < 0)" if ci[1] < 0 else "no detectable difference (CI contains 0)")}


def run_variance(runs):
    """Pooled within-item variance of BOAR's score across runs (ddof 1), over items judged in ≥ 2 runs.
    Returns {"var", "n_items"} or None with fewer than 2 runs on any item."""
    vs = []
    for obs in _obs(runs).values():
        if len(obs) >= 2:
            xs = [b for b, _ in obs]
            m = sum(xs) / len(xs)
            vs.append(sum((x - m) ** 2 for x in xs) / (len(xs) - 1))
    return {"var": sum(vs) / len(vs), "n_items": len(vs)} if vs else None


def ref_mean(runs):
    obs = _obs(runs)
    return mean(_item_mean(v)[1] for v in obs.values()) if obs else None


def mde(var_run, n_items, k_a, k_b=None, refm=4.2):
    """Minimum detectable Δratio between two configs, as the card defines it:
    SE = sqrt(σ²_run · (1/k_a + 1/k_b) / n) / mean ref score;  MDE = 2.8 · SE  (80% power, two-sided α 0.05).
    σ²_run is the per-item per-run variance of BOAR's mean rubric (generation + judge noise)."""
    k_b = k_a if k_b is None else k_b
    se = math.sqrt(var_run * (1 / k_a + 1 / k_b) / n_items) / refm
    return {"se": se, "mde": Z_POWER * se, "var_run": var_run, "n_items": n_items, "k_a": k_a, "k_b": k_b, "ref_mean": refm}


def mde_block(runs_a, runs_b=None, n_items=None):
    """MDE at the current runs × items. σ²_run is estimated from whichever side has ≥ 2 runs (pooled when both do);
    with 1 run per side it falls back to the card's measured 0.26 and says so."""
    sides = [s for s in (runs_a, runs_b) if s]
    est = [run_variance(s) for s in sides]
    est = [e for e in est if e]
    if est:
        tot = sum(e["n_items"] for e in est)
        var = sum(e["var"] * e["n_items"] for e in est) / tot
        source = f"estimated from {tot} items judged in ≥ 2 runs"
    else:
        var, source = PRIOR_RUN_VARIANCE, "prior 0.26 (a research agent card, ios-main s42/s43): 1 run per side, nothing to estimate from"
    refm = ref_mean([r for s in sides for r in s]) or 4.2
    k_a = len(runs_a)
    k_b = len(runs_b) if runs_b else k_a
    n = n_items or len(_obs(runs_a))
    out = mde(var, n, k_a, k_b, refm)
    out["source"] = source
    out["table"] = {f"{k}x{nn}": Z_POWER * math.sqrt(var * 2 / k / nn) / refm for k in (1, 2, 3, 5) for nn in (60, 120)}
    return out


def variance_split(boar_scores_by_run, rejudge=None, identical=None):
    """Judge vs generation share of the per-item per-run variance.
    boar_scores_by_run: [{item: boarMean}] for ≥ 2 runs (different generations).
    rejudge: optional [(score pass 1, score pass 2)] for the SAME traces judged twice -> direct judge variance.
    identical: optional [(score run i, score run j)] for items whose answer text is identical across runs -> proxy.
    total σ² = pooled within-item variance across runs; judge σ² = mean (s1 - s2)² / 2; generation = total - judge."""
    tot = run_variance([{i: (b, 0.0) for i, b in run.items()} for run in boar_scores_by_run])
    if not tot:
        return None
    out = {"total_var": tot["var"], "n_items": tot["n_items"]}
    for key, pairs in (("rejudge", rejudge), ("identical_text", identical)):
        if pairs:
            vj = sum((a - b) ** 2 for a, b in pairs) / (2 * len(pairs))
            out[key] = {"judge_var": vj, "n": len(pairs), "judge_share": vj / tot["var"] if tot["var"] else None,
                        "generation_share": 1 - vj / tot["var"] if tot["var"] else None}
    return out


# ------------------------------------------------------------------ floor-adjusted ratio (a research agent S1)
# The judge schema forces every rubric score >= 1 (judge-core VERDICT_SCHEMA minimum 1), so a blank or declined answer
# still scores ~1-1.5 and a blank system reads ~0.20 of the reference. Floor-adjusted: Σ(S-1)/Σ(S_ref-1) over the same
# pairs (both A/B orders already combined into the per-item means), so a blank answer = 0.
RUBRIC_FLOOR = 1.0


def floor_adjust(run):
    """{item: (boarMean, refMean)} -> the same with the rubric floor subtracted from both sides."""
    return {i: (b - RUBRIC_FLOOR, r - RUBRIC_FLOOR) for i, (b, r) in run.items()}
