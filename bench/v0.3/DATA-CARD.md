# Data card: bench/v0.3

Full card: `DATASET_CARD.md` (a skeleton filled at the freeze), `HELD-OUT.md`, `plan/README.md`.

- **What:** no items. The folder holds the pre-registered plan for v0.2 / v0.3 (`plan/analysis-plan.md`, five addenda, metric scripts, the judge-core pin, the item spec), the item schema, and the validation, similarity, assembly and reference-import scripts.
- **Why no items:** v0.3 is a held-out set written outside the Claude family by the app maintainer with a non-Claude model. Plaintext is held offline and is never committed.
- **Hash chain:** `plan/SHA256SUMS`, `SHA256SUMS.addendum-01..04`, `COMBINED.sha256` (the sha256 of `plan/SHA256SUMS`). The plan was re-issued twice for redaction (see `plan/README.md`); only the public hashes listed there are valid here. Two v0.2 safety overlays and a draft analysis (`pack-matched.md`) are withheld because they derive from a burnt held-out set.
- **Scratch:** `work/` is for local drafts (git-ignored, blocked by the pre-commit hook).
- **Licence:** docs CC BY 4.0, scripts MIT.
- **Verify:** `python3 tools/verify-pins.py`.
