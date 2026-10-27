# Arm `<label>` (<owner> <card id>): <one-line change>

TL;DR: <what changes, where (engine file / config only), base, kit, profile, bench (v0.1 for arms; never v0.2)>.

| | |
|---|---|
| Patch | `<label>.patch` sha256 `<64 hex>` (worktree `<workspace>/wt/<label>`, uncommitted); or "config-only" with the settings and their sha256 |
| Change | <the exact code or config delta, and any declared interpretation of the card, stated before any run> |
| Tests | <new tests, which of them fail on unpatched code, full-suite count, `tsc`> |

## Frozen criterion (copied verbatim from the card before any run)

<verbatim criterion + the coordinator's additions, with the date>

## Method rules (every arm)

- **Latency criteria (retrieval p50, TTFT, total time): measure base and arm in the same load window, interleaved** (base s42 → arm s42 → base s43 → arm s43, back to back on the shared mini), **or by a work count** (tokens, candidates read, passages scored). Never a single wall-clock reading against a base run from another time: the mini's 1-min load swings 17 → 27 (P-5, 2026-10-02: a first reading of 1.22× under a load mismatch; 1.08× load-matched). Report each run's median `runtime.loadAvg1m` next to the ratio.
- Replay-first arms: exact key-in-context with `--event-source-text`, at `pre`, tool sha pinned; stop before judging on a replay fail.
- Safety: rules v0.5 on both arms (base rescored); gate multi-base `--safety-version v0.5`; v0.5 `review` hits are not counted until the coordinator adjudicates them.
- Runner dir: your own (`BOAR_EVAL_RUNNER_DIR`), never `be/`.

## Runs

| Profile | Arm | Base |
|---|---|---|

## Results

(pending)
