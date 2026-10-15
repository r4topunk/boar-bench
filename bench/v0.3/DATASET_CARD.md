# Dataset card: boar-eval bench v0.3-ext (TBD items; skeleton, filled at the freeze)

TL;DR: TBD. English items in the 10 v0.2 strata, written by the maintainer with one non-Claude model in a web UI (model TBD), fact-checked by hand against Wikipedia/official `reference_sources`, with gold `answer`, judge-facing `rubric` ("Penalize:" bullets), precheck `grading`, and non-Claude web-UI references. Plaintext lives in `bench/v0.3/work/` and never in git (see HELD-OUT.md).

```sh
python3 bench/v0.3/assemble.py [--wave1]                 # work/<category>.jsonl -> private/.../questions.v03.jsonl (+ safety_rules v0.7)
python3 bench/v0.3/validate.py [--wave1]                 # G1 (+ G4 refs check when MANIFEST exists)
<venv>/bin/python bench/v0.3/similarity.py --pools all   # G2 -> similarity.json (script-only runner, logged exception)
python3 bench/v0.3/refs/import_web_refs.py               # raw/<id>.md -> refs/web__<model>.new.jsonl (blind)
python3 bench/v0.3/refs/build_manifest.py [--freeze]     # refs.jsonl (blind) + MANIFEST.jsonl / MANIFEST.json (hashes)
```

## Composition
TBD (target: explanation 21 · reasoning 21 · comparison 13 · crypto 13 · honesty-refusal 12 · health 8 · danger 10 · synthesis 6 · travel-practical 4 · travel-local 2; 60-item fallback = ids 01..w1). Region share outside Europe/North America: TBD (target ≥ 40 %, ≤ 2 items per country). refuse_ok: TBD. danger: TBD.

## Method
TBD: writer model and settings (D1), dates, minutes per item (pilot 10-08), topic longlist and picks, fact-check procedure, gate fix rounds.

## Provenance per item (field `provenance`)
TBD.

## Gates
TBD: G1 (validate.py), G2 (similarity.py, pools incl. v0.2-new and V-para), G3 (fresh-Opus topic review), G4 (refs).

## Safety rules (rules v0.7: `scorers/vendor/safety/rules.v0.7.json` + `safety_check.v0.7.py`, addendum 04)
TBD: mapped / judge-only counts. Rules v0.7 forbid rules target v0.2 danger topics, which v0.3 avoids, so most v0.3 danger items are expected to be judge-only for safety (rubric "Penalize:" bullets).

## References (`refs/`)
TBD: model, vendor UI, dates, n ok, retries, word-count median/max, n over 250 words, MANIFEST shas.

## V-style slice
TBD (only if D3 = fold): ids in `plan/vstyle.ids`, counts per category.

## Limitations
- **Judge-family bias is not fixed.** Opus `judge.v1` still scores every answer; only the optional cross-family judge (O3) addresses it.
- **One writer, one model.** All items carry one person's and one model's topic choices and style; v0.2 had two writers.
- **Reference family changed.** References come from a non-Claude model through a consumer web UI (channel `reference.v1-webui`, with the vendor's hidden system prompt), not Opus + web. This moves the ratio's denominator: v0.3 ratios are not 1:1 comparable with v0.1/v0.2 ratios. The control (cut 6) and anchor (Haiku no-web) runs measure the shift; the optional O-REF sensitivity re-judges against Opus references.
- **Worked examples in the writer prompts were written by a Claude model** (format only, topics excluded from the set); the writer model saw them.
- **No venue items.** Vitalik's literal "vegan restaurants in [city]" test needs OSM gold that a web-UI writer cannot produce; V-para's venue result stays the only venue evidence.
- **Safety coverage.** Most danger items are judge-only for safety (see above).
- **Licence.** CC-BY-4.0 on model-assisted items assumes the vendor's consumer terms leave output rights with the user; not checked.
- **Model-assisted facts.** Every gold fact was checked by hand on a cited page, but the fact-check is one person's; no second human review.

## Coordinator notes at freeze
TBD.
