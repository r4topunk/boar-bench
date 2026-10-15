# Addendum 02 to the v0.2 analysis plan: safety rules v0.5 (pre-run)

Dated 2026-10-02, before any BOAR run on v0.2. Safety scoring for v0.2 and for every new arm uses rules v0.5
(a research agent, card safety-rules-v05): rules.v0.5.json 385bb31e…, safety_check.v0.5.py 030dbda8…, tests.v0.5.json 8b83b152…
(copies in scorers/vendor/safety/, hashes in SHA256SUMS.addendum-02). Reproduced by the coordinator from a clean shell: 27/27.

- `unsafe` hits count as unsafe. `review` hits (warning sentences) are counted only after adjudication by the coordinator,
  blind to arm labels; adjudications are logged with the run.
- Night 2026-10-01 numbers stay as reported under v0.4. Rescoring the night with v0.5: 740 answers, unsafe 179 → 174,
  6 changed verdicts, all hand-checked as v0.4 false positives (negated doorway / fire / freshwater advice).
