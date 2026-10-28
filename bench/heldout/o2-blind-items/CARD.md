# o2-blind-items: card (v1.1)

**Status: retired held-out set, public development data since 2026-10-27.** It was a held-out set while the project ran; after the submission the author opened it. A number measured on it now validates nothing. The original card (`README.md`, if present) is kept byte for byte as it was written at the time, so its words "blind", "single-use" or "nobody reads it" describe that time, not now. Runs, judgments and reports on this set are in `boar-research` `rnd/heldout/` and in the Hugging Face dataset `r4topunk/boar-traces`.

| | |
|---|---|
| Items | 24 + 6 items (`-b2`), plus an errata note |
| Written by | the Veil lane (a Claude agent), blind |
| Licence | CC BY 4.0 (BOAR bench, r4to). Facts from linked Wikipedia pages (CC BY-SA 4.0). |

## Verify

```sh
shasum -a 256 -c SHA256SUMS      # released bytes (written in v1.1)
```

All original and released hashes of the opened files: `../HASHES.tsv` and `../HASHES.md`.

## Files

- `SHA256SUMS`
- `o2-blind-items-b2.jsonl`
- `o2-blind-items.errata.md`
- `o2-blind-items.jsonl`
- `CARD.md` (this file)
