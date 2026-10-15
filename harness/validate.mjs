#!/usr/bin/env node
// Validates EvalTrace jsonl files against the Zod contract (packages/protocol). Exit 1 on the first bad file.
// Usage: node harness/validate.mjs traces.jsonl [more.jsonl ...]
import { readFileSync } from "node:fs";
import { EvalTrace } from "../packages/protocol/src/index.ts";

let bad = 0;
for (const f of process.argv.slice(2)) {
  const lines = readFileSync(f, "utf8").split("\n").filter((l) => l.trim());
  const errs = [];
  lines.forEach((l, i) => {
    const r = EvalTrace.safeParse(JSON.parse(l));
    if (!r.success) errs.push(`${f}:${i + 1}: ${r.error.issues.map((x) => `${x.path.join(".")} ${x.message}`).join("; ")}`);
  });
  console.log(`${errs.length ? "INVALID" : "ok"} ${f} (${lines.length} traces${errs.length ? `, ${errs.length} invalid` : ""})`);
  for (const e of errs.slice(0, 5)) console.log(`  ${e}`);
  bad += errs.length ? 1 : 0;
}
process.exit(bad ? 1 : 0);
