// merge-shards.mjs <requests.jsonl> <out.jsonl> <N>: concatenates <out>.w0..w{N-1}.jsonl into <out> in request order
// (after --ids filtering the shards hold a subset: order follows the requests that have a trace). Fails on a duplicate.
import { readFileSync, writeFileSync } from "node:fs";
const [reqPath, out, n] = process.argv.slice(2);
const lines = (p) => readFileSync(p, "utf8").split("\n").filter((l) => l.trim());
const order = lines(reqPath).map((l) => JSON.parse(l).item.id);
const byId = new Map();
for (let i = 0; i < Number(n); i++) for (const l of lines(out.replace(/\.jsonl$/, `.w${i}.jsonl`))) {
  const id = JSON.parse(l).itemId;
  if (byId.has(id)) { console.error(`merge-shards: ${id} in two shards`); process.exit(1); }
  byId.set(id, l);
}
writeFileSync(out, order.filter((id) => byId.has(id)).map((id) => byId.get(id) + "\n").join(""));
console.log(`merge-shards: ${byId.size} traces -> ${out}`);
