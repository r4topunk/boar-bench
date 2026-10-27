#!/usr/bin/env bash
# Deep-tier memory probe (card deep-tier-streamed-moe §6b criterion 6): BigMoeOnEdge streaming (cache 3000 MiB, k = 8,
# CPU only like Android) on the deep arm's REAL prompts, peak footprint per prompt from /usr/bin/time -l.
# Env: BMOE_CLI (binary), CACHE_MB (default 3000). Runs on the mini as ONE job (optionally under a job-lock wrapper):
#   bash bmoe-probe.sh <model.gguf> <prompts-dir> <out-dir>
# <prompts-dir>: one text file per prompt (system + user content, as the engine sent them), made by bmoe-prompts.py.
set -uo pipefail
MODEL="$1"; PDIR="$2"; OUT="$3"
CLI="${BMOE_CLI:-$HOME/boar/spikes/bmoe/build-cpu/cli/bmoe-cli}"   # default 74ba18f; P0a: bmoe-v028 (v0.28.0), GGML_METAL=OFF
CACHE_MB="${CACHE_MB:-3000}"
mkdir -p "$OUT"
{ date; uptime; sysctl vm.swapusage; } > "$OUT/machine-state.txt"
for f in "$PDIR"/*.txt; do
  name="$(basename "$f" .txt)"
  { /usr/bin/time -l "$CLI" -m "$MODEL" -t 4 -n 200 -c 4096 --ubatch 512 --chatml --no-think -p "$(cat "$f")" \
      --moe-stream --cache-mb "$CACHE_MB" --io-threads 4 --overlap --dense-weights anon --csv "$OUT/$name.csv"; } > "$OUT/$name.log" 2>&1 \
    || echo "EXIT=$?" >> "$OUT/$name.log"
  fp="$(grep -E 'peak memory footprint' "$OUT/$name.log" | awk '{print $1}')"
  rss="$(grep -E 'maximum resident set size' "$OUT/$name.log" | awk '{print $1}')"
  anon="$(python3 - "$OUT/$name.csv" <<'PY'
import csv, sys
try:
    rows = list(csv.DictReader(open(sys.argv[1])))
    v = [float(r["rss_anon_mib"]) for r in rows if r.get("rss_anon_mib") not in (None, "")]
    print(f"{max(v):.0f}" if v else "NA")
except Exception:
    print("NA")
PY
)"
  echo "$name peak_footprint_bytes=${fp:-NA} max_rss_bytes=${rss:-NA} rss_anon_mib_max=${anon}" | tee -a "$OUT/summary.txt"
done
{ echo "--- after"; date; uptime; } >> "$OUT/machine-state.txt"
