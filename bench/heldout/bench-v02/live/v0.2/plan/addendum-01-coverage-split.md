# Addendum 01 to the v0.2 analysis plan: knowledge-coverage split (pre-run)

Dated 2026-10-02, before any BOAR run on v0.2 and before the items/references freeze. Proposed by Sonar
(card bench-v02-coverage-split), accepted by the coordinator. The frozen plan (combined fe100e91…855e) is unchanged.

- **What:** a descriptive secondary view. Each keyed v0.2 item gets a mechanical coverage class
  (in-kit-key / in-kit-no-key / not-in-kit / unkeyed) from `coverage_classes.py` (this directory, sha256 in SHA256SUMS),
  using the item's precheck key + reference_sources URLs × the installed text of the **claim kit's** packs.
- **When:** run once by the coordinator right after the items + references freeze, against the claim kit (pack shas from the
  corpus manifest). The output file's sha256 is appended to this addendum before any BOAR run on v0.2. Each run is classified
  against its own kit.
- **Reporting rule:** the judged ratio per class is always shown next to the raw ratio (and the floor-removed and
  above-always-decline views), never alone and never as the headline. No claim decision (E3, K5, the bar) depends on it.
- **Blindness:** researchers see aggregate counts only; per-item classes stay with the runner.

## Run record (2026-10-02, after the second freeze d8154b6, before any BOAR run on v0.2)
- Tool: coverage_classes.py fe7ba6a1… executed from rnd/research/sonar/tools/ with its helper key_in_context.py c9124e43…
  (the helper was not in the first copy; recorded here).
- Claim kit A: in-kit-key 16 · in-kit-no-key 15 · not-in-kit 79 · unkeyed 0 → output sha256 aa8e5264…7bcd1
- Kit A + vital5: in-kit-key 30 · in-kit-no-key 44 · not-in-kit 36 · unkeyed 0 → output sha256 e140571a…43bd
- For comparison, v0.1 public (Sonar, kit A + vital5): 21 / 13 / 18 / 8 unkeyed. v0.2's items sit much more outside kit A
  (72% not-in-kit). Per-item classes stay in blind/bench-v02/coverage/ (runner only).
