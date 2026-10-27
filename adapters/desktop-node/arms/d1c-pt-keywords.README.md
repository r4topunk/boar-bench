# Arm `d1c-pt-keywords`: Decision 1, option C (PT answer words mapped to English before the citation check)

TL;DR: for a Portuguese question only, the citation word check (CT-1 `checkCitations` and its inverse `attributeCitations`, `src/routing/citations.ts`) reads the answer sentence through the bundled PT->EN lexicon (`assets/lexicon/pt-en.json`, the one `englishNamesIn` uses): longest run of words first ("prova de participação" -> Proof of stake), a key unit counts as supported when its own words OR all words of its English title are in the source; PT function words ("foi", "também", "pelo") stop being key words, as English stopwords already aren't. Bars unchanged (0.5 keep, 0.75 add, ≥ 2 key units). English questions take the exact old code path. Engine: `upstream/main` 0cfd4a77 + `d1c-pt-keywords.patch`.

| | |
|---|---|
| Patch | `d1c-pt-keywords.patch` sha256 `31ece3fe6ce0a29a66a9f55a1d7cc53cf940dfb21c42791b63f5b8eedc6ffcc3` (`git diff 0cfd4a77 -- src` of worktree `<workspace>/wt/d1c`, uncommitted) |
| Files | `src/routing/citations.ts` (`ptKeyUnits`, `ptCitationSupport`, optional `lexicon` argument on `citationSupport` / `checkCitations` / `attributeCitations`), `src/routing/answer.ts` (`citationLexicon = pt ? ptLexicon() : undefined`, passed to both checks; reason codes `citations:pt-en-lexicon-kept` / `-added` when the lexicon changed the outcome), tests `src/routing/citations.pt.test.ts` (7, incl. the real asset), `src/routing/answer.test.ts` (Sextant q7: the PT greenhouse answer now keeps its [1]; EN never gets a `citations:pt-en*` code) |
| Engine tests | full suite 107 files / 1171 tests pass; `tsc --noEmit` clean (the cry-014 PT "32 ETH" test still declines) |

## Frozen success criterion (written 2026-10-01 before any arm run; patch sha above)

Seed 42, iPhone profile P2 (qwen2.5-1.5b, quick mode), PT slice (`bench/slices/citation-pt/citation-pt.jsonl` sha `8f3bf231…`, 20 PT + the 20 EN originals) and the 72-item night set. Adopt C only if ALL hold:
1. **C-pt:** PT items declined by `grounding:all-citations-removed-declined-compact` drop by **≥ 50%** vs main (PT slice; the 3 PT items of the 72 set are safety items that never reach the check). Main = 0 such items → not evaluable (reported, not a pass).
2. **C-en:** **0 change on EN items**: every EN trace (20 EN slice items + 69 EN items of the 72 set) is identical to main's after dropping wall-clock / identity fields only (`createdAt`, `runId`, `timing`, `events[].tMs`, generation `prefillMs`/`decodeMs`, `runtime.loadAvg1m`, `runtime.versions`, `engine.arm`, `engine.dirty`, `config.arm`). "Byte-identical" in that sense; any other difference fails.
3. **C-gate:** `harness/gate.py MAIN ARM --bench bench/v0.1` PASS.
Reported, not gating: `uncited-with-sources` declines on PT, and the judge on PT items whose outcome changed (a kept wrong answer is the arm's risk).

## Runs

```bash
BOAR_EVAL_MIN_FREE_GIB=13 adapters/desktop-node/setup.sh 0cfd4a77 --patch adapters/desktop-node/arms/d1c-pt-keywords.patch --arm d1c-pt-keywords
adapters/desktop-node/run.sh --commit 0cfd4a77 --arm d1c-pt-keywords --requests runs/night-2026-10-01/d1/ios-d1c-slice40-s42.requests.jsonl --out runs/night-2026-10-01/d1/ios-d1c-slice40-s42.traces.jsonl   # also -q72-s42, -s43; all runs: runs/night-2026-10-01/d1/plan.sh
python3 adapters/desktop-node/arms/d1-metrics.py MAIN.traces.jsonl ARM.traces.jsonl
```

## Results

**REJECT** (seed 42; seed 43 agrees). C-pt FAIL (PT `all-citations-removed` 11 → 10, −9%; s43 12 → 11); C-en PASS (89/89 EN traces identical at seed 42); C-gate PASS (also two-run v0.4). Quality ratio Δ inside the noise (q72 0.000, slice +0.010 vs MDE 0.039). Safe, but nearly inert: the 1.5B's PT drafts rarely contain a sentence the source supports. Details: `reports/night-2026-10-01/decision1.md`.
