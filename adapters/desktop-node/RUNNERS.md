# Which runner made which run (desktop-node)

TL;DR: until 2026-10-06 the committed `runner/adapter.ts` was NOT the runner behind the claim numbers. Those came from a mini-only variant, **be-ship** (`<runner>/kiln/<tree>/be-ship/`), = committed adapter (bb05e07b) + route gate (Anvil B4, default ON) + learned emergency detector client (`BOAR_DETECTOR`) (+ `BOAR_KV_TYPE` from 2026-10-05). server.ts and trace.ts were identical to the repo's. The committed adapter now contains all of it behind flags (below); one gate implementation (`runner/gate.ts`).

## Reproduce be-ship from the repo
Deploy the committed runner in its own dir (leaves other runner dirs alone) and run with the ship profile:
```
BOAR_EVAL_RUNNER_DIR=be-repo adapters/desktop-node/setup.sh <sha> [--patch p --arm a]
BOAR_EVAL_RUNNER_DIR=be-repo BOAR_RUNNER_PROFILE=ship BOAR_DETECTOR=mmbert BOAR_DETECTOR_URL=http://127.0.0.1:8094 BOAR_DETECTOR_HEAD=<head.json> \
  adapters/desktop-node/run.sh --commit <sha> --arm <a> --requests r.jsonl --out t.jsonl --places ...
```
| flag | effect | default (old committed runs) |
|---|---|---|
| `BOAR_RUNNER_PROFILE=ship` | route gate ON by default (be-ship behaviour) | unset: gate off |
| `BOAR_ROUTE_GATE=1` / `0` | force gate on / off (beats the profile); same-tree gate-less control = `0` | unset |
| `BOAR_DETECTOR=mmbert\|e5`, `BOAR_DETECTOR_URL`, `BOAR_DETECTOR_HEAD`, `BOAR_DETECTOR_THR` | learned emergency detector (llama-server :8094) | unset: lexical predicate |
| `BOAR_KV_TYPE=q8_0\|...` | `--cache-type-k/-v` for `--backend server` | unset: llama-server default (f16) |
| `--backend node\|server` | the gate exists on the **node** backend and on the `--installed` facade only; `--backend server` runs are gate-less in both be-ship and the repo | node |
`run.sh` forwards BOAR_ROUTE_GATE, BOAR_RUNNER_PROFILE, BOAR_DETECTOR*, BOAR_KV_TYPE.

## Runner variants (mini)
| id (adapter.ts sha256 first 8) | what | trees |
|---|---|---|
| ded927c2 `be/` | old committed (no server backend, no gate) | be-0cfd4a77 |
| a5a88603 `be/` | older still | cmpsplit-v21 |
| 0b59cde0 `be-srv/` | server backend, before multi-turn | be-0cfd4a77 |
| bb05e07b | repo HEAD before 2026-10-06 (no gate, no detector) | (this repo) |
| 949eee03 `be-ship/` | bb05e07b + runner-b4gate + health11-runner (detector); gate ON unless BOAR_ROUTE_GATE=0 | cut2, cut2-k3, cut3, cut3-vgar, cut4 (L1 runs), cv*, g4eng, tf2, cryptosel, shiph12/13, ccc7688b |
| f5c50806 `be-ship/` | 949eee03 + BOAR_KV_TYPE | instsubj4 (cut 4 final), speedpack, cut5speed, cut5lite |
| repo d6e1e55+ | all of the above behind flags, one gate (`gate.ts`) | any, as be-repo |
Trace field `runtime.versions.adapter` = `desktop-node@` + first 12 hex of sha256(adapter.ts + trace.ts + server.ts); 87943b2648a9 = be-ship 949eee03, d827a137ae0d = be-ship f5c50806, e86afc393de8 = the b4gate runner of kiln/b5gate and b6gate.

## Runs by runner (from each run's traces; scan of boar-eval/runs/**/*.traces.jsonl)
Gate column = trace files containing `other/route-gate` events (a gate call per gated question). "ls" = llama-server backend (no gate).

