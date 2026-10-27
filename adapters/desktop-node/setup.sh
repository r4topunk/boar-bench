#!/usr/bin/env bash
# desktop-node: build an engine tree on the mini at <runner>/kiln/be-<sha8>[-<arm>].
#   src/ assets/ locales/ modules/ package.json tsconfig.json  <- `git archive <sha>` from the read-only boar-app clone
#   (+ --patch applied to the archived copy, never to the clone)  COMMIT, ARM, PATCH_SHA256, ENGINE.patch
#   be/  <- this adapter's runner/ (+ vendor/: the protocol schema and zod, which the mini's shared node_modules lack)
# Node deps are symlinked, not installed (exp-06 §1):
#   <tree>/node_modules    -> <runner>/official-6c3d6c6/node_modules  (app deps: fzstd, …)
#   <tree>/be/node_modules -> <runner>/eval-runner/eval/node_modules  (node-llama-cpp 3.21.1, tsx)
# Usage (MacBook): adapters/desktop-node/setup.sh <sha> [--patch file.patch --arm label]
#   e.g. setup.sh 0cfd4a77 --patch adapters/desktop-node/arms/main+46.patch --arm main+46
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"; REPO="$(cd "$HERE/../.." && pwd)"
APP="${BOAR_APP:-<workspace>/boar-app}"
HOST="${BOAR_EVAL_HOST:?set BOAR_EVAL_HOST to the machine that runs the engine tree}"
RSH="${BOAR_EVAL_RSH:-ssh -o BatchMode=yes}"   # remote-shell command; the script needs no particular host
MIN_FREE_GIB="${BOAR_EVAL_MIN_FREE_GIB:-15}"
BE="${BOAR_EVAL_RUNNER_DIR:-be}"  # runner dir in the tree; another name (be-srv) leaves be/ and its queued runs alone
[[ "$BE" =~ ^be[A-Za-z0-9._-]*$ ]] || { echo "setup.sh: BOAR_EVAL_RUNNER_DIR must match be[A-Za-z0-9._-]*" >&2; exit 2; }

SHA="${1:?usage: setup.sh <sha> [--patch file.patch --arm label]}"; shift
PATCH=""; ARM="main"
while [[ $# -gt 0 ]]; do
  case "$1" in
    --patch) PATCH="$(cd "$(dirname "$2")" && pwd)/$(basename "$2")"; shift 2 ;;
    --arm) ARM="$2"; shift 2 ;;
    *) echo "setup.sh: unknown argument $1" >&2; exit 2 ;;
  esac
done
[[ "$ARM" =~ ^[A-Za-z0-9._+-]+$ ]] || { echo "setup.sh: arm label must match [A-Za-z0-9._+-]+" >&2; exit 2; }
if [[ -n "$PATCH" && "$ARM" == main ]]; then echo "setup.sh: a patched tree needs its own --arm label (\"main\" = unpatched)" >&2; exit 2; fi
if [[ -z "$PATCH" && "$ARM" != main ]]; then echo "setup.sh: --arm $ARM without --patch would label an unpatched tree" >&2; exit 2; fi

FULL="$(git -C "$APP" rev-parse --verify "${SHA}^{commit}")"
NAME="be-${FULL:0:8}"; [[ "$ARM" != main ]] && NAME="${NAME}-${ARM}"
DST="boar/kiln/$NAME"

free_gib="$($RSH "$HOST" "df -g ~ | awk 'NR==2{print \$4}'")"
if (( free_gib < MIN_FREE_GIB )); then echo "setup.sh: $HOST has ${free_gib} GiB free (< ${MIN_FREE_GIB})" >&2; exit 1; fi

TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
mkdir -p "$TMP/tree"
# Only the paths this commit has (locales/ moved under src/i18n by the shared engine).
PATHS=(); for p in src assets locales modules package.json tsconfig.json; do
  if [[ -n "$(git -C "$APP" ls-tree --name-only "$FULL" -- "$p")" ]]; then PATHS+=("$p"); fi; done
git -C "$APP" archive "$FULL" "${PATHS[@]}" | tar -x -C "$TMP/tree"
echo "$FULL" > "$TMP/tree/COMMIT"
echo "$ARM" > "$TMP/tree/ARM"
if [[ -n "$PATCH" ]]; then
  (cd "$TMP/tree" && git apply --whitespace=nowarn "$PATCH")
  shasum -a 256 "$PATCH" | awk '{print $1}' > "$TMP/tree/PATCH_SHA256"
  cp "$PATCH" "$TMP/tree/ENGINE.patch"
fi

# Engine files: mirror exactly (--delete), but never touch be/, node_modules or the run outputs.
$RSH "$HOST" "mkdir -p ~/$DST/$BE/vendor/node_modules"
rsync -a --delete --exclude '/be' --exclude '/be-*' --exclude /node_modules "$TMP/tree/" "$HOST:$DST/"
rsync -a --delete --exclude .cache --exclude runs --exclude vendor --exclude node_modules --exclude protocol.ts \
  --exclude '*.test.ts' "$HERE/runner/" "$HOST:$DST/$BE/"
rsync -aL "$REPO/packages/protocol/src/index.ts" "$HOST:$DST/$BE/vendor/protocol.ts"
rsync -aL --delete "$REPO/packages/protocol/node_modules/zod/" "$HOST:$DST/$BE/vendor/node_modules/zod/"
$RSH "$HOST" "cd ~/$DST && printf '%s\n' 'export * from \"./vendor/protocol\";' > $BE/protocol.ts \
  && ln -sfn <runner>/official-6c3d6c6/node_modules node_modules && ln -sfn <runner>/eval-runner/eval/node_modules $BE/node_modules \
  && mkdir -p $BE/runs && du -sh ~/$DST | cut -f1"
echo "tree ready: $HOST:~/$DST, runner $BE/ (commit $FULL, arm $ARM${PATCH:+, patch sha256 $(cat "$TMP/tree/PATCH_SHA256")})"
