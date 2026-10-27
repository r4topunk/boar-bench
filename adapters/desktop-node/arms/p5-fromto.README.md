# Arm `p5-fromto` (Sonar P-5): "get from X to Y" is a travel question, so the destination guide is retrieved

TL;DR: Sonar's P-5 (card `rnd/research/sonar/cards/p5-travel-from-to.md`, criterion frozen there 2026-10-02 evening). One regex, `FROM_TO_TRIP`, is added to `isTravelQuestion` in `src/rag/wikiPack.ts`. A point-to-point trip with capitalized origin and destination now runs the engine's existing destination logic: for vit-trv-003, the Pai guide's "Get in > By bus" goes first. Engine 0cfd4a77 + `p5-fromto.patch`. Kit A, Android 4B profile, bench v0.1 only. A stacked arm `p1p5-stack` (P-1 + P-5) is replayed alongside it, as the card suggests.

| | |
|---|---|
| Patch | `p5-fromto.patch` sha256 `f9a58bb0387e94f6d09e2188e4dbdaf4d0def7eefcaed9c742e0502f5755227c` (worktree `<workspace>/wt/p5-fromto`, uncommitted). The card's regex is applied verbatim |
| Stack | `p1p5-stack.patch` sha256 `51e0fc20a1089af5d0586b6f5041b93e10b71a1569135b1b781c0fd1691c5cc8` = `p1-keepkey.patch` + `p5-fromto.patch`, applied cleanly in that order (worktree `<workspace>/wt/p1p5-stack`) |
| Tests | `wikiPack.destination.test.ts` +1: three capitalized from–to trips are travel questions; "from zero to one", "change from Republic to Empire" and "Convert from Celsius to Fahrenheit" are not. It fails on unpatched code. Full suite 106 files / 1165 tests (stack: 1167), `tsc` clean |

## Frozen criterion (card, verbatim)

Frozen criterion (arm `p5-fromto` vs `and-qwen`, Android 4B, kit A, 0cfd4a77; `-kic` traces; replay-first: the pre-answer check below decides before any judged run):
1. **Exact key-in-context at `pre`** (`tools/key_in_context.py` c9124e43): vit-trv-003 gains the key **from a Wikivoyage: Pai passage**. Checked by title in the pre-answer sources, not only by key terms.
2. **0 keys lost** on the other keyed items; **0 items emptied**.
3. **No other item's pre-answer sources change**, except items the pattern matches (expected: none on v0.1).
4. Retrieval p50 ≤ 1.2× base.
5. Then judged (2 seeds): whole-bench paired Δratio ≥ −MDE; gate PASS v0.5; 0 new safety hits. Reported: confident-wrong on vit-trv-003 (expected down).
- Fail on 1–4 → stop before judging.

Stacked replay (reported, not gating; card): expected +3 genuine keys (lan-exp-003 and vit-cry-010 from P-1, vit-trv-003 from P-5).

Base for the replay: `runs/p1/and-main-s4x-kic` (main, same tree and config, `--event-source-text`), reused.

## Results

**Step 1 replay (`runs/p5/`, vs `runs/p1/and-main-s4x-kic`, both seeds): criteria 1–3 PASS. Criterion 4: failed first reading 1.22× under load mismatch; re-measured (1.08×, load-matched); accepted by coordinator.**
1. vit-trv-003 gains the exact key at `pre` on both seeds. Pre sources = Wikivoyage: Pai, Wikivoyage: Chiang Mai, Wikivoyage: Pai. The key matches **inside both Pai passages** and not in Chiang Mai's. PASS.
2. 0 keys lost, 0 emptied. PASS.
3. Pre-answer sources change on **vit-trv-003 only** (both seeds). PASS.
4. Retrieval p50:
   - first runs: s42 1.54× (that run's median 1-min load was **26.6**, its base's 18.1), s43 0.99×, pooled **1.22×**, a FAIL by a hair;
   - **re-measured s42** at normal load (17.7): 1.20×, answers 72/72 identical to the first s42 run, pooled **1.08×**.
   - Coordinator decision (2026-10-02): accepted on the load-matched re-run, because the patch adds no retrieval work. Labelled: *failed first reading 1.22× under load mismatch; re-measured; accepted by coordinator*. Method fix since: latency criteria are measured interleaved in one load window, or by a work count (`arms/README.template.md`).
   - The stacked arm, which carries the same regex, has a per-item paired ratio of 1.07×. The regex can't plausibly cost retrieval time on the 71 unmatched items, so the 1.22× is read as load.
- **Stack `p1p5-stack` (reported):** **+3 genuine keys on both seeds** (lan-exp-003, vit-cry-010, vit-trv-003), 0 lost, 0 emptied; paired retrieval ratio 1.07×. As the card expected.
**Judged seeds (criterion 5):** the replay arm runs `and-p5-s4x-kic` vs `and-qwen-s42/s43`, judge.v1 opus, both orders.
- whole-bench paired **Δ +0.0003** (CI −0.016 … +0.018), MDE 0.030 → ≥ −MDE, **PASS**;
- gate v0.5 multi-base **PASS**; unsafe 3 / 3 = base 3 / 3; 0 new safety hits.
- vit-trv-003 now answers from the Pai guide («a minivan from Chiang Mai's Arcade terminal… departing hourly»); judge correctness per order 3,2 / 3,3 (base) → 4,3 / 4,4.

**Verdict: P-5 PASSES** (criterion 4 accepted on the load-matched re-run, as labelled above). Outputs: `runs/p5/` (`diff-andqwen-p5.md`, `gate-p5-s42s43.v05.md`).
