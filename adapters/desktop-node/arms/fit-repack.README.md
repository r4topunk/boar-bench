# Arm `fit-repack` (Anvil Fix 1, card `rnd/research/anvil/cards/fit-estimate-repack.md`): the fit estimate counts repacked weights and the load peak

TL;DR: `estimateMemoryFit` adds `repackBytes` (0.97 × file for repackable types) and `loadPeakBytes` (file pages + repacked copy + KV + compute while loading), plus a new verdict **`repack-peak`**: the repack peak doesn't fit but a load without repack does. `LlamaEngine.load()` then passes **`no_extra_bufts: true`** to `initLlama` instead of loading a model the OS would kill. Pure TS, engine 0cfd4a77; no model or engine logic outside `memoryFit.ts` / `LlamaEngine.ts`.

| | |
|---|---|
| Patch | `fit-repack.patch` sha256 `7ba441be821b121dd19973df06e6d12a67fbe1bd3dae3c169d07371285bf98f7` (worktree `<workspace>/wt/fit-repack`, uncommitted; nothing committed to boar-app) |
| Repackable types, **verified** | llama.rn 0.13.0-rc.4 vendored `llama.h` (`llama_ftype`): 2 Q4_0, 7 Q8_0, 14 Q4_K_S, 15 Q4_K_M, 16 Q5_K_S, 17 Q5_K_M, 18 Q6_K, 25 IQ4_NL: the card's numbers are right. And `ggml-cpu/repack.cpp` on ARM (NEON + dotprod/i8mm) repacks Q4_0, Q8_0, Q4_K, Q5_K, Q6_K, IQ4_NL **and MXFP4**. So **38 MXFP4_MOE is added** to the card's set (declared deviation; the conservative direction). Q2_K repacks only on AVX-512 / RISC-V; TQ1/TQ2 and IQ2/IQ3 never |
| Verdict rule (declared interpretation) | repacked model: `loadPeak ≤ budget` → `resident`; else `repack-peak` **only if** today's no-repack verdict is resident or streaming, otherwise today's verdict (thrashing / insufficient). The card's one-liner (`anon − repack ≤ avail ? repack-peak : insufficient`) would call the iPhone 13's 4B `repack-peak`, against its own T6 "unchanged behaviour"; this rule keeps T6. Non-repackable types and unknown `general.file_type`: exactly today's estimate |
| Engine | `estimateFitAt` passes `repack: true` and `fileType = general.file_type`; `load()`: `repack-peak` → `no_extra_bufts: true` + `[engine] … loading without repack` warning. `describeFit` adds a note that doesn't tell the user to free RAM. `fits()` in defaultModel/depth is unchanged: `repack-peak` still fits, so the auto-pick is kept and only the load mode changes. llama.rn rc.4 declares `no_extra_bufts` and passes it to native (`JSIParams.cpp`) |
| Tests | `memoryFit.test.ts` +7 (Anvil's T1–T6 with the real Qwen3-4B / Qwen2.5-1.5B header shapes, + describeFit); `LlamaEngine.test.ts` +2 (7.2 GB: `repack-peak` → `initLlama` gets `no_extra_bufts: true`, load succeeds; 12 GB: resident, no flag). 7 of the 9 fail on unpatched code. Full suite **106 files / 1173 tests**, `tsc` clean |

## What the patch changes on the desktop profiles

The desktop-node adapter's `estimateFit` returns null, so **adapter runs are unaffected** (no bench result moves). The engine's own decision, evaluated with the tree's functions (`estimateMemoryFit` → `rankAnswerModels`, `contextSizeForRam`), uses the RAM the adapter shim simulates (total, available = 50%):

| Profile | nCtx (before → after) | auto-pick (before → after) | fit before → after |
|---|---|---|---|
| and-qwen (Android 12 GB, 4B) | 4096 → 4096 | 4B → 4B | resident → resident (peak 5.73 / 9.0 GiB) |
| ios8 (iOS 8 GB, 1.5B + 4B) | 4096 → 4096 | 4B → 4B | 4B resident → **repack-peak** (peak 5.73 > 5.5 GiB): **loads without repack**; 1.5B resident → resident |
| ios-main (iOS 4 GB, 1.5B) | 2048 → 2048 | 1.5B → 1.5B | 1.5B resident → **repack-peak** (peak 2.24 > 2.0 GiB): **loads without repack** |

- **No model choice and no nCtx changes on any profile.** Two load-mode changes, both on iOS.
- **Flag (decision for Anvil / the coordinator):** the iPhone 13's 1.5B, today the shipped default that loads with repack and has no jetsam kills on record, would switch to no-repack. The budget depends on the real `getAvailableRamBytes` on the phone (here the shim's 50% = 2.0 GiB; the floor is total − 2.5 GiB = 1.5 GiB). ARM prefill without repack is UNKNOWN (Probe B). Probe A's faster no-repack prefill is a macOS/Accelerate artifact and does not apply.
- Also UNKNOWN: whether iOS jetsam needs this at all for the 1.5B (it counts phys_footprint, which the repacked copy is part of).
