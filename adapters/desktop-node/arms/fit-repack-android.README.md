# Arm `fit-repack-android` (Anvil Fix 1, Android only): the repack-aware fit estimate applies on Android; iOS unchanged

TL;DR: the same as `fit-repack` (see `fit-repack.README.md` for the estimate, the verified ftype set incl. 38 MXFP4_MOE, the verdict rule and T1–T6). The difference: **`LlamaEngine.estimateFitAt` passes `repack: true` on Android only.** On iOS it estimates as today (`repack: false`: identical anon, verdict and description), and logs the would-be repack verdict when it differs (`[engine] fit (iOS, not applied): with repack would be …`) for a later device probe.

| | |
|---|---|
| Patch | `fit-repack-android.patch` sha256 `a8e431ac8cc4240efdc8229af542ec00096b8a151d5af1b4979f393b8d6bfeb6` = `fit-repack.patch` + the platform gate (worktree `<workspace>/wt/fit-repack-android`, uncommitted) |
| Why (coordinator decision, 2026-10-02) | Do not change the shipped iPhone 13 behaviour without device evidence. There are no recorded kills there today; the iOS budget estimate is evidently conservative (`fit-repack` would have switched the 1.5B to no-repack at a 2.0 GiB budget); and ARM no-repack prefill speed is unknown. The iOS path gets its own probe on the iPhone later (Plumb: 1.5B with and without repack on r4to's phone) |
| Tests | `fit-repack`'s 9 (memoryFit T1–T6 + describeFit; engine: Android 7.2 GB → `repack-peak` + `no_extra_bufts`; Android 12 GB → resident, no flag) + 2 iOS: the same 7.2 GB case on iOS is resident (repack bytes 0), loads with repack and logs the would-be `repack-peak`; an iPhone 13-sized case gets repack bytes 0 and load peak = anon (today's numbers). Full suite **106 files / 1175 tests**, `tsc` clean |

Effect on the desktop profiles (engine functions, as in `fit-repack.README.md`):
- Android 12 GB (`and-qwen`): unchanged.
- iOS 8 GB and iOS 4 GB: **now unchanged** (today's verdicts; the would-be `repack-peak` is only logged).
- No model-pick or nCtx change anywhere. Adapter runs are unaffected (`estimateFit` null).