| run dir (boar-eval/runs/...) | trace files | adapter ids | backend | files with route-gate events | dates |
|---|---|---|---|---|---|
| anchors-2026-10-02 | 4 | none | node | 0 | 2026-10-02..2026-10-02 |
| and-qwen-s44 | 1 | da2e3890fe78 | node | 0 | 2026-10-02..2026-10-02 |
| devices | 4 | none | node | 0 | 2026-10-02..2026-10-02 |
| g75desk | 2 | 3fa490ec931b | node | 0 | 2026-10-02..2026-10-02 |
| ios8 | 2 | 3fa490ec931b | node | 0 | 2026-10-02..2026-10-02 |
| kiln/b5gate | 4 | e86afc393de8 | node | 2 | 2026-10-03..2026-10-03 |
| kiln/b6gate | 4 | e86afc393de8 | node | 2 | 2026-10-03..2026-10-03 |
| kiln/bigpack-l1 | 12 | ee8bd2850ee1 | node | 0 | 2026-10-03..2026-10-03 |
| kiln/cryptosel-l1 | 2 | 87943b2648a9 | node | 2 | 2026-10-05..2026-10-05 |
| kiln/cut3-confirm | 4 | 87943b2648a9 | node | 4 | 2026-10-04..2026-10-04 |
| kiln/cut3-sameday | 2 | 87943b2648a9 | node | 2 | 2026-10-05..2026-10-05 |
| kiln/cut3-vgar-l1 | 4 | 87943b2648a9 | node | 4 | 2026-10-04..2026-10-04 |
| kiln/cut4-l1 | 2 | 87943b2648a9 | node | 2 | 2026-10-05..2026-10-05 |
| kiln/cut5lite-l1 | 4 | d827a137ae0d | node | 4 | 2026-10-06..2026-10-06 |
| kiln/cut5speed-l1 | 4 | d827a137ae0d | node | 4 | 2026-10-06..2026-10-06 |
| kiln/cvh-l1 | 2 | 87943b2648a9 | node | 2 | 2026-10-04..2026-10-04 |
| kiln/cvo-gate4-chunks | 8 | 87943b2648a9 | node | 8 | 2026-10-05..2026-10-05 |
| kiln/cvo-l1 | 8 | 87943b2648a9 | node | 8 | 2026-10-05..2026-10-05 |
| kiln/cvs-l1 | 2 | 87943b2648a9 | node | 2 | 2026-10-04..2026-10-04 |
| kiln/forge-ship | 1 | 87943b2648a9 | node | 0 | 2026-10-03..2026-10-03 |
| kiln/forge | 3 | 832e197d7e7d | node | 0 | 2026-10-03..2026-10-03 |
| kiln/g4eng-l1 | 4 | 87943b2648a9 | node | 2 | 2026-10-05..2026-10-05 |
| kiln/gatefid | 1 | d827a137ae0d | node | 0 | 2026-10-06..2026-10-06 |
| kiln/health5 | 8 | 832e197d7e7d | node | 0 | 2026-10-03..2026-10-03 |
| kiln/k3-on-cut2 | 4 | 87943b2648a9 | node | 4 | 2026-10-04..2026-10-04 |
| kiln/kvq8-l1 | 4 | d827a137ae0d | ls | 0 | 2026-10-05..2026-10-05 |
| kiln/overnight | 4 | 87943b2648a9 | node | 4 | 2026-10-04..2026-10-04 |
| kiln/pg-probes | 2 | 87943b2648a9 | node | 2 | 2026-10-03..2026-10-03 |
| kiln/rv2-l1 | 9 | ee8bd2850ee1 | node | 0 | 2026-10-03..2026-10-03 |
| kiln/speedpack-l1 | 8 | d827a137ae0d | ls | 0 | 2026-10-06..2026-10-06 |
| kiln/tf2-on-cut2 | 4 | 87943b2648a9 | node | 4 | 2026-10-04..2026-10-04 |
| kiln/vexact-cut2 | 4 | 87943b2648a9 | node | 2 | 2026-10-03..2026-10-03 |
| kiln/vexact | 16 | 87943b2648a9, none | node | 2 | 2026-10-02..2026-10-03 |
| night-2026-10-01/a1 | 22 | 42369306b7b3 | node | 0 | 2026-10-02..2026-10-02 |
| night-2026-10-01 | 50 | 1a51c0a6334c, 42369306b7b3, 6125cd8949cd, c28055849ba2, c9be49661ca8 | node | 0 | 2026-10-02..2026-10-02 |
| night-2026-10-01/d1 | 10 | 42369306b7b3 | node | 0 | 2026-10-02..2026-10-02 |
| night-2026-10-01/deep35 | 2 | da2e3890fe78 | ls | 0 | 2026-10-02..2026-10-02 |
| night-2026-10-01/fa-cards | 10 | 42369306b7b3 | node | 0 | 2026-10-02..2026-10-02 |
| night-2026-10-01/g1plus | 3 | 20457bca8d88 | node | 0 | 2026-10-02..2026-10-02 |
| night-2026-10-01/maple | 3 | a8165d2d49f3 | ls | 0 | 2026-10-02..2026-10-02 |
| night-2026-10-01/sitroute | 18 | 42369306b7b3 | node | 0 | 2026-10-02..2026-10-02 |
| night-2026-10-01/srv | 4 | 20457bca8d88, 8a519f6ed5f0 | ls/node | 0 | 2026-10-02..2026-10-02 |
| p1 | 4 | da2e3890fe78 | node | 0 | 2026-10-02..2026-10-02 |
| p2g | 2 | da2e3890fe78 | node | 0 | 2026-10-02..2026-10-02 |
| p5 | 5 | 3fa490ec931b | node | 0 | 2026-10-02..2026-10-02 |
| p7 | 2 | 3fa490ec931b | node | 0 | 2026-10-02..2026-10-02 |
| p7b | 2 | 3fa490ec931b | node | 0 | 2026-10-02..2026-10-02 |
| p8 | 2 | eb49c508be22 | node | 0 | 2026-10-03..2026-10-03 |

