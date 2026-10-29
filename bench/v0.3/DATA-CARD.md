# Data card: bench/v0.3

Full card: `DATASET_CARD.md` (an unfilled template: no items exist), `HELD-OUT.md`, `plan/README.md`.

- **What:** no items. The folder holds the pre-registered plan for v0.2 / v0.3 (`plan/analysis-plan.md`, five addenda, metric scripts, the judge-core pin, the item spec), the item schema, and the validation, similarity, assembly and reference-import scripts.
- **Why no items:** v0.3 was planned as a held-out set written outside the Claude family with a non-Claude model. That front (OF-3) was dropped before any item was written, so no v0.3 plaintext exists anywhere and nothing is withheld. The held-out sets that did exist (bench v0.2, V-para and the others) and the v0.4 ruler are retired and public under `bench/heldout/` and `bench/v0.4/` since v1.1.
- **Hash chain:** `plan/SHA256SUMS`, `SHA256SUMS.addendum-01..04`, `COMBINED.sha256` (the sha256 of `plan/SHA256SUMS`). The plan was re-issued twice for redaction (see `plan/README.md`); only the public hashes listed there are valid here, except the pins of the vendored safety rules v0.5 to v0.7 in the addenda: those files were re-released in v1.1.2 with copyright wording withheld, and `tools/verify-pins.py` lists them as KNOWN. Two v0.2 safety overlays and a draft analysis (`pack-matched.md`) are withheld because they derive from a burnt held-out set.
- **Scratch:** `work/` is for local drafts (git-ignored, blocked by the pre-commit hook).
- **Licence:** docs CC BY 4.0, scripts MIT.
- **Verify:** `python3 tools/verify-pins.py`.
