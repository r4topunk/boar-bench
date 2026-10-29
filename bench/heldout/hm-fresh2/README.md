# hm-fresh2: blind out-of-sample test set for the danger/health-question detector

## TL;DR
- 40 items in `hm-fresh2.jsonl`: **24 danger** (real health emergencies, injuries or disasters as a traveller with no signal would type them) and **16 hard negatives** (`danger: false`) that use the same vocabulary but ask nothing about a health situation.
- Written **blind** by Veil: no prototype questions, detector code or tuning sets were opened.
- Each danger item has a 1–3 sentence correct conduct, a must/must-not rubric, and 1–3 verbatim quotes (≤25 words) from public health or first-aid pages fetched on 2026-10-01.
- Frozen. Do not edit the jsonl. A new version means a new file (`hm-fresh3`).

```fish
# verify integrity
shasum -a 256 -c rnd/veil/hm-fresh2.sha256
# counts
python3 -c "import json,collections;r=[json.loads(l) for l in open('rnd/veil/hm-fresh2.jsonl')];print(collections.Counter((x['danger'],x['lang']) for x in r))"
```

## How it was written (blind protocol)
- Not opened or listed: `rnd/research/`, `rnd/kiln/exp-08c-health-no-source/`, `rnd/kiln/exp-10-main-baseline/questions*`, the text of `rnd/veil/hm-fresh.jsonl`, and any `*danger*` or `safety` track question files.
- From `hm-fresh.jsonl`, only the first line's **keys** were read, to match the schema.
- Questions were written from scratch to vary in style:
  - some name the condition, most only describe symptoms or the situation;
  - many are yes/no decisions that contain a folk-remedy trap, for example "should I push the water out", "pee on it?" or "give her insulin?";
  - several are casual, lowercase and contain typos.
- Conduct was checked against official pages with WebFetch on 2026-10-01. Quotes are verbatim; `...` marks an elision. Each source object carries an `accessed` date.

## Schema (one JSON object per line)
| key | notes |
|---|---|
| `id` | `vit-hm2-001` … `vit-hm2-040` (001–024 danger, 025–040 negatives) |
| `question`, `lang` (`en`/`pt`), `danger` (bool), `category` | negatives use the `neg_*` category prefix |
| `form` | `symptom_description`, `yes_no_decision`, `casual_typo`, `hard_negative` |
| `answer` | correct conduct (danger) or short factual answer (negatives) |
| `rubric` | `must:` / `must-not:` points (empty for negatives) |
| `reference_sources` | `[{org, url, quote, accessed}]` (empty for negatives) |
| `memory_hint` | guess whether a ~1.5B model answering from memory gets it right |
| `origin` | `veil-hm-fresh2` |
| `notes` | trap or nuance being tested |

The `hm-fresh` keys left out because they do not apply here: `kit_medical_article`, `coverage`, `why_1b_fails` (folded into `notes`), `vitalik_source`, `grading`, `grading_version`.

## Counts
| | en | pt | total |
|---|---|---|---|
| danger | 12 | 12 | 24 |
| hard negative | 9 | 7 | 16 |
| **total** | 21 | 19 | 40 |

`memory_hint` for danger items: 15 `right`, 9 `wrong`.

**Danger categories (24, one item each):** cardiac, stroke, allergy_anaphylaxis, poisoning_ingestion, eye_chemical, burns, cold_hypothermia, heat_illness, altitude, diving_dcs, marine_sting, snakebite, flood, bleeding, fracture, head_injury, drowning, electric_shock, carbon_monoxide, childbirth, diabetes_hypo, seizure, mental_health_overdose, earthquake.

**Negative categories:**
| category | items |
|---|---|
| neg_metaphor | 2 |
| neg_history | 2 |
| neg_biology | 2 |
| neg_geography | 2 |
| neg_cooking | 2 |
| neg_sports | 2 |
| neg_chemistry | 2 |
| neg_animal_fact | 1 |
| neg_travel_logistics | 1 |

**Forms:**
| form | items |
|---|---|
| yes_no_decision | 15 |
| symptom_description | 6 |
| casual_typo | 3 |
| hard_negative | 16 |

## Sources (all accessed 2026-10-01)
- **NHS** (nhs.uk): heart attack, stroke symptoms, anaphylaxis, poisoning, burns and scalds, hypothermia, heat exhaustion/heatstroke, jellyfish and sea-creature stings, head injury, help for suicidal thoughts, paracetamol for adults.
- **NHS London Ambulance Service:** advice if you are due to give birth.
- **NHS Neonatal Network South East:** prehospital management of neonates.
- **CDC:** Yellow Book chapters on high-altitude illness and scuba/decompression illness; NIOSH pages on venomous snakes and carbon monoxide; treatment of low blood sugar; first aid for seizures.
- **St John Ambulance** (sja.org.uk): stroke, life-threatening bleed, fractures, drowning, electrocution.
- **healthdirect** (Australia): objects or chemicals in the eye, jellyfish stings, electric shocks and burns.
- **Ready.gov** (FEMA): floods, earthquakes.
- **Anvisa** (gov.br): Disque-Intoxicação, 0800-722-6001.

## Known gaps / UNKNOWN
- **Childbirth (020):** the rubric says do not pull or cut the cord. No page was found that says this verbatim. The cited NHS neonatal framework only says not to clamp the cord before 60 seconds ([NHS quote withheld]).
- **Mental health (023):** the CVV 188 number, the Brazilian emotional-support line, comes from general knowledge and is not quoted from a source.
- **Brazilian numbers:** SAMU 192 and Bombeiros 193 also come from general knowledge and are not quoted.
- **Hard negatives:** answers are from general knowledge and were not checked against sources. The detector only uses the label, so answer precision is secondary.
- **Pages blocked to the fetcher (HTTP 403/404):** Mayo Clinic, American Red Cross, American Stroke Association. Those topics were sourced from NHS, St John Ambulance or healthdirect instead.
- **`memory_hint`:** an author guess, not measured.

FROZEN: 2026-10-01 21:15:28 -0300 · sha256 `c055d7cbef4c9405fb53fa36d130dcb089d2d72b9d70b0c771318584743a546f` (hm-fresh2.jsonl)
