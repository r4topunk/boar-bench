# vitalik-para1: blind paraphrase eval set

TL;DR: 58 English items (the brief asked for about 54). They are close paraphrases and same-family questions modelled on Vitalik Buterin's public example queries for the offline-research-tool bounty. All items are in the bench schema, and the venue items come with OSM gold snapshots. This set is blind: nobody on the team reads it before the final run.

```fish
shasum -a 256 -c SHA256SUMS          # check items.jsonl + README.md
shasum -a 256 gold/*.json            # compare with the gold hashes below
```

## Metadata

| Field | Value |
|---|---|
| Date written | 2026-10-03 |
| Writer | A fresh Opus subagent. Its only team inputs were the brief (`vpara-brief.md`) and `questions.schema.json`. It had no access to BOAR repos, dev sets, v0.1/v0.2 items or anything else under the team folder. |
| Language | en (all items) |
| Schema | `boar-eval/bench/v0.2/public-item` (validated with jsonschema Draft 2020-12, 0 errors) |
| Self-check | Every `answer` passes its own precheck (all must_any groups hit, no forbid hits). Every venue answer names at least `minRealVenues` gold venues. Forbid regexes were tested against correct phrasings that use negation (none trip) and against the wrong claims they target (all trip). |
| Fact checking | Rubric facts were checked on 2026-10-03 against the cited Wikipedia, Wikivoyage and official pages (NIST CSRC, ethresear.ch, ethereum.org, evisa.imigrasi.go.id, WHO). |

## Counts by category

| category | n |
|---|---|
| explanation | 17 |
| comparison | 7 |
| synthesis | 7 |
| reasoning | 7 |
| crypto | 5 |
| local-food | 7 |
| travel-local | 3 |
| travel-practical | 5 |
| **total** | **58** |

## Counts by brief section

| Section | n | origin | Notes |
|---|---|---|---|
| 1. Close paraphrases of the public example queries | 20 | `vitalik-verbatim-paraphrase` | 5 each: Japan overview (explanation), quantum-resistant signatures (crypto), Mozi's universal love (explanation), vegan venues near a GPS fix (local-food, venue-list; Kraków ×2, Tbilisi ×2, Ljubljana ×1) |
| 2. Same families × four task types | 28 | `vitalik-style` | 7 each of explanation, comparison, synthesis and reasoning. Families: country/place, post-quantum/Ethereum research, Chinese and Western philosophy, science/health, Lord of the Rings lore, plus travel arithmetic |
| 3. Specialized travel | 10 | `vitalik-style` | 2 venue-list items (vegan + outdoor seating + open now in València; vegetarian near me in Cusco), 3 transport between towns (one starts from a GPS fix), 5 practicalities (plugs, SIM, tipping, visa on arrival, time-zone arithmetic) |

Danger flags: 3 items have `danger: true` (a drug-evidence comparison, a diagnostic-test probability and a visa-on-arrival question).

## Gold venue snapshots (OpenStreetMap via Overpass, ODbL)

| gold file | OSM base timestamp | sha256 |
|---|---|---|
| gold/krakow-rynek.json | 2026-10-03T17:48:50Z | a67d27b3096f6121374baa753403bb196e8319e7983748f52dc3555b70946e4a |
| gold/krakow-kazimierz.json | 2026-10-03T17:48:50Z | d1363e61bfc235c43c704ee14cd56659802bd25693217fd3437676701e0f1d48 |
| gold/tbilisi-freedom-square.json | 2026-10-03T17:48:50Z | 753ee8cb7cd7bbd38fa0189b113e97f549103fdad29b7bbcb0fcb1172c1f6769 |
| gold/tbilisi-marjanishvili.json | 2026-10-03T17:48:50Z | 9c0fb948fa8909c558404a3c39f23cf2b2eb2d31b3253b95e319e4147c0e26aa |
| gold/ljubljana-preseren.json | 2026-10-03T17:47:51Z | 647c6a21c3fc12734aa3da3ed96ef719dc10964f6241c4ff44f4081d1370ce49 |
| gold/valencia-ajuntament-outdoor-open.json | 2026-10-03T17:48:50Z | 03cc20cc6040c925289c17b2199961c577fa3e559ff85bbed0b89865cd05bca3 |
| gold/cusco-plaza-de-armas.json | 2026-10-03T17:49:51Z | d7091e8bb289bc4fcabbaf08938ce652010aebf04f7bfead460337a72da75152 |

Because this README is listed in SHA256SUMS, these gold hashes are committed transitively.

Each gold file contains:
- `user_location` and `near_radius_m`
- the exact `overpass_query`
- every named venue, with its OSM id, tags, `distance_m` and `within_radius`
- `diet_focused`: true when `diet:vegan=only` (or `diet:vegetarian=only` for the vegetarian item), or when the cuisine tag contains vegan/vegetarian. Other venues only offer vegan options.

The València file also has `state_at_eval_time` and `matches_filter`. These hold the outdoor_seating=yes check and the opening-hours state at Saturday 2026-10-10 13:30 local time, parsed with `opening-hours-py`.

Some Tbilisi venue names are in Georgian script; `name:en` is included where OSM has it.

The Cusco gold uses a 2.5 km radius around the Plaza de Armas, not a city boundary.

## Decisions taken without team input (check before scoring)

- **origin**: the brief says `vitalik-para`, but the schema's `origin` enum doesn't contain it. To keep the set schema-valid I used `vitalik-verbatim-paraphrase` for section 1 and `vitalik-style` for sections 2 and 3. The `provenance` field of every item starts with `vitalik-para1`.
- **Item count is 58, not about 54**: the commissioning message listed Lord of the Rings lore among Vitalik's example query types, so I added one LOTR item per task type (4) on top of the brief's 24 family items.
- **grading_version**: `"2.2"`, the latest value in the enum.
- **venue-list `scorer` / `matchAgainst`**: I don't know the bench's real scorer name, so I set `scorer: "venue-list"` and described the matching contract in plain text in `matchAgainst`.
- **license**: `original (CC BY 4.0), boar-eval blind set vitalik-para1; venue gold derived from OpenStreetMap (ODbL)`.

## UNKNOWN

- I did not check similarity against v0.1, v0.2 or the dev sets, because the writer had no access to them. The coordinator must run the ≤ 0.6 similarity check. The brief asks for venue cities not used in v0.1, and I picked Kraków, Tbilisi, Ljubljana, València and Cusco without seeing v0.1.
- How the bench passes GPS context to the system: the coordinates are written inline in the question text.
- Some facts can change after 2026-10-03: the Indonesia VoA fee and duration, the Bali levy, transport frequencies and the status of FN-DSA/FIPS 206 (still a draft on the writing date). Venue hours and existence will also drift from the OSM snapshots.
