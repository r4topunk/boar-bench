# Changelog

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
