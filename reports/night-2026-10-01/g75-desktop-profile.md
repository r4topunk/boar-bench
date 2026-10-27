# Moto g75 profile on the desktop: the same-profile comparator for the device runs

TL;DR: the desktop proxy of the exact g75 profile scores **0.378** (s42 0.369, s43 0.387); the device scores **0.349** (and-q15 r1 0.346, r2 0.353). Paired 2 × 2 over 57 judged items: **device − desktop = −0.029** (CI −0.056 … −0.002; MDE 0.036). The −0.029 the device showed against the iOS 4 GB desktop profile reappears unchanged against its own profile. So the gap is device vs desktop, not a profile or kit difference.

Runs (`runs/g75desk/`): main 0cfd4a77, arm `main~g75` (config only), device `{android, 8 GB}`, model qwen2.5-1.5b only (installed alone, as on the phone), kit crypto + Wikivoyage + the bundled Full corpus (no vital5), settings copied from the device traces (`quickFirst`, `alwaysComplete` false, `loadCrashedIds: [qwen3-4b]`), node backend, questions72 (the device runs' 72 items), seeds 42/43. 0 errors. Judge judge.v1 opus, both orders; safety v0.5.

| | ratio (57 judged) | confident-wrong | declined |
|---|---|---|---|
| device and-q15 r1 / r2 (moto g75, llama.rn) | 0.346 / 0.353 | 10 / 10 | 29 / 25 |
| **desktop g75 profile s42 / s43** (node-llama-cpp) | **0.369 / 0.387** | 8 / 6 | 25 / 30 |
| reference: device ios-q15 r1 / r2 (iPhone 13) | 0.410 / 0.378 | 8 / 10 | 22 / 23 |

- Paired Δ (`runs/g75desk/diff-device-desktop.md`): desktop − device **+0.029** (CI +0.002 … +0.056), below the MDE (0.036) at 2 × 2 runs, with the CI excluding 0.
- Reading: the profile reproduces; what differs is the runtime (llama.rn on the phone vs node-llama-cpp on the desktop; sampler and chat-template details, device seeds unrecorded in the traces). A desktop number for the g75 overstates the device by about 0.03.
