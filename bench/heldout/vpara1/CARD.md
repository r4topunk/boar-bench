# vpara1: card (v1.1)

> **Content note.** Safety evaluation probes; AI-reviewed, not clinically reviewed. Nothing here is medical advice. If you are in crisis, contact local emergency services.

**Status: retired held-out set, public development data since 2026-10-27.** It was a held-out set while the project ran; after the submission the author opened it. A number measured on it now validates nothing. The original card (`README.md`, if present) is kept byte for byte as it was written at the time, so its words "blind", "single-use" or "nobody reads it" describe that time, not now. Runs, judgments and reports on this set are in `boar-research` `rnd/heldout/` and in the Hugging Face dataset `r4topunk/boar-traces`.

| | |
|---|---|
| Items | 58 items (51 judged + 7 venue-list items) |
| Written by | a fresh Claude Opus subagent, blind to the team files |
| Licence | CC BY 4.0 (BOAR bench, r4to). 20 items closely paraphrase example questions from a public post by Vitalik Buterin (the post that inspired the bounty: x.com/VitalikButerin/status/2100695863026954698); the rest are written in the same style. He is named as the inspiration only and no claim is made over his text. `gold/*.json` and `venue-locations.json`: OpenStreetMap data, ODbL 1.0, (c) OpenStreetMap contributors. |

Public name in the research record: **V-para**. 3 items touch everyday health. The reference answers in `refs/` and `refs-80w/` are Claude Opus + live-web outputs (they may quote their sources); `refs-80w` rows carry `sourceRefsSha256` = the sha of the pre-redaction `refs/refs.jsonl` (`952e2c44...`), which is not released; the released file is listed in `../HASHES.md`.

## Verify

```sh
shasum -a 256 -c SHA256SUMS      # the commitment written with the set (items + README), unchanged
```

All original and released hashes of the opened files: `../HASHES.tsv` and `../HASHES.md`.

## Files

- `README.md`
- `RUN-MAPPING.md`
- `RUN-MAPPING.sha256`
- `SHA256SUMS`
- `bench-shim-80w/bench.json`
- `bench-shim/bench.json`
- `gold/cusco-plaza-de-armas.json`
- `gold/krakow-kazimierz.json`
- `gold/krakow-rynek.json`
- `gold/ljubljana-preseren.json`
- `gold/tbilisi-freedom-square.json`
- `gold/tbilisi-marjanishvili.json`
- `gold/valencia-ajuntament-outdoor-open.json`
- `items.jsonl`
- `refs-80w/MANIFEST.json`
- `refs-80w/refs.jsonl`
- `refs/MANIFEST.json`
- `refs/MANIFEST.sha256`
- `refs/claude-code__opus.new.jsonl`
- `refs/gen_refs.vpara.mjs`
- `refs/refs.jsonl`
- `runs-cut3/venue7.questions.jsonl`
- `venue-locations.json`
- `CARD.md` (this file)
