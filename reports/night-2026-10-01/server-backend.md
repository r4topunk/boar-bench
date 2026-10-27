# desktop-node `--backend server` (llama-server b11010): parity validation

TL;DR: the new generation backend reproduces the node-llama-cpp path **exactly at temperature 0: 72/72 answers byte-identical**, with route, retrieval, shown and cited sources also 72/72. At temperature 0.7 seed 42 it matches the existing node run `and-qwen-s42` on **sources 72/72 and route 71/72**; 70/72 answers are even byte-identical. The new timing fields (visible TTFT, hidden reasoning) and peak RSS populate. The thinking-budget "gap" is closed at the source: b11010 takes a **per-request** budget. The flag fallback is wired but did not fire, because this model does not reason. Spec step 2's quality judging is left to the coordinator.

Spec: `rnd/research/anvil/specs/adapter-llama-server-backend.md` (Anvil). Implementer: Kiln-4 · 2026-10-02.

## Runs

All runs: engine 0cfd4a77 main · Qwen3-4B-Instruct-2507 Q4_K_M (sha256 `3605803b…`) · Android profile (android, 12 GB) · kit A (boar-crypto + boar-wikivoyage-en) · `runs/night-2026-10-01/questions72.jsonl` · the mini CPU ×4 · runner `be-srv/` (adapter `desktop-node@8a519f6ed5f0`). 72/72 valid traces each, 0 errors.

| Run | Backend | Temp / seed | Traces |
|---|---|---|---|
| node-t0 | node-llama-cpp 3.21.1 (default path, new adapter code) | 0 / 42 | `runs/night-2026-10-01/srv/node-t0.traces.jsonl` |
| srv-t0 | llama-server b11010 (`4bc272f`) | 0 / 42 | `runs/night-2026-10-01/srv/srv-t0.traces.jsonl` |
| srv-s42 | llama-server b11010 | 0.7 / 42 | `runs/night-2026-10-01/srv/srv-s42.traces.jsonl` |
| and-qwen-s42 (existing) | node-llama-cpp 3.21.1 (adapter `42369306b7b3`) | 0.7 / 42 | `runs/night-2026-10-01/and-qwen-s42.traces.jsonl` |

Host caveat: the 1-minute load average was **~19–21 on 10 cores** throughout, from the enwiki pack build at nice 19 outside the lock. Absolute latencies are loaded-host numbers. The backend comparison is fair only because both backends ran under the same load.

## 1. Parity at temperature 0 (gate: ≥ 68/72 byte-identical)

| Field | node-t0 vs srv-t0 |
|---|---|
| `answer.text` byte-identical | **72/72** ✅ |
| route tier / outcome / reasonCodes | 72/72 |
| retrieval raw / kept | 72/72 / 72/72 |
| answer shown / cited / declined | 72/72 / 72/72 / 72/72 |
| items with no LLM call (instant / card) | 13 (identical by construction) |

