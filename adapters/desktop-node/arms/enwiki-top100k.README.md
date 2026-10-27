# Arm `main~enwiki-top100k`: kit A + vital5 + English Wikipedia top-100k full articles (QUEUE #6 subset)

TL;DR: config-only arm (kit change) of the shared engine 0cfd4a77: adds `boar-wiki-en-top100k` (format-2 pack, 98,389 full articles = the top 100k by pageviews present in FineWiki, 1,051,771 redirects, lead vectors for the top 50,081). Base = kit A + vital5 (the iPhone's real kit). Sonar card `rnd/research/sonar/cards/full-enwiki-pack-arm.md`, §"Subset arm that fits the mini's disk today".

| | |
|---|---|
| Pack | `<runner>/shared-data/packs/boar-wiki-en-top100k.sqlite` on the mini, sha256 `aff5fd1107ba97a387aa16b4597c77cb22d4c8fa34f8b983ff6f5325727b19bd`, 2,542,215,168 bytes; manifest `boar-wiki-en-top100k.sqlite.json` (build provenance recorded) |
| Builder | `scripts/build-wiki-pack.mjs` @ upstream/main 0cfd4a77 + 1-line `--drop-rest` (worktree `<workspace>/wt/enwiki-droprest`, uncommitted); 15 FineWiki EN shards @8bd13e72 streamed, `--full-top 100000 --drop-rest --pageview-days 1`, redirects + index; built on the mini outside the heavy lock at nice 19 (log `<runner>/kiln/build-enwiki-top100k.log`) |
| Deviation | **lead vectors for the top 50,000 (+81), not 100,000**: the embedding step OOMed twice at `--embed-top 100000` (JS heap 6 GB); `--embed-top 50000` per the coordinator's decision (2026-10-02). Lead vectors only feed the lead gate / named matching |

## Frozen criterion (copied verbatim from the card before any run)

- Success criterion (frozen before any run):
  - (a) key-in-context on the 39 items rises by ≥ 6 items vs `main` (exp-03 bounds the possible gain at +15);
  - (b) on the deterministic run, citation-check declines + no-source declines on bench-60 fall by ≥ 4 items, and confident-wrong (judge+Jev band) does not rise by more than 1;
  - (c) safety veto hits not up; the 5 danger items keep their route (health route unchanged);
  - (d) desktop retrievalMs p50 ≤ 2× `main`'s; report p95 (15 shards);
  - (e) peak RSS on desktop ≤ `main` + 300 MB (proxy for the phone; device numbers come only from a later coordinator-scheduled run).
  - (a) fails → stop (more knowledge doesn't reach the prompt; fix retrieval first). (a) passes but (b) fails → knowledge reaches the model but the 1.5B doesn't use it (hand to Anvil), still worth a 4B/Android reading.

Subset arm (card §"Subset arm…", verbatim):

- **Arm:** `kitA + vital5 + enwiki-top100k` vs `kitA + vital5` (the iPhone's real kit).
  - Primary: key-in-context at `pre` (`tools/key_in_context.py`), predicted ≈ +5 to +8 of 52 keyed items: 33/42 reference articles are in the top 100k, minus the ~1/3 passage-selection loss.
  - Quality: judged on 2 seeds; predicted Δratio ≈ +0.015 to +0.025 on the 1.5B, below the MDE. So the frozen criterion keeps key-in-context primary, plus gate PASS and 0 new safety hits.
  - Also run it on the Android 4B profile, the tier near the bar.

## Frozen criterion for the approved top-100k subset arm (QUEUE #6, frozen 2026-10-02 ~07:20 BRT, before any build or run)

Arm `kitA+vital5+enwiki-top100k` vs `kitA+vital5`. Same engine 0cfd4a77 + the `--drop-rest` builder change only. Desktop adapter, iPhone profile (1.5B) and Android profile (Qwen3-4B), deterministic `-t0` pairs plus 2 judged seeds each.

- **(a) Primary.** Key-in-context at `pre` (`tools/key_in_context.py`, exact mode if protocol 1.1 has landed, else article mode) on the 52 keyed bench-v0.1 items:
  - **≥ +5 items gained** on the t0 pair;
  - **≤ 1 item lost**.
  - Both profiles share retrieval, so one count serves both. Report it per profile anyway.
- **(b) Gate.** boar-eval gate PASS vs the base on each profile and seed; 0 new safety-veto hits (rules v0.4); 0 new danger memory answers.
- **(c) Latency.** Desktop retrievalMs p50 ≤ 2× base, p95 reported. Peak RSS within +300 MB of base, reported.
- **(d) Quality: reported, not a pass condition.** Judged ratio Δ with CI on both profiles. Prediction (stated now): 1.5B +0.015 to +0.025; 4B unknown, possibly larger since it never declines. A positive 4B Δ beyond its MDE (0.030) counts as a bonus finding, not a requirement.
- **(e) Coverage sanity.** Of the 42 reference articles of exp-03's items, ≥ 30 present in the built pack. exp-04 predicts 33; fewer means the pageview ranking differs from the day-file proxy.
- **Fail (a) or (b) → not adopted.** (a) pass with (d) flat → adopt as knowledge coverage (truthfulness/citations), and report it as below MDE on quality.

## Latency risk measured before the run (cycle 13, `exp/13-retrieval-latency/`; criterion above unchanged)

- **Component profile.** Desktop CPU, 4 threads, engine code @0cfd4a77, 72 bench questions, p50:
  - query embed 5 ms;
  - Wikivoyage search 29–33 ms;
  - crypto 12–14 ms;
  - vital5 FTS 20–26 ms, cosine 6 ms;
  - **total ≈ 78 ms**, which matches the harness's 80 ms. SQLite search is ~90% of retrieval; embedding is ~6%.
- **A pack of the subset's size.** `boar-wiki-sample`, 2.13 M indexed chunks (the top-100k pack is estimated at a similar or larger chunk count), adds **+85 ms p50 / +163 ms p90** on its own. That is almost all whole-index BM25 (`bm25Candidates` 62 ms p50 / 106 ms p90); stems and named-title lookups cost 2 ms. Total ≈ 164 ms, about **2.1× the base**, so **criterion (c) (≤ 2× p50) is at risk**. Read a (c) fail together with (a).
- **Phone extrapolation (rough).** The iPhone's retrieval is ~17× the desktop's (D10 device p50 1.32 s vs desktop 0.08 s; different builds, so approximate). The subset pack could add **~+1.5 s p50** to the iPhone's ~7.9 s first token. On Android flagships, likely less (UNKNOWN).
- **Cheap path doesn't help.** Named-title passages alone reach the key on 1/52 items vs 15/52 with BM25 (`reach.txt`), so the big pack's BM25 can't be dropped.
- **Mitigation options, if (a) passes and (c) bites (not tested):**
  - (1) Cascade: query the big pack only when vital5 + the small packs leave < 2 on-topic sources after the gates.
  - (2) A lower `pool` (80 candidates) for the big pack.
  - (3) Run its FTS in parallel with the other packs. `retrieveOne` already uses `Promise.all`, but whether expo-sqlite runs separate DBs truly in parallel on device is UNKNOWN.
  - (4) Android-only shipping first, where TTFT headroom is larger.

Applied here (coordinator): key-in-context at `pre` primary (bar (a): ≥ +6 items), boar-eval gate PASS (multi-base s42+s43, v0.4), 0 new safety hits; (d) retrieval p50 and (e) peak RSS reported (peak RSS not measured by the desktop adapter: `resources` is null).

## Runs (questions72, seeds 42/43)

| Profile | Arm | Base |
|---|---|---|
| iPhone (4 GB iOS, Qwen2.5-1.5B) | `ios-enwiki-s4x` | `ios-main-v5-s4x` (existing) |
| Android (12 GB, Qwen3-4B-2507) | `and-enwiki-s4x` | `and-main-v5-s4x` (new: kit A + vital5) |

## Results

**v1 FAIL**: exact key-in-context net +3 (bar +6); the gate fails on both profiles. **v2 named-cap FAIL** (a′ lost 6, a″ no Ishiguro, gate). Report: `reports/night-2026-10-01/enwiki-top100k.md`.
