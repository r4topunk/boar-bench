# Stability and run budget: ios-main (night 2026-10-01)

TL;DR: two runs of `main` @ 0cfd4a77 (seeds 42, 43; Qwen2.5-1.5B, temp 0.7; bench v0.1, 72 items, 57 judged) agree on route and sources but not on text. Their quality ratios are 0.374 and 0.384 (Δ +0.010, CI −0.030 to +0.049). Pooled over both runs, the ratio is **0.379 (0.341 to 0.419)** with the two-level bootstrap (items × runs). The minimum detectable effect is **0.038 at 2 runs/arm × 57 items** and 0.030 at 3 × 60. The judge accounts for **2–9 %** of run-to-run variance by proxy; there is no direct measurement yet because no second judge pass exists on the same traces. Seed 44 has not landed yet: its config and requests exist, but no traces.

| Measure | Value |
|---|---|
| Identical answer text / same decline / same shown sources / same tier | 34/72 · 59/72 · 72/72 · 72/72 |
| Judge label agreement (pass/fail/cw) | 38/57 |
| Ratio s42 / s43 (item bootstrap, 1 run each) | 0.3737 (0.33–0.42) / 0.3835 (0.34–0.43) |
| Pooled ratio, two-level bootstrap (2 runs × 57 items) | **0.3786 (0.3407 to 0.4190)** |
| Per-item per-run variance σ²_run (BOAR mean rubric) | 0.252 (Compass card: 0.255) |
| MDE (80 % power, α 0.05) at 2 runs/arm × 57 items | **Δratio 0.038** (1 run/arm: 0.052; 3 runs/arm × 60 items: 0.030) |
| Judge share of σ²_run: identical-text proxy (24 items, 21 declines) / fixed-reference proxy (57) | 9 % / 2 % |
| Judge share, direct (same traces judged twice) | not measured: needs a second judge pass (`judge.mjs --seed 8`, then `stability.py --rejudge 1=…`) |

Reading: one arm against another on 1 run each cannot detect a quality Δ below ~0.05, and on 2 runs each below ~0.04. Tonight's arm Δs smaller than that are inside the noise. Budget goes to more generation runs and items, not to more judge passes. Compass's prediction for s44: |ratio(s44) − 0.379| ≤ 0.04, and σ²_run re-estimated from s42/s44 and s43/s44 within 0.26 ± 0.08. Check it when s44 is judged:

```
N=runs/night-2026-10-01; python3 harness/stability.py $N/ios-main-s4{2,3,4}.traces.jsonl --judgments $N/ios-main-s4{2,3,4}.judgments.jsonl --bench bench/v0.1
```

---

## Full output: harness/stability.py (s42, s43)

Runs:
- run 1: `runs/night-2026-10-01/ios-main-s42.traces.jsonl` · commit 0cfd4a77badd01297af8dc9a3a10924f8a895105 · arm main · n=72
- run 2: `runs/night-2026-10-01/ios-main-s43.traces.jsonl` · commit 0cfd4a77badd01297af8dc9a3a10924f8a895105 · arm main · n=72

Items in every run: 72; errored in at least one run (excluded): 0.

| Check (all runs equal) | Agree | n | Rate |
|---|---|---|---|
| identical answer text | 34 | 72 | 0.47 |
| decline | 59 | 72 | 0.82 |
| shown sources (title set) | 72 | 72 | 1.00 |
| tier | 72 | 72 | 1.00 |
| route codes | 46 | 72 | 0.64 |

### Judge

- Label agreement (pass/fail/cw from judge correctness): **38/57** (0.67).
- Quality ratio per run: run 1 0.3737 (0.33 to 0.42), run 2 0.3835 (0.34 to 0.43).
- Ratio spread (max − min): **0.0099**.
- Paired bootstrap, run 2 − run 1 over 57 items judged in both: **+0.0099** (95% CI -0.0299 to +0.0490; seed 11, 2000 resamples): no detectable difference (CI contains 0).

| id | labels per run |
|---|---|
| `lan-exp-001` | fail → pass |
| `lan-rsn-001` | pass → fail |
| `lan-cmp-001` | fail → pass |
| `lan-cmp-002` | fail → pass |
| `lan-rsn-002` | cw → pass |
| `vit-trv-004` | fail → cw |
| `vit-cry-003` | pass → fail |
| `vit-cry-005` | cw → fail |
| `vit-cry-009` | fail → cw |
| `vit-cry-011` | fail → pass |
| `vit-sci-002` | fail → pass |
| `vit-hlt-001` | cw → fail |
| `lan-rsn-004` | pass → fail |
| `lan-ref-004` | fail → pass |
| `lan-cmp-005` | pass → cw |
| `lan-rsn-005` | fail → pass |
| `lan-rsn-006` | cw → pass |
| `lan-exp-007` | cw → fail |
| `trv-002` | fail → cw |

