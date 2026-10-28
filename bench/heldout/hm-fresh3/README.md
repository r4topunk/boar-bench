# hm-fresh3: blind out-of-sample set for the danger/health-question detector

## TL;DR
- 74 items: **24 danger**, **25 hard negatives**, **25 ordinary research questions**. 36 in PT-BR, 38 in EN.
- Written blind by Veil on 2026-10-01. The author did not see the detector, its prototypes, or any earlier test items.
- Each danger item has a verified conduct answer, a must-say / must-not-say rubric, and 1–3 quotes from official sources fetched on 2026-10-01.
- **FROZEN.** Never edit `hm-fresh3.jsonl`. If something needs fixing, publish it as `hm-fresh4`.

```fish
shasum -a 256 -c rnd/veil/hm-fresh3.sha256        # verify integrity
python3 -c "import json;r=[json.loads(l) for l in open('rnd/veil/hm-fresh3.jsonl')];print(sum(x['danger'] for x in r),len(r))"
```

## How it was written blind
- I opened, listed and grepped nothing under `rnd/research/`, `rnd/kiln/`, `boar-eval/` or `rnd/bench/`.
- I read no text from any file in `rnd/veil/`. The only read was the key list of the first line of `hm-fresh2.jsonl`, to match the schema.
- I wrote the items from scratch around the scenarios a traveller without signal might type, then checked the conduct against official pages with WebFetch and WebSearch.
- IDs (`vit-hm3-001…074`) follow a shuffle with a fixed seed (`20261001`), so position and ID say nothing about the label.

## Counts

| lang | danger | hard negative | ordinary | total |
|---|---|---|---|---|
| en | 12 | 13 | 13 | 38 |
| pt | 12 | 12 | 12 | 36 |
| **total** | **24** | **25** | **25** | **74** |

Form × lang:

| form | danger en | danger pt | non-danger en | non-danger pt |
|---|---|---|---|---|
| decision (yes/no with a folk-remedy or wrong-plan trap) | 8 | 5 | – | – |
| describe (symptoms or situation only, condition not named) | 3 | 2 | – | – |
| named (condition named) | 1 | 2 | – | – |
| casual (typos, no accents) | 0 | 3 | 1 | 2 |
| info | – | – | 25 | 22 |

`memory_hint` on danger items (my guess at whether a 1.5B model answering from memory gets it right): right 17, wrong 7. The 7 marked wrong are bleach and milk, altitude/HACE, diving/DCS, jellyfish vinegar, rabies PEP urgency, hypo vs. insulin, and the asthma puff protocol.

## Categories
- **Danger (24, one each):** cardiac, stroke, allergy (anaphylaxis), poisoning-ingestion (child + bleach), eye (chemical), burn, cold (hypothermia), heat (heatstroke), altitude (HACE), diving (DCS), marine-life (box jellyfish), snake, animal-bite (rabies), bleeding, head-injury (child), drowning, electric-shock, gas-co, earthquake, diabetes (hypo), seizure, asthma, mental-health (suicidal friend), flood (driving through water).
- **Not covered:** labour, sprain/fracture, food poisoning in a child, dehydration in an elder, fire. Labour was dropped because I found no official page with quotable after-birth conduct.
- **Hard negatives (`hn-*`):** epidemiology (malaria, 1918 flu, dengue), medical history (yellow fever, Oswaldo Cruz, captopril/jararaca), metaphors ("burn your bridges", "quebre a perna"), literature (Hamlet, O Nome da Rosa), biology (box-jellyfish toxin, venenoso vs peçonhento), chemistry (bleach + ammonia), anatomy, sports-injury history, animal facts (Phoneutria, Recife sharks), disaster history (Kiss, Brumadinho), cooking with "burnt/queimada", altitude travel logistics (El Alto, EBC insurance, Huayna Potosí acclimatisation), and a physiology study question.
- **Ordinary (`ord-*`):** crypto (PoW/PoS, EIP-4844 blobs, stablecoins, BTC vs ETH), economics (Selic/CDI, stagflation, Gini, Plano Real), history, geography, science, tech (Pix, VPN vs Tor), culture, travel, local food.

## Schema
`id, category, question, lang, danger, memory_hint, form, answer, rubric, reference_sources, origin, notes`. The key order matches hm-fresh2.
- Danger items: `rubric = {must_say:[…], must_not_say:[…]}` and `reference_sources = [{org, url, quote (≤25 words), accessed}]`.
- Non-danger items: `rubric = null`, `reference_sources = []`, `memory_hint = null`. Their `notes` starts with `hard-negative:` or reads `ordinary research question`.
- `origin = "veil-hm-fresh3"` on every item.

## Sources (all fetched 2026-10-01)
- NHS: heart-attack, stroke/symptoms, anaphylaxis, poisoning, eye-injuries, burns-and-scalds, hypothermia, heat-exhaustion-heatstroke, carbon-monoxide-poisoning, head-injury-and-concussion, low-blood-sugar-hypoglycaemia, asthma-attack, what-to-do-if-someone-has-a-seizure-fit, help-for-suicidal-thoughts
- CDC Yellow Book: high-altitude travel, scuba diving / DCI, rabies
- WHO: rabies fact sheet
- healthdirect (AU): jellyfish-stings, electric-shocks-and-burns
- St John Ambulance: severe bleeding, drowning
- Ready.gov (FEMA): floods, earthquakes
- Ministério da Saúde: AVC; acidentes ofídicos plus its FAQ on torniquete
- Anvisa via Sinitox/Fiocruz: intoxicação por produtos de limpeza (CIATox 0800-722-6001)
- CVV: cvv.org.br (188)

## Caveats (UNKNOWN)
- The quotes came out of WebFetch's extraction model and I did not diff them character by character against the raw HTML. The stroke quote contains an ellipsis I added to stay within 25 words.
- St John Ambulance now says to remove a soaked pad and reapply pressure, while older guidance says to add a pad on top. The rubric accepts either, as long as pressure is maintained.
- The snake item has no official-page quote for "do not cut or suck". The Ministério da Saúde FAQ I fetched covers the tourniquet only. Secondary sources (CNN Brasil, state health departments) say the same about cutting and sucking.
- Some hard-negative and ordinary answers depend on dates or figures (Brumadinho 270 deaths, Ulaanbaatar population, El Alto 4,060 m). They are short reference answers, not graded truth.

## FROZEN
FROZEN 2026-10-01T21:27:56-03:00 · sha256(hm-fresh3.jsonl) = e99795d1c003981de92372e20e3e1c0fbc4ebbd5da7f04aca6d29c446296be70
