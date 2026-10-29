# P0: is the deep tier's 10 GiB peak real outside macOS? (card anvil/cards/deep-tier-bounded-prefill-t2.md §2)

TL;DR: **P0b PASSES the card's frozen reading 1.** On Linux with a hard cgroup cap and no swap, all 10 real deep prompts complete: 0 OOM kills, `memory.peak` 6.59 GiB ≤ 8 GiB, under a cap *stricter* than 8 GiB. Anonymous memory peaks at **4.0–4.3 GiB**. The 10 GiB number is macOS footprint accounting. **T2 is not needed for the 12 GB tier; deep35 criterion 6 becomes PASS-on-Linux, and the deep tier moves to the device step** (ADR §7: peak PSS ≤ 8 GB on a real 12 GB Android).

Model: Qwen3.6-35B-A3B UD-Q2_K_XL (sha256 `96b9c0af…`). Prompts: the same 10 real deep35 prompts (`runs/night-2026-10-01/deep35/probe-prompts`, 612–679 tokens at prefill). Engine: BigMoeOnEdge **v0.28.0** (374f562; the binary reports 0.27.0), CPU only. Android knobs: `--moe-stream --overlap --dense-weights anon --cache-mb 1500 --ubatch 512 -t 4 --io-threads 4 --chatml --no-think -n 200 -c 4096`.

| | P0a: macOS (mini, `/usr/bin/time -l`) | P0b: Linux container, cap 6750 MiB, swap 0, `--oom-score-adj 1000` |
|---|---|---|
| completed | 10/10 | **10/10, exit 0** |
| OOM | — | **0** (`oom` 0, `oom_kill` 0 on all 10) |
| peak footprint (macOS) | **10.04–10.33 GiB** (unchanged from v0.22 at cache 3000) | — |
| max RSS | 4.9–8.4 GiB | 6.57 GiB (= the cap) |
| cgroup `memory.peak` | — | **6.59 GiB** (= the cap; `memory.events max` 2,460–3,730 = reclaim of file pages at the limit) |
| `rss_anon_mib` (bmoe telemetry) | 0 (macOS: telemetry reads /proc, Linux-only) | **4,048–4,390 MiB** |
| expert reads | `o_direct=1` (F_NOCACHE on macOS) | `o_direct=1` |

- **Why 6750 MiB, not 8g/9g/10g:** Docker Desktop's VM has 7.65 GiB total and 6.9 GiB available. Its size was not changed, to avoid restarting the VM. A 6750 MiB cap keeps the VM safe and is stricter than the card's 8 GiB, so passing it settles reading 1. The descriptive 9g/10g points were not needed.
- **Reading:** under the cap the kernel reclaims file-backed pages (the cgroup sits at its limit) while anonymous memory stays at ~4.3 GiB. An LMK that counts anon + swap (PSS) would see ~4–4.5 GiB plus resident file pages, not 10 GiB.
- **Caveats:**
  - **speeds here are meaningless** (virtiofs; TTFT 59–87 s in the VM);
  - Docker Desktop's kernel (6.10.14-linuxkit) is not Android's;
  - page cache under reclaim pressure could thrash expert reads on a phone. That is a speed question for the device step, not a memory-kill question.
- Files: P0a `<runner>/kiln/deep35-probe/out-p0a/` (mini); P0b `<runner>/kiln/p0b/out-6750m/` (logs, CSVs, `summary.txt`, `machine-state.txt`). Scripts: `adapters/desktop-node/scripts/bmoe-probe.sh`, `bmoe-probe-linux.sh`. Linux build: `<runner>/spikes/bmoe-v028/build-linux` (Docker image `kiln-bmoe-build:24.04`).
