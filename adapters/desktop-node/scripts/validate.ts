/**
 * EvalTrace.parse() every line of a traces file; fail (exit 1) on any invalid line, and, with --requests, on items
 * missing from or extra to the requests (after --ids). Prints a one-line summary per check plus the run's counts.
 *   tsx scripts/validate.ts traces.jsonl [--requests requests.jsonl] [--ids a,b]
 */
import { readFileSync } from "node:fs";
import { EvalRequest, EvalTrace } from "@boar-eval/protocol";
import { summarize } from "./lib";

const argv = process.argv.slice(2);
const get = (k: string) => (argv.includes(k) ? argv[argv.indexOf(k) + 1] : undefined);
const file = argv[0];
if (!file) {
  console.error("usage: validate.ts traces.jsonl [--requests r.jsonl] [--ids a,b]");
  process.exit(2);
}
const bad: string[] = [];
const traces: EvalTrace[] = [];
readFileSync(file, "utf8").split("\n").forEach((l, i) => {
  if (!l.trim()) return;
  let j: unknown;
  try {
    j = JSON.parse(l);
  } catch (e) {
    bad.push(`line ${i + 1}: invalid JSON`);
    return;
  }
  const r = EvalTrace.safeParse(j);
  if (r.success) traces.push(r.data);
  else bad.push(`line ${i + 1}: ${r.error.issues.slice(0, 3).map((x) => `${x.path.join(".")}: ${x.message}`).join("; ")}`);
});
const reqPath = get("--requests");
if (reqPath) {
  const ids = get("--ids")?.split(",");
  const want = readFileSync(reqPath, "utf8").split("\n").filter((l) => l.trim()).map((l) => EvalRequest.parse(JSON.parse(l)).item.id)
    .filter((id) => !ids || ids.includes(id));
  const got = traces.map((t) => t.itemId);
  const missing = want.filter((id) => !got.includes(id));
  const extra = got.filter((id) => !want.includes(id));
  const dup = got.filter((id, i) => got.indexOf(id) !== i);
  if (missing.length) bad.push(`missing items: ${missing.join(",")}`);
  if (extra.length) bad.push(`items not requested: ${extra.join(",")}`);
  if (dup.length) bad.push(`repeated items: ${dup.join(",")}`);
}
if (bad.length) {
  console.error(`INVALID ${file}:\n  ${bad.join("\n  ")}`);
  process.exit(1);
}
console.log(`valid: ${traces.length}/${traces.length} EvalTrace lines (${file})`);
console.log(JSON.stringify(summarize(traces)));
