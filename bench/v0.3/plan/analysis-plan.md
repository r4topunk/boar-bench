# Bench v0.2: pre-registered analysis plan (FINAL, to be hashed by the coordinator; no edits after hashing)

Author: a research agent, 2026-10-02. Approved scope (the maintainer, 2026-10-02): bench v0.2 = v0.1 public + 110 new blind items in the same category mix as v0.1, item spec `item-spec.draft.md` unchanged, two blind writers (55/55), frozen in the private repo, published later on the maintainer's call. Any change to this plan after hashing must be a separate, dated addendum, hashed before the run it affects. This file is never edited.

## 1. Sets
- **v0.2-new:** the 110 items written blind (writers A and B, 55 each). All judgeable by the pairwise judge (no venue-list items). English.
- **v0.2 = v0.1 public (60) + v0.2-new (110).** The quality ratio uses judged items only. v0.1's three venue-list items are scored by OSM and stay outside the ratio.
- **Held-out subset = v0.2-new.** v0.1 remains the development set. **No arm decision is ever taken on v0.2-new.** It's used only for the E3 baseline and the claim.
- **Strata = category**, with danger-situation → danger and travel-local/travel-practical → travel. v0.2-new's declared quotas: explanation 21, reasoning 21, comparison 13, crypto 13, honesty-refusal 12, health 8, danger 10, synthesis 6, travel 6.

## 2. References and judge
- References: the `reference.v1` recipe (Opus 5.5 + web; prompt sha256 `d51443438dfebcc7d2c3a0136340c70a68f495e1214c00a3a8c56bcdbc755972`), generated once for v0.2-new and frozen. Missing references are regenerated before the freeze, never after.
- Judge: `judge.v1` (claude-opus-5-5, pairwise vs the reference, both A/B orders, scores averaged, disagreement = tie).
- Mean rubric of an answer = mean of correctness, completeness and usefulness, averaged over the two orders.

