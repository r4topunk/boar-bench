# Dataset card: boar-eval bench v0.2-new (110 new items)

TL;DR: 110 new English items in 10 categories, written blind to BOAR (no packs, coverage tools, traces, failure lists or research cards). Each has a gold `answer`, a judge-facing `rubric` that also names wrong answers to penalize, a precheck `grading`, and Wikipedia/official `reference_sources` checked on 2026-10-02. Two blind writers wrote 55 items each. They converged on many of the same topics, so 37 + 7 slots were rewritten by other models. The final 110 pass every similarity gate. **Limitation:** every writer and rewriter is a Claude model (see the end).

```sh
python3 bench/v0.2/assemble.py                 # rebuilds questions.v02-new.jsonl byte-identically from blind/bench-v02/ (+ safety_rules mapping)
python3 bench/v0.2/validate.py                 # schema v0.2, precheck self-test, safety_rules vs rules v0.5, refs manifest
<venv>/bin/python bench/v0.2/similarity.py     # gates -> similarity.json (needs sentence-transformers; reads rnd/veil + competitors/<testcase-repo>)
node bench/v0.2/refs/gen_refs.mjs              # Opus+web references (resumable), then:
python3 bench/v0.2/refs/build_manifest.py      # refs.jsonl (private) + MANIFEST.jsonl / MANIFEST.json (hashes)
```

## Composition
explanation 21 · reasoning 21 · comparison 13 · crypto 13 · honesty-refusal 12 · health 8 · danger 10 · synthesis 6 · travel-practical 4 · travel-local 2.
- Grading: precheck for all 110 items.
- refuse_ok: 9 items.
- `danger: true`: 10 items.
- Ids: `v02-<category>-A##` for writer A's slots, `-B##` for writer B's slots; a rewrite keeps the id of the slot it fills.
- Schema: `questions.schema.json` is the v0.1 schema plus three changes: the v0.2 id pattern, origin `veil-v0.2`, and an optional `safety_rules`.
- Every item has license `CC-BY-4.0`.

## Method
1. **Spec.** Each item follows `plan/item-spec.draft.md` (sha `0311a22e…`, frozen in the pre-registration commit):
   - the rubric is written for the judge, with 1–2 "Penalize:" bullets;
   - honesty-refusal items name their type (false premise / unknowable / time-pinned) and say when declining is correct;
   - danger conduct comes from Ready.gov / NHS / CDC / NWS pages;
   - phrasing is mixed: first-person, direct question, imperative.
2. **Two blind writers.** Writers A and B are two separate agent instances given the same spec and no access to `rnd/`. Both are from the same model family (Claude). Both writers ran as Claude Opus 5.5 (`claude-opus-5-5`, recorded by the coordinator who launched them; the item `provenance` field says `writer-a/b 2026-10-02`). Rewriters: Sonnet (rewrite-sonnet), Fable (rewrite-fable), Opus (rewrite-r2-opus).
3. **Convergence found (round-1 gates).** Run over the 110 first drafts:
   - 23 cross-writer pairs exceeded word-Jaccard 0.30 or bge cosine 0.90 (one pair had identical question text: "Why did the Western Roman Empire fall?");
   - a manual review found 13 more same-topic pairs plus 2 items duplicating safety-track items;
   - 1 item hit a competitor team question (J 0.46).

   The two writers had picked largely the same "canonical" topics: sky colour, tides, Silk Road, Monty Hall, the birthday problem, the rule of 72, Tokyo→Honolulu, boiling point in La Paz, fission/fusion, the halving, the Merge.
4. **Resolution.** Pairs were sorted by writer-A id and resolved by alternation (keep A, keep B, …). The losing slot keeps its category and is rewritten. One coordinator override: keep comparison-A03, rewrite only comparison-B01. That gave 37 round-1 rewrites:
   - writer-A slots (17) rewritten by **Claude Sonnet** (`rewrite-sonnet 2026-10-02`);
   - writer-B slots (20) rewritten by **Fable** (`rewrite-fable 2026-10-02`).
5. **Convergence again (round 2).** The Sonnet and Fable rewrites collided with each other on 7 topics: Lightning Network, Bitcoin difficulty retarget, rip current, South Asian monsoon, caffeine limits, distance to the horizon, Aral Sea. Alternation kept one of each pair. The other 7 slots were rewritten by **Claude Opus** (`rewrite-r2-opus 2026-10-02`); 5 of those 7 are centred outside Europe/North America.
6. **Fact fixes by the coordinator** (originals kept as `*.pre-factfix.jsonl` in `blind/bench-v02/`):
   - comparison-A04 (Mont Blanc: 4,807.3 m in the 2025 survey; rubric range 4,805.59–4,810.02 m; precheck accepts plain "4807"/"4809");
   - reasoning-A05 (a billion seconds ≈ 31 years 251 days, not 287).
7. **Final gates** (`similarity.py` → `similarity.json`): 0 threshold collisions over the final 110, against themselves, v0.1 public, safety track v0.3, held-out v0.1 and a competitor team @87bb6e9.

   | pool | max word-Jaccard | max bge cosine |
   |---|---|---|
   | among the 110 | 0.280 | 0.774 |
   | v0.1 public | 0.290 | 0.788 |
   | safety track | 0.294 | 0.787 |
   | held-out | 0.294 | 0.875 |
   | a competitor team | 0.273 | 0.703 |

   The topic review found no duplicate. Five overlaps are recorded as "watch" in `similarity.json` (e.g. hypothermia and heatstroke clauses vs the safety track).

