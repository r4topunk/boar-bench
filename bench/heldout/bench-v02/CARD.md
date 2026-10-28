# bench-v02: card (v1.1)

> **Content note.** Safety evaluation probes; AI-reviewed, not clinically reviewed. Nothing here is medical advice. If you are in crisis, contact local emergency services.

**Status: retired held-out set, public development data since 2026-10-27.** It was a held-out set while the project ran; after the submission the author opened it. A number measured on it now validates nothing. The original card (`README.md`, if present) is kept byte for byte as it was written at the time, so its words "blind", "single-use" or "nobody reads it" describe that time, not now. Runs, judgments and reports on this set are in `boar-research` `rnd/heldout/` and in the Hugging Face dataset `r4topunk/boar-traces`.

| | |
|---|---|
| Items | 110 items (v0.2-new) + two writers' drafts and rewrite rounds |
| Written by | two blind Claude Opus writers (writer-a, writer-b); 44 slots rewritten by Sonnet/Fable/Opus agents (see the v0.2 card) |
| Licence | CC BY 4.0 (BOAR bench, r4to). Facts were checked against linked pages (Wikipedia CC BY-SA 4.0, NHS, CDC, ready.gov); no third-party text is reproduced in the items. The reference answers (`live/v0.2/refs/`) are Claude Opus + live-web outputs and may quote their cited sources, which keep their own terms. |

Some items are danger/health probes. `spec/` holds the bench v0.1 card and validator that the writers used as their spec. Files that the v0.2 hash chain lists but that live in `boar-research` (`assemble.py`, `validate.py`, `similarity.py`, `similarity.json`): `rnd/heldout/bench-v02/live/v0.2/`.

## Verify

```sh
cd live/v0.2 && shasum -a 256 -c SHA256SUMS.items   # 4 entries live in boar-research (see above)
cd plan && shasum -a 256 -c SHA256SUMS && shasum -a 256 SHA256SUMS   # = COMBINED.sha256
python3 tools/verify-pins.py   # from the repo root: every pin, with the documented KNOWN entries
```

All original and released hashes of the opened files: `../HASHES.tsv` and `../HASHES.md`.

## Files

- `README.md`
- `live/v0.2/COMBINED-FREEZE.sha256`
- `live/v0.2/DATASET_CARD.md`
- `live/v0.2/SHA256SUMS.items`
- `live/v0.2/plan/COMBINED.sha256`
- `live/v0.2/plan/README.md`
- `live/v0.2/plan/SHA256SUMS`
- `live/v0.2/plan/SHA256SUMS.addendum-01`
- `live/v0.2/plan/SHA256SUMS.addendum-02`
- `live/v0.2/plan/SHA256SUMS.addendum-03`
- `live/v0.2/plan/SHA256SUMS.addendum-04`
- `live/v0.2/plan/addendum-01-coverage-split.md`
- `live/v0.2/plan/addendum-02-safety-v05.md`
- `live/v0.2/plan/addendum-03-safety-v06.md`
- `live/v0.2/plan/addendum-04-safety-v07.md`
- `live/v0.2/plan/analysis-plan.md`
- `live/v0.2/plan/coverage_classes.py`
- `live/v0.2/plan/floor_metrics.py`
- `live/v0.2/plan/item-spec.draft.md`
- `live/v0.2/plan/judge-core.judge.v1.mjs`
- `live/v0.2/plan/key_in_context.py`
- `live/v0.2/plan/overlay.v02-danger.v0.6.json`
- `live/v0.2/plan/overlay.v02-danger.v0.7.json`
- `live/v0.2/plan/paired_gap.py`
- `live/v0.2/plan/strata.py`
- `live/v0.2/questions.schema.json`
- `live/v0.2/questions.v02-new.jsonl`
- `live/v0.2/refs/MANIFEST.json`
- `live/v0.2/refs/MANIFEST.jsonl`
- `live/v0.2/refs/build_manifest.py`
- `live/v0.2/refs/claude-code__opus.new.jsonl`
- `live/v0.2/refs/gen_refs.mjs`
- `live/v0.2/refs/refs.jsonl`
- `rewrites-a.NOTES.md`
- `rewrites-a.jsonl`
- `rewrites-a.pre-factfix.jsonl`
- `rewrites-b.NOTES.md`
- `rewrites-b.jsonl`
- `rewrites-r2.NOTES.md`
- `rewrites-r2.jsonl`
- `spec/DATASET_CARD.md`
- `spec/REWRITE-BRIEF.md`
- `spec/questions.schema.json`
- `spec/validate.py`
- `writer-a/NOTES.md`
- `writer-a/questions.jsonl`
- `writer-a/questions.pre-factfix.jsonl`
- `writer-b/NOTES.md`
- `writer-b/questions.jsonl`
- `CARD.md` (this file)
