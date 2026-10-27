# Data card: bench/slices

| Slice | Size | What | Reference side | Licence |
|---|---|---|---|---|
| `longsession-v1` | 80 turns in 10 sessions | multi-turn drift: does a long chat degrade answers (turn shapes: coreference 30, topic switch 25, deepen 25) | `refs/refs.jsonl`: standalone answers of the engine itself (no history) | CC BY 4.0 (`NOTICE.md`); Wikipedia and Wikivoyage excerpts CC BY-SA 4.0 |
| `chat-fu-v1` | 30 chats, 159 turns | intent-change and anchor probe (24 intent-change chats + 6 controls); labels `expected_intent`, `expected_anchor`, `capability_request`; for routing replay, not answer quality | labels only | CC BY 4.0 (`NOTICE.md`) |
| `chainwhen-v1` | 150 | the 150 contexts of the RELGATE experiment, copied verbatim from nine pack self-test sets | self-test gold | as `bench/selftest` |
| `packread-v1` | 54 | first six ids of nine pack self-test sets, for the pack-reading experiment | self-test gold | as `bench/selftest` |
| `mathroute-v1` | 26 | arithmetic and unit questions for routing (2 copied from v0.1) | `gold.jsonl` | CC BY 4.0 (`NOTICE.md`) |
| `citation-pt` | 20 | 20 non-danger v0.1 items in faithful Brazilian Portuguese, for the citation check; frozen sha256 in its README | v0.1 originals | CC BY 4.0; quoted sources by attribution |

- All slices are dev data written by AI agents of the research team (2026-10-01 to 2026-10-18); none is a held-out set and none is a claim set. `SHA256SUMS` files pin each slice where one exists.
- `chat-fu-v1` chat `c01` reproduces a real chat with the app on 2026-10-18 (a technical question about smart contracts); it contains no personal data.
- Health content (first aid in `chat-fu-v1`, `longsession-v1`, `chainwhen-v1`) is AI-reviewed, not clinically reviewed; not medical advice.
- Known limits: small n; labels written before any replay but by the same team; slices were used to decide arms, so their numbers are development numbers.
