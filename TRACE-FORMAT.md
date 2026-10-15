# Trace format and judging: how any team scores its app on the bench 

TL;DR: run your app on `bench/v0.1/questions.public.jsonl` and write one JSON line per question (an **EvalTrace**). Then run `harness/judge.mjs`. It compares each answer with a frozen frontier-plus-web reference in both A/B orders, using Claude through Claude Code (`claude -p`). Finally, compute the three scales with `metrics/floor_metrics.py`. The judge is a closed model: re-runs agree closely, but not bit for bit.

```sh
pnpm i                                                      # zod + tsx for the validator
node harness/validate.mjs my.traces.jsonl                   # optional strict schema check (full EvalTrace)
node harness/judge.mjs --traces my.traces.jsonl --out my.judgments.jsonl --bench bench/v0.1 --dry-run   # counts calls, no spend
node harness/judge.mjs --traces my.traces.jsonl --out my.judgments.jsonl --bench bench/v0.1            # Opus, judge.v1
python3 metrics/floor_metrics.py --dir . --runs my --questions bench/v0.1/questions.public.jsonl --decline-ratio 0.306
python3 scorers/score.py --traces my.traces.jsonl --judgments my.judgments.jsonl --bench bench/v0.1 --json my.score.json   # win/tie/loss + precheck + safety
```
(`floor_metrics.py --runs my` reads `my.traces.jsonl` and `my.judgments.jsonl` from `--dir`.)

## 1. What judge.mjs reads from a trace

One JSON object per line. The last line per `itemId` wins. Items with `grading.type == "venue-list"` (3 of 60) are not judged, so v0.1 gives **57 judged items = 114 calls** per run.

| Field | Required by judge.mjs | Notes |
|---|---|---|
| `itemId` | **yes** | the bench `id` (e.g. `lan-exp-001`) |
| `answer.text` | **yes** | the full text the user would see, citations included |
| `error` | **yes** (`null` when ok) | `{code, message}` on failure. Errored traces are dropped with a WARN, or scored at the floor with `--floor-errored` (recommended for public numbers: a failure must count against the app) |
| `engine.commit`, `engine.arm` | no | optional: your build id and a label, e.g. `"a1b2c3d"`, `"main"`. If they are absent the judge labels the system `system@unknown` (override with `--system NAME`) |
| `runId` | yes (copied into rows) | any string |
| `answer.declined` | for the measured D only | `true` when the app declined; needed only if you do not pass `--decline-ratio 0.306` |
| `route`, `retrieval`, `timing`, `runtime`, `config`, `events`, `question`, `protocol`, `createdAt` | no (judge) / **yes for `validate.mjs`** | the full EvalTrace v1 (`packages/protocol/src/index.ts`) |

The "judge-minimal" trace is enough to get a judge verdict. The full EvalTrace is what `validate.mjs` and `scorers/score.py` check, and what a leaderboard row should carry (latency and sources make the number auditable).

### Example row (full EvalTrace v1, one line in the file; wrapped here)
```json
{"protocol":"1.0.0","runId":"myapp-v1.2-s42","itemId":"lan-exp-001","question":"<copied from the bench>",
 "engine":{"commit":"a1b2c3d","arm":"main","dirty":false},
 "runtime":{"adapter":"android-app","host":"Pixel 8a Android 16","model":"qwen3-4b-instruct-2507-q4_k_m","sampler":{"temperature":0.7,"seed":42},"versions":{}},
 "config":{"commit":"a1b2c3d","arm":"main","modelId":"qwen3-4b","settings":{},"kit":[],"device":{"platform":"android","ramGb":8}},
 "route":{"task":null,"tier":null,"outcome":null,"reasonCodes":[]},
 "retrieval":{"raw":[],"kept":[{"title":"Singapore","section":null,"source":"wikipedia","similarity":0.71}],"dropped":[]},
 "answer":{"text":"Singapore is a city-state ... [1]","cited":["Singapore"],"shown":["Singapore"],"declined":false,"weakSources":false,"warnings":[]},
 "timing":{"ttftMs":2100,"totalMs":9800,"retrievalMs":300,"prefillMs":null,"decodeTokPerSec":null,"promptTokens":null,"outputTokens":null},
 "resources":null,"events":[],"error":null,"createdAt":"2026-10-20T12:00:00Z"}
```
Judge-minimal equivalent: `{"runId":"myapp-v1.2-s42","itemId":"lan-exp-001","answer":{"text":"…"},"error":null}` (add `"engine":{"commit":"…","arm":"…"}` if you want it in the judgment rows).

