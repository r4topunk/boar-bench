# Arm `cmpsplit`: comparison entity split retrieval (QUEUE.md #3)

TL;DR: a two-entity comparison ("Japan or Germany", "bigger than a grizzly bear", "difference between A and B") is also searched once per side, and each side's best passage takes one of the usual top-K slots. Source: Sonar card `rnd/research/sonar/cards/comparison-entity-split-retrieval.md`. Engine: `upstream/main` 0cfd4a77 + `cmpsplit.patch`.

| | |
|---|---|
| Patch | `cmpsplit.patch` sha256 `9928cd28f13a6d28377090436d62cccf9a809515c614596a07f6d2870ed8847e` (`git diff 0cfd4a77` of worktree `<workspace>/wt/cmpsplit`, uncommitted) |
| Files | `src/rag/comparison.ts` (new, pure: `comparisonSides`, `bestForSide`, `mergeComparison`), `src/rag/retrieve.ts` (+25 lines: `retrieve()` = the question's own search, then the split), tests `src/rag/comparison.test.ts` (37), `src/rag/retrieve.comparison.test.ts` (3) |
| Engine tests | full suite 108 files / 1204 tests pass; `tsc --noEmit` clean |
| Behind a flag | no (it is an arm) |

## Frozen success criterion (copied verbatim from the card before any run)

- Primary metric (deterministic, so not hit by the 0.031 run noise): **both-sides-in-context rate** = share of comparison items where the final prompt's sources include ≥ 1 chunk titled with each side (gold sides listed per item before the run; I can supply them for the bench-60 comparison items + the 30 o2b comparisons, which stay internal).
- Success criterion (frozen before any run):
  - (a) both-sides-in-context on comparison items rises by ≥ 30 pp vs main (replay predicts ~57% → ~85% of sides);
  - (b) on the deterministic desktop run of bench-60, citation-check declines (`all-citations-removed` + `uncited-with-sources`) on comparison items fall by ≥ 3 items;
  - (c) no non-comparison item changes its retrieved sources (the splitter must not fire on them: check on all 60; ≤ 1 false fire allowed, hand-checked);
  - (d) confident-wrong (judge+Jev band) on comparison items does not rise; safety unchanged;
  - (e) desktop retrieval time p50 +≤ 50 ms on comparison items.
  - Fail (a) or (c) → stop. Pass → device full mode ×2 (coordinator schedules).

## What the patch does (card steps 1-4)

1. `comparisonSides(query)`: deterministic patterns `difference(s) between A and B`, `compare A and/with/to B`, `A vs/versus B`, `A differ(s) from B`, `A or B`, `A <comparative> … than B` (comparative within 4 words before "than"; never `more than <number>`, `rather/other than`); PT `diferença entre A e B`, `A ou B`, `mais/menos … (do) que B`, PT sides mapped through `englishNamesIn`. Strips determiners, possessives (`Mozi's idea of …` → `Mozi`) and aspect heads (`the Confucian view` → `Confucian`). Returns null (no split) for: a question word on one side (`Which countries are bigger than India`), a choice of actions (`Should I … or …`, `Devo … ou …`), sides with pronouns/auxiliaries, sides > 5 words, `either/whether`.
2. Each side: `retrieveOne(side, 3, { titles: [side] })` (format-2 packs: named-article path regardless of `NAMED_MIN_SHARE`); best passage = one whose title equals the side or its last words, singular (`adult male moose` → `Moose`), else the side search's top hit; disambiguation pages never.
3. Merge: side passages first (question order), then the question's own results; a side whose article is already in the question's top-K keeps that passage (moved first, no new passage); dedupe + `dedupeArticleCopies`; cut at the same top-K.
4. Skipped when `isHealthQuestion(query)` (imported from `src/routing/context.ts`). The action-choice guard also covers safety items `isHealthQuestion` misses (saf-004 burn, saf-007 earthquake, saf-009 frostbite).

## Comparison slice (gold sides, listed before the run)

A source counts for a side when its title matches the side's regex (case-insensitive). `split` = the patch's splitter fires (checked offline on the question text before the run).

| Item | Set | Category | Gold sides (title regex) | split |
|---|---|---|---|---|
| vit-hum-002 | bench v0.1 + vitalik58 | comparison | `mozi\|mohis` · `confucian` | Mozi · Confucian |
| lan-cmp-001 | bench v0.1 | comparison | `brazil` · `russia` | Brazil · Russia |
| lan-cmp-002 | bench v0.1 | comparison | `polar bear` · `grizzly\|brown bear` | polar bear · grizzly bear |
| vit-sci-002 | bench v0.1 + vitalik58 | comparison | `japan` · `german` | Japan · Germany |
| lan-cmp-004 | bench v0.1 | comparison | `moose` · `bison` | adult male moose · adult male American bison |
| lan-cmp-005 | bench v0.1 | comparison | `saltwater crocodile` · `nile crocodile` | saltwater crocodile · Nile crocodile |
| vit-cry-005 | bench v0.1 + vitalik58 | crypto (two-entity "difference between") | `privacy pool` · `tornado` | Privacy Pools · Tornado Cash |
| lan-cmp-003 | bench v0.1 | comparison, ONE named side ("Which countries … than India") | `india` | no split (by design) |
| vit-fa-004 | vitalik58 | comparison | `japan` · `nigeria` | Japan · Nigeria |
| vit-fa-005 | vitalik58 | comparison | `rhino` · `elephant` | rhinos · elephants |
| vit-fa-006 | vitalik58 | reasoning | `blue whale` · `dinosaur\|sauropod\|argentinosaurus` | blue whale · largest dinosaur |
| vit-fa-021 | vitalik58 | comparison | `lion` · `tiger` | lions · tigers |
| vit-fa-022 | vitalik58 | comparison | `elephant` · `rhino` | African elephant · white rhinoceros |
| vit-fa-014 | vitalik58 | comparison, ONE named side | `japan` | no split (by design) |

Slice for (a)/(b)/(e) on bench v0.1 (questions72): the 7 two-entity items above (6 `comparison` + vit-cry-005). Splitter fires on no other item of questions72 (60 public + 12 safety) nor of vitalik58: 0 false fires offline; (c) is re-checked on the traces (retrieval.raw of every non-slice item must equal main's).

## Kit coverage (checked 21:35, before any arm run)

The night's iPhone kit (essential bundled corpus + boar-crypto + boar-wikivoyage-en) has **no article for most gold sides**: no Mozi/Mohism, Confucianism, Polar bear, Grizzly bear, Moose, American bison, Saltwater/Nile crocodile or Privacy Pools title anywhere (SQL title search on the three libraries). Present: Wikivoyage Brazil/Russia/Japan/Germany destinations, crypto `Tornado Cash`. The card's replay ran on `wiki-vital5` (sha `d3b87d56…`), where every side exists. So on the night kit the split can recover at most vit-sci-002 (Japan) and one side of vit-cry-005: criterion (a) is bounded by coverage, not ranking. Hence one extra deterministic pair with the card's pack added (below); the criterion is evaluated on both and reported separately.

## Runs

iPhone profile (P2: 4 GB iOS, qwen2.5-1.5b, quick mode, crypto + Wikivoyage), questions72, seeds 42 and 43 (temp 0.7) as the night's main runs, + one temp-0 run for (b) ("deterministic desktop run").

| Run | Kit | Items | Sampler |
|---|---|---|---|
| `ios-cmpsplit-s42`, `-s43` (vs `ios-main-s42`, `-s43`) | night kit | questions72 | temp 0.7, seeds 42/43 |
| `ios-cmpsplit-t0` (vs `ios-main-t0`) | night kit | questions72 | temp 0 |
| `ios-cmpsplit-v5-t0` vs `ios-main-v5-t0` (extra) | night kit + `wiki-vital5` (`d3b87d56…`, linked as `<runner>/shared-data/packs/wiki-vital5.sqlite` → `pinned/d3b87d56…/`) | `questions-cmp78.jsonl` = questions72 + vitalik58 vit-fa-004/005/006/014/021/022 | temp 0 |

Slice script: `python3 adapters/desktop-node/arms/cmpsplit-slice.py MAIN.traces.jsonl ARM.traces.jsonl` ((a), (b), (c), (e); (d) needs the judge).

```bash
adapters/desktop-node/setup.sh 0cfd4a77 --patch adapters/desktop-node/arms/cmpsplit.patch --arm cmpsplit
adapters/desktop-node/run.sh --commit 0cfd4a77 --arm cmpsplit --requests runs/night-2026-10-01/ios-cmpsplit-s42.requests.jsonl --out runs/night-2026-10-01/ios-cmpsplit-s42.traces.jsonl
python3 harness/gate.py runs/night-2026-10-01/ios-main-s42.traces.jsonl runs/night-2026-10-01/ios-cmpsplit-s42.traces.jsonl --bench bench/v0.1
```

## Results

**v1 FAILS (a)** on both kits (vital5 t0: both sides in the prompt 3/12 → 4/12, +8 pp; night kit +0 pp); (c) PASS (0 false fires), gate PASS on all pairs, (e) +47…+97 ms desktop. Retrieval recovers sides (vital5 raw 17/24 → 22/24); context assembly loses them. Report: `reports/night-2026-10-01/cmpsplit.md`; v2 = `cmpsplit-v2.README.md`.

Release note (2026-10-27): the patch file itself is not published (it embeds questions of a competitor team's public test set as test strings). The `.sha256` pin next to this README is kept as the record.
