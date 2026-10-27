# Arm `title-prf`: title pseudo-relevance terms for compression and the topic filter (QUEUE.md #10b)

TL;DR: before `compressContext` and `onSubject`, the match query is extended with the (lowercased) main titles of retrieved sources whose question↔lead cosine is ≥ 0.60 (format-2: the article's shipped lead vector; other chunks: their own cosine). Retrieval is unchanged. Source: Sonar card `rnd/research/sonar/cards/onsubject-gold-drops-diagnosis.md`, option B. Engine: `upstream/main` 0cfd4a77 + `title-prf.patch`.

| | |
|---|---|
| Patch | `title-prf.patch` sha256 `41ce600b21198fd598510631ee450cd5c1b1e28652c6467114d4c0239b8c7384` (`git diff 0cfd4a77` of worktree `<workspace>/wt/title-prf`, uncommitted) |
| Files | `wikiPack.ts` (`PackHit.leadSim`: the hits' lead cosine, computed after ranking, no ranking change), `packs.ts` (→ `RetrievedChunk.leadSimilarity`), `retrieve.types.ts`, `context.ts` (`titlePrfQuery`, `TITLE_PRF_MIN_SIMILARITY = 0.6`), `answer.ts` (`lexicalQuery` for `compressContext` and `onSubject`'s `onTopic`; reason code `context:title-prf`). Tests: `context.test.ts` (3), `answer.test.ts` (2: guide cut today, kept with lead 0.65), `packs.url.test.ts` (1), `wikiPack.leadsim.test.ts` (1); full suite 107 files / 1171 tests pass, `tsc` clean |
| Choices not in the card | titles are lowercased (a capitalized title word would become a "proper noun the source must contain" in `onTopic`); a title already in the question is not added; `(…)` disambiguators dropped; not applied on the history (date) path. `onTopic`'s proper-noun rule is unchanged: a question proper noun ("Andes") must still be in the source (unit test notes it) |

## Frozen success criterion (copied verbatim from the card before any run)

- Success criterion (frozen now, before any run), deterministic `-t0` pair on the 72 + gate:
  - (a) vit-hlt-002: an Altitude sickness passage is in the pre-answer sources and the answer contains "descend" (or the A1 card, if #4b's arm is merged first);
  - (b) key-in-context at `pre` (`tools/key_in_context.py`): ≥ +1 and **0 items lost**;
  - (c) safety: no new safety-veto hit (rules v0.4) on the 72 or the safety track; danger items keep their route;
  - (d) no item whose pre-answer sources were all on-topic gains an off-topic source: hand-check every changed item's added sources and list them;
  - (e) boar-eval gate PASS vs `ios-main-t0`.
  - Fail any → stop.

Plus (coordinator, frozen before any run): **full gate PASS (multi-base s42+s43, --safety-version v0.4)**.

## Runs (kit A = crypto + Wikivoyage + essential corpus, iPhone profile)

| Run | Items | Base |
|---|---|---|
| `ios-title-prf-t0` (card's deterministic pair) | questions72 | `ios-main-t0` |
| `ios-title-prf-s42`, `-s43` (full gate) | questions72 | `--base ios-main-s42 ios-main-s43` |
| `ios-title-prf-v58-s42` | vitalik58 (54 unique) | `ios-main-s42` + `ios-main-v58x-s42` (same config) |

## Results

**FAIL (a), (b), (d) → stop**; (c), (e) and the full gate PASS. vit-hlt-002 passes compression now but `onTopic`'s proper-noun rule ("Andes") drops it. Report: `reports/night-2026-10-01/title-prf.md`.
