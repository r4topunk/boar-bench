#!/usr/bin/env node
// Pairwise judge over EvalTrace: each traced answer vs the bench's frozen Opus+web reference, both A/B orders, with
// Claude Code headless (`claude -p`, no tools) on the subscription. Thin wrapper: prompt, schema, blinding, order
// draw, verdict mapping and the CLI call are the vendored eval lib (scorers/vendor/eval-lib); the loop and row
// fields follow rnd/bench/judge/judge_bench.mjs (sha256 7bc91413…). Rows are what scorers/score.py reads.
// Any API error or rate limit stops the run (no retry); rerunning resumes (done = ok rows already in --out).
// Venue-list items are not judged (OSM scores them).
// Errored traces (t.error) are dropped with a WARN naming the count (FAILCLOSED-2026-10-11); --strict makes that (and any id without a trace or
// reference) exit 5 before any call; --floor-errored keeps them and appends, without any LLM call, a floor-score row per order (boar 1/1/1 on the
// 1-5 rubric, winner "ref", reference scores imputed from this file's judged rows, fields error/floorScored/refImputed) so the item stays in the ratio.
// Resume provenance (PIPELINE-AUDIT 2026-10-13 F1): an ok row already in --out is reused only if its tracesSha256, questionsSha256,
// refsSha256, judgeVersion and requested model match this run (legacy rows without requestedModel: judgeModel must contain the
// requested --judge-model). Otherwise exit 7 before any call, naming the stale rows, unless --allow-splice declares the splice
// (multi-set files, the verdict copy for byte-identical answers, hybrid files); new rows carry requestedModel.
// F4: floor rows are not "done" once the item's trace is no longer errored (they are dropped from --out and the item is judged).
// F9: --ids entries are trimmed; ids not in the questions file are named on stderr (exit 5 with --strict).
//
// Usage: node harness/judge.mjs --traces T.jsonl --out J.jsonl [--bench DIR] [--refs FILE] [--ids a,b] [--limit CALLS]
//          [--seed 7] [--gap-ms 5000] [--judge-model opus] [--system NAME] [--dry-run] [--floor-errored] [--strict] [--allow-splice]
import { appendFileSync, existsSync, mkdirSync, readFileSync, readdirSync, renameSync, writeFileSync } from "node:fs";
import { createHash } from "node:crypto";
import { execFileSync } from "node:child_process";
import { basename, dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const HERE = dirname(fileURLToPath(import.meta.url));
const REPO = join(HERE, "..");
const LIB = process.env.BOAR_EVAL_LIB ?? join(REPO, "scorers", "vendor", "eval-lib");
const { cleanEnv, isRateLimited, logSpend, runClaude, sleep, totalSpend } = await import(join(LIB, "claude-cli.mjs"));
const { JUDGE_SYSTEM, VERDICT_SCHEMA, blind, firstOrders, judgePrompt, mapVerdict } = await import(join(LIB, "judge-core.mjs"));
// --effort <level> (opt-in): separate judge version judge.v1-<level>; never compare it with judge.v1 numbers.
const JUDGE_EFFORT = process.argv.includes("--effort") ? process.argv[process.argv.indexOf("--effort") + 1] : undefined;
const JUDGE_VERSION = JUDGE_EFFORT ? `judge.v1-${JUDGE_EFFORT === "medium" ? "med" : JUDGE_EFFORT}` : "judge.v1";

const a = process.argv.slice(2);
const get = (k, d) => (a.includes(k) ? a[a.indexOf(k) + 1] : d);
const tracesPath = get("--traces"); const out = get("--out");
if (!tracesPath || !out) throw new Error("--traces and --out are required");
const seed = Number(get("--seed", "7")); const gapMs = Number(get("--gap-ms", "5000")); const limit = Number(get("--limit", "0"));
const judgeModel = get("--judge-model", "opus"); const dryRun = a.includes("--dry-run");
const sha = (p) => createHash("sha256").update(readFileSync(p)).digest("hex");
const readJsonl = (p) => readFileSync(p, "utf8").split("\n").filter((l) => l.trim()).map((l) => JSON.parse(l));

// ---- bench resolution (same lookup as scorers/bench.py)
const cfg = existsSync(join(HERE, "config.json")) ? JSON.parse(readFileSync(join(HERE, "config.json"), "utf8")) : {};
const benchDir = resolve(get("--bench", process.env.BOAR_EVAL_BENCH ?? join(REPO, cfg.bench ?? "")));
const man = existsSync(join(benchDir, "bench.json")) ? JSON.parse(readFileSync(join(benchDir, "bench.json"), "utf8")) : {};
// A bench without bench.json (v0.2): its refs/MANIFEST.json names the questions file and the frozen refs file's sha256.
const refsMan0 = existsSync(join(benchDir, "refs", "MANIFEST.json")) ? JSON.parse(readFileSync(join(benchDir, "refs", "MANIFEST.json"), "utf8")) : {};
const qPath = [man.questions, "questions.public.jsonl", "questions.jsonl", refsMan0.questions_file].filter(Boolean).map((f) => join(benchDir, f)).find(existsSync);
if (!qPath) throw new Error(`no questions file in ${benchDir}`);
function refsPath() {
  if (get("--refs")) return resolve(get("--refs"));
  if (man.refs) return join(benchDir, man.refs);
  const rd = join(benchDir, "refs");
  const c = existsSync(rd) ? readdirSync(rd).filter((f) => f.endsWith(".jsonl") && !f.startsWith("MANIFEST")) : [];
  if (c.length === 1) return join(rd, c[0]);
  // Several jsonl files (v0.2: raw + frozen): the one whose sha256 the MANIFEST pins.
  const pinned = refsMan0.refs_jsonl_sha256 && c.find((f) => sha(join(rd, f)) === refsMan0.refs_jsonl_sha256);
  if (pinned) return join(rd, pinned);
  const legacy = join(benchDir, "..", "..", "refs", basename(benchDir), "claude-code__opus.jsonl");
  if (existsSync(legacy)) return legacy;
  throw new Error(`no references for ${benchDir}: pass --refs`);
}
const refPath = refsPath();
const refManPath = join(dirname(refPath), "MANIFEST.json");
const refManifest = existsSync(refManPath) ? JSON.parse(readFileSync(refManPath, "utf8")) : null;
const refsSha = sha(refPath); const qSha = sha(qPath);
if (refManifest?.jsonl_sha256 && refManifest.jsonl_sha256 !== refsSha) throw new Error("references sha mismatch vs MANIFEST");
if (refManifest?.refs_jsonl_sha256 && refManifest.refs_jsonl_sha256 !== refsSha) throw new Error("references sha mismatch vs MANIFEST (refs_jsonl_sha256)");
if (refManifest?.questions_sha256 && refManifest.questions_sha256 !== qSha) throw new Error("questions sha mismatch vs references MANIFEST");

const questions = Object.fromEntries(readJsonl(qPath).map((q) => [q.id, q]));
const FLOOR_ERRORED = a.includes("--floor-errored"); const STRICT = a.includes("--strict");
const traces = {}; const erroredIds = new Set();
for (const t of readJsonl(tracesPath)) { // last trace per item wins
  if (t.error) { if (FLOOR_ERRORED) traces[t.itemId] = t; else if (!traces[t.itemId]) erroredIds.add(t.itemId); } // without the flag an earlier ok trace still stands (as before)
  else { erroredIds.delete(t.itemId); traces[t.itemId] = t; }
}
const ref = Object.fromEntries(readJsonl(refPath).filter((r) => r.ok).map((r) => [r.id, r]));
const t0r = Object.values(traces).find((t) => !t.error) ?? Object.values(traces)[0];
const system = get("--system", `${t0r?.engine?.arm ?? "system"}@${t0r?.engine?.commit ?? "unknown"}`);
const onlyIds = get("--ids") ? new Set(get("--ids").split(",").map((x) => x.trim()).filter(Boolean)) : null;
const unknownIds = onlyIds ? [...onlyIds].filter((id) => !questions[id]) : [];
if (unknownIds.length) { console.error(`WARN --ids: ${unknownIds.length} ids not in the questions file (${qPath}): ${unknownIds.join(",")}`); if (STRICT) process.exit(5); }
let ids = Object.keys(questions).filter((id) => questions[id].grading?.type !== "venue-list" && (!onlyIds || onlyIds.has(id)));
const droppedErrored = ids.filter((id) => erroredIds.has(id) && !FLOOR_ERRORED && ref[id]);
if (droppedErrored.length) console.warn(`WARN dropped ${droppedErrored.length} errored traces (item left out of the ratio; use --floor-errored to score at the floor): ${droppedErrored.join(",")}`);
const skipped = ids.filter((id) => !traces[id] || !ref[id]);
if (STRICT && (droppedErrored.length || skipped.length)) { console.error(`STRICT: ${droppedErrored.length} errored traces dropped, ${skipped.length} ids without trace/reference; exiting before any call`); process.exit(5); }
if (skipped.length) console.warn(`skipping ${skipped.length} ids without both a trace and a reference: ${skipped.join(",")}`);
ids = ids.filter((id) => traces[id] && ref[id]);
mkdirSync(dirname(resolve(out)), { recursive: true });
const SPEND = join(REPO, "runs", "judge-spend.jsonl"); mkdirSync(dirname(SPEND), { recursive: true });
const floorIds = FLOOR_ERRORED ? ids.filter((id) => traces[id].error) : [];
ids = ids.filter((id) => !traces[id].error);
const tracesSha = sha(tracesPath); const ALLOW_SPLICE = a.includes("--allow-splice");
let prev = existsSync(out) ? readJsonl(out) : [];
// F4: a floor row stops counting as done once its trace is no longer errored (dropped from --out below, the item is judged instead)
const supersededFloor = prev.filter((r) => r.ok && r.floorScored && traces[r.queryId] && !traces[r.queryId].error);
if (supersededFloor.length) {
  console.warn(`floor rows superseded (trace no longer errored): ${supersededFloor.length} rows (${[...new Set(supersededFloor.map((r) => r.queryId))].join(",")})` + (dryRun ? "; would be dropped" : "; dropped from " + out));
  prev = prev.filter((r) => !supersededFloor.includes(r));
  if (!dryRun) { writeFileSync(out + ".tmp", prev.map((r) => JSON.stringify(r) + "\n").join("")); renameSync(out + ".tmp", out); }
}
// F1: resume reuses an ok row only when its provenance matches this run (or the splice is declared with --allow-splice)
const planned = new Set([...ids, ...floorIds].flatMap((id) => ["boarA", "boarB"].map((o) => `${id}|${o}`)));
const modelOk = (r) => (r.requestedModel !== undefined ? r.requestedModel === judgeModel : r.floorScored || String(r.judgeModel ?? "").includes(judgeModel));
const PROV = [["tracesSha256", (r) => r.tracesSha256 === tracesSha], ["questionsSha256", (r) => r.questionsSha256 === qSha], ["refsSha256", (r) => r.refsSha256 === refsSha],
              ["judgeVersion", (r) => r.judgeVersion === JUDGE_VERSION], ["model", modelOk]];
const stale = prev.filter((r) => r.ok && planned.has(`${r.queryId}|${r.order}`)).map((r) => [r, PROV.filter(([, f]) => !f(r)).map(([k]) => k)]).filter(([, bad]) => bad.length);
if (stale.length) {
  const by = {}; for (const [, bad] of stale) for (const k of bad) by[k] = (by[k] ?? 0) + 1;
  const msg = `${stale.length} ok rows in ${out} differ in provenance from this run (${Object.entries(by).map(([k, v]) => `${k}: ${v}`).join(", ")}; ` +
    `this run: traces ${tracesSha.slice(0, 12)} questions ${qSha.slice(0, 12)} refs ${refsSha.slice(0, 12)} ${JUDGE_VERSION} model ${judgeModel}); first: ${stale.slice(0, 5).map(([r]) => `${r.queryId}|${r.order}`).join(",")}`;
  if (!ALLOW_SPLICE) { console.error(`STALE: ${msg}. Refusing to resume (exit 7, no call): use a new --out, or pass --allow-splice to declare the splice.`); process.exit(7); }
  console.warn(`SPLICE (--allow-splice): reusing ${msg}`);
}
const done = new Set(prev.filter((r) => r.ok).map((r) => `${r.queryId}|${r.order}`));
const todo = ids.flatMap((id) => ["boarA", "boarB"].map((o) => `${id}|${o}`)).filter((k) => !done.has(k));
console.log(`judge: ${ids.length} items, ${todo.length} calls to do (${done.size} done), refs ${refsSha.slice(0, 12)}, questions ${qSha.slice(0, 12)}` + (FLOOR_ERRORED ? `, ${floorIds.length} errored items to floor-score` : ""));
if (dryRun) process.exit(0);

const cliVersion = execFileSync("claude", ["--version"], { env: cleanEnv(), encoding: "utf8" }).trim();
const first = firstOrders(ids, seed);
let calls = 0; const t0 = Date.now();
for (const id of ids) {
  const q = questions[id]; const notes = (q.rubric ?? []).join(" / "); const tr = traces[id];
  const orders = first[id] === "boarA" ? ["boarA", "boarB"] : ["boarB", "boarA"];
  for (const order of orders) {
    if (done.has(`${id}|${order}`)) continue;
    if (limit && calls >= limit) { console.log(`limit ${limit} reached`); process.exit(0); }
    if (calls++) await sleep(gapMs);
    const boarIsA = order === "boarA";
    const [answerA, answerB] = boarIsA ? [blind(tr.answer.text), blind(ref[id].answer)] : [blind(ref[id].answer), blind(tr.answer.text)];
    const r = await runClaude({ prompt: judgePrompt({ question: q.question, notes, answerA, answerB }), systemPrompt: JUDGE_SYSTEM,
                                model: judgeModel, effort: JUDGE_EFFORT, tools: [], jsonSchema: VERDICT_SCHEMA, timeoutMs: 180_000 });
    logSpend(SPEND, `boar-eval-judge:${system}`, r);
    if (isRateLimited(r)) { console.error(`RATE LIMITED at ${id}/${order}: ${r.error ?? r.stderr}. Stopped; rerun resumes.`); process.exit(3); }
    const verdict = r.json?.structured_output; const ok = r.ok && verdict != null;
    if (!ok) { console.error(`API/verdict ERROR at ${id}/${order}: ${r.error ?? "no structured_output"}. Stopped (no retry); rerun resumes.`); process.exit(4); }
    const row = { queryId: id, category: q.category, order, ok, verdict, mapped: mapVerdict(verdict, boarIsA), system,
                  reference: `${basename(dirname(refPath))} ${basename(refPath, ".jsonl")}`, runId: tr.runId, commit: tr.engine?.commit, arm: tr.engine?.arm,
                  judgeModel: r.json ? Object.keys(r.json.modelUsage ?? {})[0] : undefined, requestedModel: judgeModel, judgeVersion: JUDGE_VERSION, seed,
                  durationMs: r.json?.duration_ms, listPriceEquivalentUsd: r.json?.total_cost_usd, cliVersion, tracesSha256: tracesSha,
                  refsSha256: refsSha, questionsSha256: qSha, createdAt: new Date().toISOString() };
    appendFileSync(out, JSON.stringify(row) + "\n");
    console.log(`${id} ${order} ${verdict.winner}->${row.mapped.winner} ${((row.durationMs ?? 0) / 1000).toFixed(1)}s elapsed=${((Date.now() - t0) / 1000).toFixed(0)}s`);
  }
}
if (floorIds.length) { // errored traces: floor-score both orders, no LLM call
  const K = ["correctness", "completeness", "usefulness"]; const real = readJsonl(out).filter((r) => r.ok && !r.floorScored);
  if (!real.length) { console.error(`--floor-errored: no judged rows in ${out} to impute the reference side from; ${floorIds.length} errored items NOT floor-scored (the row-count check will fail)`); process.exit(6); }
  const refMean = Object.fromEntries(K.map((k) => [k, real.reduce((x, r) => x + r.mapped.ref[k], 0) / real.length]));
  const have = new Set(readJsonl(out).filter((r) => r.ok).map((r) => `${r.queryId}|${r.order}`)); let n = 0;
  for (const id of floorIds) for (const order of ["boarA", "boarB"]) {
    if (have.has(`${id}|${order}`)) continue; const tr = traces[id]; const e = tr.error;
    const err = typeof e === "string" ? e : `${e.code ?? "error"}: ${e.message ?? JSON.stringify(e)}`;
    const row = { queryId: id, category: questions[id].category, order, ok: true, verdict: null, mapped: { winner: "ref", boar: Object.fromEntries(K.map((k) => [k, 1])), ref: refMean },
                  floorScored: true, refImputed: true, error: `errored trace scored at the rubric floor (1/1/1): ${err}`, system, runId: tr.runId, commit: tr.engine?.commit, arm: tr.engine?.arm,
                  judgeModel: "none (floor)", requestedModel: judgeModel, judgeVersion: JUDGE_VERSION, seed, tracesSha256: tracesSha, refsSha256: refsSha, questionsSha256: qSha, createdAt: new Date().toISOString() };
    appendFileSync(out, JSON.stringify(row) + "\n"); n++;
  }
  console.log(`floor-errored: ${n} rows for ${floorIds.length} errored items (${floorIds.join(",")})`);
}
console.log(`done ${out}; cumulative list-price equivalent ${totalSpend(SPEND).toFixed(2)} USD (runs/judge-spend.jsonl)`);
