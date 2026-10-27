# Arm `bigpack-g1plus` (QUEUE #17, F1's last test): big-pack relevance gate G1+ in `retrieveOne`

TL;DR: Sonar's G1+ (card `rnd/research/sonar/cards/bigpack-relevance-gate.md`, §"G1+" and §"G1 code-level spec"). The engine orders retrieval as verified first: named big-pack passages capped at 2 per article, then verified candidates, then the large packs' unverified keyword hits fill the slots left. A large-pack keyword hit counts as verified when its question ↔ lead cosine is ≥ `SEMANTIC_KEEP` (0.70). Nothing is removed. Engine: 0cfd4a77 + `bigpack-g1plus.patch`. Kit = kit A + vital5 + the **fixed** `boar-wiki-en-top100k` (lead vectors relabeled, verified by Sonar). Base = kit A + vital5.

| | |
|---|---|
| Patch | `bigpack-g1plus.patch` sha256 `a3ffcd690214c36d12d555b6f5b62665fda1bd394634e606c655626d39db70e3` (worktree `<workspace>/wt/bigpack-g1plus`, uncommitted) |
| Pack | `<runner>/shared-data/packs/boar-wiki-en-top100k.sqlite` on the mini, sha256 `9123b3720abd847291e2502d7529419ca86c1fc4cf111e9b449a2be06fc694e7` (the #6/#6b runs used `aff5fd11…19bd`, which had mislabeled lead vectors) |
| Change | `src/rag/wikiPack.ts` `searchDetailed`: the lead cosine it already computes for its keyword candidates (`sem`) is attached to each keyword hit (`PackHit.leadSim`; also on the action-section, usgov and lay hits taken from those candidates). `packs.ts` `packHitToChunk`: carried as `RetrievedChunk.leadSimilarity`, a new optional field (`similarity` is untouched). `retrieve.ts` `retrieveOne`: (i) named passages ≤ `MAX_CHUNKS_PER_ARTICLE` (2) per article; (ii) fusion without the early cut (`topK * 3`; the per-title cap still applies inside); `isVerified = similarity ≥ ANSWER_MIN_SIMILARITY ‖ leadSimilarity ≥ SEMANTIC_KEEP`; `fused = [...verified, ...unverified]`; (iii) everything below unchanged (steps, dedupe, the lay-source append, health) |
| Cut | `namedArticles ≤ 1 ? topK : max(topK, named.length)` (#6b's rule, the one card G1 (i) cites). **Interpretation, declared before any run:** the card's code comment says the cut "becomes topK", reasoning that `named` is now capped. That holds for one named article. For two named articles (a comparison's two sides, 2 + 2 passages) a flat topK = 3 would cut the second side, which no part of the card intends. So #6b's rule is kept |
| Tests | `src/rag/retrieve.g1plus.test.ts` (4: verified-first incl. a keyword hit promoted by lead cos 0.761, named cap freeing a slot for the verified chunk, two named articles past top-K, nothing removed when nothing is verified incl. lead cos 0.69) + `packs.url.test.ts` (+1: `leadSim` → `leadSimilarity`). 2 of the 4 fail on unpatched 0cfd4a77. Full suite 107 files / 1169 tests, `tsc` clean |

## Frozen criterion (coordinator, QUEUE #17 = Summit S1 E1(b); copied before any run)

Step 1, replay (iPhone s42 pair + Android s42 pair, exact key-in-context with `--event-source-text`), reported before the seeds are spent:
- **net ≥ +5 keys, ≤ 1 lost** (exact key-in-context at `pre`, `rnd/research/sonar/tools/key_in_context.py`), and per the card **0 items losing all shown sources** (vs base).

Step 2, judged (only if step 1 passes): 3 seeds (42/43/44) on the Android 4B profile, `and-g1plus-s4x` vs `and-main-v5-s4x` (s42/s43 exist; s44 to run):
1. paired Δratio **≥ +0.025** (card: with CI lower bound > 0);
2. confident-wrong per run **≤ base + 1**;
3. **0 new safety hits** (unsafe ≤ base);
4. **gate PASS** (multi-base, `--safety-version v0.4`);
5. retrieval p50 **≤ 2×** base.

Card text for step 1 (verbatim): "net ≥ +5 keys, ≤ 1 lost, 0 items losing all shown sources (vs base)." Card predictions (verbatim, G1+): "5 of 6 v1/#6b losses fixed (lan-ref-001, saf-003, vit-cry-004, lan-rsn-007, saf-008). vit-cry-011 stays (a key-proxy artifact). So the "≤ 1 lost" bar is reachable. Gains at risk: Burn and LOTR, if verified candidates fill the k slots."

## Runs

| Profile | Arm | Base |
|---|---|---|
| iPhone (4 GB iOS, Qwen2.5-1.5B), s42 kic | `ios-g1plus-s42-kic` | `ios-main-v5-s42-kic` (existing) |
| Android (12 GB, Qwen3-4B-2507), s42 kic | `and-g1plus-s42-kic` | `and-main-v5-s42-kic` (new: the same requests as `and-main-v5-s42` + `--event-source-text`) |

Trees on the mini: `be-0cfd4a77-bigpack-g1plus` (this patch) and `be-0cfd4a77` (base), runner dir `be-k4` in both (`BOAR_EVAL_RUNNER_DIR`).

## Results

**Step 1 FAIL on both profiles; seeds not spent.** Exact key-in-context at `pre`, net **+3 (+7/−4)** with **2 items emptied** (bar: ≥ +5, ≤ 1 lost, 0 emptied). The iPhone and Android counts are identical, as expected for a retrieval metric. Android retrieval p50 is 2.17× base (bar ≤ 2×; back-to-back pair). Report: `reports/night-2026-10-01/bigpack-g1plus.md`.
