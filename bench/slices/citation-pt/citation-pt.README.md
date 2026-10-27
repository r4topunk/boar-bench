# Slice `citation-pt`: PT-BR vs EN for the compact tier's citation check (Decision 1)

TL;DR: 20 non-danger bench v0.1 public items whose answers come from the night kit's packs (Wikivoyage EN, boar-crypto), each in a faithful Brazilian-Portuguese version (`citation-pt.jsonl`), plus the same 20 English originals by reference. Question: does the citation word check (`src/routing/citations.ts`, CT-1) erase PT answers that EN answers keep? Built by Kiln-2 on 2026-10-01 for arms `d1a-unconfirmed` and `d1c-pt-keywords` (`adapters/desktop-node/arms/`).

```bash
shasum -a 256 bench/slices/citation-pt/citation-pt.jsonl   # must print the frozen sha below
```

| | |
|---|---|
| File | `citation-pt.jsonl`, 20 lines |
| **Frozen sha256** | `8f3bf231ce893dcf422cff732bd2860e17da60aa03743d96cc7cb4d38bbc74cb` (frozen 2026-10-01 before any arm run) |
| Item fields | the public item's fields, with `id` = original id + `-pt`, `lang: "pt"`, `question`/`answer`/`rubric` translated, `grading` adapted (PT terms added next to the English ones, regexes rewritten for PT), `origin: "kiln2-pt-slice"`, `source_item` = original id, same `category`, `danger` (all false), `grading_version`, `reference_sources`, `license` |
| Schema | NOT `questions.schema.json`-valid on purpose: the id pattern has no `-pt` suffix and the schema has no `source_item` |
| Gold answers | the 11 items that have one (`origin: lantern-v0.1`) carry the translated answer; each passes its own (PT) precheck |
| References for the judge | the original English Opus+web reference (`refs/refs.jsonl`, private) keyed by the `-pt` id; the judge compares content, the language difference is stated in the report |

## Selection rule (decided before any run)

From bench v0.1 public (60): not `danger`, category not `health`/`danger*`, not `local-food` (venue lists), and on the night-2026-10-01 `ios-main-s42`/`-s43` traces (iPhone profile, night kit) the engine **showed on-topic pack sources** (a Wikivoyage destination, an EIP, an ethereum.org page). 21 qualified; `vit-cry-008` (Glamsterdam, an honesty-refusal item whose right answer depends on the pack's date) was left out to keep 20.

## The 20 English originals (by reference, from `questions.public.jsonl`)

| # | EN id (original) | PT id | Category | Grading |
|---|---|---|---|---|
| 1 | lan-exp-001 | lan-exp-001-pt | explanation | precheck |
| 2 | lan-exp-002 | lan-exp-002-pt | explanation | precheck |
| 3 | lan-rsn-001 | lan-rsn-001-pt | reasoning | precheck |
| 4 | lan-cmp-001 | lan-cmp-001-pt | comparison | precheck |
| 5 | vit-trv-003 | vit-trv-003-pt | travel-local | precheck |
| 6 | vit-cry-001 | vit-cry-001-pt | crypto | precheck |
| 7 | vit-cry-002 | vit-cry-002-pt | crypto | precheck |
| 8 | vit-cry-003 | vit-cry-003-pt | crypto | precheck |
| 9 | vit-cry-004 | vit-cry-004-pt | crypto | precheck |
| 10 | vit-cry-005 | vit-cry-005-pt | crypto | precheck |
| 11 | vit-cry-009 | vit-cry-009-pt | reasoning | precheck |
| 12 | vit-cry-010 | vit-cry-010-pt | synthesis | precheck |
| 13 | lan-ref-002 | lan-ref-002-pt | honesty-refusal | precheck |
| 14 | lan-cmp-003 | lan-cmp-003-pt | comparison | precheck |
| 15 | lan-exp-004 | lan-exp-004-pt | explanation | precheck |
| 16 | lan-exp-005 | lan-exp-005-pt | explanation | precheck |
| 17 | lan-exp-006 | lan-exp-006-pt | explanation | precheck |
| 18 | lan-rsn-007 | lan-rsn-007-pt | reasoning | precheck |
| 19 | lan-exp-007 | lan-exp-007-pt | explanation | precheck |
| 20 | trv-002 | trv-002-pt | travel-practical | judge-only |

EN ids, one line: `lan-exp-001,lan-exp-002,lan-rsn-001,lan-cmp-001,vit-trv-003,vit-cry-001,vit-cry-002,vit-cry-003,vit-cry-004,vit-cry-005,vit-cry-009,vit-cry-010,lan-ref-002,lan-cmp-003,lan-exp-004,lan-exp-005,lan-exp-006,lan-rsn-007,lan-exp-007,trv-002`

## Notes

- Translation style: how a Brazilian user would ask (informal "Me dá…", "Como vou de…"), names in their PT form where one is common (Singapura, Quioto, Saara, Groenlândia, Muro de Berlim), crypto terms kept in English where Brazilian users keep them (hard fork, stake, blob, EIP-xxxx).
- Location: `bench/slices/citation-pt/`, outside the frozen `bench/v0.1/` (coordinator, 2026-10-02; it first lived in `bench/v0.1/slices/`, same bytes, same sha). It is not covered by `bench/v0.1/SHA256SUMS.json`; the sha above is its freeze.
