#!/usr/bin/env bash
# Sends one boar-eval request file to BOAR on a USB Android phone, waits, and pulls the rows back.
# Why this exists: `npm run eval:device` on UPSTREAM_REPO/boar-app main (0cfd4a77) only sends the legacy request
# ({requestId, models, adaptive, queries}); it can't send pipeline "answer" with our 72 questions. This script uses
# the same transport as that CLI (adb run-as, base64; scripts/lib/eval-device-lib.mjs) and the same status protocol
# (src/eval/deviceEvalRequest.ts). The app must be a DEBUG build, open on the chat, with JS served by Metro in
# DEV mode (`npx expo start --localhost`): on main, src/ui-android/ChatScreen.tsx only polls when __DEV__ is true.
#
#   devices/android-run.sh REQUEST.json REP [--tag ARM] [--serial S] [--package <DEFAULT_BUNDLE_ID>] [--out DIR] [--timeout-min 240] [--pickup-min 5]
#   devices/android-run.sh REQUEST.json REP --pull-only     # re-pull rows of a run that finished (or was resumed)
#   devices/android-run.sh REQUEST.json REP --dry-run       # print the adb commands, touch nothing
#
# REP (1, 2, ...) becomes the requestId suffix (-r1, -r2); --tag ARM inserts the arm name (be-and-qwen3-4b-quick-ARM-r1).
# The app keys its result file by requestId: re-sending the SAME file + REP (+ tag) after the OS killed the app resumes
# from the last answered question, so an arm run MUST carry its --tag or it would reuse the baseline's answers.
# Output: OUT/<requestId>/{rows.jsonl,status.json,device.txt,kit.txt,battery-before.txt,battery-after.txt,request.json}
set -euo pipefail
REQ=${1:?request file}; REP=${2:?rep number}; shift 2
PKG="${BOAR_APP_PACKAGE:?set BOAR_APP_PACKAGE or pass --package}"; SERIAL=; OUT=eval-results/boar-eval; TIMEOUT_MIN=240; DRY=0; PULL_ONLY=0; TAG=; PICKUP_MIN=5
while [ $# -gt 0 ]; do
  case "$1" in
    --serial) SERIAL=$2; shift 2 ;;
    --tag) TAG=$2; shift 2 ;;
    --pickup-min) PICKUP_MIN=$2; shift 2 ;;
    --package) PKG=$2; shift 2 ;;
    --out) OUT=$2; shift 2 ;;
    --timeout-min) TIMEOUT_MIN=$2; shift 2 ;;
    --dry-run) DRY=1; shift ;;
    --pull-only) PULL_ONLY=1; shift ;;
    *) echo "unknown option $1" >&2; exit 2 ;;
  esac
done
[[ "$REP" =~ ^[0-9]+$ ]] || { echo "REP must be a number" >&2; exit 2; }
[[ "$PKG" =~ ^[A-Za-z0-9_.]+$ ]] || { echo "bad --package" >&2; exit 2; }
command -v node >/dev/null || { echo "node is required" >&2; exit 2; }

