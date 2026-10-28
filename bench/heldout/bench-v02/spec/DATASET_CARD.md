<!-- v1.1: this is the bench v0.1 card that the v0.2 writers used as their spec. The text is the public boar-bench v1.0 wording (bench/v0.1/DATASET_CARD.md, competitor anonymised); the private draft differed only in naming. -->
# Dataset card: boar-eval bench v0.1 (Offline Research Bench)

TL;DR: 60 public questions (33 carried over unchanged from v0, 27 new), the safety track v0.3, OSM gold for 3 venue items, and the held-out split as a hash only. **What changed from v0:** the 27 test cases taken from a competitor team's public repository were removed, and each slot now holds an original item of the same category and grading type. The competitor team is another entry in the same bounty (poidh #31). Its licence would have allowed reuse with credit, but we decided on 2026-10-01: **no competitor test cases in our bench.**

```sh
python3 bench/v0.1/build.py        # maintainer-only: rebuilds from the private workspace (reads rnd/bench, a private held-out dir, a competitor checkout); needs BOAR_PRIVATE_WORKSPACE
python3 bench/v0.1/validate.py     # exit 0 = all checks pass; run with --skip-heldout in this public repo
node bench/v0.1/refs/gen_refs.mjs  # only to regenerate missing new-item references (resumable), then build.py again
node harness/judge.mjs --traces my.traces.jsonl --out my.judgments.jsonl --bench bench/v0.1   # bench.json gives the harness its paths
shasum -a 256 bench/v0.1/questions.public.jsonl
```

## What changed from v0

| | v0 (`rnd/bench/questions/v0`, sha `dc859ebd…6b4f`) | v0.1 (this directory) |
|---|---|---|
| Test cases from the competitor team's fork (commit `87bb6e9abd`, `tools/e2e_cases.json` + `tools/e2e_battery_cases.json`) | 27 items, verbatim questions | **0**: removed |
| Original replacement items (`origin: "lantern-v0.1"`) | none | 27, one per removed slot, same position, category and grading type |
| Other v0 items (originals modelled on, and short quotes from, the post that inspired the bounty, BOAR eval v2 items) | 33 | 33, byte-identical lines |
| Items with a written gold `answer` | none | the 27 new items |

How the removed items were found: by their `provenance` field (`a competitor team's public test-case repo @87bb6e9`), not by guessing. Their ids, and the ids that replace them, are in `replacements.json`; no removed text is kept anywhere in v0.1.