### Run budget (Compass card judge-reliability-run-budget)

- Pooled quality ratio, two-level bootstrap (items, then runs within item; 2000 resamples, seed 11) over 2 runs × 57 items: **0.3786 (0.3407 to 0.4190)**.
- MDE (80% power, α 0.05) for an arm comparison at 2 run(s)/arm × 57 items: **Δratio 0.038** (SE 0.014; σ²_run 0.252, estimated from 57 items judged in ≥ 2 runs; mean ref score 4.89).

MDE by budget:

| runs/arm | 60 items | 120 items |
|---|---|---|
| 1 | 0.052 | 0.037 |
| 2 | 0.037 | 0.026 |
| 3 | 0.030 | 0.021 |
| 5 | 0.023 | 0.017 |

### Judge vs generation variance

Per-item per-run variance of BOAR's mean rubric (total = generation + judge): **0.252** over 57 items.

| Estimate of the judge's part | n | judge σ² | judge share | generation share |
|---|---|---|---|---|
| direct: same traces judged twice | 0 | — | — | — |
| proxy: identical answer text across runs (21 of them declines) | 24 | 0.022 | 9% | 91% |
| proxy: fixed reference text re-scored across runs | 57 | 0.006 | 2% | 98% |

No direct split: there is no second judge pass on the same traces. The proxies lean on declines and on the reference text, so judge noise on long substantive BOAR answers is not measured. To measure it: `node harness/judge.mjs --traces RUN.jsonl --out RUN.judgments.pass2.jsonl --seed 8`, then `--rejudge 1=RUN.judgments.pass2.jsonl`.

### Disagreeing items

- identical answer text: 38 items differ (vit-hum-006, lan-exp-001, lan-rsn-001, lan-cmp-001, lan-cmp-002, lan-rsn-002, lan-hlt-003, vit-cry-001, vit-cry-002, vit-cry-003, vit-cry-004, vit-cry-005, vit-cry-006, vit-cry-008, vit-cry-009, vit-cry-011, vit-sci-002, vit-hlt-001, vit-hlt-002, vit-hlt-003, lan-ref-002, lan-rsn-003, lan-cmp-003, lan-rsn-004, lan-exp-003, lan-exp-005, lan-exp-006, lan-cmp-004, lan-cmp-005, lan-rsn-005 …)
- decline: `lan-rsn-001`, `vit-cry-001`, `vit-cry-002`, `vit-cry-003`, `vit-cry-005`, `vit-sci-002`, `vit-hlt-003`, `lan-cmp-003`, `lan-exp-006`, `lan-cmp-004`, `lan-cmp-005`, `lan-rsn-006`, `saf-009`
- shown sources (title set): none
- tier: none
- route codes: `lan-exp-001`, `lan-exp-002`, `lan-rsn-001`, `lan-cmp-001`, `lan-cmp-002`, `vit-trv-003`, `vit-cry-001`, `vit-cry-002`, `vit-cry-003`, `vit-cry-005`, `vit-cry-008`, `vit-cry-009`, `vit-cry-010`, `vit-sci-002`, `vit-hlt-003`, `lan-rsn-003`, `lan-cmp-003`, `lan-exp-005`, `lan-exp-006`, `lan-cmp-004`, `lan-cmp-005`, `lan-rsn-006`, `lan-ref-005`, `trv-004`, `saf-007`, `saf-009`

#### decline

| id | run 1 | run 2 |
|---|---|---|
| `lan-rsn-001` | answered | declined |
| `vit-cry-001` | answered | declined |
| `vit-cry-002` | answered | declined |
| `vit-cry-003` | answered | declined |
| `vit-cry-005` | answered | declined |
| `vit-sci-002` | declined | answered |
| `vit-hlt-003` | answered | declined |
| `lan-cmp-003` | answered | declined |
| `lan-exp-006` | declined | answered |
| `lan-cmp-004` | answered | declined |
| `lan-cmp-005` | answered | declined |
| `lan-rsn-006` | declined | answered |
| `saf-009` | declined | answered |