## 3. Primary metric (the bar)
- **Quality ratio, raw** = Σ mean-rubric(BOAR) / Σ mean-rubric(reference) over all v0.2 judged items. **The bar (> 0.50) is judged on this number** (the maintainer's decision, 2026-10-02).
- **CI: stratified two-level bootstrap.** Resample items within each stratum, then runs within each item; 2,000 resamples; seed 11; percentile 95 % interval. The plain (unstratified) two-level interval is reported beside it.
- Runs for the claim: seeds 42, 43, 44 (≥ 2 required; 3 planned).
- Implementation: `floor_metrics.py --questions <v0.2 questions> --decline-ratio 0.306 --runs <runs>`; the `raw` field.

## 4. Companion metrics (shown side by side with the raw ratio in every publication)
1. **Rubric minimum removed:** Σ(S − 1) / Σ(R − 1). `floor_metrics.py`, `above_min` field.
2. **Above an always-decline system:** (raw − D) / (1 − D), with **D fixed at 0.306**. D is the mean judge rubric of 79 declined answers across 7 night-2026-10-01 runs, divided by the mean reference rubric. It is robust to the mix (v0.2-weighted 0.307). `floor_metrics.py`, `above_decl` field. The D measured on the claim run's own declines is reported beside it.
3. Each with the same stratified two-level CI.

## 5. Secondary metrics (reported, never instead of §3–4)
1. **Held-out ratio** (v0.2-new only), same three scales and CI (`floor_metrics.py --ids <v0.2-new ids>`). Reported per writer (A, B) as well.
2. **Gap to the 1B-class baseline** (the fallback framing): BOAR Android vs the iPhone 1.5B configuration on the same v0.2 items, paired, on all three scales. `paired_gap.py --a <BOAR runs> --b <1.5B runs> --questions <v0.2 questions>`, stratified two-level, seed 11.
3. Win / tie / loss vs the reference; share of items judged correct (mean correctness ≥ 4).
4. Per-category table of the three scales.
5. **Abstention**, scored separately. A "decline" is an answer the engine marks declined.
   - Decline precision = share of declines on items whose rubric says a decline is acceptable (honesty-refusal items with an explicit decline rule).
   - Decline recall = share of those items that BOAR declined.
   - Reported, not combined with the ratio.
6. Truthfulness, safety, retrieval, latency, resources and stability as in boar-eval's 7-axis report (never averaged).

## 6. External checks
1. **Cross-family judge (conditional on the maintainer's approval before the claim run):**
   - The final run is re-scored once by a judge from another model family, with the same `judge.v1` prompt, schema, pairs and both orders.
   - The judge model is named in a dated addendum, hashed before that re-score.
   - Candidates: a gateway model (e.g. `openai/gpt-5.5`; reference text leaves the machine), or a local open-weights model (keeps references local).
   - **Rule:** if its raw ratio differs from judge.v1's by more than 0.05, the lower of the two is the headline.
   - Report Cohen's κ between the judges on pass/not-pass.
2. **Human labels:**
   - **Sample:** 40 pairs from the final run, drawn with seed 7, stratified by category in proportion to the set.
   - **Presentation:** blind. A/B order randomized with seed 7, system names removed, the app's own notices kept.
   - **Raters:** the maintainer and the upstream maintainer, independently, each labeling (a) better answer (A/B/tie), (b) BOAR correct on the core question (y/n), (c) anything unsafe (y/n).
   - **Report:** inter-rater κ, judge-vs-human κ on (b), and the share of pairs where humans prefer BOAR or tie. Disagreements are reported, not resolved by the judge.

## 7. E3: held-out baseline check (before the claim)
- `main` (Android 4B profile), seeds 42 and 43, on v0.2-new.
- **PASS** if (a) the held-out raw ratio is within ±0.04 of 0.512, and (b) the stratified CI half-width on all v0.2 judged items is ≤ 0.035.
- **K5 (a research agent S1):** held-out raw ratio < 0.48 → the claim uses the fallback framing and the remaining time goes to latency, safety and the demo.
- **Power note:** at ~110 held-out items the CI half-width alone is about 0.037, so the ±0.04 band only flags shifts beyond sampling noise. Read any miss with the per-category and per-writer tables.

## 8. Claim wording rules
- The first paragraph states the raw ratio with its CI and says plainly whether the CI lies above 0.50, contains it, or lies below it. If it contains 0.50, the wording is "consistent with the bar, not shown above it".
- The three scales (§3–4) appear together, at the same size, each with its CI.
- The 1B-class gap (§5.2) appears with its paired CI.
- Device numbers, not the desktop proxy, are the headline. Desktop numbers are labelled as such.

## 9. Leakage and integrity rules
- Nobody outside the writers and the coordinator reads `private/` or v0.2-new item text before the claim run. Researchers receive aggregates only.
- No item is dropped after the freeze, except for a factual error in its gold answer found during reference generation, listed with the reason in the manifest.
- The manifest (items, references, judge prompt, this plan, `item-spec.draft.md`, `floor_metrics.py`, `paired_gap.py`) gets per-file sha256 and one combined sha256. Only the combined hash is committed publicly before any BOAR run on v0.2-new.

## 10. Reference results on v0.1 (for orientation; computed with the frozen scripts)
- Android Qwen3-4B (`and-qwen` s42/s43), stratified:
  - raw 0.512 (0.466–0.558);
  - rubric-min-removed 0.387 (0.330–0.444);
  - above-decline 0.297 (0.231–0.363).
- iPhone 1.5B (`ios-main` s42/43/44): raw 0.381 (0.350–0.414); rubric-min-removed 0.222 (0.183–0.263); above-decline 0.108 (0.063–0.156).
- Paired gap 4B − 1.5B: raw +0.131 (+0.095 … +0.171); rubric-min-removed +0.165 (+0.120 … +0.215); above-decline +0.189 (+0.137 … +0.246).
