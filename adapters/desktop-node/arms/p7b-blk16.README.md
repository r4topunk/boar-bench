# Arm `p7b-blk16` (Sonar P-7b): packs rebuilt with 16 KB zstd blocks: step 0 PASS

TL;DR: both step-0 checks pass. Size **+4.61% / +5.31%, +18.1 MB combined** (bar ≤ +6% per pack and ≤ +25 MB; card predicted +4.6% / +5.3%, +18.2 MB). Pre-answer sources byte-identical **72/72**. Steps 1–2 (moto g75 retrieval p50 ≤ 0.8×, TTFT) go into the next phone session.

Criterion: card `rnd/research/sonar/cards/p7b-pack-block-16k.md` (frozen before any build), not restated. Rebuild: `<runner>/kiln/p7b/build.sh`, the same 2026-09-26 recipes as P-7 (`p7-blk8.README.md`), only `--block-kb 16`; SQLite page size unchanged (8192). New files only; the current packs are untouched.

| Pack | current | 16 KB | Δ |
|---|---|---|---|
| boar-wikivoyage-en | 351,092,736 B `ff8595e3…` | 367,288,320 B `9db1aa378d1dd8918934dd6573497cb188214acb51a79e8f985cbe65a89f7742` | +16.2 MB, **+4.61%** |
| boar-crypto | 36,093,952 B `ae9fbd2c…` | 38,010,880 B `d08070bfef3c195024550f79bc0c5d418c6eee48b0210fafc12e0054b55adc90` | +1.9 MB, **+5.31%** |
| combined | | | **+18.1 MB** |

- Pre-check (`runs/p7b/`, iPhone `ios-main-v5` config, s42, `--event-source-text`, base with the current packs and arm with `BOAR_EVAL_PACK_DIRS=<runner>/kiln/p7b/16:…` back to back): pre-answer sources (title, section, source, similarity, passage text) **72/72 byte-identical**; `retrieval.raw` 72/72; answer text 72/72. The adapter sha-checked the 16 KB packs.
- Files for the phone session: `the mini:<runner>/kiln/p7b/16/{boar-wikivoyage-en,boar-crypto}.sqlite`.
