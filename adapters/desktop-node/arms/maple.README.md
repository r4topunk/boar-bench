# Arm `maple` (QUEUE #15): Maple-Preview 20B-A1B as the Android fast reader, llama-server backend

TL;DR: a model-only arm of the shared engine 0cfd4a77 (kit A, Android 12 GB profile). Maple runs on `--backend server` (llama.cpp b11010 `4bc272f`, which has the `maple` arch); the comparator is Qwen3-4B on the **same** backend and seeds. Plan and criteria are frozen in `rnd/research/anvil/cards/maple-20b-a1b-fast-reader.md` §"Run plan for #15" and are not restated here beyond the table below.

| | |
|---|---|
| Model | `<runner>/shared-models/maple-preview-TQ2_0-head-Q4_K.gguf`, 5,901,782,560 bytes, sha256 `221f792cc9760d27a34f449b4229e258fa968a63bd4213993e45d9c0bb477a9e` (checked by the adapter every run) |
| Catalog | 0cfd4a77's catalog has no Maple. The adapter supplies the entry the app would have, shaped like the Android default: `answerTier: "default"`, roles general + fast, chat template, `sizeBytes` 5,901,782,560. Traces carry `versions["catalog.entry"] = "adapter"`. With one installed model and 12 GB RAM, the engine's low-RAM block and deep tier don't apply, so routing is the 4B's |
| Runs (questions72) | `maple/and-maple-s42` → `srv/srv-s42` (Qwen server s42, the parity run: same profile, kit, backend and requests as `and-qwen-s42`, reused per the card) → `maple/and-maple-s43` → `maple/qwen-srv-s43` |
| Safety | disk watchdog `<runner>/kiln/harness/watchdog-disk.sh` on the Maple GGUF (kill-and-delete below 12 GiB), 46 GiB free at start |

## Declared before any full run (2026-10-02 ~12:10): the thinking budget is enforced

- The card says the server backend "does not enforce the 256 cap". It was written before the backend was built.
- The backend now sends the engine's per-item `thinking_budget_tokens` (fast tier: 256) with the app's budget message. b11010 enforces it per request when the template declares thinking tags; see `reports/night-2026-10-01/server-backend.md` §6.
- That is what llama.rn does in the app, so this run is closer to the app than the card assumed.
- `reasoningTokens` and `route.thinkingBudgetExceeded` are still recorded per item, and the card's reading rule is applied as written: more than 5/72 exceeded, or a pass that rests on exceeded items → INCONCLUSIVE.
- `max_tokens` = 512 + 256 = 768, as the card says.
- Smoke (3 items, s42, discarded): 76 / 77 / 131 hidden tokens, 0 exceeded, 0 empty, peak RSS ≤ 4.2 GiB.

## Results

**FAIL**: criteria 2 (CW 20/15 vs 10/12), 3 (unsafe 5/6 vs 3/4) and 4 (first visible 1.85×, total 1.4×) fail; 1 (Δ −0.028), 5 (0 empty) and 6 (4.6 GB) pass. The 8 flagged items per seed all stop at 264 = 256 + the budget message (the cap fired). Report: `reports/night-2026-10-01/maple.md`.
