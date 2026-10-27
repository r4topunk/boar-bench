#!/usr/bin/env bash
# desktop-node: run EvalRequest jsonl through the engine tree on the mini (optional job-lock wrapper BOAR_EVAL_WRAP) and fetch one EvalTrace per
# request; every line is then EvalTrace.parse()d on the MacBook (scripts/validate.ts) and the script fails on any
# invalid line or a missing/extra item.
# Usage (MacBook): adapters/desktop-node/run.sh --commit <sha> [--arm label] --requests requests.jsonl --out traces.jsonl
#                  [--ids a,b] [--threads 4] [--backend server --server-bin <runner>/spikes/llama-b11010/build-cpu/bin/llama-server]
#                  [--parallel N]  (L1 only, needs --backend server: one llama-server -np N + N shards; latency null when N > 1)
# BOAR_EVAL_PACK_DIRS (optional, mini paths ':'-separated): where the runner looks for kit packs (default in runner).
# BOAR_EVAL_RUNNER_DIR (default be): the runner directory inside the tree (setup.sh deploys it), e.g. be-srv for a
# runner under test next to the one queued runs use.
# Outputs: <out> and <out minus .jsonl>.log. Keep them under boar-eval/runs/desktop-node/<runId>/ (gitignored).
# HEAVY_CLASS defaults to "short" (a 54-item run takes ~3 min); set HEAVY_CLASS=normal for long runs (read by the optional wrapper only).
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
APP="${BOAR_APP:-<workspace>/boar-app}"
HOST="${BOAR_EVAL_HOST:?set BOAR_EVAL_HOST to the machine that runs the engine tree}"
RSH="${BOAR_EVAL_RSH:-ssh -o BatchMode=yes}"   # remote-shell command; the script needs no particular host
BE="${BOAR_EVAL_RUNNER_DIR:-be}"
[[ "$BE" =~ ^be[A-Za-z0-9._-]*$ ]] || { echo "run.sh: BOAR_EVAL_RUNNER_DIR must match be[A-Za-z0-9._-]*" >&2; exit 2; }

SHA=""; ARM="main"; REQ=""; OUT=""; IDS=""; EXTRA=(); PAR=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --commit) SHA="$2"; shift 2 ;;
    --arm) ARM="$2"; shift 2 ;;
    --requests) REQ="$2"; shift 2 ;;
    --out) OUT="$2"; shift 2 ;;
    --ids) IDS="$2"; shift 2 ;;
    --threads|--timeout-ms|--token-events-max|--backend|--server-bin|--deep-model|--dump-prompts|--installed|--places) EXTRA+=("$1" "$2"); shift 2 ;;
    --event-source-text) EXTRA+=("$1"); shift ;;
    --parallel) PAR="$2"; shift 2 ;;
    *) echo "run.sh: unknown argument $1" >&2; exit 2 ;;
  esac
done
[[ -n "$SHA" && -n "$REQ" && -n "$OUT" ]] || { echo "usage: run.sh --commit <sha> [--arm label] --requests r.jsonl --out t.jsonl [--ids a,b]" >&2; exit 2; }
FULL="$(git -C "$APP" rev-parse --verify "${SHA}^{commit}")"
NAME="be-${FULL:0:8}"; [[ "$ARM" != main ]] && NAME="${NAME}-${ARM}"
DST="boar/kiln/$NAME"
$RSH "$HOST" "test -f ~/$DST/COMMIT && test -f ~/$DST/$BE/adapter.ts" || { echo "run.sh: no tree $HOST:~/$DST; run setup.sh $SHA first" >&2; exit 1; }

RUN_ID="$(head -1 "$REQ" | python3 -c 'import json,sys; print(json.load(sys.stdin)["runId"])')"
[[ "$RUN_ID" =~ ^[A-Za-z0-9._+-]+$ ]] || { echo "run.sh: runId must match [A-Za-z0-9._+-]+" >&2; exit 2; }
REMOTE="$BE/runs/$RUN_ID"
mkdir -p "$(dirname "$OUT")"
LOG="${OUT%.jsonl}.log"
$RSH "$HOST" "mkdir -p ~/$DST/$REMOTE"
scp -q "$REQ" "$HOST:$DST/$REMOTE/requests.jsonl"

ARGS="--requests $REMOTE/requests.jsonl --out $REMOTE/traces.jsonl ${IDS:+--ids $IDS} ${EXTRA[*]:-}"
# --parallel N (L1 only, --backend server): one llama-server -np N + N adapter shards (runner/parallel.sh); latency
# fields are null when N > 1. Without it (L2/L3) the command is exactly as before.
RUNNER="$BE/node_modules/.bin/tsx $BE/adapter.ts"
if [[ -n "$PAR" ]]; then
  [[ " ${EXTRA[*]:-} " == *" --backend server "* ]] || { echo "run.sh: --parallel needs --backend server --server-bin <llama-server>" >&2; exit 2; }
  RUNNER="bash $BE/parallel.sh $PAR $RUNNER"
fi
set +e
$RSH "$HOST" "bash -lc 'cd ~/$DST && ${BOAR_EVAL_PACK_DIRS:+BOAR_EVAL_PACK_DIRS=$BOAR_EVAL_PACK_DIRS} ${BOAR_EVAL_SQL_COUNT:+BOAR_EVAL_SQL_COUNT=$BOAR_EVAL_SQL_COUNT} ${BOAR_ROUTE_GATE:+BOAR_ROUTE_GATE=$BOAR_ROUTE_GATE} ${BOAR_RUNNER_PROFILE:+BOAR_RUNNER_PROFILE=$BOAR_RUNNER_PROFILE} ${BOAR_DETECTOR:+BOAR_DETECTOR=$BOAR_DETECTOR} ${BOAR_DETECTOR_URL:+BOAR_DETECTOR_URL=$BOAR_DETECTOR_URL} ${BOAR_DETECTOR_HEAD:+BOAR_DETECTOR_HEAD=$BOAR_DETECTOR_HEAD} ${BOAR_KV_TYPE:+BOAR_KV_TYPE=$BOAR_KV_TYPE} ${EXPO_PUBLIC_BOAR_PERF:+EXPO_PUBLIC_BOAR_PERF=$EXPO_PUBLIC_BOAR_PERF} HEAVY_CLASS=${HEAVY_CLASS:-short} ${BOAR_EVAL_WRAP:-} $RUNNER $ARGS > $REMOTE/run.log 2>&1'"
RC=$?
set -e
scp -q "$HOST:$DST/$REMOTE/run.log" "$LOG" || true
if [[ $RC -ne 0 ]]; then echo "run.sh: remote run failed (rc=$RC); tail of $LOG:" >&2; tail -20 "$LOG" >&2; exit $RC; fi
scp -q "$HOST:$DST/$REMOTE/traces.jsonl" "$OUT"
scp -q "$HOST:$DST/$REMOTE/traces.server.log" "${OUT%.jsonl}.server.log" 2>/dev/null || true
pnpm -s -C "$HERE" exec tsx scripts/validate.ts "$(cd "$(dirname "$OUT")" && pwd)/$(basename "$OUT")" \
  --requests "$(cd "$(dirname "$REQ")" && pwd)/$(basename "$REQ")" ${IDS:+--ids "$IDS"}
