# Diff: main → d1c

Runs: A `runs/night-2026-10-01/ios-main-s42.traces.jsonl`, `runs/night-2026-10-01/ios-main-s43.traces.jsonl` · B `runs/night-2026-10-01/d1/ios-d1c-q72-s42.traces.jsonl`, `runs/night-2026-10-01/d1/ios-d1c-q72-s43.traces.jsonl`

- A (main): `runs/night-2026-10-01/ios-main-s42.traces.jsonl` · commit 0cfd4a77badd01297af8dc9a3a10924f8a895105 · arm main · n=72
- B (d1c): `runs/night-2026-10-01/d1/ios-d1c-q72-s42.traces.jsonl` · commit 0cfd4a77badd01297af8dc9a3a10924f8a895105 · arm d1c-pt-keywords · n=72

| | main | d1c |
|---|---|---|
| items (shared) | 72 | 72 |
| errors | 0 | 0 |
| declined | 25/72 | 25/72 |
| weak_sources | 35/72 | 35/72 |
| no shown sources | 27/72 | 27/72 |
| tier | {'fast': 62, 'instant': 10} | {'fast': 62, 'instant': 10} |
| TTFT p50 / p95 (desktop) | 1.50 s / 3.21 s | 1.46 s / 3.10 s |
| total p50 / p95 (desktop) | 2.57 s / 4.28 s | 2.51 s / 4.24 s |
| retrieval p50 (desktop) | 0.08 s | 0.08 s |

Identical answer text: **72/72** · items that lost their shown sources: **0**.
Latency is desktop (desktop-node): relative between arms on the same host, not a phone number.

## Quality (paired)

Quality ratio over 57 items judged on both sides, 2 run(s) A × 2 run(s) B: A 0.3786 → B 0.3786; **Δ +0.0000 (95% CI -0.0197 to +0.0183)**, paired two-level bootstrap (items, then runs within item; 2000 resamples, seed 11): no detectable difference (CI contains 0).

MDE (80% power, α 0.05) for an arm comparison at 2 run(s)/arm × 57 items: **Δratio 0.038** (SE 0.014; σ²_run 0.252, estimated from 114 items judged in ≥ 2 runs; mean ref score 4.89).

**|Δ| 0.000 < MDE 0.038: inside the noise at this budget; not decidable on quality.**

MDE by budget:

| runs/arm | 60 items | 120 items |
|---|---|---|
| 1 | 0.052 | 0.037 |
| 2 | 0.037 | 0.026 |
| 3 | 0.030 | 0.021 |
| 5 | 0.023 | 0.017 |

**Worse: 0**


**Better: 0**


**Other changes (same decline/source status): 0**

