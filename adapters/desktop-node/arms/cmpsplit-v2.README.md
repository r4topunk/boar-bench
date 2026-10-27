# Arm `cmpsplit-v2`: comparison split + one pinned passage per side (QUEUE.md #3b)

TL;DR: v1 (`cmpsplit.README.md`) retrieved the missing side but lost it in context assembly (compression's relative floor, the topic filter, k = 3, Wikivoyage guides taking the side slot). v2 marks a side's own-article passage in retrieval and pins it through `compressContext` and `onSubject`; a non-travel side resolves to its encyclopedia article before the travel guide. Engine: `upstream/main` 0cfd4a77 + `cmpsplit-v2.patch` (v1 included; the patch is the whole change vs 0cfd4a77).

| | |
|---|---|
| Patch | `cmpsplit-v2.patch` sha256 `27d8dd799a9b419a23a4a06575d36381913af9666c1f327c7817e5b3f9201290` (`git diff 0cfd4a77` of worktree `<workspace>/wt/cmpsplit-v2` = v1 + v2, uncommitted) |
| v2 changes over v1 | `retrieve.types.ts`: optional `comparisonSide` on a chunk. `comparison.ts`: `bestForSide(hits, side, travel)` = side's own non-guide article > own guide > any non-guide > top hit (travel question: pack order); `mergeComparison` marks the side passage only when its title names the side. `retrieve.ts`: non-travel side searched first without the large packs (bundled corpus, format-1 packs such as vital5), the named large-pack path only when that finds no article of the side. `answer.ts` (+5): marked passages join the existing `pinned` set (`context:pinned-N`) and pass `onSubject`. Card step 4 (k 3 → 4) NOT done |
| Tests | v1's + `bestForSide` v2, marking, retrieve order, `answer()` pins 2 sides (`context:pinned-2`) and pins nothing unmarked; full suite 108 files / 1209 tests pass, `tsc` clean |

## Frozen criterion (copied verbatim from the card's v2 section before any v2 run)

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

## Runs (decide: the vital5 pair at t0; plus the full gate on questions72 must PASS)

| Run | Kit | Items | Base |
|---|---|---|---|
| `ios-cmpsplit-v2-v5-t0` | night kit + wiki-vital5 | questions-cmp78 | `ios-main-v5-t0` |
| `ios-cmpsplit-v2-t0` | night kit | questions72 | `ios-main-t0` (gate) |

## Results

vital5 pair: (a') 5/6 PASS, (c') PASS, (e') PASS, (b) FAIL (unreachable); **full gate on questions72 FAILS** (lan-cmp-004: an unnamed non-guide fallback, Economics of bitcoin, displaced the only on-topic guide). Not adopted as is; v2.1 fix described in `reports/night-2026-10-01/cmpsplit.md` § v2.

Release note (2026-10-27): the patch file itself is not published (it embeds questions of a competitor team's public test set as test strings). The `.sha256` pin next to this README is kept as the record.
