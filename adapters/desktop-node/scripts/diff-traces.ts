/**
 * Determinism check: two trace files of the same config must be identical except timing, createdAt and loadAvg
 * (lib.ts VOLATILE: tMs, *Ms, tokPerSec, createdAt, loadAvg1m). Pairs by itemId; exit 1 if any item differs.
 *   tsx scripts/diff-traces.ts a.jsonl b.jsonl
 */
import { firstDiff, readTraces, stable } from "./lib";

const [fa, fb] = process.argv.slice(2);
if (!fa || !fb) {
  console.error("usage: diff-traces.ts a.jsonl b.jsonl");
  process.exit(2);
}
const a = readTraces(fa);
const b = new Map(readTraces(fb).map((t) => [t.itemId, t]));
// runId differs between two runs by construction; everything else must match.
const norm = (t: (typeof a)[number]) => stable({ ...t, runId: null, config: t.config });
let same = 0;
const diffs: string[] = [];
for (const t of a) {
  const u = b.get(t.itemId);
  if (!u) {
    diffs.push(`${t.itemId}: missing in ${fb}`);
    continue;
  }
  const d = firstDiff(norm(t), norm(u));
  if (d) diffs.push(`${t.itemId}: differs at ${d}`);
  else same++;
}
const textSame = a.filter((t) => b.get(t.itemId)?.answer.text === t.answer.text).length;
console.log(`identical (ignoring timing/createdAt/loadAvg/runId): ${same}/${a.length} · answer text identical: ${textSame}/${a.length} · items only in b: ${[...b.keys()].filter((k) => !a.some((t) => t.itemId === k)).length}`);
for (const d of diffs) console.log(`  ${d}`);
process.exit(diffs.length || b.size !== a.length ? 1 : 0);