How the new items were written:
- Each was written from the slot's category and grading type (overview of a place, numeric sanity, comparison with a clear verdict, honest refusal, health with hedging). None is a paraphrase of a removed question.
- **Word-Jaccard** (normalized token sets) of each new question: max **0.30** against the 31 competitor questions and max **0.29** against every other question in this split and the safety track (threshold < 0.5). Against the held-out split it is max 0.33 (threshold 0.8). Per-item numbers: `similarity.json`.
- Every new item has a gold `answer`, a `rubric`, a precheck `grading` (must_any / must_k / forbid / refuse_ok) and Wikipedia or official `reference_sources`. Facts were checked against those pages on 2026-10-01. **Each gold answer passes its own precheck** (`validate.py`).
- No item depends on "now" (prices, today's news). Population-of-a-year questions were replaced by stable facts.
- The mix follows the use stated in the post that inspired the bounty, "a casual info lookup / research tool": places a traveller may go to, history anchors, nature and science comparisons, everyday health.
- All new items are English, because v0 had no PT-BR items in these slots. PT-BR stays in the safety track.

| Removed (v0 id) | New id | Category | What the new item asks |
|---|---|---|---|
| vit-fa-001 | lan-exp-001 | explanation | Singapore: location, independence, official languages |
| vit-fa-002 | lan-exp-002 | explanation | Montenegro: capital, euro, coast, 2006 independence |
| vit-fa-003 | lan-rsn-001 | reasoning | Great Wall length; visible from the Moon? |
| vit-fa-004 | lan-cmp-001 | comparison | Brazil vs Russia population, verdict first |
| vit-fa-005 | lan-cmp-002 | comparison | Polar bear vs grizzly size, Kodiak caveat |
| vit-fa-006 | lan-rsn-002 | reasoning | Burj Khalifa at Baikal's deepest point: submerged? |
| vit-fa-007 | lan-ref-001 | honesty-refusal | 2017 Literature Nobel; declining is acceptable |
| vit-fa-008 | lan-hlt-001 | health | Raw vegan diet long term: hedged risks |
| vit-fa-009 | lan-hlt-002 | health | WHO weekly physical activity guideline for adults |
| vit-fa-010 | lan-hlt-003 | health | Mosquito-borne diseases; mosquitoes cannot transmit HIV |
| vit-fa-011 | lan-ref-002 | honesty-refusal | American Civil War winner, history anchor |
| vit-fa-012 | lan-ref-003 | honesty-refusal | Moonwalk before 1970? Apollo 11 anchor |
| vit-fa-013 | lan-rsn-003 | reasoning | Fastest land animal and how long it lasts |
| vit-fa-014 | lan-cmp-003 | comparison | Countries larger than India by area |
| vit-fa-015 | lan-rsn-004 | reasoning | World population in 1900; first billion |
| vit-fa-016 | lan-ref-004 | honesty-refusal | Iceland's area in km²; declining is acceptable |
| vit-fa-017 | lan-exp-003 | explanation | Kenya: location, capital, languages, independence year |
| vit-fa-018 | lan-exp-004 | explanation | Kyoto: what it is known for, former capital |
| vit-fa-019 | lan-exp-005 | explanation | Sahara: size, countries, Green Sahara past |
| vit-fa-020 | lan-exp-006 | explanation | Kilimanjaro: height, Tanzania, dormant volcano |
| vit-fa-021 | lan-cmp-004 | comparison | Bull moose vs bull bison weight |
| vit-fa-022 | lan-cmp-005 | comparison | Saltwater vs Nile crocodile size |
| vit-fa-023 | lan-rsn-005 | reasoning | Longest rivers; why Nile vs Amazon is disputed |
| vit-fa-024 | lan-rsn-006 | reasoning | Hundred Years' War: real length, two kingdoms |
| vit-fa-025 | lan-rsn-007 | reasoning | Berlin Wall: year built, year opened |
| vit-fa-026 | lan-ref-005 | honesty-refusal | 2016 Summer Olympics host city; declining is acceptable |
| vit-fa-027 | lan-exp-007 | explanation | Greenland: governance, capital, population, ice cover |

Composition is unchanged: explanation 11 · reasoning 11 · comparison 7 · crypto 7 · honesty-refusal 6 · health 4 · synthesis 3 · local-food 3 · danger-situation 3 · danger 2 · travel-practical 2 · travel-local 1. Grading: precheck 52 · venue-list 3 · firstaid 3 · judge-only 2. Five items are `danger: true` (all kept from v0; the overlay of safety track v0.3 still targets them).

## Files and licenses

| File | What | License |
|---|---|---|
| `questions.public.jsonl` | The 60-item public split, schema `questions.schema.json` | Per item `license` field: the 27 new items are **CC BY 4.0** (original); the 33 kept items keep their v0 terms (CC BY 4.0 bench originals; short quotations with link; public-health notes quoted with attribution) |
| `src/lantern-v0.1.items.json` | Source of the 27 new items, with the slot each one replaces | CC BY 4.0 |
| `replacements.json` | Removed v0 id → new id, category, grading type (ids only) | CC BY 4.0 |
| `similarity.json` | Jaccard numbers per new item (numbers only) | CC BY 4.0 |
| `competitor.denylist.json` | sha256 of each normalized competitor question plus its token count. **Hashes only; no text.** Used by `validate.py` to prove there is no residue | CC BY 4.0 (hashes) |
| `gold/food-00{1,2,6}.json`, `gold/NOTICE.md` | OSM vegan venue snapshots for the 3 venue-list items (copied from v0) | ODbL 1.0, © OpenStreetMap contributors |
| `corpus-manifest.json` | Pack, model and OSM snapshot pins at `boar-app@14de107` (copied from v0) | CC BY 4.0 |
| `heldout.manifest.json` | Held-out split: per-file sha256, counts, canonical sha256 (copied from v0). **The 30 items are never published** | CC BY 4.0 (hashes) |
| `safety/track.v0.3.jsonl`, `safety/rules.v0.3.json`, `safety/overlay.v0.3.json` | Safety track v0.3. In the public re-issue, `rules.v0.3.json` no longer carries the quoted NHS wording (rule ids, patterns and source URLs are kept; the quotes field is replaced by a count) | CC BY 4.0 (short quotations of public US guidance, with links) |
| `refs/MANIFEST.jsonl`, `refs/MANIFEST.json` | Per-item sha256 of each reference answer, model, CLI, prompt sha, date | CC BY 4.0 (hashes) |
| `refs/refs.jsonl`, `refs/NOTE.md` | Reference answer **text** (public re-issue: local-path field removed, answers byte-identical to the private file; see `refs/NOTE.md`) | CC BY 4.0 for our wrapper; answers are Claude Opus + web search output and may quote their cited sources, which keep their own terms |
| `build.py`, `validate.py`, `refs/gen_refs.mjs`, `questions.schema.json` | Builder, validator, reference generator, item schema | Apache-2.0 |
| `bench.json` | Layout for the harness (`scorers/bench.py`): questions, refs, safety dir and track | CC BY 4.0 |
| `gold/sources.json` (from `src/gold-sources.json`) | Gold source titles for the retrieval axis: 26 new items plus 13 kept items whose subject article is unambiguous; the rest are left out on purpose | CC BY 4.0 |
| `safety/safety_check.py` | Safety matcher v0.3, a byte copy (identical to `scorers/vendor/safety`), so the bench safety dir loads on its own | Apache-2.0 |
| `SHA256SUMS.json` | sha256 of every committed file in this directory | — |

## References (frontier + web)

- **33 kept items:** the frozen v0 answers are reused by hash (`claude-opus-5-5`, Claude Code 2.1.286, prompt `reference.v1` sha `d5144343…`, generated 2026-09-30 22:28–22:54Z). `validate.py` checks that each one hashes to the same value as the frozen v0 file (sha `cfb8cecc…`).
- **27 new items:** generated for v0.1 with the same recipe: `claude-opus-5-5` (all 27 rows), Claude Code 2.1.287, prompt `reference.v1`, between 2026-10-02 00:08:49Z and 00:18:11Z. That is 27 sequential calls with 0 failures, 448 s of call time. **All 27 pass their item's precheck.** One forbid term (`lan-ref-004`) was narrowed after generation because it also matched a correct glacier area; no question text changed.
- Recipe (same as v0): the shared `claude -p` helper with API keys stripped from the environment (no API key, own CLI login), `--model opus`, system prompt `reference.v1`, tools WebSearch + WebFetch, one call at a time with a 5 s gap, 1 retry on error, stop on a rate limit.
- These answers are AI-generated and reflect the web on their generation date. They are **not ground truth**.

## Checks (`validate.py`)

SHA256SUMS · schema · 60 items, unique ids, 5 danger, 33 kept + 27 new · kept lines byte-identical to v0 · replacement slots keep category and grading type · new items complete, and each gold answer passes its own precheck · every precheck term compiles · venue gold files · safety overlay targets · **competitor residue = 0** (no provenance, URL or id; a hashed n-gram scan of every file in this directory; a literal grep of the 31 question strings when the local checkout exists; the denylist is re-derived from git) · Jaccard < 0.5 · held-out integrity and contamination (counts only) · references hash-checked and complete.

## Decisions / Options / Tasks

- **Flagged items:** 25 items (`vit-*`, origin `vitalik-verbatim` / `vitalik-style` / `vitalik-verbatim-paraphrase`) quote or paraphrase public posts by a named author as short quotations, each with its source link in `reference_sources`; we release only our question wrapper under CC BY 4.0 and make no claim over the quoted text. If you object to a quotation, open an issue and the item will be replaced. Three danger items (`dng-001`, `dng-002`, `dng-005`) quote public-health guidance in their rubric notes (US CDC/NIOSH, short and attributed).
- **Public re-issue (2026-10):** the files here are a curated snapshot. The released `SHA256SUMS.json` covers this directory as shipped; `build.py` is the maintainers' builder and reproduces the private tree, which differs in the files listed in `refs/NOTE.md` and in the safety rules (NHS wording removed). The emergency detector used by BOAR's own runner is not released. `corpus-manifest.json` is also a re-issue: the two pack `sourceUrl` values point at the public dataset `r4topunk/boar-packs`, so its sha256 differs from the private copy; the pack file hashes inside it are unchanged.
- **Decisions:** no competitor test cases in the bench (team, 2026-10-01). v0 stays frozen; v0.1 is a new version. The kept items are not edited, not even for known grading fixes; fixes go into v0.2.
- **Options:** human (non-Claude) spot-check of the 27 gold answers; add GPS-context items once the app injects location.

## UNKNOWN

- Whether the build is reproducible off the origin machine: it reads private inputs (v0 split and refs, the held-out files, a competitor checkout). Elsewhere, verify with `validate.py --skip-heldout` and the hashes.
- The device and proxy numbers from v0 do not carry over to the 27 new items. They need new runs.
- The new gold answers and rubrics were written and fact-checked by an AI agent against the cited pages. No human has reviewed them yet. Health, first-aid and safety content (v0.1 health and danger items, their gold answers, the safety track and the safety rules) is AI-reviewed, not clinically reviewed. Nothing in this repository is medical advice.
