# Contributing to the bench 

TL;DR: there are two kinds of contribution. (A) **Held-out items** in the v0.3 schema: you commit the hashes first and release the plaintext only on the published date, so nobody can tune on them. (B) **Leaderboard rows**: aggregate numbers from your own traces, judged with the frozen judge, plus the hashes that tie them to your files. Item text never goes into a PR before its release date.

## Rules that apply to everyone
1. **No tuning on held-out items.** Once you have seen a held-out item's text, its answer or any per-item number, it is dev data for you. Any engine change chosen after seeing a held-out number turns that set into dev for your app. A new claim then needs a new set (the "burn rule").
2. **Writer family.** Items, gold and references are written by a human or by a model from a **different family than the app's model and than the judge** (the judge is Claude). Record the exact model name in `provenance`. Do not show the writer model any bench material, app output or traces.
3. **Plaintext stays out of git until its release date.** Only hashes, ids, counts and numbers go in. The pre-commit hook (`tools/hooks/pre-commit`; install it with `git config core.hooksPath tools/hooks`) blocks the common leaks: item lines, `questions.v0N*.jsonl`, `refs/refs*.jsonl`, `refs/raw/`.
4. **One claim run per build per held-out set**, authorised in writing (commit, patch sha, seeds, judge version) and hashed before the run.
5. Every exposure (a run, a judge pass, someone reading an item) is one line in the set's exposure log.

## A. Contributing held-out items (v0.3 schema)

**Schema:** `bench/v0.3/questions.schema.json`. Writer prompts with format-only examples (ids `…-98/-99`) are in `docs/contrib/writer-prompts.md`, and the reference recipe is in `docs/contrib/refs-prompt.md`.

| Field | Rule |
|---|---|
| `id` | `v03-<category>-NN` within your batch; maintainers re-prefix contributor batches (e.g. `v03x-<team>-<category>-NN`) |
| `category` | explanation · reasoning · comparison · crypto · honesty-refusal · health · danger · synthesis · travel-practical · travel-local |
| `question` | English; a mix of first-person, direct-question and imperative phrasing; does not depend on "now" (no prices, no news) |
| `answer` (gold) | required; must pass its own `grading` precheck |
| `rubric` | written for the judge: what a good answer contains, plus 1–2 `Penalize:` bullets. Honesty items name their type and a `Decline rule:` |
| `grading` | precheck: `must_any` / `must_k` / `forbid` / `refuse_ok` (refuse_ok true only for unknowable or time-pinned items) |
| `reference_sources` | 1–5 URLs. The key fact and every number in the rubric must appear on a cited page; check them by hand |
| `origin`, `license`, `provenance` | `"v0.3-ext"`, `"CC-BY-4.0"`, `"writer-human+<model exactly as in the picker> YYYY-MM-DD"` |
| `danger` | true for danger items; conduct must come from public guidance (Ready.gov, CDC, NWS, WHO, NIH) |

Quality bars, checked by the maintainers' gates G1–G4 (the scripts in `bench/v0.3/`):
- ≥ 40 % of items centred outside Europe and North America; at most 2 per country; each item hinges on ≥ 1 concrete checkable fact. No canonical or textbook-famous topics (see the do-not-use list in the writer prompts).
- Similarity: 0 pairs with word-Jaccard > 0.30 or bge-small cosine ≥ 0.90 against the public set, the safety track and every held-out pool. The maintainers run this script-only and publish ids and numbers only.
- A fresh topic reviewer (a model that has never seen the bench internals) looks for same-topic pairs the thresholds miss.

**Hash first, plaintext later:**
1. Write the items locally in a folder **outside any git repo**.
2. Run `python3 bench/v0.3/validate.py --dir <your folder>` (format + precheck).
3. Commit only `SHA256SUMS.items` (sha256 of each canonical item line), `COMBINED-FREEZE.sha256` and a `DATASET_CARD.md` (counts, writer model, dates, limits) in a PR. Also send the plaintext to the maintainers through a private channel they name (not in the PR).
4. The maintainers run G1–G4 and the references (same recipe, a non-Claude model with web search), then freeze. The freeze commit carries the hashes and a release date.
5. **Release schedule:** the plaintext + references are published on the release date (proposal: after the bounty's judging window, or after the last scheduled claim run, whichever is later). Anyone can then check that the plaintext hashes to the frozen file.

## B. Contributing a leaderboard row (aggregate only)

1. Run your app on `bench/v0.1` (and on a held-out set only through the maintainers' claim-run protocol). Two seeds is recommended.
2. Judge with `harness/judge.mjs`: Opus, judge.v1, both orders, `--strict --floor-errored`. See TRACE-FORMAT.md.
3. Compute `metrics/floor_metrics.py` (raw, floor-adjusted, above-decline with CIs) and W/T/L.
4. Open a PR that adds **one row** to `leaderboard/README.md` and one folder `leaderboard/<team>-<date>/` with:
   - `row.json`: app name and version, engine commit, model + quantisation, device or desktop proxy, offline yes/no, seeds, n judged, raw / floor-adjusted / above-decline with CIs, W/T/L, p50 latency, judge model + CLI version.
   - `SHA256SUMS`: the sha256 of your traces and judgments files. The files themselves are optional for v0.1 (it is public); **never** include files for held-out sets.
5. Maintainers re-check the arithmetic from your judgment rows if you share them. Rows without shareable judgments are marked "self-reported".

Not accepted: numbers from a different judge or from regenerated references in the main table (a separate "other judge" table is fine); items written by the same model family as the app; any PR that contains held-out item text before its release date.
