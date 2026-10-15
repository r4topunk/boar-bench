#!/bin/bash
# test-pre-commit.sh [hook] [scratch-dir] -- offline regression test of the blind-plaintext pre-commit hook (PIPELINE-AUDIT 2026-10-13 F3).
# Builds a throwaway git repo per case, stages FAKE items only (never real blind data), commits, and asserts BLOCKED / PASS.
# The fixture lines are assembled at runtime (kv/item below) so this file itself never holds an item-shaped line and passes the hook.
# The v0.1-exemption case copies line 1 of the public bench/v0.1/questions.public.jsonl (public dev data). Exit 0 = all pass.
set -u
D=$(cd "$(dirname "$0")" && pwd); HOOK=${1:-$D/pre-commit}; ROOT=${2:-${TMPDIR:-/tmp}/hooktest}
PUBF=${BOAR_V01_PUBLIC:-$D/../../bench/v0.1/questions.public.jsonl}; export BOAR_V01_PUBLIC=$PUBF
RND=/nonexistent; PASS=0; FAIL=0
QK=ques; QK=${QK}tion                                   # the key name, never written whole in this file
kv() { printf '"%s": "%s"' "$1" "$2"; }                 # kv key value -> "key": "value"
FQ="FAKE: what is the fake capital of Testland?"
item() { printf '{%s, %s}' "$(kv id "$1")" "$(kv "$QK" "$FQ")"; }        # item <id>: id first
item_qfirst() { printf '{%s, %s}' "$(kv "$QK" "$FQ")" "$(kv id "$1")"; } # item_qfirst <id>: key order swapped
rm -rf "$ROOT"; mkdir -p "$ROOT"
G() { git -c user.name=hooktest -c user.email=hooktest@example.invalid -c commit.gpgsign=false "$@"; }
run() { local want=$1 name=$2 path=$3 r=$ROOT/$(printf '%02d' $((PASS+FAIL+1))); shift 3
  mkdir -p "$r/hooks"; cp "$HOOK" "$r/hooks/pre-commit"; chmod +x "$r/hooks/pre-commit"
  ( cd "$r" && git init -q . && git config core.hooksPath hooks && echo seed > README && G add README hooks && G commit -qm seed --no-verify ) || { echo "setup failed"; exit 2; }
  mkdir -p "$r/$(dirname "$path")"; printf '%s\n' "$@" > "$r/$path"
  out=$(cd "$r" && G add -- "$path" && G commit -qm case 2>&1); rc=$?
  got=PASS; [ $rc != 0 ] && got=BLOCKED
  if [ $got = $want ]; then PASS=$((PASS+1)); echo "  [ok]   $want  $name ($path)${out:+  :: $(echo "$out" | head -1 | cut -c1-90)}"
  else FAIL=$((FAIL+1)); echo "  [FAIL] want $want got $got: $name ($path) :: $(echo "$out" | head -2 | tr '\n' ' ' | cut -c1-160)"; fi; }
echo "hook: $HOOK (sha256 $(shasum -a 256 "$HOOK" | cut -c1-16))"
[ -f "$RND" ] && { cmp -s "$HOOK" "$RND" && echo "  rnd copy identical: $RND" || { FAIL=$((FAIL+1)); echo "  [FAIL] rnd copy differs: $RND"; }; }
echo "Must be BLOCKED (audit F3 bypasses + originals)"
run BLOCKED "v0.3 questions path (original)"            bench/v0.3/questions.v03.jsonl "$(item v03-travel-01)"
run BLOCKED "id before question, 2 digits (original)"   data/items.jsonl "$(item v03-travel-01)"
run BLOCKED "question before id"                        data/items.jsonl "$(item_qfirst v03-travel-01)"
run BLOCKED "pretty-printed multi-line item"            data/item.json '{' "  $(kv id v03-travel-01)," "  $(kv category travel)," "  $(kv "$QK" "$FQ")" '}'
run BLOCKED "one-digit id"                              data/items.jsonl "$(item v03-travel-1)"
run BLOCKED "upper-case id"                             data/items.jsonl "$(item V03-TRAVEL-01)"
run BLOCKED "pack-matched id v03p-...-001"              data/items.jsonl "$(item v03p-qa-travel-se-001)"
run BLOCKED "V-para-style id vit-hum-001, fake text"    data/para.jsonl "{$(kv id vit-hum-001), $(kv "$QK" "FAKE paraphrase: explain the fake philosopher?")}"
run BLOCKED "hf- id"                                    data/h.jsonl "$(item hf-fake-07)"
run BLOCKED "es- id"                                    data/e.jsonl "$(item es-fake-12)"
run BLOCKED "chat- id"                                  data/c.jsonl "$(item chat-fake-3)"
run BLOCKED "meta- id"                                  data/m.jsonl "$(item meta-fake-101)"
run BLOCKED "blind id in another key + question"        data/x.jsonl "{$(kv queryId vit-fake-002), $(kv "$QK" "$FQ")}"
run BLOCKED "prose line: question + id anywhere"        notes/n.md "The \"$QK\" for es-fake-12 was reworded."
run BLOCKED "path questions_v03.jsonl"                  data/questions_v03.jsonl '{"x": 1}'
run BLOCKED "path questions.v03.jsonl.bak"              bench/v0.3/questions.v03.jsonl.bak '{"x": 1}'
run BLOCKED "non-ASCII path blind/questoes"             "blind/questões.jsonl" '{"x": 1}'
run BLOCKED "upper-case Blind/ dir"                     Blind/notes.txt 'x'
run BLOCKED "path bench/v0.2/questions.jsonl"           bench/v0.2/questions.jsonl '{"x": 1}'
run BLOCKED "path refs/refs-v03.jsonl.bak"              bench/v0.3/refs/refs-v03.jsonl.bak '{"x": 1}'
run BLOCKED "path refs/raw/"                            bench/v0.3/refs/raw/a.txt 'x'
echo "Must PASS (benign)"
run PASS "prose .md commit"                             notes/plan.md '# Plan' '' 'Prose about the v0.3 bench and its id format; no item text here.'
run PASS "published v0.1 references path"              bench/v0.1/refs/refs.jsonl '{"x": 1}'
run PASS "worked example v03-travel-98"                 docs/example.jsonl "$(item v03-travel-98)"
run PASS "self-test id st-qa-fake-001"                  data/st.jsonl "$(item st-qa-fake-001)"
if [ -f "$PUBF" ]; then run PASS "public v0.1 line (vit id, public text, sha-pinned)" data/v01.jsonl "$(head -1 "$PUBF")"
  run BLOCKED "public v0.1 line with question text altered" data/v01.jsonl "$(head -1 "$PUBF" | sed "s/\"$QK\": \"/\"$QK\": \"FAKE /")"
else echo "  [skip] v0.1 public file not found: $PUBF"; fi
echo "RESULT: $PASS passed, $FAIL failed (scratch $ROOT)"; [ $FAIL = 0 ]
