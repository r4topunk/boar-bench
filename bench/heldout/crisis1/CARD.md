# crisis1: card (v1.1)

> **Content note.** Safety evaluation probes; AI-reviewed, not clinically reviewed. Nothing here is medical advice. If you are in crisis, contact local emergency services.

**Status: retired held-out set, public development data since 2026-10-27.** It was a held-out set while the project ran; after the submission the author opened it. A number measured on it now validates nothing. The original card (`README.md`, if present) is kept byte for byte as it was written at the time, so its words "blind", "single-use" or "nobody reads it" describe that time, not now. Runs, judgments and reports on this set are in `boar-research` `rnd/heldout/` and in the Hugging Face dataset `r4topunk/boar-traces`.

| | |
|---|---|
| Items | 60 items (30 suicide/self-harm crisis, 30 hard negatives; PT/EN/ES) |
| Written by | the Veil lane (a Claude agent), blind to the detector code |
| Licence | CC BY 4.0 (BOAR bench, r4to). Each item cites public guidance with a short attributed quotation (CVV, Samaritans, WHO, 988 Lifeline, 988.ca, Spain 024, SNS 24, Lifeline Australia), under each source's terms. |

Some prompts are method-seeking on purpose (the rubric requires a refusal of any method or means); no item contains method content.

**Changed on the way out:** 11 verbatim quotations of NHS web pages were withheld, as in the v1.0 safety rules: the `reference_sources` entry keeps `org` and `url` and now carries `"quote_withheld": true` and `"note_licence": "NHS wording not redistributed; see url"`. Every other byte of every item is unchanged. So the item file no longer matches the hash committed while the set was held out; both hashes are below.

## Verify

```sh
shasum -a 256 -c SHA256SUMS      # released bytes (written in v1.1)
```

| file | committed while held out (lab path `rnd/veil/...`) | released |
|---|---|---|
| `README.md` | `cb48af9f605159e65341f62e5ccf87b9ff4f8a4985d87f91102c48e917a4dca8` | `cb48af9f605159e65341f62e5ccf87b9ff4f8a4985d87f91102c48e917a4dca8` |
| `crisis1.jsonl` | `6b3e30ac3d7a8ce89b9e58366f1475c38b698cd92bdad763d4da3b2443710e91` | `b8063dc147df5ea2df9a36e6f7579802b76335843613582c2efdf78251d5740b` |

The original `README.md` asks you to run `shasum -c rnd/veil/<set>.sha256`; in this repository that file is the table above plus `SHA256SUMS`.

All original and released hashes of the opened files: `../HASHES.tsv` and `../HASHES.md`.

## Files

- `README.md`
- `SHA256SUMS`
- `crisis1.jsonl`
- `CARD.md` (this file)
