# Diff: main → d1c

Runs: A `runs/night-2026-10-01/d1/ios-main-slice40-s42.traces.jsonl`, `runs/night-2026-10-01/d1/ios-main-slice40-s43.traces.jsonl` · B `runs/night-2026-10-01/d1/ios-d1c-slice40-s42.traces.jsonl`, `runs/night-2026-10-01/d1/ios-d1c-slice40-s43.traces.jsonl`

- A (main): `runs/night-2026-10-01/d1/ios-main-slice40-s42.traces.jsonl` · commit 0cfd4a77badd01297af8dc9a3a10924f8a895105 · arm main · n=40
- B (d1c): `runs/night-2026-10-01/d1/ios-d1c-slice40-s42.traces.jsonl` · commit 0cfd4a77badd01297af8dc9a3a10924f8a895105 · arm d1c-pt-keywords · n=40

| | main | d1c |
|---|---|---|
| items (shared) | 40 | 40 |
| errors | 0 | 0 |
| declined | 21/40 | 20/40 |
| weak_sources | 22/40 | 21/40 |
| no shown sources | 2/40 | 2/40 |
| tier | {'fast': 39, 'instant': 1} | {'fast': 39, 'instant': 1} |
| TTFT p50 / p95 (desktop) | 2.60 s / 3.65 s | 2.61 s / 3.61 s |
| total p50 / p95 (desktop) | 3.85 s / 5.63 s | 3.91 s / 5.52 s |
| retrieval p50 (desktop) | 0.10 s | 0.13 s |

Identical answer text: **39/40** · items that lost their shown sources: **0**.
Latency is desktop (desktop-node): relative between arms on the same host, not a phone number.

## Quality (paired)

Quality ratio over 40 items judged on both sides, 2 run(s) A × 2 run(s) B: A 0.3226 → B 0.3329; **Δ +0.0103 (95% CI -0.0104 to +0.0427)**, paired two-level bootstrap (items, then runs within item; 2000 resamples, seed 11): no detectable difference (CI contains 0).

MDE (80% power, α 0.05) for an arm comparison at 2 run(s)/arm × 40 items: **Δratio 0.039** (SE 0.014; σ²_run 0.178, estimated from 80 items judged in ≥ 2 runs; mean ref score 4.77).

**|Δ| 0.010 < MDE 0.039: inside the noise at this budget; not decidable on quality.**

MDE by budget:

| runs/arm | 60 items | 120 items |
|---|---|---|
| 1 | 0.045 | 0.032 |
| 2 | 0.032 | 0.023 |
| 3 | 0.026 | 0.018 |
| 5 | 0.020 | 0.014 |

| id | judge label A → B | correctness A → B |
|---|---|---|
| `lan-rsn-001-pt` | cw → fail | 1 → 2 |

**Worse: 0**


**Better: 1**

| id | change | codes main | codes d1c | shown main | shown d1c |
|---|---|---|---|---|---|
| `lan-rsn-001-pt` | declined True→False; kept 0→3; dropped 4→1; route codes; answer text | citations:removed-1, generate:user-model-qwen2.5-1.5b-instruct-q4km, grounding:all-citations-removed-declined-compact, instant:preview, instant:source-language-lead, match:pt-en-names, offer-deep:multipass, retrieve:yes, task:chat | citations:pt-en-lexicon-kept, generate:user-model-qwen2.5-1.5b-instruct-q4km, instant:preview, instant:source-language-lead, match:pt-en-names, offer-deep:multipass, retrieve:yes, task:chat | Wikivoyage: Great Wall of China · Wikivoyage: Great Wall of China · Wikivoyage: Great Wall of China | Wikivoyage: Great Wall of China · Wikivoyage: Great Wall of China · Wikivoyage: Great Wall of China |

**Other changes (same decline/source status): 0**


## Answer text changes

| id | main | d1c |
|---|---|---|
| `lan-rsn-001-pt` | Os trechos encontrados não sustentam esta resposta. | A Muralha da China, também conhecida como "Great Wall of China", tem aproximadamente 15,000 quilômetros de comprimento total. [1] |
