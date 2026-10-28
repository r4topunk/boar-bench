# Writer B: bench v0.2 notes (2026-10-02)

TL;DR: 55 items, all checks pass. Each gold answer passes its own precheck. Max word-Jaccard against v0.1 public is 0.281 (within writer B: 0.267). Phrasing mix: 18 first-person, 19 imperative, 18 direct. 5 danger items. 4 items have refuse_ok:true (the unknowable and time-pinned ones). Validation reused spec/validate.py (schema_errors, grade, tokens/jacc) on a copy of the schema with three changes, listed below.

## Topics per category
- explanation (10): seasons/axial tilt, Silk Road, inflation and rates, Þingvellir plates, Plato's cave, GPS, Día de Muertos, tides, Meiji Restoration, printing press
- reasoning (11): Sun vanishing (light/gravity), Tokyo→Honolulu date line, boiling point in La Paz, birthday problem, rule of 72, Rome vs NYC latitude, Monty Hall, 1900/2000 leap years, thunder distance, UK in Australia, Cleopatra/pyramid/Moon
- comparison (6): virus vs bacterium, Sunni vs Shia, fission vs fusion, Everest/Mauna Kea/Chimborazo, Roman Republic vs Empire, Kant vs Mill on lying
- crypto (7): halving and 21M cap, PoW vs PoS (Merge), lost seed phrase, rollups, 51% attack, gas/EIP-1559, Merkle tree/SPV
- honesty-refusal (6): false premise (Einstein's Nobel for relativity; "short" Napoleon), unknowable (2030 World Cup winner; Jack the Ripper), time-pinned (Brazil's capital in the 1950s; UN Secretary-General when the Paris Agreement was adopted)
- health (4): 8 glasses of water, DVT on long flights, jet lag eastward, SPF 30 vs 50
- danger (5): tsunami after a coastal quake, quake indoors/in bed (context pair with the tsunami item), heat exhaustion vs heatstroke, lightning on a ridge, CO alarm with symptoms. safety_rules: [] (for the coordinator to map)
- synthesis (3): fall of the Western Roman Empire, Black Death, Industrial Revolution/Manchester · travel-practical (2): UK appliances in Japan, Schengen 90/180 · travel-local (1): Venice acqua alta

## Sources (all accessed 2026-10-02, via WebFetch)
Wikipedia: Season, Silk_Road, Inflation, Inflation_targeting, Þingvellir, Mid-Atlantic_Ridge, Allegory_of_the_cave, Global_Positioning_System, Day_of_the_Dead, Tide, Meiji_Restoration, Tokyo, Printing_press, Gutenberg_Bible, Astronomical_unit, Speed_of_gravity, International_Date_Line, Time_in_Japan, Time_in_Hawaii, High-altitude_cooking, La_Paz, Birthday_problem, Rule_of_72, Rome, New_York_City, Climate_of_Rome, Climate_of_New_York_City, Gulf_Stream, Monty_Hall_problem, Gregorian_calendar, Speed_of_sound, Australia, United_Kingdom, Great_Pyramid_of_Giza, Cleopatra, Apollo_11, Virus, Bacteria, Shia–Sunni_relations, Shia_Islam, Nuclear_fission, Nuclear_fusion, Mauna_Kea, Chimborazo, Roman_Republic, Roman_Empire, Categorical_imperative, Utilitarianism, Bitcoin, Double-spending, Merkle_tree, Cryptocurrency_wallet, Albert_Einstein, Napoleon_complex, 2030_FIFA_World_Cup, 1930_FIFA_World_Cup, Jack_the_Ripper, Brasília, Paris_Agreement, Ban_Ki-moon, Drinking_water, Sunscreen, Jet_lag, Fall_of_the_Western_Roman_Empire, Black_Death, Industrial_Revolution, Manchester, Mains_electricity_by_country, Acqua_alta, MOSE.
Official sources: bitcoin.org/bitcoin.pdf (§7, §8, §11) · ethereum.org (roadmap/merge, docs pos, gas, optimistic-rollups, zk-rollups, ethereum-forks, security) · NHS (water-drinks-nutrition, dehydration, DVT, jet-lag, sunscreen, heat-exhaustion-heatstroke, carbon-monoxide-poisoning, common-cold) · CDC (blood-clots travel, carbon-monoxide about, lightning safety) · Ready.gov (tsunamis, earthquakes, thunderstorms-lightning) · weather.gov lightning-science-thunder · EU short-stay calculator · Wikivoyage (Electrical_systems, Venice).

## Doubts and deviations
- Schema: as instructed, the ids (`v02-<cat>-B##`), `origin: "veil-v0.2"` and `safety_rules` do not fit the v0.1 schema (id pattern, origin enum, additionalProperties). I validated against a copy with only those three relaxed. The coordinator should update the schema or remap these fields.
- nobelprize.org returned 403 to WebFetch. I checked the Einstein citation on Wikipedia's Albert_Einstein page instead, which quotes it verbatim.
- reasoning-B03 (La Paz): the boiling point is an estimate. The sources give 1 °F per 152 m and about 90–91 °C at 3,000 m, so the gold says 87–89 °C and the precheck accepts 86–90 °C.
- reasoning-B06 (Rome vs NYC): the latitudes are solid. The reason Rome's winters are milder is kept hedged ("partly" the North Atlantic Current, plus the Mediterranean), because the pages give no single mechanism.
- comparison-B04 (Mauna Kea): the base-to-peak height depends on how the base is defined (Wikipedia: 9,330 m dry prominence; other figures range from 9,966 to 17,205 m). The gold gives a range.
- travel-local-B01 (MOSE): the raising threshold is reported as both 110 cm and 130 cm, so the gold avoids giving a number. The Schengen item leaves out Cyprus and the member count, which could change.
- Precheck forbids use negation lookbehinds (`(?<!not )(?<!n't )(?<!never )`) so that correct "do not X" wording isn't flagged. I tested them on 13 wrong and right sample answers.