- **CLAIM-RESULTS-cut3** (rnd/research/coordinator/CLAIM-RESULTS-cut3.md, claim runs 2026-10-05; traces live under blind/, not read here): its own header cites "be-ship adapter.ts sha 949eee0355032eb1 (bb05e07b + runner-b4gate + health11-runner); detector v3b ON". So the cut 3 claim runs (v0.2 L3, V-para, P5 ...) used the **node backend, gate ON, detector ON** be-ship runner. They are NOT gate-less (A15-LATENCY-BUDGET's "no gate on desktop" was true only for the committed runner).
- Gate-less runs: everything before 2026-10-03 (adapter ids other than 87943b26.../e86afc39.../d827a137...), and every `--backend server` run (kvq8-l1, speedpack-l1, night srv/maple/deep35), plus kiln/gatefid (BOAR_ROUTE_GATE=0 control).
- GATEFID (arms/gatefid): gate ON vs OFF on cut 4/cut 5, v0.1 EN s44: 0/60 text changes.

## Verification (2026-10-06)
Cut 5 tree (be-0cfd4a77-cut5lite, patch ae0a3dce...), node backend, detector on, heavy lock, 9 rows (France warm-up + first 8 v0.1 EN s44 items): mini-only `be-ship` (f5c50806) vs the committed adapter deployed as `be-repo` with `BOAR_RUNNER_PROFILE=ship`: answer text, tier and reason codes identical **9/9**, 0 errors, 4 gate events in each (the others skipped by the cut 5 rule). Driver: `rnd/research/coordinator/arms/cut5lite/tools/runner-verify.sh`. Detector stopped by port afterwards.
