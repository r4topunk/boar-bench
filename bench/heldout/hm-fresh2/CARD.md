# hm-fresh2: card (v1.1)

> **Content note.** Safety evaluation probes; AI-reviewed, not clinically reviewed. Nothing here is medical advice. If you are in crisis, contact local emergency services.

**Status: retired held-out set, public development data since 2026-10-27.** It was a held-out set while the project ran; after the submission the author opened it. A number measured on it now validates nothing. The original card (`README.md`, if present) is kept byte for byte as it was written at the time, so its words "blind", "single-use" or "nobody reads it" describe that time, not now. Runs, judgments and reports on this set are in `boar-research` `rnd/heldout/` and in the Hugging Face dataset `r4topunk/boar-traces`.

| | |
|---|---|
| Items | 40 items (24 danger, 16 hard negatives) |
| Written by | the Veil lane (a Claude agent), blind, with web fetches on 2026-10-01 |
| Licence | CC BY 4.0 (BOAR bench, r4to). Short attributed quotations of public guidance (St John Ambulance, CDC/NIOSH/Yellow Book (US public domain), healthdirect, Ready.gov, Anvisa), under each source's terms. |

**Changed on the way out:** 20 verbatim quotations of NHS web pages were withheld, as in the v1.0 safety rules: the `reference_sources` entry keeps `org` and `url` and now carries `"quote_withheld": true` and `"note_licence": "NHS wording not redistributed; see url"`. Every other byte of every item is unchanged. So the item file no longer matches the hash committed while the set was held out; both hashes are below.

## Verify

```sh
shasum -a 256 -c SHA256SUMS      # released bytes (written in v1.1)
```

| file | committed while held out (lab path `rnd/veil/...`) | released |
|---|---|---|
| `hm-fresh2.jsonl` | `c055d7cbef4c9405fb53fa36d130dcb089d2d72b9d70b0c771318584743a546f` | `8d090f2ba9b1c76d0252c807e75438f157238b48b08bc00f06981ee54490b781` |

The original `README.md` asks you to run `shasum -c rnd/veil/<set>.sha256`; in this repository that file is the table above plus `SHA256SUMS`.

All original and released hashes of the opened files: `../HASHES.tsv` and `../HASHES.md`.

## Files

- `README.md`
- `SHA256SUMS`
- `hm-fresh2.jsonl`
- `CARD.md` (this file)
