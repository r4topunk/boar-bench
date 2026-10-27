# Calibration ladder: BOAR vs Claude answering from memory (bench v0.1)

Every row is judged the same way: `harness/judge.mjs` (judge.v1, judge = Opus, pairwise, both A/B orders, blind) against the frozen **Opus + web** references of bench v0.1, over the 57 non-venue items. Anchors are Claude models run by `harness/anchors.mjs`: `claude -p`, **no tools, no web**, system prompt `anchor.v1` = the reference prompt `reference.v1` minus its web lines, user prompt = the bare question. The only differences vs the reference are web access and the model.

- **raw** = Σ S / Σ S_ref (judge-core ratio). Reference itself (Opus + web) = 1.000 by construction.
- **floor-adj** = Σ(S−1)/Σ(S_ref−1): removes the judge's rubric floor of 1 (a blank answer = 0).
- **above decline** = (raw − 0.306)/(1 − 0.306): share of the gap between an always-decline system (raw 0.306, `../rnd/research/QUEUE.md`, 79 judged declines at 1.50/5) and the reference. CI = the raw CI mapped through the same line.
- 95% CI: two-level bootstrap (items, then runs within item; 2,000 resamples, seed 11). **Anchors: one run each**, so their CI is an item bootstrap only (generation noise not represented; BOAR's σ²_run ≈ 0.25 suggests ±0.02–0.03 more).

## Ladder (ordered by raw ratio)

| # | System | runs × items | raw (95% CI) | floor-adj (95% CI) | above decline (95% CI) | source |
|---|---|---|---|---|---|---|
| — | **Opus + web (the reference)** | — | 1.000 (by construction) | 1.000 | 1.000 | `bench/v0.1/refs/` |
| 1 | **Claude fable, no web (anchor) · `claude-fable-5-1`** | 1 × 57 | 1.048 (1.022–1.076) | 1.061 (1.028–1.098) | 1.069 (1.032–1.110) | `runs/anchors-2026-10-02/fable.judgments.jsonl` |
| 2 | **Claude opus, no web (anchor) · `claude-opus-5-5`** | 1 × 57 | 1.029 (1.007–1.053) | 1.036 (1.009–1.069) | 1.041 (1.010–1.077) | `runs/anchors-2026-10-02/opus.judgments.jsonl` |
| 3 | **Claude sonnet, no web (anchor) · `claude-sonnet-5-5`** | 1 × 57 | 0.950 (0.913–0.990) | 0.937 (0.890–0.987) | 0.929 (0.874–0.986) | `runs/anchors-2026-10-02/sonnet.judgments.jsonl` |
| 4 | **Claude haiku, no web (anchor) · `claude-haiku-4-5-20251001`** | 1 × 57 | 0.653 (0.603–0.704) | 0.564 (0.502–0.627) | 0.500 (0.428–0.573) | `runs/anchors-2026-10-02/haiku.judgments.jsonl` |
| 5 | Android Qwen3-4B, kit A (desktop proxy) | 2 × 57 | 0.512 (0.461–0.567) | 0.387 (0.324–0.456) | 0.297 (0.224–0.376) | `reports/night-2026-10-01/and-qwen.md`; cited 0.512 |
| 6 | Android Gemma 4 E4B (desktop proxy, not adopted) | 2 × 57 | 0.496 (0.451–0.545) | 0.367 (0.311–0.428) | 0.274 (0.209–0.344) | `reports/night-2026-10-01/and-gemma-s42.md`; cited 0.496 |
| 7 | iPhone Qwen2.5-1.5B, desktop proxy (v5) | 2 × 57 | 0.395 (0.352–0.443) | 0.240 (0.186–0.300) | 0.128 (0.067–0.198) | `reports/night-2026-10-01/ios-main-v5.md`; cited 0.395 |
| 8 | iPhone Qwen2.5-1.5B, device (q15) | 2 × 57 | 0.394 (0.353–0.441) | 0.239 (0.187–0.298) | 0.127 (0.068–0.195) | `reports/devices-2026-10-02/ios-q15.md`; cited 0.394 |
| 9 | Always-decline (every answer a decline) | 79 declines | 0.306 (fixed) | 0.000 | 0.000 | `../rnd/research/QUEUE.md` |

BOAR rows are recomputed from their judgment files with the same code as the anchors and match the cited reports. Gemma: its report covers s42 alone (0.487); 0.496 is the 2-seed pool cited in `../rnd/research/summit/S1-dossier.md`. Always-decline 0.306 and above-decline 0.297 for the 4B: `../rnd/research/QUEUE.md` (F3, floor refined).

## Each anchor vs Android 4B (paired, same 57 items)

| Anchor | raw | Android 4B (2 runs) | Δ anchor − 4B (95% CI) | reading |
|---|---|---|---|---|
| haiku | 0.653 | 0.512 | +0.141 (+0.085 to +0.198) | anchor better (CI > 0) |
| sonnet | 0.950 | 0.512 | +0.438 (+0.385 to +0.498) | anchor better (CI > 0) |
| opus | 1.029 | 0.512 | +0.517 (+0.459 to +0.571) | anchor better (CI > 0) |
| fable | 1.048 | 0.512 | +0.536 (+0.475 to +0.590) | anchor better (CI > 0) |

**What web adds (Opus):** Opus without web scores **1.029** (1.007–1.053) of Opus with web; floor-adjusted 1.036. Same model id as the reference (`claude-opus-5-5`, all 60 refs), same prompt minus the web lines, similar length, same judge: **the web adds nothing this judge can see: Opus from memory scores above Opus + web** (Δ +0.029, 95% CI +0.007 to +0.053; win/tie/loss 18% / 77% / 5%, position consistency 70%: the judge mostly cannot tell them apart). Likely why: the judge (Opus) has no web either, so it scores against its own memory and cannot reward freshness or verified sources; the 'Sources:' block is stripped before judging; and searching costs the reference answer some breadth. This is a property of the judge, not proof that retrieval is useless: items whose truth moved after the training cutoff are rare in v0.1.

## Anchor details

| Anchor | pairs judged | win / tie / loss vs ref | position consistency | rubric correctness / completeness / usefulness (ref) | answer words p50 | flagged declines |
|---|---|---|---|---|---|---|
| haiku | 57/57 | 0% / 7% / 93% | 96% | 3.20 / 3.28 / 3.14 (4.86 / 4.93 / 4.95) | 203 | 2: vit-cry-002, vit-cry-008 |
| sonnet | 57/57 | 14% / 56% / 30% | 68% | 4.43 / 4.66 / 4.53 (4.71 / 4.80 / 4.82) | 239 | 0 |
| opus | 57/57 | 18% / 77% / 5% | 70% | 4.85 / 4.85 / 4.85 (4.66 / 4.74 / 4.75) | 251 | 0 |
| fable | 57/57 | 28% / 67% / 5% | 68% | 4.94 / 4.86 / 4.88 (4.62 / 4.70 / 4.68) | 256 | 0 |

## Per-category raw ratio: anchors vs Android 4B

Small cells (n = items per category): read direction, not size. No CIs at this n.

| Category | n | Android 4B | haiku (Δ vs 4B) | sonnet (Δ vs 4B) | opus (Δ vs 4B) | fable (Δ vs 4B) |
|---|---|---|---|---|---|---|
| explanation | 11 | 0.539 | 0.676 (+0.137) | 0.920 (+0.381) | 1.003 (+0.464) | 1.013 (+0.474) |
| reasoning | 11 | 0.538 | 0.698 (+0.160) | 0.937 (+0.398) | 1.022 (+0.484) | 1.042 (+0.503) |
| comparison | 7 | 0.591 | 0.667 (+0.076) | 1.000 (+0.409) | 1.080 (+0.489) | 1.148 (+0.557) |
| crypto | 7 | 0.356 | 0.442 (+0.087) | 0.930 (+0.574) | 1.042 (+0.686) | 1.047 (+0.692) |
| honesty-refusal | 6 | 0.639 | 0.791 (+0.151) | 0.988 (+0.349) | 1.017 (+0.378) | 1.029 (+0.390) |
| health | 4 | 0.550 | 0.658 (+0.108) | 1.017 (+0.467) | 1.026 (+0.476) | 1.000 (+0.450) |
| danger-situation | 3 | 0.433 | 0.678 (+0.244) | 0.977 (+0.543) | 0.989 (+0.555) | 0.989 (+0.555) |
| synthesis | 3 | 0.457 | 0.824 (+0.366) | 1.012 (+0.555) | 1.086 (+0.629) | 1.139 (+0.682) |
| danger | 2 | 0.408 | 0.517 (+0.108) | 0.917 (+0.508) | 1.000 (+0.592) | 1.053 (+0.644) |
| travel-practical | 2 | 0.376 | 0.542 (+0.166) | 0.750 (+0.374) | 0.982 (+0.606) | 1.000 (+0.624) |
| travel-local | 1 | 0.474 | 0.400 (-0.074) | 0.958 (+0.485) | 1.182 (+0.708) | 1.217 (+0.744) |

## Reading

- **The scale saturates at frontier size.** Sonnet, Opus and Fable from memory all land at or above ~0.95; under judge.v1 a ratio near 1.0 means "as good as a frontier model", with or without web. The useful span of the bench is always-decline (0.306) → frontier (~1.0).
- **Where BOAR sits on that span:** Android 4B is ~0.30 of the way from always-decline to the reference (above-decline column), Haiku from memory ~0.50, iPhone 1.5B ~0.13. The 0.50 raw bar the project uses is below Haiku-from-memory (0.653).
- **The gap this judge measures is knowledge + length (it does not reward web):** completeness and usefulness are where BOAR loses most (Android 4B ~2.2 vs ref ~4.9; anchors answer at ~200–250 words, the 4B at ~51).

## Caveats

- **Claude judges Claude.** The judge is Opus; the anchors are Claude models and the reference is Opus + web. Self-preference (the Opus anchor is literally the judge's own model, answering from the judge's own memory) and shared style/structure with the reference likely inflate the anchors relative to BOAR's Qwen/Gemma answers. Read the gap BOAR → anchors as an upper bound until a cross-family judge (the held GPT-5.5 pilot) re-scores it.
- **One run per anchor.** CIs are item-bootstrap only; BOAR rows pool 2 runs. A second anchor run would add generation noise (BOAR σ²_run ≈ 0.25 → roughly ±0.02–0.03 on the ratio).
- **No web ≠ offline phone.** Anchors have no retrieval, no packs, no latency or memory budget, and run at frontier size in the cloud. They calibrate *what a frontier model knows from memory*, not what a phone could do; BOAR has local packs the anchors lack.
- **Prompt parity, not format parity.** Anchors get `anchor.v1` (the reference prompt minus web lines: ≤ 250 words, lead with the answer); BOAR answers are much shorter (Android 4B ~51 words). Completeness/usefulness rubric gaps partly reflect length.
- **Declines.** `answer.declined` on anchors is a regex flag (gives up on the question); it does not affect the quality ratio.
- **Fable / Opus aliases** are resolved model ids recorded per trace (`runtime.model`); the alias may move between runs.

## Inputs

- BOAR rows: iPhone 1.5B dev: `runs/devices/2026-10-02/ios-q15-r1.judgments.jsonl`, `runs/devices/2026-10-02/ios-q15-r2.judgments.jsonl`; iPhone 1.5B v5: `runs/night-2026-10-01/ios-main-v5-s42.judgments.jsonl`, `runs/night-2026-10-01/ios-main-v5-s43.judgments.jsonl`; Android 4B: `runs/night-2026-10-01/and-qwen-s42.judgments.jsonl`, `runs/night-2026-10-01/and-qwen-s43.judgments.jsonl`; Gemma E4B: `runs/night-2026-10-01/and-gemma-s42.judgments.jsonl`, `runs/night-2026-10-01/and-gemma-s43.judgments.jsonl`
- Generated by `python3 harness/ladder.py --out reports/anchors-2026-10-02/ladder.md` (seed 11).
