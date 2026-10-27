# desktop-node adapter

TL;DR: BOAR's real `createAnswerer` (`src/routing/answer.ts`) at any engine commit, in Node on a separate machine (the mini), optionally behind a job lock. `EvalRequest` jsonl in, one `EvalTrace` per request out, each line `EvalTrace.parse`d. Derived from `rnd/kiln/exp-06-desktop-answerer` (same wiring, sampler and shims) and reproduces its baseline exactly. Zero edits to engine source.

```bash
# 1. requests (pnpm -C runs in packages/protocol: pass absolute paths or paths relative to it)
pnpm -s -C packages/protocol exec tsx src/makeRequests.ts --questions /abs/questions.jsonl \
  --config ../../adapters/desktop-node/configs/p2-iphone13-0cfd4a77-t0.json --run-id gate-0cfd4a77-t0-a > runs/desktop-node/gate-0cfd4a77-t0-a/requests.jsonl
# 2. engine tree on the mini: <runner>/kiln/be-<sha8>[-<arm>] (git archive from the read-only clone)
adapters/desktop-node/setup.sh 0cfd4a77
adapters/desktop-node/setup.sh 0cfd4a77 --patch adapters/desktop-node/arms/main+46.patch --arm main+46
# 3. run (optional job-lock wrapper via BOAR_EVAL_WRAP; BOAR_EVAL_HOST and BOAR_EVAL_RSH select the machine), fetch, validate
adapters/desktop-node/run.sh --commit 0cfd4a77 --requests runs/desktop-node/<runId>/requests.jsonl --out runs/desktop-node/<runId>/traces.jsonl [--ids a,b] [--arm main+46]
# 4. checks
pnpm -s -C adapters/desktop-node exec tsx scripts/diff-traces.ts /abs/a/traces.jsonl /abs/b/traces.jsonl   # determinism
pnpm -s -C adapters/desktop-node exec tsx scripts/parity-exp06.ts /abs/exp06-rows.jsonl /abs/traces.jsonl  # exp-06 parity
```

## Files

