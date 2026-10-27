# Chat slice v0 through the full engine: multi-turn adapter + base routing repro (Kiln, 2026-10-02)

TL;DR: the desktop-node adapter now passes multi-turn history. Base routing on the full engine **reproduces Compass's L0 baseline exactly**:
- accuracy **44%**, false-search **32/34**, missed-search **0/23**;
- **64/64 items match `decisions.main.jsonl` item by item**;
- history reaches the model's messages on **13/13** multi-turn items.

| | |
|---|---|
| Change | protocol `EvalItem.history.turns` (optional; `es` added to `lang`); `makeRequests` reads the chat-slice `turns` format; the runner passes `turns[:-1]` as `AnswerContext.history = {summary: null, turns}` (the ChatScreen shape). Single-turn requests are unchanged (no `history` key, same `ctx`) |
| Tests | protocol 13/13 (+2: turn split, rejects), desktop-node 28/28 (+2: `answerContext`), `tsc` clean on both. Uncommitted |
| Run | `runs/kiln/chat-slice-base-s42/`: engine 0cfd4a77 main, Android 12 GB, qwen3-4b-instruct-2507-q4km, kit crypto + Wikivoyage, corpus essential (config = and-qwen-s42, the L1 base), seed 42, node backend, adapter `desktop-node@da6d51521b99`, runner dir `be-kiln`. 64/64 valid, 0 errors, 412 s; median load 18.5 |
| Slice | `rnd/research/compass/chat-slice/slice.v0.jsonl` sha256 `836be86f84de…` |
| Score | `score_l0.py --traces` → `runs/kiln/chat-slice-base-s42/score_l0.json` |

| group | n | acc | false-search | missed-search |
|---|---|---|---|---|
| ALL | 64 | 44% | 32/34 | 0/23 |
| greeting | 20 | 5% | 19/20 | — |
| meta | 8 | 0% | 8/8 | — |
| follow-up | 13 | 73% | 3/3 | 0/8 |
| mixed / research | 7 / 8 | 100% | — | 0/15 |
| ambiguous | 8 | 33% | 2/3 | — |

Checks:
- Decision parity: `searched_from_trace` on every trace equals Compass's `decisions.main.jsonl` (smallTalk + classify copy at a6633f8d) on 64/64 items. smallTalk.ts and classify.ts are identical at 0cfd4a77 and a6633f8d. The engine's other pre-retrieval branches (safety, calc, geo, current events) change no decision on this slice.
- History: `--dump-prompts` shows every earlier turn's text in the generate messages for all 13 multi-turn items. Each one carries one `other/history` event; no single-turn item does.
- Replies to follow-ups resolve their reference: Lisboa climate, Guernica → Reina Sofía, Canberra population, "he" → other García Márquez books, Machu Picchu route.

Spot notes for Anvil (L1 reading; not scored here):
- cs-041 "ok gracias" (ES) gets an English reply.
- cs-031 / cs-037 (summarise / translate the previous answer) search anyway, but the reply does what was asked.
- cs-034 "compare with the other one" assumes a comparison set without saying so.
- cs-040 (ES hypothermia follow-up) is safety-relevant: worth a read under rules v0.7 when routing changes.
