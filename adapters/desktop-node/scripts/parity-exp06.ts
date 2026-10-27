/**
 * Parity with exp-06: an exp-06 answerer row file vs EvalTraces of the same config. Compares, per item: answer text,
 * tier, outcome, reason codes, declined, final sources (title+section), shown titles, cited titles.
 *   tsx scripts/parity-exp06.ts rnd/kiln/exp-06-desktop-answerer/runs/p2-iphone13-1.5b.jsonl traces.jsonl
 */
import { readFileSync } from "node:fs";
import { readTraces, summarize } from "./lib";

const [fRows, fTraces] = process.argv.slice(2);
if (!fRows || !fTraces) {
  console.error("usage: parity-exp06.ts exp06-rows.jsonl traces.jsonl");
  process.exit(2);
}
const rows = readFileSync(fRows, "utf8").split("\n").filter((l) => l.trim()).map((l) => JSON.parse(l));
const traces = new Map(readTraces(fTraces).map((t) => [t.itemId, t]));
const key = (s: { title: string; section: string | null }) => `${s.title}§${s.section ?? ""}`;
const checks: Record<string, (r: any, t: any) => boolean> = {
  answerText: (r, t) => r.answer === t.answer.text,
  tier: (r, t) => r.tier === t.route.tier,
  outcome: (r, t) => r.outcome === t.route.outcome,
  reasonCodes: (r, t) => JSON.stringify(r.reasonCodes) === JSON.stringify(t.route.reasonCodes),
  declined: (r, t) => r.flags.declined === t.answer.declined,
  weakSources: (r, t) => r.flags.weak_sources === t.answer.weakSources,
  keptSources: (r, t) => JSON.stringify(r.sources.map(key)) === JSON.stringify(t.retrieval.kept.map(key)),
  shownTitles: (r, t) => JSON.stringify(r.shownSources.map((s: any) => s.title)) === JSON.stringify(t.answer.shown),
  citedTitles: (r, t) => JSON.stringify(r.citedTitles) === JSON.stringify(t.answer.cited),
};
const ok: Record<string, number> = Object.fromEntries(Object.keys(checks).map((k) => [k, 0]));
const misses: string[] = [];
let paired = 0;
for (const r of rows) {
  const t = traces.get(r.id);
  if (!t) {
    misses.push(`${r.id}: no trace`);
    continue;
  }
  paired++;
  for (const [k, f] of Object.entries(checks)) {
    if (f(r, t)) ok[k]++;
    else misses.push(`${r.id}: ${k}`);
  }
}
const base = {
  declined: rows.filter((r) => r.flags.declined).length,
  noShownSources: rows.filter((r) => !r.shownSources.length).length,
  tiers: rows.reduce((m: Record<string, number>, r) => ((m[r.tier] = (m[r.tier] ?? 0) + 1), m), {}),
};
console.log(`exp-06 rows: ${rows.length} · traces paired: ${paired}`);
console.log(`exp-06 baseline: ${JSON.stringify(base)}`);
console.log(`traces:          ${JSON.stringify(summarize([...traces.values()]))}`);
for (const [k, n] of Object.entries(ok)) console.log(`  ${k.padEnd(12)} ${n}/${paired}`);
for (const m of misses) console.log(`  DIFF ${m}`);
process.exit(misses.length ? 1 : 0);