| Path | What |
|---|---|
| `setup.sh` | engine tree on the mini: `src/ assets/ [locales/] modules/` at the commit, `COMMIT`, `ARM`, and for a patched arm `PATCH_SHA256` + `ENGINE.patch`. Runner in `<tree>/be/`, protocol + zod vendored in `be/vendor/`. Refuses to run under 15 GiB free |
| `run.sh` | uploads requests to `<tree>/be/runs/<runId>/`, runs `be/adapter.ts` (through the `BOAR_EVAL_WRAP` command if set), fetches `traces.jsonl` + `.log`, runs `scripts/validate.ts` (fails on an invalid line, a missing or an extra item) |
| `runner/adapter.ts` | the runner (mini side). Checks the tree's COMMIT/ARM against the requests, the model/embedding sha256 and every kit pack's sha256 (`<id>.sqlite` in `BOAR_EVAL_PACK_DIRS`, default `<runner>/shared-data/{packs,crypto}`) |
| `runner/trace.ts` | pure event/retrieval helpers (unit-tested) |
| `runner/server.ts` | `--backend server` pure helpers: request bodies, SSE parsing, reasoning/content split, RSS sampler (unit-tested) |
| `runner/app-shims/` | exp-06 shims: expo-sqlite → `node:sqlite`, expo-file-system → fs, llama.rn embeddings → node-llama-cpp, ram-monitor → simulated RAM (`BOAR_EVAL_RAM_BYTES`), react-native → simulated platform |
| `configs/` | the P2 iPhone 13 profile on 14de107 / 0cfd4a77 / temperature 0 / main+46 |
| `arms/main+46.patch` | `git diff dc3866f5^ 0ccc4911` (#46 hypothermia), sha256 `88df66f3…` |

## Multi-turn items

`item.history.turns` (protocol, optional; engine `ConversationTurn {role, text}`) = the earlier turns, oldest first; `item.question` = the last user turn. The runner passes them as the engine's `AnswerContext.history` = `{ summary: null, turns }` (what ChatScreen sends before a chat is long enough to summarise; `answerContext` in `runner/trace.ts`). Single-turn items: no `history` key, `ctx` unchanged, so traces are as before. `makeRequests` reads the chat-slice format (`turns: [...]` instead of `question`); `item.lang` also takes `es`. Multi-turn traces carry one `{type: "other", kind: "history", origin: "adapter", turns: n}` event at tMs 0. Validation (chat slice v0, 64 items): `reports/kiln-2026-10-02/chat-slice-baseline.md`.

## How trace fields are filled

- `retrieval.raw`: every chunk the engine's `retrieve` dependency returned (wrapped in the runner, before onTopic / compressContext / the source gates), passage level, rank order. `kept`: the AnswerResult's final `sources`. `dropped`: raw entries whose title + section is not in kept.
- `answer.shown`: titles of the last `sources` event (what the chat lists, kept on a decline; exp-06's `shownSources`). `cited`: the done event's `[n]` resolved against kept. `declined` / `weakSources`: from `weak_sources` warning events.
- `events`: the engine's emit() events with `tMs` since `answer()` started. `answerId` and `at` are dropped (wall-clock based). Types outside the protocol enum (`stage`, `location`, `places`, `deep_available`) become `type: "other", kind: <engine type>`. Source lists keep title/section/source/similarity/relevance, never passage text. The adapter adds `retrieve` events (query, k, n, ms, sources; `origin: "adapter"`) and one `other/generation` event per model call (prompt/output tokens, prefill/decode ms, temperature).
- **Token cap:** above 64 token events (`--token-events-max N`, 0 = off), the first 32 and last 32 are kept and one `{type: "other", kind: "tokens-elided", count, chars}` replaces the run. The full text is always in `answer.text`.
- `timing`: `ttftMs`/`retrievalMs` from the engine's receipt (an instant snippet counts as first text), `totalMs` measured around `answer()`, `prefillMs`/`promptTokens`/`decodeTokPerSec` from the last generation, `outputTokens` summed over generations. Desktop numbers, never phone numbers.
- `runtime.sampler`: the last generation's effective temperature (request override, else the engine's, default 0.7) and the seed. `versions`: node-llama-cpp, node, engine (full sha), adapter (sha256 of runner code), protocol, model/embedding sha256, corpus, `engine.patch.sha256` on an arm. `resources: null`.
- `engine.dirty` = true when the tree carries an arm patch.

## `--backend server` (llama-server instead of node-llama-cpp)

Generation through a pinned `llama-server` over HTTP/SSE, behind the same `AnswerEngine` (`makeServerEngine` in `runner/adapter.ts`, pure helpers in `runner/server.ts`). Use it for architectures node-llama-cpp's bundled llama.cpp lacks (Maple), or to get hidden-reasoning time and peak RSS. The default (`--backend node`) is unchanged. Spec: `rnd/research/anvil/specs/adapter-llama-server-backend.md`; validation: `reports/night-2026-10-01/server-backend.md`.

```bash
# binary (once; ~210 MB source + 54 s build in the heavy queue): rnd/kiln/exp-01-inram-moe-reader/harness/build-b11010.sh
# runner in a side dir so be/ (and the adapter sha its queued runs pin) stays as is
BOAR_EVAL_RUNNER_DIR=be-srv adapters/desktop-node/setup.sh 0cfd4a77
BOAR_EVAL_RUNNER_DIR=be-srv HEAVY_CLASS=normal adapters/desktop-node/run.sh --commit 0cfd4a77 --requests r.jsonl --out t.jsonl \
  --backend server --server-bin <runner>/spikes/llama-b11010/build-cpu/bin/llama-server
```

- Server, once per run: `-m <gguf> -t N -tb N -c 4096 -ngl 0 -np 1 --jinja --no-webui --cache-ram 0 --reasoning-format deepseek` on a free localhost port. `modelLoadMs` = until `GET /health` is 200. The template comes from `GET /props`. The server log is `<out>.server.log`. The server is killed on exit, error or signal.
- Per generate: `POST /v1/chat/completions` (messages) or `POST /completion` (prompt, same stop fallback), `stream: true`, `cache_prompt: false`. `max_tokens` and the sampler are the node path's (temp override → engine → 0.7, top_k 40, top_p 0.95, min_p 0.05, seed). `chat_template_kwargs.enable_thinking=false` only when the engine says `enableThinking: false`.
- SSE: `delta.reasoning_content` is hidden, counted (1 chunk ≈ 1 token) and never sent to `onToken`. `delta.content` is what the app sees. The final `timings` fill prefill/decode.
- **Thinking budget:** b11010 takes a **per-request** `thinking_budget_tokens` (server-common.cpp, the same reasoning-budget sampler as llama.rn). It is sent with the app's budget message whenever the engine sets `thinkingBudget`, so the end tag is forced at the budget as on the phone, but only for templates that declare thinking tags. Fallback: an item whose hidden tokens still exceed the budget gets `route.thinkingBudgetExceeded: true`, meaning it is not app-faithful.
- Extra trace fields (optional in the protocol, server backend only): `runtime.backend = "llama-server"`, `versions["llama-server"]`, `timing.firstVisibleMs` (first non-blank visible text since `answer()`), `timing.reasoningMs` (hidden thinking before it, 0 if none), `timing.reasoningTokens`, `route.thinkingBudgetExceeded`, `resources.peakRssMb` (the server's RSS, `ps` every 250 ms during the item's generations; desktop number). The run's idle and peak RSS are in the last log line. Generation events also carry `reasoningTokens`, `firstTextMs` and `firstReasoningMs`.
- Not comparable across backends at temperature > 0 (sampler chains differ). Hold the backend fixed within a comparison.

Node backend thinking control: on node-llama-cpp 3.21.1, `enable_thinking=false` through jinja render params does not stop a thinking model. So the chat path also passes `budgets: { thoughtTokens }`: 0 when the engine turns thinking off, the item's `thinkingBudget` when it sets one (`server.ts` `nodeBudgets`). Thought segments (`onResponseChunk`) are counted. When any appear, the trace gets the same hidden-reasoning fields as the server backend, with `thinkingBudgetExceeded` = thought tokens > the enforced limit. With none, the trace is unchanged.

## `--deep-model <id>` (deep tier on the server backend)

The backend holds the **deep** model's GGUF (e.g. `qwen3.6-35b-a3b-ud-q2kxl`). The engine sees two installed LLMs: the config's model as the active fast one (role `fast`, never loaded) and the deep one (role `reasoning`). With `settings.alwaysComplete: true` and `settings.deepModelId: <id>` (required to match), `planAnswer` takes its deep branch: k 6 / 400 context tokens / 200 answer tokens / thinking off. Models missing from the tree's catalog get an adapter entry (`versions["deep.catalog.entry"] = "adapter"`).

A **model guard** tracks what the engine believes is loaded (`load(filename, meta)`; `getModelInfo` reports it). It refuses any generate unless that is the backend's file, and the item then fails with `error.code = "adapter:model-guard"`, so a fast-model or verifier call can never run silently on the deep model. Arm: `arms/deep35.criterion.md` (frozen, sha256 in `.sha256`).

## Multi-pass (`settings.alwaysComplete: true`, no deep model) — MP4B

`planAnswer` then takes the engine's multi-pass Deep Research (decompose → research × n → synthesize). The runner passes the tree's own `runDeepResearch` (`src/services/orchestrator.ts`, imported, not copied) as `runMultipass`. The orchestrator generates through the tree's `llamaEngine` singleton: the runner sets `llamaEngine.generate` / `hasEmbeddedChatTemplate` as instance properties to its own engine (model guard, sampler, one `other/generation` event per stage; `onTimeout` is called when a stage's generation timed out). Its direct `retrieve` import is redirected by the resolve hook to `app-shims/orchestrator-retrieve.mjs` (every export of the tree's `src/rag/retrieve.ts` unchanged, `retrieve` wrapped), so each sub-question search is a `retrieve` event with `via: "multipass"` and its chunks join `retrieval.raw`. Engine source untouched. Any other config keeps the old stub (throws).

Trace fields (optional in the protocol): `route.mode` = `"multipass"` | `"single"` on always-complete configs only (absent otherwise, so other traces are unchanged); `timing.retrievalMs2` = ms of every retrieve outside the receipt's `retrievalMs` (multi-pass sub-question searches; DEEPITER follow-up searches = every `deps.retrieve` after the first), absent when there is none; nulled in parallel mode. Fidelity: the singleton's other methods (stop, KV prefix) are not wired; `stop()` during multi-pass reaches only the runner engine through answer.ts.

## Limits (same as exp-06 §4)

node-llama-cpp sampler/chat template instead of llama.rn; no KV-prefix reuse; RAM simulated only for the engine's decisions; places only via `--places`; `item.lang` is not used (the engine detects the language from the question); the bundled "essential" corpus is always installed (`--corpus`).

## be-ship profile (the runner behind the CUT4..CUT5 / cut 3 claim runs)
The runs from 2026-10-03 on used a mini-only variant (route gate, learned emergency detector, KV cache type). It is merged here behind flags; defaults are unchanged. `BOAR_RUNNER_PROFILE=ship` (gate on by default; `BOAR_ROUTE_GATE=0|1` overrides), `BOAR_DETECTOR=mmbert|e5` + `BOAR_DETECTOR_URL` + `BOAR_DETECTOR_HEAD` (+ `BOAR_DETECTOR_THR`), `BOAR_KV_TYPE` (server backend). The gate is node backend only. Which run used which runner: `RUNNERS.md`. Gate code: `runner/gate.ts` (tests `gate.test.ts`).
