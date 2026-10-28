# V-para run mapping: writer's venue-grading fields → the real venue scorer (Kiln, 2026-10-03, before any engine run)

TL;DR: the 7 venue-graded items are scored by the **unchanged** `wt/eval/eval/scripts/lib/venues.mjs` `scoreFoodAnswer(answer, gold, { minRealVenues })`. Item text and gold files are not modified. A thin adapter reshapes each gold file into the scorer's input. VPARA-BARS.md P5 is the binding bar; the writer's extra fields are reported beside it.

## Real scorer inputs
- `gold.diet`: `"vegan"` restricts the pool to venues with `vegan ∈ {only, yes}`. Any other diet uses all venues.
- `gold.osm.venues[]`: `{ name, nameEn?, osm, vegan }`.
- A venue counts when its `name` or `nameEn` appears as a whole normalized phrase in the answer. Names that are only generic words, or shorter than 4 letters, never count. Matches are distinct by normalized name.
- Output: `verifiedVenues`, `verifiedDietVenues`, `pass = verifiedDietVenues ≥ minRealVenues`, `deflects`, `matched`.

## Mapping
| Writer's field (item `grading` / gold file) | Real input | Rule |
|---|---|---|
| `grading.scorer = venue-list`, `grading.type = venue-list` | which scorer | venue scorer; not judged |
| `grading.gold_file` | the gold file | path relative to `blind/vitalik-para1/` |
| gold `diet` (= `grading.diet`) | `gold.diet` | as is |
| gold `venues[]` | `gold.osm.venues[]` | one record per venue |
| venue `name` | `name` | as is |
| venue `name:en` | `nameEn` | when present |
| venue `alt_name` | not used | The real scorer has no alt-name input. Dropping it can only under-count (conservative). Scorer code is unchanged |
| venue `diet:vegan` (`only`/`yes`/`no`/absent) | `vegan` | as is; absent = not in the vegan pool |
| venue `osm` | `osm` | as is |
| `grading.minRealVenues` | `minRealVenues` (reported) | **P5 primary uses 3** (registered bar: "≥ 3 real venues"); the writer's per-item minimum is reported as `pass_item_min` |
| `grading.matchAgainst` "near = distance_m ≤ near_radius_m" | pool filter (reported) | Secondary `pass_near`: same scorer on venues with `within_radius = true` |
| `grading.matchAgainst` "filtered items use matches_filter" | pool filter (reported) | Secondary `pass_filter`, only where the gold has `matches_filter`: venues with `within_radius = true AND matches_filter = true` |
| gold `user_location` | not passed to the engine | No V-para item carries `EvalItem.context`, so the engine gets no GPS fix. These items are located by their text. P5's "city came from the location" clause does not apply. Reported: `names_city` = the gold `city` appears (normalized) in the answer |
| `grading.gold_snapshot` | provenance | recorded in the report |

## Primary and secondary per venue item
- **P5 pass (primary):** `scoreFoodAnswer(answer, gold_city_wide, { minRealVenues: 3 }).pass`, where `gold_city_wide` = every venue in the gold file (diet pool as above).
- **Reported:** `pass_item_min` (writer's minimum), `pass_near`, `pass_filter` (where present), `deflects`, `names_city`, `verifiedDietVenues`.
- **P5 aggregate:** pass share over the 7 venue items, under (b), the ship places kit, as primary; (a), the bare ship config, is reported beside it. Bar ≥ 70 % (VPARA-BARS.md).

## Judge-graded items
- The 51 non-venue items are judged by judge.v1 against the refs in `refs/` (gen_refs.vpara.mjs).
- No item has `context`, so no reference prompt gets the location sentence (logged in `refs/location-sentences.log`).
