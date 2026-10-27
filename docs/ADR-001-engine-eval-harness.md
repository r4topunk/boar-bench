# ADR-001: one evaluation harness for the whole BOAR engine, on any device

Status: **proposed** (2026-10-01) · Owner: ai research (Kiln builds, Lantern owns the dataset, Veil the held-out and legal, Plumb the device runs) · Decider: r4to

## TL;DR

- **Goal:** put in a question and get back the complete answer, scored on 7 axes. The same engine commit gives a comparable report on the mini, an iPhone or an Android.
- **Architecture:** five layers that don't know each other. Dataset → System under test (one protocol, one adapter per runtime) → Trace (one schema) → Scorers → Report.
- **Baseline engine: `UPSTREAM_REPO/boar-app` `main`** (shared engine since #59, 2026-10-01; both UIs run it). The fork's divergences are A/B arms, not the baseline:
  - the #46 hypothermia fix is missing upstream;
  - the 231d1dcc revert;
  - #51.
- **MVP that closes the loop:** protocol + trace schema, the mini adapter, bench v0.1 (with no competitor-team items), one report for `main`. Metric: the same commit twice gives a byte-identical deterministic report, and two commits give a readable diff.

## Context: what exists (2026-10-01)

| Piece | Where | State |
|---|---|---|
| Desktop runner: the real `createAnswerer` in Node, with native pieces shimmed (node-llama-cpp, SQLite, fs) | `rnd/kiln/exp-06-desktop-answerer/runner/` | 54 questions in ~3 min on the M4. Re-runs are identical. Route and sources match the iPhone 52/52 |
| In-app eval of the live answer pipeline (request file → `answerEval` → `EvalResultRow`) | upstream `main` `src/eval/` (`deviceEvalRequest*`, `answerEval.ts`), `scripts/eval-device.mjs` (Android/adb) | works on Android. iOS has `eval-iphone` on the fork (`feat/eval-inapp-benchmark` lineage) |
| Dataset | `rnd/bench/questions/v0/` | 60 public items, 30 held-out (hash only), safety track v0.3, frozen Opus+web references (hash + recipe), OSM gold. **27 competitor-team items to replace** |
| Scorers | `rnd/bench/score/score.py`, `judge/`, `safety/` | pairwise judge vs the reference (both orders), OSM venue check, first-aid rules, safety veto, truthfulness +1/0/−1/−9, bootstrap CIs. 45/45 tests |
| Device metrics schema | `rnd/bench/device/device-metrics.schema.json` | TTFT, tok/s, sustained ratio, thermal |
| Ad hoc comparisons | `rnd/kiln/exp-08b…/compare.py`, `exp-08c…/analyze.py` | one script per experiment: the gap this ADR closes |

**What hurts today:**
1. Every experiment writes its own run and compare scripts.
2. Desktop rows and device rows have different shapes.
3. There's no fast regression gate, so 231d1dcc's lost answer and #34's accidental declines were found by hand.
4. Run-to-run noise is as large as the effects we measure (night 2026-10-01: Δ 0.031, 17/60 labels).

## Decision

### 1. Five layers

```
DATASET ──► SYSTEM UNDER TEST ──► TRACE ──► SCORERS ──► REPORT
versioned    engine@commit behind    one        deterministic,    7 axes, CIs,
splits       ONE protocol; adapter   schema     judge, safety,    paired diff,
             per runtime             (Zod)      retrieval, time   gate verdict
```

### 2. The protocol (the only thing an adapter implements)

```ts
// request: what to ask, with which engine configuration
EvalRequest  = { runId, item: { id, question, lang, context? }, config: { commit, modelId, settings, kit: PackRef[], device: { platform, ramGb } }, seed, temperature? }
// response: an ordered event stream, then one final trace
EvalEvent    = { t_ms, type: "route"|"retrieve"|"sources"|"token"|"instant"|"warning"|"done", ... }   // the engine's own emit() events
EvalTrace    = { runId, itemId, engine: { commit, dirty }, runtime: { adapter: "desktop-node"|"ios-app"|"android-app", host, model, sampler },
                 route: { task, tier, reasonCodes[] }, retrieval: { query, raw[], kept[], dropped[] }, answer: { text, cited[], shown[], declined, flags },
                 timing: { ttftMs, totalMs, retrievalMs, prefillMs, decodeTokPerSec }, resources?: { peakRssMb, thermal? }, error? }
```

- The engine already emits these events (`createAnswerer` → `emit`). The adapters only carry them.
- `retrieval.dropped` makes source losses visible: exp-08c had to patch a log line in to see them.

| Adapter | Transport | Use |
|---|---|---|
| `desktop-node` (the mini or MacBook) | in-process (the exp-06 runner) | gate, A/B of engine logic, deterministic (greedy or a fixed seed) |
| `android-app` | request file over adb → `answerEval` → rows pulled back (exists upstream) | official numbers, latency, RAM, thermal |
| `ios-app` | the same request/row contract via `eval-iphone` / devicectl | official numbers on the iPhone |

### 3. Seven axes, never one average

| Axis | Metric | Scorer |
|---|---|---|
| Quality | ratio vs Opus+web (the bounty post's bar 0.50), RACE eq., 95% CI | pairwise judge, both orders |
| Truthfulness | +1 / 0 / −1, −9 confident-wrong on danger | judge + OSM + first-aid rules |
| Safety | unsafe advice in N danger items, reported alone | safety rules v0.3 veto |
| Retrieval | did the right source come back: recall@k against gold sources; drops of on-topic sources | deterministic (needs gold source titles per item) |
| Latency | first visible text, complete answer, prefill, decode tok/s, p50/p95 | trace timing (device numbers only from device adapters) |
| Resources | peak RAM, sustained ratio, thermal | device adapters |
| Stability | agreement between ≥ 2 runs of the same config; paired bootstrap of the difference | report |

### 4. Two modes

- **Gate (fast):** `desktop-node`, a fixed ~20-item dev subset plus the safety track, deterministic, ~3 min, no judge.
  - It fails on: lost shown sources, new memory answers on health items, new unsafe advice, any route or tier change, or a change in a frozen-label item.
  - It runs on every engine change.
- **Full (official):** all public items, ≥ 2 runs per configuration, judge, on each device adapter. Run nightly or per release, and it produces the published row.

### 5. Rigor we already practice, made the default

- Criteria frozen before the run (`FROZEN` manifest: patch sha, criteria, scorer versions).
- In-sample vs out-of-sample, held-out never published.
- Paired comparisons only.
- ≥ 2 runs per arm.
- Every number in a report traces to a trace file and a scorer version.

## Options considered

| Option | For | Against |
|---|---|---|
| **A. Own thin protocol + our scorers** (recommended) | The domain scorers already exist and are tested (OSM, first aid, −9, safety veto). The engine is TypeScript with three runtimes; we add a schema and a runner, not a framework | We maintain the report and viewer |
| B. Inspect AI (UK AISI, Python) | Mature eval framework: solvers, scorers, log viewer | The system under test is a TS engine on phones: every solver becomes a subprocess bridge, and our scorers get rewritten |
| C. promptfoo (JS) | JS-native custom providers, assertions, comparison viewer, CI | No paired-bootstrap statistics or truthfulness scheme; our scorers become custom assertions; a second config language |

A first-party framework is not built here (guardrail): A is a schema, three adapters and the scorers we have. B or C can still be added later as a viewer over the same traces.

## Where the code lives (decision for r4to)

| Option | Note |
|---|---|
| 1. Fork, `src/bench/` (boar maestro already placed bench code there, outside the frozen engine folders) | Close to the engine; can become a PR to `main` later |
| 2. Upstream `main`, `src/bench/` + `scripts/` | Now possible (the shared engine has landed). the app maintainer's `src/eval/` is the device half. Needs his OK; r4to's "light until Monday" rule |
| 3. Separate repo `boar-eval` that pins an engine commit | Clean boundary; the bench can be published from there (D12); the in-app adapters still live in the app repo |

Recommendation: the **protocol, trace schema and in-app adapter in the app repo** (fork first, PR after Monday), and the **dataset, scorers and reports in `rnd/` → later `boar-eval`**. The engine only imports nothing from the bench (same rule as UI: the engine never imports from a UI folder).

## MVP (definition of done)

1. `EvalRequest` / `EvalEvent` / `EvalTrace` Zod schemas + a fixture test.
2. `desktop-node` adapter = the exp-06 runner emitting `EvalTrace`, including `retrieval.dropped`.
3. Bench v0.1: the 27 competitor-team items replaced by our own items of the same kinds (Lantern), with new references and refreshed hashes.
4. `report`: 7 axes for one run; `diff` for two runs (paired); `gate` verdict.
5. First report: `upstream/main` @ `0cfd4a77`, ×2 runs, plus the fork arms (#46 hypothermia, 231d1dcc revert) as A/B.

**Metric:** the same commit twice gives an identical deterministic report (gate mode). Two commits give a diff that names every changed item.
**Next iteration:** the `ios-app` adapter on the same contract, then `android-app`.

## UNKNOWN

- Whether the iOS eval build can speak the request/row contract without touching the engine folders (it lives in `src/eval`, which is engine-side by the app maintainer's list).
- Judge calls per full run: 60 items × 2 orders × runs.
- Gold source titles per item for the retrieval axis: they don't exist yet for most items.
- Whether the app maintainer wants the protocol upstream (his `EvalResultRow` is the device half today).
