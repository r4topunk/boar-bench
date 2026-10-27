#!/usr/bin/env bash
# P0b (card deep-tier-bounded-prefill-t2 §2): the same bmoe build for Linux, in a Docker container with a hard memory cap
# and no swap, one container per prompt, so cgroup v2 memory.peak is per prompt. Records memory.peak, memory.events
# (oom / oom_kill), exit code, /usr/bin/time -v max RSS and bmoe's CSV (rss_anon_mib). Speeds are meaningless here
# (Docker Desktop VM, virtiofs); only Linux's memory accounting is the point.
# Usage (mini, inside one heavy-lock job): bmoe-probe-linux.sh <model.gguf> <prompts-dir> <out-dir> <cap, e.g. 6750m>
set -uo pipefail
MODEL="$1"; PDIR="$2"; OUT="$3"; CAP="$4"; CACHE_MB="${CACHE_MB:-1500}"
SRC="$HOME/boar/spikes/bmoe-v028"; D=/usr/local/bin/docker; IMG=kiln-bmoe-build:24.04
mkdir -p "$OUT"
{ date; $D info --format 'docker {{.ServerVersion}} vm_mem {{.MemTotal}} cpus {{.NCPU}} kernel {{.KernelVersion}} cgroup {{.CgroupVersion}}'; $D stats --no-stream --format '{{.Name}} {{.MemUsage}}'; } > "$OUT/machine-state.txt"
for f in "$PDIR"/*.txt; do
  name="$(basename "$f" .txt)"
  $D run --rm --name "kiln-p0b-$name" --memory="$CAP" --memory-swap="$CAP" --oom-score-adj=1000 --cpus=4 \
    -v "$(dirname "$MODEL")":/models:ro -v "$PDIR":/p:ro -v "$SRC":/src:ro -v "$OUT":/out "$IMG" bash -c '
      /usr/bin/time -v /src/build-linux/cli/bmoe-cli -m /models/'"$(basename "$MODEL")"' -t 4 -n 200 -c 4096 --ubatch 512 --chatml --no-think \
        -p "$(cat /p/'"$name"'.txt)" --moe-stream --cache-mb '"$CACHE_MB"' --io-threads 4 --overlap --dense-weights anon \
        --csv /out/'"$name"'.csv > /out/'"$name"'.log 2>&1
      echo "exit=$?" >> /out/'"$name"'.log
      echo "memory.peak=$(cat /sys/fs/cgroup/memory.peak)" >> /out/'"$name"'.log
      echo "memory.max=$(cat /sys/fs/cgroup/memory.max)" >> /out/'"$name"'.log
      sed "s/^/memory.events: /" /sys/fs/cgroup/memory.events >> /out/'"$name"'.log'
  peak="$(grep -o 'memory.peak=[0-9]*' "$OUT/$name.log" | cut -d= -f2)"
  ex="$(grep -o 'exit=[0-9]*' "$OUT/$name.log" | cut -d= -f2)"
  oomk="$(grep 'memory.events: oom_kill' "$OUT/$name.log" | awk '{print $3}')"
  rss="$(grep 'Maximum resident set size' "$OUT/$name.log" | awk '{print $NF}')"
  anon="$(grep -v '^#' "$OUT/$name.csv" 2>/dev/null | python3 -c 'import csv,sys
r=list(csv.DictReader(sys.stdin)); v=[float(x["rss_anon_mib"]) for x in r if x.get("rss_anon_mib")]
print(f"{max(v):.0f}" if v else "NA")' 2>/dev/null || echo NA)"
  echo "$name cap=$CAP exit=${ex:-NA} oom_kill=${oomk:-NA} memory.peak_bytes=${peak:-NA} maxrss_kib=${rss:-NA} rss_anon_mib_max=${anon}" | tee -a "$OUT/summary.txt"
done
