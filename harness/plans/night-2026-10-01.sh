#!/usr/bin/env bash
# Night 2026-10-01 -> 02 (coordinator: ai research). Phase 1 = engine runs on the mini (heavy lock), phase 2 = judge
# (claude -p on this MacBook), phase 3 = reports. Usage: bash harness/plans/night-2026-10-01.sh <runs|judge|report>
# Items: bench v0.1 public 60 + safety track v0.3 12 = 72. Engine: shared main 0cfd4a77. Seeds 42 and 43 (temp 0.7) =
# two runs per configuration (stability axis); one temp-0 run of ios-main = the gate baseline.
set -uo pipefail
cd "$(dirname "$0")/../.."
N=runs/night-2026-10-01; mkdir -p "$N"
Q="$PWD/$N/questions72.jsonl"
[ -f "$Q" ] || cat bench/v0.1/questions.public.jsonl bench/v0.1/safety/track.v0.3.jsonl > "$Q"
BASE=adapters/desktop-node/configs/p2-iphone13-0cfd4a77.json
# name  arm      platform ram model                          seed temp
CONFIGS=(
  "ios-main-s42      main    ios     4  qwen2.5-1.5b-instruct-q4km   42 -"
  "ios-main-s43      main    ios     4  qwen2.5-1.5b-instruct-q4km   43 -"
  "and-qwen-s42      main    android 12 qwen3-4b-instruct-2507-q4km  42 -"
  "and-gemma-s42     main    android 12 gemma-4-e4b-it-q4_0          42 -"
  "ios-main46-s42    main+46 ios     4  qwen2.5-1.5b-instruct-q4km   42 -"
  "and-qwen-s43      main    android 12 qwen3-4b-instruct-2507-q4km  43 -"
  "and-gemma-s43     main    android 12 gemma-4-e4b-it-q4_0          43 -"
  "ios-main46-s43    main+46 ios     4  qwen2.5-1.5b-instruct-q4km   43 -"
  "ios-main-t0       main    ios     4  qwen2.5-1.5b-instruct-q4km   42 0"
)
log() { echo "[$(date '+%F %T')] $*" | tee -a "$N/plan.log"; }
runs() {
  adapters/desktop-node/setup.sh 0cfd4a77 >> "$N/plan.log" 2>&1
  adapters/desktop-node/setup.sh 0cfd4a77 --patch adapters/desktop-node/arms/main+46.patch --arm main+46 >> "$N/plan.log" 2>&1
  for c in "${CONFIGS[@]}"; do
    read -r name arm plat ram model seed temp <<< "$c"
    [ -s "$N/$name.traces.jsonl" ] && { log "skip $name (done)"; continue; }
    python3 - "$BASE" "$arm" "$plat" "$ram" "$model" "$seed" "$temp" > "$N/$name.config.json" <<'PY'
import json,sys
b,arm,plat,ram,model,seed,temp=sys.argv[1:]
c=json.load(open(b)); c.update(arm=arm, modelId=model, device={"platform":plat,"ramGb":float(ram)}, seed=int(seed))
if temp!="-": c["temperature"]=float(temp)
print(json.dumps(c))
PY
    pnpm -s -C packages/protocol exec tsx src/makeRequests.ts --questions "$Q" --config "$PWD/$N/$name.config.json" --run-id "night1001-$name" > "$N/$name.requests.jsonl" 2>>"$N/plan.log"
    [ "$(wc -l < "$N/$name.requests.jsonl")" -eq 72 ] || { log "FAILED $name: requests file has $(wc -l < "$N/$name.requests.jsonl") lines, expected 72"; continue; }
    log "run $name"
    if adapters/desktop-node/run.sh --commit 0cfd4a77 --arm "$arm" --requests "$N/$name.requests.jsonl" --out "$N/$name.traces.jsonl" >> "$N/plan.log" 2>&1; then log "done $name"; else log "FAILED $name"; fi
  done
}
judge() {
  for name in ios-main-s42 ios-main-s43 and-qwen-s42 and-gemma-s42 ios-main46-s42 and-qwen-s43 and-gemma-s43 ios-main46-s43; do
    [ -s "$N/$name.traces.jsonl" ] || { log "judge skip $name (no traces)"; continue; }
    log "judge $name"
    node harness/judge.mjs --traces "$N/$name.traces.jsonl" --out "$N/$name.judgments.jsonl" --bench bench/v0.1 --system "$name" >> "$N/judge.log" 2>&1 || { log "judge STOPPED at $name (rate limit or error; rerun resumes)"; return 1; }
    log "judged $name"
  done
}
report() {
  mkdir -p reports/night-2026-10-01
  for t in "$N"/*.traces.jsonl; do
    name=$(basename "$t" .traces.jsonl); j="$N/$name.judgments.jsonl"
    python3 harness/report.py "$t" $( [ -s "$j" ] && echo --judgments "$j" ) --bench bench/v0.1 --out "reports/night-2026-10-01/$name.md" >> "$N/plan.log" 2>&1 && log "report $name"
  done
}
"${1:?runs|judge|report}"