No differing ids. The template risk the spec flagged (node-llama-cpp's Qwen wrapper vs the GGUF jinja template via `--jinja`) did not show up for this model. 59 generated answers with identical bytes imply identical rendered prompts and greedy paths.

## 2. Same instrument at temperature 0.7 seed 42: srv-s42 vs the existing and-qwen-s42 (node)

| Field | Match |
|---|---|
| retrieval raw / kept | **72/72 / 72/72** ✅ |
| answer.shown / declined | **72/72 / 72/72** ✅ |
| route tier / outcome | 72/72 |
| route reasonCodes | 71/72 |
| answer.cited | 71/72 |
| answer.text byte-identical | 70/72 (not expected at 0.7; the spec only expected quality parity) |

The 2 items whose text differs:
- **lan-exp-007**: the text diverges at char 30 ("…governed by the Government of Greenland…" vs "…the Greenlandic self-rule government…"). The server answer cites nothing, so the engine adds `grounding:uncited-warning`. That is the only reasonCode difference, and it comes from the text, not the route.
- **saf-012**: the text diverges at char 52 (heat illness: "Remove any excess clothing…" vs "Offer water…"). The route is the same.

Why: sampling at 0.7 over two llama.cpp builds (node-llama-cpp's bundled version vs b11010). The sampler params and seed are the same and the prompts are the same (§1), so a near-tie at one token flips. The quality judge (gate mode + judge, |Δratio| < 0.036, confident-wrong/unsafe ±1) is **pending, by the coordinator**.

## 3. New trace fields (server backend only; optional in the protocol)

| Field | srv-t0 | srv-s42 |
|---|---|---|
| `timing.firstVisibleMs` populated | 59/59 generated items (null on the 13 with no LLM call) | 59/59 |
| `timing.firstVisibleMs` p50 | 5.78 s | 6.07 s |
| `timing.reasoningMs` / `reasoningTokens` | 0 / 0 on all (Qwen3-4B-Instruct-2507 does not think) | 0 / 0 |
| `route.thinkingBudgetExceeded` | 0/72 | 0/72 |
| `runtime.backend`, `versions["llama-server"]` | `llama-server`, `b11010 (4bc272f; 0.4.1-dev build 1)` | same |

- `firstVisibleMs` vs the engine's `ttftMs` (srv-t0): 56/59 items agree within 9 ms (51 within 0.15 ms; the rest are probably whitespace-first chunks, where the engine counts the first token and the adapter the first non-blank one). On 3 items (lan-cmp-002, vit-trv-004, vit-cry-011) `firstVisibleMs` is later by 4.5–7.8 s. There the engine counts an **instant snippet** (shown at ~85 ms) as first text, while `firstVisibleMs` is the first visible **model** text. Reasoning is excluded by construction (`delta.reasoning_content` never reaches `onToken`), so on a thinking model `firstVisibleMs − reasoningMs` exposes the hidden think time.
- Generation events also carry `reasoningTokens`, `firstTextMs`, `firstReasoningMs` and `thinkingBudgetExceeded`.

## 4. Peak RSS (llama-server process, `ps -o rss=` every 250 ms during each generate)

| | srv-t0 | srv-s42 |
|---|---|---|
| RSS right after load (run peak) | 4794 MiB (4.68 GiB) | 5077 MiB (4.96 GiB) |
| per-item `resources.peakRssMb` max / p50 / p90 | 4408 / 3270 / 3308 MiB | 5076 / 3262 / 3483 MiB |

- The run peak sits close to exp-01 §5's clean probe for the same model and flags (4.60 GiB peak RSS, `--cache-ram 0`).
- Per-item RSS **falls** over a run (≈4.4 → ≈3.3 GiB). RSS counts the mmap'd GGUF pages plus the anonymous repacked copy (exp-01 §5). Under the mini's memory pressure tonight the OS evicted clean file-backed pages. Treat the run peak as the criterion-6 number; per-item values on a loaded host are a lower bound. A footprint measurement (`/usr/bin/time -l` or `footprint`, which exp-01 used) is not wired: UNKNOWN for this run.

## 5. Speed sanity (spec step 3, ±10%; same host, threads and load)

| p50 over the 59 generated items | node-t0 | srv-t0 | Δ |
|---|---|---|---|
| prefill tok/s | 77.9 | 80.4 | +3.2% |
| decode tok/s | 21.2 | 21.6 | +1.9% |
| model load (`modelLoadMs`) | 1.4 s | 5.5 s (until `/health` 200) | the server number includes process start + repack |

Within ±10%. `promptTokens` reads 1 higher on the server (`prompt_n` vs node's context-minus-first-chunk count), and `outputTokens` ±1 (EOG counting). These are counting conventions, not different prompts; §1 proves the prompts are the same.

## 6. The thinking-budget gap and how the fallback behaves

- **Finding: no gap in b11010.** `tools/server/server-common.cpp` reads a per-request `thinking_budget_tokens` (alias `reasoning_budget_tokens`) and `reasoning_budget_message` on `/v1/chat/completions`, and feeds them to the same common reasoning-budget sampler llama.rn uses. When the budget runs out, the sampler forces the end tag. The server-wide `--reasoning-budget` is only the default.
- **What the backend sends:** `thinking_budget_tokens = o.thinkingBudget` plus the app's message (`"\nI have thought enough; answering now.\n"`, copied from LlamaEngine.ts, where it is not exported). It is sent whenever the engine sets a budget and thinking is not disabled. `max_tokens = nPredict + budget` (the node path's arithmetic). The node path itself never enforced the budget, so the server backend is the more app-faithful of the two.
- **Limit:** the server applies the budget only when the chat template declares thinking tags (`chat_params.thinking_end_tags` non-empty). llama.rn takes explicit tags from `thinkingTagsFor(arch)` instead.
- **Fallback (flag):** while streaming, `reasoning_content` chunks are counted (1 chunk ≈ 1 token). An item whose hidden tokens still exceed `o.thinkingBudget` gets `route.thinkingBudgetExceeded: true`, and its generation event is flagged too. Such items are not app-faithful. The abort-and-reissue cap from the spec's minimum variant was not built, because the server already enforces the budget natively.
- **Not exercised tonight:** the engine's fast tier asks every model for thinking (`depth.ts`: `thinking: true`, so `thinkingBudget` 256 and `enableThinking` undefined). The server runs therefore sent `thinking_budget_tokens: 256` on every generation. Qwen3-4B-Instruct-2507 simply never reasons (0 reasoning tokens), so the budget never bound and the flag stayed at 0/144. The first thinking-model run (Maple, #15) is where to check that `reasoningTokens ≤ budget` holds and the flag stays at 0.
- **Node backend (follow-up, Anvil's heads-up):** on node-llama-cpp 3.21.1, `enable_thinking=false` through jinja render params does not stop a thinking model (MiniCPM5-1B: empty answers after ~19 s). Only the prompt option `budgets.thoughtTokens` does. The node path now passes `budgets: { thoughtTokens: 0 }` when the engine turns thinking off, and `thoughtTokens: <budget>` when it sets a budget (the fast tier: 256). The render params are kept. Thought segments are tracked through `onResponseChunk`. When any thought tokens appear, the trace gets the same fields as the server (`timing.reasoningMs` / `reasoningTokens` / `firstVisibleMs`, and `route.thinkingBudgetExceeded`, meaning thought tokens > the enforced limit, 0 when off). With 0 thought tokens nothing is added, so non-thinking traces keep their shape. Check: Qwen3-4B temp 0, 3 items (vit-hum-001, lan-exp-007, saf-012) re-run on the node backend: answer text **and** whole trace identical to node-t0, ignoring timing and the adapter sha. Unit tests use a stubbed `LlamaChatSession.prompt` that honors `budgets`.

## Implementation notes

- Code: `adapters/desktop-node/runner/adapter.ts` (`makeServerEngine`, `--backend node|server`, `--server-bin`), `runner/server.ts` (pure: bodies, SSE, split, RSS sampler, version), `runner/server.test.ts` (15 tests), `packages/protocol` (+5 optional fields: `runtime.backend`, `route.thinkingBudgetExceeded`, `timing.{firstVisibleMs,reasoningMs,reasoningTokens}`, + 1 test). The default node path is unchanged in behavior: node-t0 ran on the new code.
- `run.sh` passes `--backend` and `--server-bin` through. `run.sh` and `setup.sh` take `BOAR_EVAL_RUNNER_DIR` (default `be`), so a runner under test lives in `<tree>/be-srv/` and `be/` keeps the adapter sha its queued runs pin. setup.sh's tree mirror now also excludes `/be-*`.
- Server: started once per run with Kiln's exp-01/02 flags plus `--cache-ram 0 --reasoning-format deepseek` on a free localhost port; log `<out>.server.log`; killed on exit, error or signal. HTTP errors fail the item loudly.
- **Binary:** `<runner>/spikes/llama-b11010` had been deleted on 2026-09-30 (exp-02 README). It was re-cloned (source only, 210 MB, nice 19) and rebuilt via `build-b11010.sh` through the heavy queue (55 s, HEAD asserted `4bc272f`, 296 MB). No model downloads. Mini disk: 12 → 15 GiB free at the end (other agents' cleanups).

UNKNOWN:
- Whether the per-request budget actually binds on Maple's template (does it declare thinking tags?). The flag will show it.
- Peak footprint (anonymous memory) for these runs; only RSS was sampled.
- Quality Δ for spec step 2 (judge pending).
