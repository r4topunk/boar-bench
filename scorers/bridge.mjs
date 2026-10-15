#!/usr/bin/env node
// Node bridge for score.py: runs the EXISTING eval graders (judge-core, venues, firstaid-check) on JSON from stdin
// and prints JSON to stdout. No reimplementation: every number comes from the imported modules.
// Request:  {"ops": [{"op": "judge", "path": "<judgments.jsonl>", "ids": ["..."] | null, "seed": 11},
//                    {"op": "venues", "items": [{"id", "answer", "gold_path", "minRealVenues"}]},
//                    {"op": "firstaid", "items": [{"id", "rule", "answer"}]},
//                    {"op": "info"}]}
// Response: {"results": [...]} in the same order.
// boar-eval: vendored from rnd/bench/score/bridge.mjs (see vendor/SOURCE.md). Only change: the eval lib path
// defaults to the vendored copy in scorers/vendor/eval-lib; override with BOAR_EVAL_LIB.
import { readFileSync } from "node:fs";
import { createHash } from "node:crypto";
import { dirname, join } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const LIB = process.env.BOAR_EVAL_LIB ?? join(dirname(fileURLToPath(import.meta.url)), "vendor", "eval-lib");
const load = (f) => import(pathToFileURL(join(LIB, f)).href);
const sha = (f) => createHash("sha256").update(readFileSync(join(LIB, f))).digest("hex");
const readJsonl = (p) => readFileSync(p, "utf8").split("\n").filter((l) => l.trim()).map((l) => JSON.parse(l));

async function judge({ path, ids, seed = 11 }) {
  const { combineOrders, summarize, meanScore } = await load("judge-core.mjs");
  const keep = ids ? new Set(ids) : null;
  // Same grouping as eval/scripts/report.mjs pairsFor() and rnd/plumb/analyze.mjs: ok rows only, last row per
  // (queryId, order) wins, queries missing one order are left out, pair order = first appearance in the file.
  const byQ = {};
  let rows = 0, okRows = 0;
  for (const j of readJsonl(path)) {
    rows++;
    if (!j.ok || (keep && !keep.has(j.queryId))) continue;
    okRows++;
    (byQ[j.queryId] ??= {})[j.order] = j;
  }
  const single = Object.entries(byQ).filter(([, o]) => !(o.boarA && o.boarB)).map(([q]) => q);
  const pairs = Object.entries(byQ)
    .filter(([, o]) => o.boarA && o.boarB)
    .map(([queryId, o]) => ({ queryId, category: o.boarA.category, ...combineOrders(o.boarA.mapped, o.boarB.mapped) }));
  const meta = [...new Set(Object.values(byQ).flatMap((o) => Object.values(o)).map((j) => `${j.judgeModel}|${j.judgeVersion}|${j.reference}|${j.system}`))];
  return {
    op: "judge",
    rows,
    okRowsInScope: okRows,
    singleOrderDropped: single,
    judgeMeta: meta,
    summary: pairs.length ? summarize(pairs, { seed }) : null,
    correctRate: pairs.length ? pairs.filter((p) => p.boar.correctness >= 4).length / pairs.length : null,
    pairs: pairs.map((p) => ({ ...p, boarMean: meanScore(p.boar), refMean: meanScore(p.ref) })),
  };
}

async function venues({ items }) {
  const { scoreFoodAnswer } = await load("venues.mjs");
  return {
    op: "venues",
    items: items.map((it) => {
      const gold = JSON.parse(readFileSync(it.gold_path, "utf8"));
      return { id: it.id, ...scoreFoodAnswer(it.answer ?? "", gold, { minRealVenues: it.minRealVenues ?? 3 }) };
    }),
  };
}

async function firstaid({ items }) {
  const { checkFirstAid } = await load("firstaid-check.mjs");
  // Content check only (no retrievedTitles): shown-source topicality is a product gate, not answer truthfulness.
  return { op: "firstaid", items: items.map((it) => ({ id: it.id, rule: it.rule, ...(checkFirstAid(it.rule, { answer: it.answer ?? "" }) ?? { pass: null, failures: ["no rule"], warnings: [] }) })) };
}

function info() {
  const files = ["judge-core.mjs", "venues.mjs", "firstaid-check.mjs", "preface.mjs"];
  return { op: "info", lib: LIB, sha256: Object.fromEntries(files.map((f) => [f, sha(f)])) };
}

const req = JSON.parse(readFileSync(0, "utf8"));
const OPS = { judge, venues, firstaid, info };
const results = [];
for (const o of req.ops) {
  if (!OPS[o.op]) throw new Error(`unknown op ${o.op}`);
  results.push(await OPS[o.op](o));
}
process.stdout.write(JSON.stringify({ results }));