Rules for a fair trace:
- The question is sent **exactly** as written (no rewriting, no system prompt that names the bench).
- The app runs offline, as shipped. Say in the leaderboard row what device or desktop proxy it ran on.
- One run per seed, with no cherry-picking across seeds. Report the seeds you ran.

## 2. Running the judge with Claude Code

- Needs the `claude` CLI logged in (subscription or API). `judge.mjs` strips API-key variables from the child environment (`cleanEnv`), so a subscription login is used when present. Each call is `claude -p` with no tools and a JSON schema (`scorers/vendor/eval-lib/judge-core.mjs`, prompt **judge.v1**).
- **Both orders:** every item is judged twice, once with your answer as A and once as B. The first order per item is drawn with `--seed 7`. Both answers are blinded first (`<think>` blocks, trailing `Sources:` lists, URLs, markdown links and `[n]` markers removed) so the judge cannot tell which is the reference.
- **Default model:** `--judge-model opus` (judge.v1). These are the only numbers comparable with ours.
- **Cheap triage:** `--judge-model claude-haiku-5-5 --effort low`. The rows are then tagged `judgeVersion: judge.v1-low`. Never mix them with judge.v1 numbers: Haiku agrees with Opus on the winner (54/57 items) but compresses gaps, so it ranks systems without sizing the difference.
- **Resume:** rerun the same command. Rows already in `--out` are reused only if the traces, questions and references shas, the judge version and the model all match (otherwise it exits 7). Rate limit → exit 3; API error → exit 4. Nothing is retried silently.
- **Parallel:** run N shards with disjoint `--ids` and `--gap-ms 0`, then concatenate (we use N = 4 for Opus).
- **Cost:** about $0.027 list-equivalent per Opus call. One v0.1 run is 114 calls (≈ $3; ≈ 27 min sequential at ≈ 9 s per call plus the default 5 s gap; ≈ 5 min at N = 4).
- **Pass `--strict`** for a public number: it exits before any call if a trace or reference is missing.

## 3. Reading the three scales (our definitions)

Per answer, the judge gives correctness, completeness and usefulness on 1–5. Mean rubric = their mean. Both orders are averaged. S = your answer's mean rubric, R = the reference's.

| Scale | Formula | Read it as | Our 4B claim build (for scale) |
|---|---|---|---|
| **Raw ratio** | Σ S / Σ R | the pre-registered metric. Trap: a blank or wrong answer still gets 1/5 on each axis, so an app that declines everything scores ≈ 0.31 for free | v0.2 0.512, V-para 0.413 |
| **Floor-adjusted** (`above_min`) | Σ (S − 1) / Σ (R − 1) | quality above the rubric minimum; **our headline**. 0.50 here = "half as good as the reference" | v0.2 0.388, V-para 0.261 |
| Above always-decline (`above_decl`) | (raw − D) / (1 − D), D = 0.306 | gain over a system that declines every question (D measured on 79 declines in 7 runs) | v0.2 0.297, V-para 0.155 |
| **Win / tie / loss** | per item: the two orders agree → that winner; they disagree → tie | how often the app's answer is preferred outright | 0 wins on every set so far |

- CIs: stratified (by category) two-level bootstrap (items, then runs within item), 2,000 resamples, seed 11 (`floor_metrics.py`). Paired differences between two apps: `metrics/paired_gap.py`.
- Always report **all three ratios plus W/T/L**, with n and seeds. A raw 0.50 alone is not "half as good".
- v0.1 references are Claude Opus + web, and the judge is also Claude: the judge may favour Claude-style answers. That bias is the same for every team, so comparisons between apps are fairer than the absolute level.

## 4. Reproducibility, stated plainly

- The judge is a **closed, hosted model**. The same traces judged twice agree closely: a second judge model agreed with the primary judge on 453/456 verdicts in an internal check, and two-seed means move by about ± 0.014 (deep tier, three seeds on our internal paraphrase set). They are not bit-identical, and the model behind an alias can change. Every row records `judgeModel`, `cliVersion`, `judgeVersion` and the three input shas; publish them with your numbers.
- The references are frozen files (sha in `bench/v0.1/refs/MANIFEST.json`). If you regenerate them, your ratio is on a different denominator and is **not comparable**.
- Everything else (traces → metrics) is deterministic given the judgment rows.
