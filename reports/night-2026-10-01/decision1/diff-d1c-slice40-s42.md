# Diff: main → d1c

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