## Provenance per item (field `provenance`; 110 = 38 + 35 + 14 + 16 + 7)
- **writer-a (38):** explanation-A01 A02 A03 A05 A08 A09 A10 A11 · reasoning-A01 A03 A06 A07 A09 A10 · comparison-A01–A07 · crypto-A04 A05 A06 · honesty-refusal-A02–A06 · health-A01 A02 A04 · danger-A02 A03 A05 · synthesis-A02 · travel-practical-A02 · travel-local-A01
- **writer-b (35):** explanation-B02 B03 B06 B07 B09 B10 · reasoning-B02 B04 B05 B06 B08 B10 · comparison-B02 B04 B06 · crypto-B01 B02 B03 B05 B07 · honesty-refusal-B01 B02 B04 B05 B06 · health-B01 B02 B04 · danger-B01 B03 B04 · synthesis-B01 B03 · travel-practical-B01 · travel-local-B01
- **rewrite-sonnet (14):** explanation-A04 A07 · reasoning-A02 A04 A05 · crypto-A01 A02 · honesty-refusal-A01 · health-A03 · danger-A01 A04 · synthesis-A01 A03 · travel-practical-A01
- **rewrite-fable (16):** explanation-B01 B04 B05 B08 · reasoning-B01 B03 B07 B09 B11 · comparison-B01 B03 B05 · crypto-B06 · honesty-refusal-B03 · danger-B05 · travel-practical-B02
- **rewrite-r2-opus (7):** explanation-A06 · reasoning-A08 · crypto-A03 B04 · health-B03 · danger-B02 · synthesis-B02

All inputs and gate records are in `blind/bench-v02/`: writer files and NOTES, `collisions.json`/`.md` (round 1, with every pair score and the override), rewrites-{a,b}.jsonl and their NOTES, `collisions-r2.json`, and `rewrites-r2.jsonl` with its NOTES.

## Safety rules (rules v0.5: `scorers/vendor/safety/rules.v0.5.json` + `safety_check.v0.5.py`)
v0.5 has the same rule ids and patterns as v0.4; only the matcher changed (negation handling, `review` status). `safety_check.rules_for` reads `safety_rules` directly, so a rule is assigned only when two things hold: its conduct is the item's conduct, and the item's gold answer passes it.
- **danger-A03 → `hypo-exertion`.** This covers the moderate-hypothermia branch. Caveat: an answer that correctly allows gentle exercise in the *mild* branch could be flagged.
- **Need a new rule (no v0.5 rule fits), `[]` for now:**
  - danger-A01: rip current. Forbid "swim straight back to shore".
  - danger-A02: generator in an attached garage. `co-leave-and-call` covers suspected poisoning; as an omission rule it would flag a correct prevention answer.
  - danger-A04: adult choking.
  - danger-A05: driving through floodwater.
  - danger-B01: tsunami after a coastal quake. The `quake-*` rules cover indoor conduct.
  - danger-B02: monkey scratch, rabies PEP.
  - danger-B03: heat exhaustion in an alert person. `heat-fluids-confused` does not apply, because fluids are correct here.
  - danger-B04: lightning on a ridge.
  - danger-B05: tornado warning in a mobile home.

  Until those rules exist, the judge rubric is the only safety check on these 9 items.

## References (`refs/`)
- Recipe: reference.v1, the same as v0.1 (`bench/v0.1/refs/gen_refs.mjs`):
  - `claude -p` with a clean env ([usage detail removed] only, no API key), model `opus`;
  - system prompt `reference.v1.md` (sha `d5144343…`), tools WebSearch + WebFetch;
  - sequential with a 5 s gap, one retry, stop on rate limit; resumable.
- What changed in the v0.2 copy:
  - input file and origin filter;
  - spend tag;
  - freeze check: there is no SHA256SUMS before the freeze, so a row counts only if its question text equals the current item's (a rewritten item is regenerated).
- `build_manifest.py` writes:
  - `refs.jsonl`: the text, gitignored, never published;
  - `MANIFEST.jsonl`: per-item sha256, model, CLI, prompt sha and date;
  - `MANIFEST.json`: totals plus the questions sha. `--freeze` sets `frozen: true` only at 110/110.

## Limitations
- **Single model family.** All writers and rewriters are Claude models (two blind writers from the same family, plus Sonnet, Fable and Opus). They converged strongly: round 1 produced 36 same-topic pairs out of 55 slot pairs, and even the independent rewriters collided on 7 of 37 topics. The item pool therefore leans toward topics Claude models consider canonical, and it may correlate with the strengths or weaknesses of Claude-based systems and references (the references are also Opus). **Recommendation for v0.3:** add a writer from another model family and/or a human writer, and report per-writer results.
- The topic review is a judgment call, recorded in `similarity.json` and `blind/bench-v02/collisions.*`.
- Facts were checked on 2026-10-02. Some may drift: Dead Sea level, ZTL fines, Japan IDP country lists, and Bitcoin Core RBF defaults are the most time-sensitive. Time-pinned honesty items are pinned on purpose.
- English only. 9 of the 10 danger items have no automatic safety rule in v0.5 (see above).

## Coordinator notes at freeze (2026-10-02)
- Topic overlaps kept on purpose (different angle, below every gate): antibiotics in health-A01 vs comparison-A03; lightning in reasoning-A06 (arithmetic) vs danger-B04 (conduct); Australia's area in comparison-A01 vs reasoning-B10; hypothermia in danger-A03 vs safety-track contrast (spec §3); heat in danger-B03 vs saf-012.
- Safety rules: 9 of 10 danger items have no matching v0.5 rule. Until new rules exist (a dated pre-run addendum), their safety is scored by the judge rubric's penalize bullets only, and reports must say so.
- Fact fixes by the coordinator before freeze: comparison-A04 (Mont Blanc 2025 survey), reasoning-A05 (a billion seconds = 31 years 251 days). Originals kept under blind/bench-v02/*.pre-factfix.jsonl.
