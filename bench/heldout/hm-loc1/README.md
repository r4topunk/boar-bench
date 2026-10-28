# hm-loc1: blind, location-anchored danger test set

**TL;DR:** 45 items (30 `danger: true`, 15 `danger: false`). Each one is a traveller in a named place asking about a health or safety situation. Veil wrote the items blind to the teammate's list of unsafe pack sentences. Every danger item cites official conduct sources that were fetched on 2026-10-02 and whose quotes were checked word for word. The file is frozen; see the bottom line.

```fish
shasum -a 256 -c rnd/veil/hm-loc1.sha256          # integrity
jq -c 'select(.danger) | {id,lang,form,category,place}' rnd/veil/hm-loc1.jsonl
```

## How the blind was kept
- I did not open, list or grep anything under `rnd/research/`, `rnd/kiln/`, `boar-eval/`, `rnd/bench/` or `shared-data/`. I did not read the text of any file in `rnd/veil/`.
- The only thing I read was the **key list** of line 1 of `rnd/veil/hm-fresh3.jsonl` (`jq 'keys'`). I used it to match the schema.
- I wrote the questions, traps, answers and rubrics from general first-aid knowledge. Then I checked each answer against official pages fetched that day. Nothing came from the pack text.
- The generator script and the downloaded source pages are in a session scratchpad and are not part of this deliverable.

## Schema (one JSON object per line)
`id` (`vit-loc1-001…045`), `question`, `lang` (`pt`|`en`), `danger`, `category`, `place`, `form` (`decision`|`describe`|`named`|`casual`|`info`), `answer` (correct conduct, 1–3 sentences), `rubric` (`{must_say:[], must_not_say:[]}`), `reference_sources` (`[{org,url,quote,accessed}]`; empty for non-danger items), `origin: "veil-hm-loc1"`, `memory_hint: null` (kept only so the keys match hm-fresh3), `notes`.

Form definitions:
- `decision`: a yes/no question. Every danger decision item contains a trap, either a folk/outdated remedy or a risky action such as a tourniquet, urine, alcohol, a doorway, waiting for a warning, or "sleep it off".
- `describe`: the user gives symptoms or a scene without naming the hazard.
- `named`: the user names the condition or animal, with no trap.
- `casual`: informal register with typos or slang.
- `info`: a non-emergency planning question.

## Counts

| lang | danger | decision | describe | named | casual | info | total |
|---|---|---|---|---|---|---|---|
| pt | true | 7 | 3 | 1 | 3 | – | 14 |
| en | true | 9 | 4 | 1 | 2 | – | 16 |
| pt | false | – | – | – | – | 7 | 7 |
| en | false | – | – | – | – | 8 | 8 |
| **all** | | 16 | 7 | 2 | 5 | 15 | **45** |

**Danger categories (30):**

| Category | Items |
|---|---|
| marine_sting | 3 |
| cyclone | 2 |
| altitude | 2 |
| heat_illness | 2 |
| animal_bite_rabies | 2 |
| snakebite, scorpion_sting, flood, rip_current, lightning, diarrhoea_dehydration, carbon_monoxide, hypothermia, earthquake, frostbite, tsunami, spider_bite, volcano, wildfire, travellers_diarrhoea, drowning, road_crash, methanol_poisoning, avalanche | 1 each |

**Non-danger categories (15):**

| Category | Items |
|---|---|
| earthquake_info | 2 |
| water_safety | 2 |
| vaccines, altitude_prep, flood_prep, first_aid_kit, cyclone_prep, air_quality, monsoon_prep, malaria, volcano_info, cold_prep, seasickness | 1 each |

## Places / countries
- **Danger set: 21 countries.**
  - Brazil (9 items): Pantanal, Belo Horizonte, Petrópolis, Florianópolis, Porto de Galinhas, Chapada Diamantina, Manaus, Gramado, Rio de Janeiro.
  - Other countries: Portugal, Mozambique, Bolivia, Chile, Argentina, Japan, Indonesia, Morocco, Australia (×2), USA, Iceland, Canada, Nepal, India, Egypt, South Africa, Kenya, Philippines, Vietnam, Switzerland.
- **Non-danger set adds** Peru, Colombia, Mexico, Thailand, New Zealand, Tanzania, Italy, Norway and Antarctica (Drake Passage).
- **Overall:** 29 countries plus Antarctica, covering every continent.

## Sources (all accessed 2026-10-02)

| Org | Page(s) | Used for |
|---|---|---|
| Ministério da Saúde (BVS/MS) | `bvsms.saude.gov.br` (acidentes ofídicos; picada de escorpião) | 001, 002 |
| Ministério da Saúde | gov.br cartilha doenças diarreicas agudas (PDF) | 007 |
| SESA-PR (state health dept.) | saude.pr.gov.br Acidentes por Escorpião | 002 |
| Ready.gov / FEMA | floods, hurricanes, earthquakes, tsunamis, volcanoes, wildfires | 003, 010, 012, 015, 021, 022, 028 |
| NOAA / NWS | Ocean Today rip-current guide; lightning-safety; lightning-outdoors; hurricane_safety.pdf | 004, 006, 010 |
| NHS | hypothermia, frostbite, CO poisoning, jellyfish/sea-creature stings, altitude sickness, heatstroke | 005, 008, 009, 011, 013, 014, 020, 023, 025 |
| CDC Yellow Book | high-altitude illness; travelers' diarrhea | 011, 023, 024 |
| WHO | rabies fact sheet | 016, 017 |
| healthdirect (AU) | sea-creature stings, jellyfish stings, spider bites | 018, 019, 025 |
| St John Ambulance Australia | rescuing a drowning person; spinal and neck injury | 026, 027 |
| NaTHNaC/TravelHealthPro; UK FCDO Travel Aware | methanol poisoning | 029 |
| Avalanche Canada; Avalanche.org | companion rescue | 030 |

**How the quotes were verified:**
- **curl:** every quote except the two from CDC was downloaded with curl, converted to text, and matched as a whitespace-normalised substring by the generator. If any quote had failed to match, the build would have stopped.
- **WebFetch:** CDC returns HTTP 403 to curl. I checked its two altitude quotes word for word with WebFetch instead and corrected one of them to the exact wording.
- **Length:** all quotes are 25 words or fewer.

## Known gaps (UNKNOWN)
- **No source for some claims:** the helmet detail in 027 (leave the helmet on unless it blocks breathing) is standard first-aid teaching, but the cited St John page only supports "do not move". Landslide risk in Petrópolis (003) and rabies endemicity in Bali and Morocco (016, 017) are background knowledge, not quoted.
- **Non-danger answers have no sources:** facts such as hurricane season dates, Vesuvius' 1944 eruption, the Chiang Mai burning season and Recife's SMS 40199 alert line were written from knowledge and not fetched.
- **Emergency numbers were not checked against a source:** 192/193/199 (Brazil), 112, 000, 911, 115 (Vietnam), 999/112 (Kenya) and 112 by mobile (South Africa).
- **Non-official sources:** the avalanche and methanol sources come from specialist or travel-health bodies rather than health ministries.

FROZEN 2026-10-02T00:54:28-03:00 · sha256(hm-loc1.jsonl) = ac16b33cbc06c1126b6f96bd6fdddcb144ea7fca162d360ef5d1717ab317d742 · file set read-only (chmod 444). Do not edit; publish corrections as hm-loc2.
