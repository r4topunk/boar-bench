# P-8 step 0: batch the pack search's single-row SQLite lookups: desktop pre-check PASS

TL;DR: **all three step-0 items PASS.**
- (a) the full unit suite passes on the patched tree;
- (b) on the g75-matched desktop profile, pre-answer sources, `retrieval.raw` / `kept`, route and answer text are **byte-identical 72/72**;
- (c) async SQLite calls to the packs per question fall **476 → 190 median (−60%), 565 → 209 mean (−63%)**. The card predicted 445 → ~164 (−63%).

Steps 1–2 (moto retrieval p50 ≤ 0.9× the same packs without the patch; TTFT) go into the next phone session, back to back as the card says.

Card: `rnd/research/sonar/cards/p8-pack-sql-batching.md` (criterion frozen 2026-10-03), not restated.

| | |
|---|---|
| Patch | Sonar's `exp/24-sql-batching/p8-wikiPack.patch` sha256 `75751ea52af4f2cb989bf9ee286d8d76b279161a0b27f14532f0d0406e909500`, **verified**. It is a plain `diff -u` of loose files (`wikiPack.upstream.ts` → `wikiPack.p8.ts`), so it was applied with `patch(1)` to `src/rag/wikiPack.ts`. Checks: `wikiPack.upstream.ts` is byte-identical to 0cfd4a77's `src/rag/wikiPack.ts`, and the patched file is byte-identical to Sonar's `wikiPack.p8.ts`. The same change re-exported git-style for `setup.sh`: `arms/p8-sqlbatch.patch` sha256 `4e5f1e4d369a23f741eb345050992ff57e9203c5c7210558cb1bb4ded619f860` (worktree `<workspace>/wt/p8-sqlbatch`, uncommitted). `wikiPack.ts` only, +84 / −7 |
| Packs | the current packs on both sides (`boar-wikivoyage-en` `ff8595e3…`, `boar-crypto` `ae9fbd2c…`), as criterion 0 says: "the same packs without the patch" |

| # | Step-0 item | Result | Verdict |
|---|---|---|---|
| a | full unit suite passes | 106 files / 1164 tests on the patched tree (the patch adds none); `tsc` clean | **PASS** |
| b | desktop replay, v0.1, kit crypto + Wikivoyage + bundled Full, 1.5B, Android 8 GB (the g75-matched profile; settings as the device runs), s42, `--event-source-text`, base and patch back to back | pre-answer sources (title, section, source, similarity, passage text) **72/72**; `retrieval.raw` 72/72; `retrieval.kept` 72/72; route 72/72; answer text 72/72. 0 errors either side | **PASS** |
| c | async SQLite calls per question, base vs patch | pack DBs (`boar-wikivoyage-en`, `boar-crypto`), 68 items that retrieve: **median 476 → 190 (−60%)**, **mean 565 → 209 (−63%)**. All DBs incl. the app's corpus DB: median 456 → 183 | **PASS** (ratio as predicted) |

- How (c) was counted: the adapter's `expo-sqlite` shim counts every async call per database file (`execAsync`, `getAllAsync`, `getFirstAsync`, `runAsync`, prepared `executeAsync`; on the phone each one crosses the JS↔native bridge). The count is behind `BOAR_EVAL_SQL_COUNT=1`, so default traces are unchanged; one `other/sql-calls` event per item. The absolute numbers are ~7% above the card's because they cover the whole answer path per item (every retrieve the engine issues), not only Sonar's pack-search replay. The reduction ratio matches.
- Outputs: `runs/p8/` (base and patch traces with `sql-calls` events).
