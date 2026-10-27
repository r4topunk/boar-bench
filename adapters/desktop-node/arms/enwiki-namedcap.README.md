# Arm `enwiki-namedcap` (QUEUE #6b): top-100k enwiki kit + named-article cap in `retrieveOne`

TL;DR: the enwiki arm (#6, `enwiki-top100k.README.md`) plus one engine rule: named-article passages from the large packs are capped at `MAX_CHUNKS_PER_ARTICLE` (2) per article, as the fusion already caps every other article; a single named article keeps the usual top-K cut. Engine: 0cfd4a77 + `enwiki-namedcap.patch`; kit = kit A + vital5 + `boar-wiki-en-top100k` (sha256 `aff5fd11…19bd`).

| | |
|---|---|
| Patch | `enwiki-namedcap.patch` sha256 `df25549d4dfdc40606c8d60c4eee6f00e974686e363143465b83aeef52c27e56` (worktree `<workspace>/wt/enwiki-namedcap`, uncommitted) |
| Change | `src/rag/retrieve.ts` `retrieveOne`: `named` filtered to ≤ 2 passages per `docId`; slice at `topK` when the named passages come from one article (else `max(topK, named.length)` as before). Test `src/rag/retrieve.namedcap.test.ts` (2). Full suite 107 files / 1166 tests, `tsc` clean |

## Frozen criterion (copied verbatim from the card's v2 section before any run)

## v2 proposal: named-article cap (pre-validated on the v1 traces, 2026-10-02 ~10:40)

- **Change (engine, `retrieve.ts` `retrieveOne`, 1 rule):**
  - apply the existing per-article cap `MAX_CHUNKS_PER_ARTICLE = 2` (`pure.ts`, today applied only inside `fuseRetrievalResults`) to the named-article passages too;
  - keep `named` first, at most 2 per article;
  - cut at `topK` instead of `max(topK, named.length)` when the named passages come from one article.
- **Why:** with k = 3 (lookup) a single named article from the big pack took every slot.
  - lan-ref-001: "Nobel Prize in Literature" ×3 displaced vital5's "Kazuo Ishiguro"; then the year rule dropped all 3, so declined.
- **Pre-validation on `ios-enwiki-s42-kic`:**
  - 18/72 items have one title holding ≥ 3 raw slots, e.g. Nobel ×3, Wikivoyage: Accra ×3 (d/acc), Population density ×3, Headache ×3, Hypothermia ×3, Burn ×3.
  - In **0** of the keyed ones does the answer key appear only in the 3rd+ passage of that title (checked on the shown passage text). So the cap costs no key on this run and frees a slot in 18 items.
  - What fills the freed slot is unknown without a run: the next fused candidate (for lan-ref-001, base raw rank 2 = Kazuo Ishiguro).
- **Criterion for `enwiki-top100k + named-cap` (frozen now; same pair design and gate as v1):**
  - (a′) exact key-in-context `pre` vs `ios-main-v5-s42-kic`: ≥ +5 gained and ≤ 1 lost;
  - (a″) lan-ref-001 has a source with "Ishiguro" in the pre-answer sources;
  - (b), (c), (e) as v1;
  - (d) quality reported only.

Plus (coordinator): gate PASS (multi-base, v0.4). Runs: iPhone s42 with `--event-source-text` (exact key-in-context vs `ios-main-v5-s42-kic`), then the Android 4B only if (a′) holds.

## Results

**FAIL**: (a′) gained 8 / lost 6; (a″) lan-ref-001's freed slot went to Wikivoyage: Nobel tourism; gate lost-shown-sources 3. Android not run. Report: `reports/night-2026-10-01/enwiki-top100k.md` § v2.
