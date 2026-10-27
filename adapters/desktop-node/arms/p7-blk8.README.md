# Arm `p7-blk8` (Sonar P-7): format-2 packs rebuilt with 8 KB zstd blocks: step 0 (rebuild + desktop pre-check)

TL;DR: **pre-check 0 PASSES** (72/72 pre-answer sources byte-identical). **Criterion 3 FAILS**: the packs grow +9.8% / +9.5%, bar ≤ +5%. The compressed text grows only +7.6% (the card's estimate). The rest is SQLite page slack: 15,014 blobs of ~7.8 KB in 4 KB pages, with overflow chains. Steps 1–2 (moto retrieval) are for the next phone session, if the coordinator still wants them under the failed size bar.

Criterion: card `rnd/research/sonar/cards/p7-pack-block-size.md` (frozen 2026-10-02 night), not restated.

Rebuild (`<runner>/kiln/p7/build.sh`, one heavy-lock job, nice 10): the exact 2026-09-26 recipes (`<runner>/knowledge-build/voyage.sh`, `crypto-rd.sh`: builder `scripts-crypto/build-wiki-pack.mjs`, the same dumps and manifests, bge-small lead embeddings on Metal). Only `--block-kb` changes. New files only; the current packs are untouched. A 64 KB control was built alongside.

| Pack | current | 64 KB control (same recipe) | **8 KB** | 8 KB vs current |
|---|---|---|---|---|
| boar-wikivoyage-en | 351,092,736 B, `ff8595e3…` | 351,068,160 B, `40f91d4b…` | **385,605,632 B**, `97faf9c9a611b9a4161c791d0b10f382c5e4a410a74162d4116023a812815ba1` | **+9.83%** |
| boar-crypto | 36,093,952 B, `ae9fbd2c…` | 36,093,952 B, `3713e8ab…` | **39,518,208 B**, `ed45ed469f1cd8b7fac15dcee16321b69139cb9d7faab6b0a09d4d9faf382399` | **+9.49%** |

- The control is not byte-identical to the current packs (`builtAt` in `meta`; 24 KB less FTS). The pre-check below compares the 8 KB arm against the **current** packs, as the criterion says.
- Wikivoyage `blocks` table:
  - current 3,531 blocks, 108.8 MB of zstd data in a 113.1 MB table;
  - 8 KB 15,014 blocks, 117.1 MB of zstd data (+7.6%) in a **147.7 MB** table.
  - FTS, chunks and lead vectors are unchanged.
- **Criterion 0, desktop pre-check (iPhone `ios-main-v5` config, s42, `--event-source-text`, base and arm back to back):** pre-answer sources (title, section, source, similarity, passage text) **byte-identical 72/72**; `retrieval.raw` 72/72; answer text 72/72. **PASS.**
- Desktop retrieval p50 (V8 with the JIT; not the target): 113 → 143 ms (loads 14.5 / 16.2). The card's claim concerns JIT-less Hermes on the phone (steps 1–2).
- Options for the size bar (not tested, for Sonar):
  - 16 KB blocks (card: 0.422 compressed ratio, fewer overflow pages);
  - a larger SQLite `page_size` for the blocks table;
  - storing blocks outside SQLite.
