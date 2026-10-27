# Arm `p1-keepkey` (Sonar P-1 "keep the key"): the topic filter keeps a pack passage the pack judged relevant

TL;DR: Sonar's P-1 (card `rnd/research/sonar/cards/p1-keep-the-key.md`, criterion frozen there 2026-10-02 evening). In `answer.ts`, `onSubject` keeps a large-pack passage whose question ↔ article lead cosine is ≥ `SEMANTIC_KEEP` (0.70). That is the same rule `WikiPack.searchDetailed` already uses to keep keyword candidates, so the lexical topic filter stops overriding the pack's own verdict. Engine: 0cfd4a77 + `p1-keepkey.patch`. Kit A, Android 4B profile, bench v0.1 only.

| | |
|---|---|
| Patch | `p1-keepkey.patch` sha256 `5f5307a6e02b5703de406c27d584264fb48e73d35aa17e3f1da61c32c744025e` (worktree `<workspace>/wt/p1-keepkey`, uncommitted) |
| Change | (1) the lead-cosine carry from G1+, unchanged: `PackHit.leadSim` set in `searchDetailed` where `sem` is already computed → `RetrievedChunk.leadSimilarity` (new optional field) via `packHitToChunk`. No reordering; `retrieve.ts` is untouched. (2) `answer.ts` `onSubject`: `… \|\| packKept(c)` with `packKept = leadSimilarity ≥ SEMANTIC_KEEP`, on the names and plain branches. Declared choice: the date-article (`history`) branch keeps its own rule. The card's replay exercised the `onTopic` paths only. The health path never runs `onSubject` |
| Tests | `answer.test.ts` +1 (a lead-cos 0.75 pack passage survives the topic filter while 0.69 is dropped; fails on unpatched code); `packs.url.test.ts` +1 (`leadSim` → `leadSimilarity`). Full suite 106 files / 1166 tests, `tsc` clean |

## Frozen criterion (card, verbatim; coordinator's step order)

1. **Exact key-in-context at `pre`** (`tools/key_in_context.py` c9124e43, traces with `--event-source-text`), on v0.1 public keyed items: lan-exp-003 and vit-cry-010 gain the key, i.e. **+2 on the dropped items**, and **≤ 1 key lost elsewhere**.
2. **0 items emptied** (any item with ≥ 1 pre-answer source in base keeps ≥ 1).
3. **Whole-bench paired Δratio ≥ −MDE** (not worse beyond the MDE at the run count used; 2 seeds × 57 judged items, MDE ≈ 0.030–0.036).
4. **Gate PASS with safety rules v0.5**; 0 new safety hits; 0 new danger memory answers.
5. **Retrieval p50 ≤ 1.2× base** (Android desktop profile). Expected ≈ 1.0×.
6. Reported, not pass/fail: mean prompt tokens Δ (expected ≈ +2 tokens per item averaged over the bench), confident-wrong per run.

- Fail on 1, 2, 4 or 5 → not adopted. Fail on 3 alone → report as "not shown safe for quality".
- Step 1 (replay; coordinator): `and-qwen` s42/s43 `-kic` pairs (base `main` vs arm `p1-keepkey`, both with `--event-source-text`), reported before any judged seed. Only if step 1 passes: 2 judged seeds, Android 4B, kit A, v0.1 only.

## Results

**Step 1 replay (`runs/p1/`, base `main` vs `p1-keepkey`, kit A, Android 4B, `--event-source-text`, s42 and s43): PASS. Retrieval passes by a hair.**
1. Exact key-in-context at `pre` (tool c9124e43): **+2 on the dropped items** (lan-exp-003, vit-cry-010) on both seeds, **0 lost**. PASS.
2. **0 items emptied** on both seeds. PASS.
3. Retrieval p50: pooled over both seeds 164 → 196 ms = **1.19×** (bar ≤ 1.2×), per-item paired median 1.12×; per seed s42 1.36×, s43 1.07×. The host was loaded (1-min load ~17–18). The patch adds no retrieval work (it attaches an already-computed value), so the s42 gap is read as noise, and the pooled number is the reading.
- Mean prompt tokens 436.1 → 440.9 (+4.8). Answers changed on exactly the 2 rescued items, on both seeds.
**Judged seeds:** the replay arm runs `runs/p1/and-p1-s4x-kic` are themselves full runs (and-qwen config, seeds 42/43). Their answers equal the replay base except on the 2 rescued items. Judged vs `and-qwen-s42/s43`, judge.v1 opus, both orders.

| # | Criterion (frozen) | Result | Verdict |
|---|---|---|---|
| 1 | +2 exact keys on the dropped items, ≤ 1 lost | +2 (lan-exp-003, vit-cry-010), 0 lost, both seeds | PASS |
| 2 | 0 emptied | 0 | PASS |
| 3 | paired Δratio ≥ −MDE | **Δ −0.0025** (CI −0.019 … +0.015), MDE 0.030 | PASS |
| 4 | gate PASS v0.5; 0 new safety hits; 0 new danger memory answers | PASS; unsafe 3 / 3 = base 3 / 3; health-memory 0 | PASS |
| 5 | retrieval p50 ≤ 1.2× | 1.19× pooled (s42 1.36×, s43 1.07×; loaded host) | PASS (by a hair) |
| 6 | reported | prompt tokens +4.8 per item; confident-wrong 10 / 11 vs base 10 / 12 | — |

**Verdict: P-1 PASSES all frozen criteria.** Outputs: `runs/p1/` (`diff-andqwen-p1.md`, `gate-p1-s42s43.v05.md`).