# Compact JSON with the rep's requestId (validated like the app does: 1-64 lowercase letters, digits, dashes).
BODY=$(node -e '
const fs = require("fs"); const r = JSON.parse(fs.readFileSync(process.argv[1], "utf8"));
r.requestId = String(r.requestId).replace(/-r\d+$/, "") + (process.argv[3] ? "-" + process.argv[3] : "") + "-r" + process.argv[2];
if (!/^[a-z0-9][a-z0-9-]{0,63}$/.test(r.requestId)) throw new Error("bad requestId " + r.requestId);
if (r.pipeline !== "answer" || !Array.isArray(r.questions)) throw new Error("not a pipeline \"answer\" request");
process.stdout.write(JSON.stringify(r));' "$REQ" "$REP" "$TAG")
RID=$(node -e 'process.stdout.write(JSON.parse(process.argv[1]).requestId)' "$BODY")
NQ=$(node -e 'process.stdout.write(String(JSON.parse(process.argv[1]).questions.length))' "$BODY")
B64=$(printf '%s' "$BODY" | base64 | tr -d '\n')
DIR="$OUT/$RID"

ADB=(adb); [ -n "$SERIAL" ] && ADB=(adb -s "$SERIAL")
RUNAS() { "${ADB[@]}" exec-out "run-as $PKG $1"; }
STATUS="files/eval/requests/$RID.status.json"
WRITE="sh -c 'umask 077 && mkdir -p files/eval/requests && echo $B64 | base64 -d > files/eval/requests/pending.json'"

if [ $DRY = 1 ]; then
  echo "# request $RID ($NQ questions, ${#B64} base64 bytes) -> $DIR"
  echo "${ADB[*]} devices"
  echo "${ADB[*]} shell dumpsys package $PKG | grep -c DEBUGGABLE"
  echo "${ADB[*]} shell \"run-as $PKG $WRITE\"" | cut -c1-200; echo "   ... (base64 elided)"
  echo "${ADB[*]} exec-out run-as $PKG cat $STATUS          # every 15 s until state done|failed"
  echo "${ADB[*]} exec-out run-as $PKG cat files/eval/$RID.answer.jsonl > $DIR/rows.jsonl"
  exit 0
fi

mkdir -p "$DIR"; printf '%s\n' "$BODY" > "$DIR/request.json"
"${ADB[@]}" get-state >/dev/null 2>&1 || { echo "✗ no device (adb devices; pass --serial when several)" >&2; exit 1; }
DBG=$("${ADB[@]}" shell dumpsys package "$PKG" | grep -c 'pkgFlags=\[[^]]*DEBUGGABLE' || true)
[ "${DBG:-0}" -gt 0 ] || { echo "✗ $PKG is not a debuggable build: run-as can't reach its files (install the dev client: npx expo run:android)" >&2; exit 1; }

pull() {
  RUNAS "cat $STATUS" > "$DIR/status.json" 2>/dev/null || true
  local rp; rp=$(node -e 'try{const s=JSON.parse(require("fs").readFileSync(process.argv[1],"utf8"));process.stdout.write(s.resultPath||"")}catch{}' "$DIR/status.json")
  [ -n "$rp" ] || rp="files/eval/$RID.answer.jsonl"   # answerEval.ts writes here after every question
  [[ "$rp" =~ ^files/eval/[A-Za-z0-9._-]+\.jsonl$ ]] || { echo "✗ unexpected result path $rp" >&2; exit 1; }
  RUNAS "cat $rp" > "$DIR/rows.jsonl"
  local n; n=$(grep -c '"queryId"' "$DIR/rows.jsonl" || true)
  [ "${n:-0}" -gt 0 ] || { echo "✗ no rows in $rp: $(head -c 200 "$DIR/rows.jsonl")" >&2; exit 1; }
  echo "✓ $n rows -> $DIR/rows.jsonl (status $(node -e 'try{const s=JSON.parse(require("fs").readFileSync(process.argv[1],"utf8"));process.stdout.write(s.state+" "+(s.completed??"?")+"/"+(s.total??"?")+(s.stopped?" STOPPED":""))}catch{process.stdout.write("unreadable")}' "$DIR/status.json"))"
}
battery() { "${ADB[@]}" shell dumpsys battery | grep -E 'level|temperature|AC powered|USB powered|status' > "$DIR/battery-$1.txt" || true; }

if [ $PULL_ONLY = 1 ]; then pull; battery after; exit 0; fi

{ for p in ro.product.manufacturer ro.product.model ro.soc.model ro.build.version.release; do echo "$p=$("${ADB[@]}" shell getprop $p | tr -d '\r')"; done
  "${ADB[@]}" shell cat /proc/meminfo | grep MemTotal; } > "$DIR/device.txt"
# Kit evidence: which models/packs are on the phone (retrieval only matches desktop when the kits match).
RUNAS "ls -lR files" 2>/dev/null | grep -E '\.(sqlite|gguf|bin)$|^files/' > "$DIR/kit.txt" || true
battery before
SENT=$(($(date +%s) * 1000))
"${ADB[@]}" shell "run-as $PKG $WRITE"
echo "✓ request $RID written ($NQ questions). BOAR must stay open on the chat (screen on); the app polls every 3 s."
T0=$(date +%s); LAST=
while :; do
  sleep 15
  S=$(RUNAS "cat $STATUS" 2>/dev/null || true)
  LINE=$(node -e '
let s; try { s = JSON.parse(process.argv[1]) } catch { process.stdout.write("waiting"); process.exit(0) }
if ((s.updatedAt ?? 0) < Number(process.argv[2]) - 5000) { process.stdout.write("waiting (old status)"); process.exit(0) }
process.stdout.write([s.state, `${s.completed ?? 0}/${s.total ?? "?"}`, s.current ?? "", s.error ?? ""].join(" ").trim())' "$S" "$SENT")
  EL=$(( $(date +%s) - T0 ))
  [ "$LINE" != "$LAST" ] && printf '  [%02d:%02d] %s\n' $((EL/60)) $((EL%60)) "$LINE"; LAST=$LINE
  case "$LINE" in
    done*) break ;;
    failed*) echo "✗ the app reported: $LINE" >&2; exit 1 ;;
    waiting*) [ $EL -gt $((PICKUP_MIN * 60)) ] && { echo "✗ not picked up in $PICKUP_MIN min: is BOAR open on the chat, a debug build, JS from Metro in dev mode (not --no-dev)?" >&2; exit 1; } ;;
  esac
  [ $EL -gt $((TIMEOUT_MIN * 60)) ] && { echo "✗ timed out after $TIMEOUT_MIN min; the run may still be going: re-run with --pull-only later" >&2; exit 1; }
done
pull; battery after
echo "Send back: $DIR (whole folder; rows.jsonl is the result)"
