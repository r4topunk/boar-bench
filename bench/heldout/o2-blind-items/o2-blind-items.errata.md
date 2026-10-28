# Errata: o2-blind-items.jsonl (frozen, sha256 46d5f5b7…afea7)

TL;DR: I checked the 12 answers marked "standard reference" against their source pages on 2026-09-30. None has a wrong key answer (the name/number the grading hinges on). Three have imprecise supporting detail, corrected below. **The frozen file is unchanged.** Graders should apply these corrections when judging the free-text part.

| Item | Frozen answer | Correction | Effect on grading | Source |
|---|---|---|---|---|
| vit-o2b-002 | Indonesia, ~280 M vs ~212 M, gap ~70 M | Indonesia is still correct. The page's current figures are about 288 M vs 214 M, a gap of about 73 M | None for `must_any` (["indonesia"]). Accept 270–290 M for Indonesia and 205–215 M for Brazil as "plausible" | https://en.wikipedia.org/wiki/List_of_countries_and_dependencies_by_population |
| vit-o2b-017 | Amazonas, "cerca de 6.400 km" | Amazonas is still correct. The length is disputed: estimates run from about 6,400 km to about 6,990 km (Brazil's INPE), and it vies with the Nile for the world title | None for `must_any` (["amazonas"]). The rubric line "roughly 6,400 km" should accept anything from 6,400 to 7,000 km | https://pt.wikipedia.org/wiki/Rio_Amazonas |
| vit-o2b-018 | 118; "o último completou o 7º período em 2016" | 118 is correct. The last four elements were confirmed in December 2015; their names were approved in November 2016 | None (`must_any` = ["118"]). Accept 2015 or 2016 if a date is given | https://pt.wikipedia.org/wiki/Tabela_periódica |

Checked and correct as frozen: vit-o2b-003 (206; about 270 at birth), 004 (eight planets in order; Pluto a dwarf planet), 005 (21 M cap), 006 (the Merge, 15 Sep 2022), 009 (Antarctic largest, Sahara largest hot), 011 (five neighbours), 019 (12 s slot, 32-slot epoch), 020 (four halvings, the latest in April 2024, now 3.125 BTC), 021 (Ecuador uses the US dollar).

Sources for these are the links already in each item, except for 020, whose halving count was confirmed on https://en.wikipedia.org/wiki/Bitcoin_halving (the item links the Bitcoin article).

Metric: 12/12 re-checked, 0 wrong key answers, 3 detail corrections.
