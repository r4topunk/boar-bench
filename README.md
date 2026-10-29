# BOAR bench: the open benchmark and harness for an offline research assistant

TL;DR: this repository is the complete evaluation side of the BOAR research (poidh bounty #31: an offline Android research assistant that is more than 50 % as good as internet plus a frontier model, on at most 12 GB of RAM, English only). It holds the public questions with frozen frontier-plus-web reference answers, the pairwise judge (Claude Opus, both A/B orders) and a cross-family judge (OpenAI gpt-5.6-sol via the Codex CLI), the scorers, the desktop adapter that simulates the phone, the arm patches and their criteria, the pre-registered plans, 14 pack self-test sets and 6 slices, and the reports. The held-out sets are retired and public since v1.1 (`bench/heldout/`, `bench/v0.4/`); no v0.3 items were ever written. Author: r4to, independent researcher. Status: v1.1.2, 2026-10-29 (full open record first published as v1.0 on 2026-10-26; one commit per release; earlier releases remain in the git history). The research record (reports, method, aggregates, pack cards) is the sibling repository `boar-research`; the live article is https://r4topunk.github.io/boar-research/.

Licences: code MIT (`LICENSE`), questions, docs and data wrappers CC BY 4.0 (`LICENSE-DATA`), third-party derived data under its source licence (`NOTICE`). Health, first-aid and safety content is AI-reviewed, not clinically reviewed, and is not medical advice.

## Quick start (about 5 minutes, no model needed)

```sh
pnpm install                         # zod, tsx, vitest (lockfile pinned)
pnpm test                            # protocol + desktop-node unit tests (TypeScript): 14 + 38 tests
pnpm test:all                        # + Python unit tests, judge-codex test, pre-commit hook test, data validation, hash pins
python3 bench/v0.1/validate.py --skip-heldout   # data checks on the public v0.1 split
python3 tools/verify-pins.py                    # every published sha256 pin in the tree
```

Last run of this exact tree (2026-10-26, macOS, Node 24, Python 3.14, pnpm 11): `pnpm install && pnpm test` passes; `pnpm test:all` passes (details in the release build log). Two Python tests skip by design because the real-run fixtures they need are not published.

## Map of the folders

| Path | What |
|---|---|
| `bench/v0.1/` | 60 public questions (`questions.public.jsonl`), gold, the safety track (12 items), frozen reference answers (`bench/v0.1/refs/refs.jsonl`), dataset card, `SHA256SUMS.json`, `validate.py` |
| `bench/v0.3/` | pre-registered analysis plan (hashed, with 5 addenda), schema, validation, similarity and assembly scripts; no items: no v0.3 items were ever written (the OF-3 front was dropped) |
| `bench/v0.4/` | the 75-item "ruler" (public since v1.1, 2026-10-27): items, candidate, rejects, both reference halves, drafts, critiques, fact-checks, disagreements, changelog; the item files match the v1.0 commitments byte for byte |
| `bench/heldout/` | the retired held-out sets (public development data since v1.1): bench v0.2, V-para, health-fresh1-3, chat-v3, meta-fresh1, es-fresh1-2, crisis1, hm-*, h1/h2, o2 sets; one `CARD.md` per set, `HASHES.md` (original vs released hashes). **Content note:** safety probes (medical emergencies, crisis and self-harm); AI-reviewed, not clinically reviewed; if you are in crisis, contact local emergency services |
| `bench/selftest/` | 14 pack self-test sets (13 x 20 + 30 items) with agent-written gold from public pack passages; dev only |
| `bench/slices/` | 6 dev slices: `longsession-v1` (multi-turn drift), `chat-fu-v1` (intent changes), `chainwhen-v1`, `packread-v1`, `mathroute-v1`, `citation-pt` |
| `harness/` | `judge.mjs` (pairwise judge), `judge-codex.mjs` (cross-family judge), `judge-v2.mjs` (pointwise checklist judge for the ruler), `validate.mjs`, `anchors.mjs`, gate / diff / stability / ladder / report / length-control scripts and their tests |
| `scorers/`, `metrics/` | scoring, bootstrap statistics, retrieval and timing scorers, safety rules and checkers, vendored judge libraries (`scorers/vendor/SOURCE.md` pins every vendored file) |
| `packages/protocol/` | the `EvalRequest` / `EvalTrace` contract (zod schema) |
| `adapters/desktop-node/` | the engine's `createAnswerer` run in Node on a second machine, with shims for the phone-only modules; run profiles (`adapters/desktop-node/configs/`), 19 arm patches (`arms/*.patch`, each with a `.sha256`), arm READMEs and criteria |
| `devices/` | device kit and request builder for the Android and iOS runs, agreement metric |
| `reports/` | night, device and anchor reports (what was run, what passed, what failed) |
| `docs/`, `prompts/`, `tools/`, `leaderboard/` | ADR-001, contributor writer prompts, reference prompt, pre-commit hook against held-out leaks, leaderboard rows (none submitted yet) |
| `README.md`, `DATA-CARD.md`, `BOM.md`, `NOTICE`, `CHANGELOG.md`, `CITATION.cff`, `TRACE-FORMAT.md`, `CONTRIBUTING.md` | this layer |

How to read the record: start with `TRACE-FORMAT.md` (what is measured and how), then `bench/v0.1/DATASET_CARD.md`, then the arm READMEs in `adapters/desktop-node/arms/` (one page per experiment: change, frozen criterion, result) and `reports/`. Paths like `rnd/...` in provenance fields resolve against the sibling repository `boar-research` (same layout); paths that were withheld are listed in its `docs/EXCLUDED.md`. `runs/...` is the bulk run folder, not published (see "What is not here").

## The lanes (agent names you will meet)

The research was run by a coordinator session and a small team of AI agent sessions ("lanes"), hosted in a canvas tool called Maestri. Lane names appear in comments, origin fields and report headers: **Sonar** (retrieval, packs, health), **Anvil** (models, latency, quantisation), **Compass** (evaluation, safety rules), **Forge** (native app, bench app, deep tier), **Kiln** (experiment runner), **Lantern** (dataset owner of v0.1), **Veil** (held-out sets and legal review), **Plumb** (device runs), **Summit** (reviewer). Decisions were taken by r4to; every pass/fail criterion was frozen (sha256) before the run that decided something.

## Reproduce the key results

The headline measurement is: run an app on the 60 public questions, judge every answer against the frozen reference in both A/B orders (Opus, `judge.v1`, 57 judged items = 114 calls), then report the floor-adjusted quality ratio with bootstrap confidence intervals, the win/tie/loss rate, and the above-decline ratio (always-decline ratio D = 0.306). Raw ratio alone flatters weak systems; read floor-adjusted and win rate first.

**Step 0: verify the data** (no model, no network): the commands in "Quick start".

**Step 1: score your own traces** (any app, any device). Write one `EvalTrace` per question (`TRACE-FORMAT.md`; the judge needs only `itemId`, `answer.text`, `error: null`), then:

```sh
node harness/validate.mjs my.traces.jsonl                                   # optional strict schema check
node harness/judge.mjs --traces my.traces.jsonl --out my.judgments.jsonl --bench bench/v0.1 --dry-run   # expect: 57 items, 114 calls
node harness/judge.mjs --traces my.traces.jsonl --out my.judgments.jsonl --bench bench/v0.1 --strict --floor-errored
python3 metrics/floor_metrics.py --dir . --runs my --questions bench/v0.1/questions.public.jsonl --decline-ratio 0.306
python3 scorers/score.py --traces my.traces.jsonl --judgments my.judgments.jsonl --bench bench/v0.1 --json my.score.json
```

**Run the judge on your own traces.** The judge needs the `claude` CLI logged in (Claude Code); API-key variables are stripped from its environment. Each call is `claude -p` without tools and with a JSON schema; both answers are blinded first. A rate limit stops the run and rerunning resumes; `--judge-model claude-haiku-5-5 --effort low` is a cheap triage mode whose rows are tagged `judge.v1-low` and must never be mixed with Opus numbers. For a second family, `harness/judge-codex.mjs` takes the same arguments and runs OpenAI gpt-5.6-sol through the Codex CLI (`--dry-run`, then `--limit 4` for a two-item pilot). Reading from the research: the Claude judge is the stricter family by roughly 0.10 on the ratio, the ranking is unchanged, so name the judge family next to every ratio.

**Step 1b: a no-cost demo of the scoring path** (no model, no judge; needs a clone of `boar-research` next to this repository, and the trace and judgment files of that arm, which live on Hugging Face and not in git: the `hf download` line below fetches them, about 1 MB). It re-scores stored traces and judgments of a recorded arm and should reproduce the recorded ratio (the script writes it to the `--json` file):

```sh
pipx install huggingface_hub         # provides the `hf` command (pip install -U huggingface_hub also works inside a venv; plain pip fails on Homebrew and system Python, PEP 668)
hf download r4topunk/boar-traces --repo-type dataset --include "rnd/research/coordinator/arms/headpass-st/gen/v01sw-cut7-headpass-on-s42.*" --local-dir ../boar-research
A=../boar-research/rnd/research/coordinator/arms/headpass-st/gen
python3 scorers/score.py --traces $A/v01sw-cut7-headpass-on-s42.traces.jsonl --judgments $A/v01sw-cut7-headpass-on-s42.judgments.jsonl --bench bench/v0.1 --json demo.score.json
# expect: "quality_ratio": 0.5210... in demo.score.json, the raw ratio 0.521 recorded in that arm's aggregates/agg.json ("v01sw all ON")
```

**Step 2: regenerate our traces** (needs a second machine with Node and about 15 GiB free disk, plus the pins in `BOM.md`). The engine is the app maintainer's open-source app (MIT) at commit `0cfd4a77`, pinned in `bench/v0.1/corpus-manifest.json` and `adapters/desktop-node/configs/*.json`; it is not copied here. Get it from the author's public fork, which contains that commit: `git clone https://github.com/r4topunk/boar-app && git -C boar-app checkout 0cfd4a77`. The scripts reach the engine machine over `ssh`; to use one machine, enable Remote Login and set `BOAR_EVAL_HOST=localhost`.

```sh
# 1. requests (the 60 public questions, profile P2 = iPhone-13 class, 1.5B model; the 12 safety items are `bench/v0.1/safety/track.v0.3.jsonl`)
pnpm -s -C packages/protocol exec tsx src/makeRequests.ts --questions $PWD/bench/v0.1/questions.public.jsonl \
  --config ../../adapters/desktop-node/configs/p2-iphone13-0cfd4a77.json --run-id repro-0cfd4a77-a > requests.jsonl
# 2. engine tree on the second machine (BOAR_APP = your checkout of the app, read only; BOAR_EVAL_HOST = the machine)
export BOAR_APP=/path/to/boar-app BOAR_EVAL_HOST=my-second-machine
adapters/desktop-node/setup.sh 0cfd4a77
adapters/desktop-node/setup.sh 0cfd4a77 --patch adapters/desktop-node/arms/sitroute.patch --arm sitroute   # an arm
# 3. run and fetch traces (each line is EvalTrace-validated; the script fails on a bad, missing or extra item)
adapters/desktop-node/run.sh --commit 0cfd4a77 --requests requests.jsonl --out main.traces.jsonl
# 4. compare two runs for determinism, then judge and score as in Step 1
pnpm -s -C adapters/desktop-node exec tsx scripts/diff-traces.ts $PWD/a.traces.jsonl $PWD/b.traces.jsonl
```

Every arm has a README with its frozen criterion and the exact comparison it was judged on (`adapters/desktop-node/arms/<arm>.README.md`); `deep35.criterion.md` is the hash-pinned criterion of the deep-tier arm. Numbers from the desktop adapter are desktop numbers, not phone numbers; the device kit (`devices/DEVICE-KIT.md`) and the device reports (`reports/devices-2026-10-02/`) show how phone runs were done and compared.

## Held-out policy

**Since v1.1 (2026-10-27) every held-out set of this project is retired and public** (`bench/heldout/`, `bench/v0.4/`): the project was submitted and the author opened everything that is not private to him or to the app maintainer. The rules below describe how the sets were kept while the project ran, and how a new held-out set should be kept.

Held-out sets exist so that nobody (including us) can tune on them. Rules: (1) plaintext never goes into git; only hashes, ids, counts and numbers do (`tools/hooks/pre-commit` blocks the usual leaks: install with `git config core.hooksPath tools/hooks`); (2) held-out items are written outside the Claude family, since Claude is the judge and wrote the v0.1 references; (3) once someone has seen an item or a per-item number, the set is development data for them (the burn rule); (4) one claim run per build per held-out set, authorised and hashed before the run. Published in v1.0: the v0.3 plan and its hash chain, and the v0.4 commitments (`bench/v0.4/SHA256SUMS`: items `f9ad2f2f...`, candidate `23b6febf...`). Published in v1.1: the v0.4 plaintext, which hashes to those values, and every other held-out set (`bench/heldout/`, with `HASHES.md` for what changed on the way out).

## What is not here, and why

| Not published | Why |
|---|---|
| (v1.0 only) Held-out and burnt sets and the traces of runs on them | published in v1.1 (`bench/heldout/`, `bench/v0.4/`; runs and traces in `boar-research` and on Hugging Face `r4topunk/boar-traces`) |
| The bulk run folder `runs/` (1.8 GB of v0.1 traces and judge outputs) | size, and retrieved third-party passages need a filter pass; the per-arm v0.1 traces and judgments that back published numbers are in the Hugging Face dataset `r4topunk/boar-traces` under `rnd/research/coordinator/arms/*/gen` and `.../runs` (fetch with `hf download`, see `boar-research/TRACES.md`; the git repositories hold only the small files) |
| Three arm patches `adapters/desktop-node/arms/cmpsplit*.patch` | they embed several questions of a competitor team's public test set as test strings; their READMEs and `.sha256` pins stay as the record |
| The app maintainer's data, traces and telemetry, a volunteer tester's device runs, private chat relays | other people's data |
| A competitor team's published test questions (`rivalset`) and their repository's test cases | third-party content without a licence on record; only hashes of the removed test cases ship (`bench/v0.1/competitor.denylist.json`) |
| First-aid condition cards that paraphrase NHS pages (`fa-cards.patch`); NHS wording in safety rules | NHS content is not redistributed; rule ids, patterns and URLs are kept (arm README and report remain) |
| Model weights, knowledge packs, retrieval replay caches (about 1.6 GB) | large binaries: listed in `BOM.md` with source URL, sha256 and licence; replay caches regenerate with `adapters/desktop-node/tools/replay-retrieval.sh` (see the note below the table: the tool assumes the lab layout unless you set its env vars and flags) |
| Credentials, keys, the app's release keystores | never |
| Usage details of the judge runs (accounts, plans, prices) | not method (judge call counts are kept) |

**Regenerating the replay caches.** `adapters/desktop-node/tools/replay-retrieval.sh` (retrieval only, no LLM, no judge) was written for the lab's directory layout: its defaults resolve against the parent directory of this repository (`wt/detmax`, `wt/eval/eval/node_modules`, `shared-models/`, `shared-data/...`, `boar-eval/runs/...`), and none of those exist in a fresh checkout. The `--gold` default is this repository's `bench/v0.1/gold/sources.json` and needs no flag. A stranger must set: `BOAR_SHARED_MODELS` (directory holding `bge-small-en-v1.5-q8_0.gguf`, see `BOM.md`), `BOAR_REPLAY_NODE_MODULES` (a `node_modules` that contains `node-llama-cpp`; default `wt/eval/eval/node_modules`) and `BOAR_REPLAY_CACHE` (where the app dir and the indexed seed corpus are written; default `boar-eval/runs/replay-cache`), and pass `--tree` (the engine tree built by `setup.sh`, for example the `0cfd4a77` tree; default `wt/detmax`), `--packs a.sqlite,b.sqlite` (the pack files from `BOM.md`; defaults are `shared-data/crypto/boar-crypto.sqlite` and `shared-data/packs/boar-wikivoyage-en.sqlite`), plus `--questions bench/v0.1/questions.public.jsonl`. Without them the script stops with a missing-path error. Not tested outside the lab layout.

Names: the creator of the Boar app is credited by his public handle @vaipraonde (his app's data is not published, by policy); a volunteer tester and a competitor team are not named. Vitalik Buterin appears only as the author of the post that inspired the bounty: the prefix `vit-` in item ids and the origin tags `vitalik-style` / `vitalik-verbatim` mean "modelled on, or quoting, that post"; `vitalik58` is a 58-question dev set built the same way (its runs are in the v1.1 traces; the 27 rows that came from a competitor team's test set carry ids only). The ids are pinned by hashes, so they are not renamed. `UPSTREAM_REPO/boar-app` stands for the app maintainer's public repository.

## Known limits

One model family (Claude) wrote the v0.1 references and is the main judge; v0.1 is a development set with small n (57 judged items, confidence intervals of about +/-0.04 to 0.06); the self-test references are agent-written from pack passages and are not frontier references; the judge is a closed model and is not bit-reproducible; 25 v0.1 items quote or paraphrase a named author's public posts as short quotations with links; desktop numbers are not phone numbers. See `DATA-CARD.md` and the dataset cards for per-set limits.

## Contributing

Items and leaderboard rows: `CONTRIBUTING.md`. Cite: `CITATION.cff`. Changes: `CHANGELOG.md`.
