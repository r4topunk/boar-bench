# iOS 8 GB profile ("what would an iPhone 15 Pro get?"): the engine picks the 4B, quality = the Android 4B

TL;DR: with both models installed and no saved pick, engine 0cfd4a77 routes **every answer generation to Qwen3-4B** on an 8 GB iOS device. Rule: `rankAnswerModels` (`src/routing/defaultModel.ts`) picks the default tier when RAM > 4.5 GB and its fit is not thrashing/insufficient. The engine's own fit for the 4B on 8 GB: 8 − 2.5 GiB reserve = 5.5 GiB usable, vs ≈ 3.1 GiB needed → "resident". Quality: **0.514, +0.119 over the iPhone 1.5B** (CI +0.073 … +0.166), the same as the Android 4B (+0.002, CI −0.035 … +0.040). It never declines, so confident-wrong is higher than the 1.5B's.

Runs (`runs/ios8/`): main 0cfd4a77, arm `main~ios8` (config only), device `{ios, 8 GB}`, `--installed qwen2.5-1.5b-instruct-q4km,qwen3-4b-instruct-2507-q4km` (new adapter option: the engine picks, the adapter loads what it asks), iPhone kit (crypto + Wikivoyage + wiki-vital5, as `ios-main-v5`), node backend, the same 72 items as `ios-main-v5`, seeds 42/43. 0 errors. Judge judge.v1 opus; safety v0.5.

| | ios-main-v5 (iPhone 4 GB, 1.5B) | **ios8 (iPhone 8 GB)** | and-qwen (Android 12 GB, 4B, kit A) |
|---|---|---|---|
| model per tier | fast: 1.5B (51 gens); instant: none (13 items) | **fast: 4B (58 / 58 gens)**; instant: none (13); deep: none installed → multipass if asked | fast: 4B (59); instant (10) |
| ratio s42 / s43 | 0.391 / 0.399 | **0.525 / 0.503** | 0.518 / 0.493 (2-seed 0.512) |
| paired Δ (2 × 2, 57 items) | — | **+0.119** vs 1.5B (CI +0.073 … +0.166); **+0.002** vs Android 4B (CI −0.035 … +0.040) | — |
| confident-wrong s42 / s43 | 9 / 7 | 12 / 16 | 10 / 12 |
| declined | 21 / 22 | **0 / 0** | 0 / 0 |
| unsafe (v0.5, 17 danger) | 4 / 3 | 3 / 3 | 3 / 3 |
| desktop TTFT / total p50 (not phone numbers) | 1.8 / 3.3 s | 5.6 / 9.6 s | 4.9 / 9.1 s |

- Why no 1.5B: it would be picked only if the 4B didn't fit or was measured under 6 tok/s on the device (`compact-does-not-fit` / `compact-default-too-slow`). Neither holds on 8 GB in this profile, where speeds are unmeasured and an unmeasured tier model is never disqualified. On a real iPhone 15 Pro, a measured 4B speed under 6 tok/s would flip it back to the 1.5B: UNKNOWN until device numbers exist.
- Confident-wrong rises vs the 1.5B because the 4B answers everything. The 1.5B's compact citation-decline path (21–22 declines) never applies to the 4B (`isCompactModel` false).
- The comparison with and-qwen mixes kits (vital5 is in the iPhone kit, not in kit A). Quality is equal anyway.
- Device caveats: jetsam limits, thermal and real tok/s on an A17 Pro are not measured here.
