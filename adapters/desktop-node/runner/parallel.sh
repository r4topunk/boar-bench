#!/usr/bin/env bash
# parallel.sh: L1 parallel mode (mini side). ONE llama-server with -np N (continuous batching, one copy of the model,
# 4096 context per slot) and N adapter shards (--shard i/N --server-url) running at once, then the shard traces merged
# back into request order. Latency fields are null in the traces when N > 1 (adapter: invalidateTiming).
#   cd <tree> && bash be/parallel.sh N be/node_modules/.bin/tsx be/adapter.ts --requests R --out O --backend server --server-bin B [adapter args]
# N = 1 runs the same path with -np 1 (the parity reference for N > 1). L2/L3 never use this script.
set -euo pipefail
N="$1"; shift
[[ "$N" =~ ^[1-9][0-9]*$ ]] || { echo "parallel.sh: N must be a positive integer" >&2; exit 2; }
CMD=("$1" "$2"); shift 2
ARGS=("$@")
arg() { local k="$1" d="${2:-}"; for ((j = 0; j < ${#ARGS[@]}; j++)); do [[ "${ARGS[$j]}" == "$k" ]] && { echo "${ARGS[$((j + 1))]}"; return; }; done; echo "$d"; }
OUT="$(arg --out)"; BIN="$(arg --server-bin)"; THREADS="$(arg --threads 4)"
[[ -n "$OUT" && -n "$BIN" && "$(arg --backend)" == server ]] || { echo "parallel.sh: needs --out, --backend server and --server-bin" >&2; exit 2; }
BIN="${BIN/#\~/$HOME}"
MODEL="$("${CMD[@]}" "${ARGS[@]}" --print-model)"
PORT="$(python3 -c 'import socket; s=socket.socket(); s.bind(("127.0.0.1", 0)); print(s.getsockname()[1])')"
BASE="http://127.0.0.1:$PORT"; SLOG="${OUT%.jsonl}.server.log"; T0=$(date +%s)
echo "$BIN -m $MODEL -np $N -c $((4096 * N))" > "$SLOG"
"$BIN" -m "$MODEL" -t "$THREADS" -tb "$THREADS" -c $((4096 * N)) -ngl 0 -np "$N" --jinja --no-webui --cache-ram 0 \
  --reasoning-format deepseek --host 127.0.0.1 --port "$PORT" >> "$SLOG" 2>&1 &
SPID=$!
trap 'kill $SPID 2>/dev/null || true' EXIT
for ((w = 0; w < 600; w++)); do
  curl -fs "$BASE/health" >/dev/null 2>&1 && break
  kill -0 $SPID 2>/dev/null || { echo "parallel.sh: llama-server exited during load, see $SLOG" >&2; exit 1; }
  sleep 1
done
curl -fs "$BASE/health" >/dev/null || { echo "parallel.sh: llama-server not healthy after 600 s" >&2; exit 1; }
# Shard args: the same list with --out replaced by the shard's file.
pids=()
for ((i = 0; i < N; i++)); do
  SA=(); for ((j = 0; j < ${#ARGS[@]}; j++)); do
    if [[ "${ARGS[$j]}" == --out ]]; then SA+=(--out "${OUT%.jsonl}.w$i.jsonl"); j=$((j + 1)); else SA+=("${ARGS[$j]}"); fi; done
  "${CMD[@]}" "${SA[@]}" --shard "$i/$N" --server-url "$BASE" > "${OUT%.jsonl}.w$i.log" 2>&1 &
  pids+=($!)
done
rc=0; for p in "${pids[@]}"; do wait "$p" || rc=$?; done
for ((i = 0; i < N; i++)); do echo "== shard $i/$N"; tail -2 "${OUT%.jsonl}.w$i.log"; done
[[ $rc -eq 0 ]] || { echo "parallel.sh: a shard failed (rc=$rc)" >&2; exit $rc; }
node "$(dirname "$0")/merge-shards.mjs" "$(arg --requests)" "$OUT" "$N"
echo "{\"parallel\":$N,\"wallS\":$(( $(date +%s) - T0 )),\"out\":\"$OUT\"}"
