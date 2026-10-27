#!/bin/bash
# Test plan for audit-2026-10-13-judge.patch (PIPELINE-AUDIT 2026-10-13 F1 F4 F6 + F9 ids). 0 judge calls (claude is stubbed; JUDGE_CMD stub for F6).
# Usage: audit-2026-10-13-judge.test.sh check|apply|verify
#   check  : no judge running, patch sha256 matches its .sha256, patch applies cleanly (patch -p1 --dry-run from <workspace>)
#   apply  : check, then apply (refuses while judge.mjs / shard_judge.sh / grade.py / a judge_chain runs)
#   verify : harness unit tests; arms/_lib/tests/run.sh (expect 61 passed: 51 + T9-T11); Repro A and Repro B with a stub claude (expect refusal)
set -u
B=<workspace>; D=$(cd "$(dirname "$0")" && pwd); P=$D/audit-2026-10-13-judge.patch; E=$B/boar-eval; A=$B/rnd/research/coordinator/arms
busy() { pgrep -fl "judge\.mjs|shard_judge|grade\.py|judge_chain\.sh" | grep -v "audit-2026-10-13-judge.test.sh"; }
check() { if busy; then echo "BUSY: a judge chain is running; do not patch now"; return 1; fi
  (cd "$D" && shasum -a 256 -c audit-2026-10-13-judge.patch.sha256) || return 1
  (cd "$B" && patch -p1 --dry-run < "$P") || return 1; echo "CHECK OK"; }
case ${1:-check} in
  check) check;;
  apply) check && (cd "$B" && patch -p1 < "$P") && echo "APPLIED";;
  verify)
    T=$(mktemp -d "${TMPDIR:-/tmp}/judgepatch.XXXXXX"); mkdir -p "$T/bin"
    printf '#!/bin/bash\n[ "$1" = --version ] && { echo 0.0-stub; exit 0; }\necho "$@" >> %s/claude.calls; exit 1\n' "$T" > "$T/bin/claude"; chmod +x "$T/bin/claude"
    (cd "$E" && python3 -m unittest discover -s harness/tests 2>&1 | tail -3)
    bash "$A/_lib/tests/run.sh" 2>&1 | grep -E "^\s+\[FAIL\]|^RESULT"
    cp "$A/deepread/deep35-R450.judgments.jsonl" "$T/J.jsonl"
    (cd "$E" && PATH=$T/bin:$PATH node harness/judge.mjs --traces "$A/deeppar/bmoe-R450.traces.jsonl" --out "$T/J.jsonl" --bench "$E/bench/v0.1" --judge-model claude-haiku-5-5 --dry-run 2>&1 | cut -c1-160; exit ${PIPESTATUS[0]}); echo "Repro A rc=$? (expect 7, STALE)"
    jq -r .itemId "$A/deeppar/bmoe-R450.traces.jsonl" > "$T/ids"; mkdir -p "$T/rb/out.shards"; cp "$A/deepread/deep35-R450.judgments.jsonl" "$T/rb/out.shards/shard-0.jsonl"
    PATH=$T/bin:$PATH bash "$A/deepthink/tools/shard_judge.sh" "$A/deeppar/bmoe-R450.traces.jsonl" "$T/rb/out.jsonl" "$E/bench/v0.1" "$T/ids" reproB 1 opus > "$T/rb.out" 2>&1; r=$?
    grep -v "^wall" "$T/rb.out" | cut -c1-160; grep -h "^STALE" "$T/rb/out.shards/shard-0.log" | cut -c1-120; echo "Repro B rc=$r (expect 3: shard exit 7 + PROVENANCE)"
    echo "judge calls: $(cat "$T/claude.calls" 2>/dev/null | wc -l | tr -d ' ') (expect 0)"; rm -rf "$T";;
  *) echo "usage: $0 check|apply|verify"; exit 2;;
esac
