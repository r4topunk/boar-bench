# BOAR blind eval — chat-v3

- Date: 2026-10-03
- Writer: fresh Opus subagent (claude-opus-5-5), no access to team files (only this directory was touched)
- File: `items.jsonl` — 64 items, one JSON object per line
- Purpose: per-message routing (search offline library vs answer directly) + reply-language fidelity

## Schema

`{"id","lang":"pt|en|es","kind":"greeting|meta|followup|mixed|research|ambiguous","turns":[{"role","text"}...],"expected_search":"yes|no|either","safety":bool,"expected":"<one line>"}`

- Score only the reply to the last `user` turn; earlier turns are history.
- `lang` = expected reply language (dominant language for mixed-language messages).
- `safety: true` = urgent health/safety situation; all have `expected_search: yes`.
- Item order is shuffled (seed 20261003).

## Counts

| lang | n |
|---|---|
| pt | 26 |
| en | 22 |
| es | 16 |

| kind | n | pt | en | es | yes | no | either | safety |
|---|---|---|---|---|---|---|---|---|
| greeting | 20 | 8 | 7 | 5 | 0 | 20 | 0 | 0 |
| meta | 8 | 3 | 3 | 2 | 0 | 8 | 0 | 0 |
| followup | 13 | 5 | 5 | 3 | 7 | 5 | 1 | 2 |
| mixed | 7 | 3 | 2 | 2 | 7 | 0 | 0 | 2 |
| research | 8 | 4 | 2 | 2 | 8 | 0 | 0 | 2 |
| ambiguous | 8 | 3 | 3 | 2 | 1 | 1 | 6 | 1 |
| **total** | **64** | **26** | **22** | **16** | **23** | **34** | **7** | **7** |

Safety by lang: pt 3 / en 2 / es 2.

## Integrity

`shasum -a 256 -c SHA256SUMS`
