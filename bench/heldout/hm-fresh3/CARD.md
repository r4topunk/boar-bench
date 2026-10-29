# hm-fresh3: card (v1.1)

> **Content note.** Safety evaluation probes; AI-reviewed, not clinically reviewed. Nothing here is medical advice. If you are in crisis, contact local emergency services.

**Status: retired held-out set, public development data since 2026-10-27.** It was a held-out set while the project ran; after the submission the author opened it. A number measured on it now validates nothing. The original card (`README.md`, if present) is kept byte for byte as it was written at the time, so its words "blind", "single-use" or "nobody reads it" describe that time, not now. Runs, judgments and reports on this set are in `boar-research` `rnd/heldout/` and in the Hugging Face dataset `r4topunk/boar-traces`.

| | |
|---|---|
| Items | 74 items (24 danger, 25 hard negatives, 25 ordinary research questions; PT-BR/EN) |
| Written by | the Veil lane (a Claude agent), blind |
| Licence | CC BY 4.0 (BOAR bench, r4to). Short attributed quotations of public guidance (CDC, healthdirect, St John Ambulance, Ready.gov, Ministério da Saúde, Fiocruz, WHO, CVV), under each source's terms; NHS, healthdirect and St John wording withheld (org and URL kept). |

**Changed on the way out:** 25 verbatim quotations of NHS web pages were withheld, as in the v1.0 safety rules: the `reference_sources` entry keeps `org` and `url` and now carries `"quote_withheld": true` and `"note_licence": "NHS wording not redistributed; see url"`. In v1.1.2, 8 more copyright quotations (4 healthdirect and 4 St John Ambulance) were withheld the same way, with `"note_licence": "copyright wording not redistributed; see url"`. Every other byte of every item is unchanged. So the item file no longer matches the hash committed while the set was held out; both hashes are below.

## Verify

```sh
shasum -a 256 -c SHA256SUMS      # released bytes (written in v1.1)
```

| file | committed while held out (lab path `rnd/veil/...`) | released |
|---|---|---|
| `hm-fresh3.jsonl` | `e99795d1c003981de92372e20e3e1c0fbc4ebbd5da7f04aca6d29c446296be70` | `f95838d6090fa2fd8bbb05656a5ba942dc9ebe7779eb9bb8318e083dab97d74c` |

The original `README.md` asks you to run `shasum -c rnd/veil/<set>.sha256`; in this repository that file is the table above plus `SHA256SUMS`.

All original and released hashes of the opened files: `../HASHES.tsv` and `../HASHES.md`.

## Files

- `README.md`
- `SHA256SUMS`
- `hm-fresh3.jsonl`
- `CARD.md` (this file)
