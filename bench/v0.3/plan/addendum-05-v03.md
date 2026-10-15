# Addendum 05 (DRAFT): bench v0.3-ext, the claim set written outside the Claude family

**DRAFT, not in force. Hash before any run on v0.3** (add `SHA256SUMS.addendum-05` next to this file and record the combined
sha in `COMBINED-FREEZE.sha256` at the 10-20 freeze). Fields marked TBD are filled at the freeze, before any BOAR run on
v0.3; nothing here is edited after hashing (a change = a new hashed addendum). Source: rnd/research/coordinator/BENCH-V03-SPEC.md.

The files in this folder other than this addendum (and `vstyle.ids`, if D3 = fold) are byte-identical copies of
`bench/v0.2/plan/`, addenda 01–04 included; `analysis-plan.md` applies to v0.3 as amended below. Known at copy time
(2026-10-07): `SHA256SUMS.addendum-01` fails on `addendum-01-coverage-split.md`, as it does in v0.2, because the
"Run record" section was appended in `a913563` after that sum was taken; the other four SHA256SUMS files verify.

## 1. Set
- **v0.3-ext:** n = TBD (110, or the pre-declared 60 = ids 01..w1 per category, spec §2 and §9 D2), origin `v0.3-ext`,
  English, all precheck-graded, refuse_ok = 8 (110) / TBD (60), danger = 10 (110) / 6 (60). Strata as v0.2 (`strata.py`).
- **Writer:** the maintainer, by hand, with one non-Claude model in its web UI (no API, no automation): model TBD (D1), exact picker
  name recorded per item in `provenance` (`writer-human+<model> 2026-10-DD`). Questions, gold answers, rubrics and
  precheck terms were fact-checked by hand against `reference_sources`; Claude did not edit item text.
- **Gates:** G1 `validate.py`, G2 `similarity.py` (incl. v0.2-new and V-para pools), G3 fresh-Opus topic review, G4 refs;
  results TBD (sha of `similarity.json`, G1 log line).
- **Safety:** rules v0.7 (addendum 04) via the explicit `safety_rules` mapping in `assemble.py`; unmapped danger items
  (expected: most) are scored for safety by the judge rubric's "Penalize:" bullets only. Mapped count TBD.

## 2. References
- Channel `reference.v1-webui`: reference.v1 (sha256 `d5144343…`) pasted verbatim into a ChatGPT Project or Gemini Gem,
  same model and account as the writer, memory off, one fresh chat per item, question only. Model TBD; vendor TBD.
- Imported by `refs/import_web_refs.py`, frozen by `refs/build_manifest.py --freeze` (n/n). MANIFEST shas TBD.
- References are no longer from the judge's family, so v0.3 ratios are **not 1:1 comparable** with v0.1/v0.2 ratios.

## 3. Headline and reporting (amends analysis-plan §3–§4 for v0.3)
- **Headline:** floor-adjusted ratio Σ(S−1)/Σ(R−1) (`floor_metrics.py`, `above_min`), with win/tie/loss vs the
  reference and the share of items with usefulness ≥ 3/5, each with the stratified two-level CI. Raw ratio second.
  (Per pipeline audit D1 and the workspace state block; formal decision status: TBD.)
- Above-decline: D measured on this run's own declines, shown beside the fixed D = 0.306.
- Reference mean R on v0.3 is reported beside ≈ 4.9 on v0.2 (first signal of the reference-family effect).
- **V-style slice** (only if D3 = fold): ids in `vstyle.ids`, floor-adjusted + win rate, descriptive only.

## 4. Runs
- **Claim build:** TBD (cut 6 or cut 7), seeds 42 + 43, judge.v1 both orders, outputs in `private/bench-v03/runs-<build>/`.
- **Control:** cut 6 on v0.3 (cut-to-cut on the same set); reduces to judging FACTS-fired items if the claim build is cut 7.
- **Anchor:** Haiku no-web, 1 seed (0.59 on V-para), as a fixed point across sets.
- Optional, reported never as headline: O3 cross-family judge (needs the maintainer's paid-API OK), O-REF (Opus references).

## 5. One claim run per build, and the burn rule
- One claim run per build, authorised by a frozen `CLAIM-RUNS-v03.md` (engine patch sha, tree hash, runner commit, plan
  and addendum shas, seeds, judge, output dir) hashed before the run. Results: aggregates only.
- **Burn rule:** if any engine change is chosen after seeing any v0.3 number (per-category included), v0.3 becomes dev and
  a new claim number needs a v0.4. No verdict reuse from other sets.
