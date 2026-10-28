# Changelog

## v1.1, 2026-10-27: held-out sets and the v0.4 ruler opened

The project was submitted; the author retired every held-out set and opened everything that is not private to him or to the app maintainer.

Added
- `bench/heldout/`: 19 retired held-out sets (bench v0.2 with drafts, rewrites, plan, addenda and references; V-para with OSM venue gold and references; health-fresh1-3; chat-v3; meta-fresh1; es-fresh1-2; crisis1; hm-fresh, hm-fresh2, hm-fresh3, hm-loc1; h1-fresh; h2-fresh; h2-pool; o2-blind-items; o2v2c-fresh). One `CARD.md` per set (status, writer, licence, content note, verification); the original set READMEs are kept byte for byte. `HASHES.md` / `HASHES.tsv`: original and released sha256 of every opened file.
- `bench/v0.4/`: the ruler in plaintext: `items.jsonl` and `items.candidate.jsonl` (byte-identical to the v1.0 commitments `f9ad2f2f...` / `23b6febf...`), `REJECTED.jsonl`, `refs/v2/` (Claude and Codex reference halves and call logs), `drafts/`, `DISAGREEMENTS.md`, `CHANGELOG.md`; the card is the freeze card with a v1.1 status, licence and change note.

Changed
- `bench/v0.4/refs/v2/MANIFEST.json`: the Claude reference pin changed from `b27eac37...` to `d83e5186...` (per-call usage fields dropped, answers byte-identical); the file's own sha changed from `c6d58017...` to `41b38585...`.
- `tools/verify-pins.py`: v0.4 items are checked (no longer WITHHELD); pin files written for the private lab layout are reported as KNOWN with the reason; a pin file one folder below the root it names resolves.
- README, NOTICE, LICENSE-DATA, DATA-CARD: held-out sections updated, licence rows and content note for the opened sets.

Withheld (still)
- 75 NHS quotations in crisis1, hm-fresh2, hm-fresh3 and hm-loc1 (org and URL kept); spend, token and plan fields; the app maintainer's data (none was found in any set); a competitor team's test questions.

## v1.0, 2026-10-26: full open record

History is not exported: this is a clean, single-snapshot release that supersedes the earlier curated public release of 2026-10-15 (bench v0.1 + harness only).

Added
- The whole evaluation side of the research: the cross-family judge (`harness/judge-codex.mjs`), the pointwise checklist judge (`harness/judge-v2.mjs`), gate / diff / stability / ladder / report tools, the vendored judge libraries and safety checkers v0.3 to v0.7.
- `adapters/desktop-node/` (the engine runner, shims, run profiles, replay tool), 19 arm patches with `.sha256` pins, 21 arm READMEs and one frozen criterion.
- 14 pack self-test sets and 6 slices under `bench/selftest/` and `bench/slices/`; `bench/v0.3/` plan, scripts and addenda; `bench/v0.4/` commitments (hashes only, derived card).
- `devices/` kit, `reports/` (night, device, anchor reports), `docs/ADR-001`, `tools/verify-pins.py`, `BOM.md`, `DATA-CARD.md`, `CITATION.cff`.
- `pnpm test:all` (TypeScript, Python, Node and hook tests plus data validation and hash pins).

Changed
- Code licence is MIT (was Apache-2.0 in the 2026-10-15 release); data and docs stay CC BY 4.0.
- `bench/v0.1/refs/refs.jsonl` re-issued: the per-call price fields (`listPriceEquivalentUsd`, `costBasis`) were dropped and the `via` label neutralised, so the file sha256 changed from `689c6f0457db...` to `4a7da939ed84...`. Answer texts are byte-identical, and the judge reads `answer` only, so existing numbers stand. `refs/MANIFEST.json`, `refs/NOTE.md` and `SHA256SUMS.json` were re-pinned.
- The competitor test-case repository is no longer named: the denylist file that carried its name is now `bench/v0.1/competitor.denylist.json` (hashes unchanged), and the similarity keys and `validate.py` were renamed to match.
- `bench/v0.3/plan` was re-issued a second time (`item-spec.draft.md`, `README.md`); `SHA256SUMS` and `COMBINED.sha256` regenerated, the hash map in the plan README lists the valid public hashes.
- Wording that named the account or plan the judge runs on, per-call USD prints, host names, device identifiers and bundle ids were neutralised in code, docs and reports (behaviour unchanged). Vendored files whose comments changed were re-pinned in `scorers/vendor/SOURCE.md`.
- `scorers/score.py` / `harness/report.py`: the JSON key and label `vitalik_bar` became `bounty_bar`.
- `harness/tests/judge-codex.test.mjs` resolves the adapter relative to itself (it failed when run from the repository root).
- Per-item ids and condition words of private held-out sets were removed from arm READMEs and reports (counts and verdicts kept).

Withheld
- Held-out and burnt sets, traces and judgments of runs on them, the app maintainer's data, run traces (`runs/`), model weights, packs and replay caches (listed in `BOM.md`), `fa-cards.patch`, the competitor team's published questions. See README, "What is not here".

Pre-push pass (2026-10-27)
- Three arm patches (`adapters/desktop-node/arms/cmpsplit*.patch`) withheld: they embed questions of a competitor team's public test set; their READMEs and `.sha256` pins stay, and `tools/verify-pins.py` reports them as WITHHELD.
- README: the engine base is reachable through the author's public fork (`github.com/r4topunk/boar-app`, contains `0cfd4a77`); a no-cost scoring demo on traces stored in `boar-research`; `rnd/...` provenance paths resolve against `boar-research`; one-machine runs via `BOAR_EVAL_HOST=localhost`.
- `BOM.md`: corpus URLs point at the public fork (`raw.githubusercontent.com/r4topunk/boar-app/<commit>/...`).
- The research record quotes the old `refs.jsonl` sha256 (`689c6f04…`) in its queue; judgments made against it stay valid (answers byte-identical, see `bench/v0.1/refs/NOTE.md`).

## 2026-10-15: first public release (superseded)

bench v0.1, harness, scorers and metrics under Apache-2.0 / CC BY 4.0 (single commit, not retained).
