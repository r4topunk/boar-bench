# Arm `cmpsplit-v21`: cmpsplit v2 + one-line fallback fix (QUEUE.md #3b, v2.1)

TL;DR: v2 (`cmpsplit-v2.README.md`) failed the full gate on lan-cmp-004: with no article of a side, `bestForSide` preferred any non-guide hit ("Economics of bitcoin") over the side search's top hit. v2.1: only the side's own article is preferred over the guide; otherwise the side search's top hit (v1 rule). Approved by the coordinator 2026-10-02.

| | |
|---|---|
| Patch | `cmpsplit-v21.patch` sha256 `2430f5bfd916475c14e447cb07534c56509a7294442697aea70237e128b01dcd` (`git diff 0cfd4a77` of worktree `<workspace>/wt/cmpsplit-v21` = v1 + v2 + this fix, uncommitted) |
| Change vs v2 | `src/rag/comparison.ts` `bestForSide`: drop the `hits.find(non-guide)` fallback; test updated (bison side keeps Wikivoyage: North American wildlife over Economics of bitcoin) |
| Tests | full suite 108 files / 1209 tests pass, `tsc` clean |

## Frozen criterion: v2's, unchanged (copied verbatim from the card's v2 section)

**v2 (small, same arm name + `-pin`):**
1. Pin the best chunk of each detected side through the existing `pinned` set in `answer.ts`. It is already used for identifier pages: `compressContext(matchQuery, raw, { tokenBudget, pinned })`, and pinned chunks bypass the relative floor and go first. A comparison then always keeps one passage per side within the 450-work budget.
2. Make sure `onSubject` keeps a chunk whose title equals a detected side.
3. For a non-travel comparison, resolve the side to the Wikipedia/vital5 article before the Wikivoyage guide: v1 put "Wikivoyage: Japan" / "Wikivoyage: Germany" ahead of vital5's Japan / Germany leads (the format-2 named path wins). This is consistent with `wikivoyage-lead-gate`.
4. Optional: raise the comparison's k from 3 to 4 (one per side + one shared), or the lookup budget only for comparisons. Measure the TTFT cost.

v2 criterion (frozen now, before any v2 run), on the same pair design (`-v5-t0`, deterministic):
- (a') both sides in the shown pre-answer sources on the 6 two-sided comparison items: ≥ 5/6 (main 3/6);
- (b) unchanged from v1;
- (c') key-in-context at `pre` on non-comparison items unchanged (0 lost);
- (d) unchanged from v1: confident-wrong not up, safety unchanged;
- (e') prompt tokens on comparison items within +150 of main.
- Added by the coordinator at queueing (QUEUE #3b, after #5): the slice is only 6 items, so the deterministic t0 pair decides, and the full boar-eval gate on all 72 items must also PASS.

Slice for (a'): the 6 two-sided `comparison` items of questions72 (vit-hum-002, lan-cmp-001, lan-cmp-002, vit-sci-002, lan-cmp-004, lan-cmp-005; gold side regexes as in `cmpsplit.README.md`), on the shown pre-answer sources (`answer.shown`). (b)/(d) as in v1. (c') with Sonar's `rnd/research/sonar/tools/key_in_context.py --vital5`. (e') `timing.promptTokens` on the same 6 items.

Plus (coordinator, frozen 2026-10-02 before any v2.1 run): **full gate on questions72 PASS (multi-base s42+s43, --safety-version v0.4)**.

## Runs

| Run | Kit | Items | Base |
|---|---|---|---|
| `ios-cmpsplit-v21-v5-t0` (decides the card criterion) | night kit + wiki-vital5 | questions-cmp78 | `ios-main-v5-t0` |
| `ios-cmpsplit-v21-s42`, `-s43` (full gate) | night kit | questions72 | `--base ios-main-s42 ios-main-s43` |

## Results

(a') 5/6 PASS, (c') PASS, (e') +86 PASS, safety PASS, **full gate on questions72 (multi-base s42+s43, v0.4) PASS**; (b) FAIL, unreachable on this pair (main has 1 citation-check decline on the slice). Report: `reports/night-2026-10-01/cmpsplit.md` § v2.1.

Release note (2026-10-27): the patch file itself is not published (it embeds questions of a competitor team's public test set as test strings). The `.sha256` pin next to this README is kept as the record.
