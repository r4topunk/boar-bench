#!/usr/bin/env node
// CLI-login-only Codex adapter. Bench resolution, blinding, seeded A/B ordering, mapping,
// and resume provenance mirror judge.mjs; all rubric logic is imported unchanged from judge-core.
// --dry-run plans without a call; --limit 4 executes the two-item pilot. No held-out text is logged.
// Fixed sampling: high reasoning effort; codex exec exposes no temperature control.
import { appendFileSync, existsSync, mkdirSync, readFileSync, readdirSync, renameSync, writeFileSync, mkdtempSync, rmSync } from "node:fs";
import { createHash } from "node:crypto";
import { spawn, execFileSync } from "node:child_process";
import { basename, dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import { tmpdir } from "node:os";

const HERE = dirname(fileURLToPath(import.meta.url));
const REPO = join(HERE, "..");
const LIB = process.env.BOAR_EVAL_LIB ?? join(REPO, "scorers", "vendor", "eval-lib");
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const { JUDGE_SYSTEM, VERDICT_SCHEMA, blind, firstOrders, judgePrompt, mapVerdict } = await import(join(LIB, "judge-core.mjs"));
const JUDGE_VERSION = "judge.v1-codex";
const SAMPLING = Object.freeze({ temperature: null, temperatureControl: "unavailable in codex exec", reasoningEffort: "high" });

// Only CLI-login authentication is permitted. No parent session, provider routing, or API credentials.
export function cleanEnv() {
  const keep = new Set(["PATH", "HOME", "USER", "LOGNAME", "TMPDIR", "LANG", "LC_ALL", "CODEX_HOME"]);
  return Object.fromEntries(Object.entries(process.env).filter(([k]) => keep.has(k)));
}

export function validVerdict(v) {
  const exact = (o, keys) => o && typeof o === "object" && !Array.isArray(o) &&
    Object.keys(o).length === keys.length && keys.every((k) => Object.hasOwn(o, k));
  const score = (s) => exact(s, ["correctness", "completeness", "usefulness"]) &&
    Object.values(s).every((n) => Number.isInteger(n) && n >= 1 && n <= 5);
  return exact(v, ["scores_A", "scores_B", "winner", "rationale"]) && score(v.scores_A) && score(v.scores_B) &&
    ["A", "B", "tie"].includes(v.winner) && typeof v.rationale === "string";
}

// Prompts stay in memory, transmitted on stdin; only the public system/schema enter the empty cwd.
// Never echo subprocess output: errors and rationales may contain held-out text.
export async function runCodex({ prompt, systemPrompt, model, jsonSchema, timeoutMs = 300_000, onCall = () => {} }) {
  for (let attempt = 1; attempt <= 2; attempt++) {
    const cwd = mkdtempSync(join(tmpdir(), "boar-eval-codex-"));
    const schemaPath = join(cwd, "schema.json"), systemPath = join(cwd, "system.txt");
    writeFileSync(schemaPath, JSON.stringify(jsonSchema));
    writeFileSync(systemPath, systemPrompt);
    const argv = ["exec", "--ignore-user-config", "--ignore-rules", "--ephemeral", "--skip-git-repo-check",
      "--sandbox", "read-only", "--model", model, "--output-schema", schemaPath, "--json", "--color", "never",
      "-c", "forced_login_method=\"chatgpt\"", "-c", "model_provider=\"openai\"",
      "-c", `model_instructions_file=${JSON.stringify(systemPath)}`, "-c", "project_doc_max_bytes=0",
      "-c", "model_reasoning_effort=\"high\"", "-c", "web_search=\"disabled\"",
      "-c", "features.shell_tool=false", "-c", "features.apps=false", "-c", "features.multi_agent=false",
      "-c", "features.js_repl=false", "-c", "features.memory_tool=false", "-c", "personality=\"none\"", "-"];
    const start = performance.now();
    const result = await new Promise((resolveCall) => {
      const child = spawn("codex", argv, { cwd, env: cleanEnv(), stdio: ["pipe", "pipe", "pipe"] });
      let stdout = "", stderr = "", timedOut = false, spawnError = false;
      child.stdout.on("data", (d) => { stdout += d; });
      child.stderr.on("data", (d) => { stderr += d; });
      child.stdin.on("error", () => {});
      child.on("error", () => { spawnError = true; });
      child.stdin.end(prompt);
      let killTimer;
      const timer = setTimeout(() => { timedOut = true; child.kill("SIGTERM"); killTimer = setTimeout(() => child.kill("SIGKILL"), 2000); }, timeoutMs);
      child.on("close", (code) => {
        clearTimeout(timer); clearTimeout(killTimer);
        const wallMs = Math.round(performance.now() - start);
        const events = stdout.split("\n").flatMap((line) => { try { return [JSON.parse(line)]; } catch { return []; } });
        const toolCalls = events.filter((e) => e.type?.startsWith("item.") && e.item &&
          !["agent_message", "reasoning", "plan", "error"].includes(e.item.type));
        const final = events.findLast((e) => e.type === "item.completed" && e.item?.type === "agent_message")?.item.text;
        let verdict; try { verdict = JSON.parse(final); } catch { /* strict whole-message JSON only */ }
        const failed = events.some((e) => ["error", "turn.failed"].includes(e.type));
        const diagnostics = events.filter((e) => ["error", "turn.failed"].includes(e.type) || e.item?.type === "error")
          .map((e) => String(e.error?.message ?? e.message ?? e.item?.message ?? "")).join("\n");
        // Never scan successful verdicts, token counts, or random thread IDs for "429".
        const rateLimited = (code !== 0 || failed || !validVerdict(verdict)) &&
          /rate.?limit|usage limit|usage_limit|\b429\b|too many requests/i.test(stderr + diagnostics);
        const error = rateLimited ? "rate limit" : timedOut ? "timeout" : spawnError ? "spawn failed" :
          code !== 0 || failed ? "CLI failed (output withheld)" : toolCalls.length ? "unexpected tool use" :
          !validVerdict(verdict) ? "invalid verdict JSON/schema" : undefined;
        resolveCall({ ok: !error, rateLimited, error, parseFailure: error === "invalid verdict JSON/schema", wallMs, toolCalls: toolCalls.length, toolTypes: [...new Set(toolCalls.map((e) => e.item.type))],
          usage: events.findLast((e) => e.type === "turn.completed")?.usage,
          json: !error ? { structured_output: verdict, duration_ms: wallMs, modelUsage: { [model]: {} } } : undefined });
      });
    });
    rmSync(cwd, { recursive: true, force: true });
    onCall({ attempt, ok: result.ok, error: result.error, wallMs: result.wallMs, toolCalls: result.toolCalls, usage: result.usage });
    if (!result.parseFailure || attempt === 2) return result;
  }
}

export async function main() {
const a = process.argv.slice(2);
const get = (k, d) => (a.includes(k) ? a[a.indexOf(k) + 1] : d);
const tracesPath = get("--traces"); const out = get("--out");
if (!tracesPath || !out) throw new Error("--traces and --out are required");
const seed = Number(get("--seed", "7")); const gapMs = Number(get("--gap-ms", "5000")); const limit = Number(get("--limit", "0"));
const concurrency = Number(get("--concurrency", "1"));
if (!Number.isInteger(concurrency) || concurrency < 1 || concurrency > 4 || !Number.isInteger(limit) || limit < 0 || !Number.isFinite(gapMs) || gapMs < 0 || !Number.isInteger(seed)) throw new Error("invalid numeric options");
const judgeModel = get("--judge-model", "gpt-5.6-sol"); const dryRun = a.includes("--dry-run");
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
              ["judgeVersion", (r) => r.judgeVersion === JUDGE_VERSION], ["model", modelOk], ["sampling", (r) => JSON.stringify(r.sampling) === JSON.stringify(SAMPLING)]];
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

const cliVersion = execFileSync("codex", ["--version"], { env: cleanEnv(), encoding: "utf8" }).trim();
const first = firstOrders(ids, seed);
let calls = 0; const t0 = Date.now();
const jobs = ids.flatMap((id) => (first[id] === "boarA" ? ["boarA", "boarB"] : ["boarB", "boarA"])
  .filter((order) => !done.has(`${id}|${order}`)).map((order) => ({ id, order })));
const selected = limit ? jobs.slice(0, limit) : jobs;
let next = 0, stopped = false;
async function worker() {
  let localCalls = 0;
  while (!stopped && next < selected.length) {
    const { id, order } = selected[next++];
    const q = questions[id], notes = (q.rubric ?? []).join(" / "), tr = traces[id];
    if (localCalls++) await sleep(gapMs);
    if (stopped) return;
    calls++;
    const boarIsA = order === "boarA";
    const [answerA, answerB] = boarIsA ? [blind(tr.answer.text), blind(ref[id].answer)] : [blind(ref[id].answer), blind(tr.answer.text)];
    const r = await runCodex({ prompt: judgePrompt({ question: q.question, notes, answerA, answerB }), systemPrompt: JUDGE_SYSTEM,
                                model: judgeModel, jsonSchema: VERDICT_SCHEMA,
                                onCall: (call) => appendFileSync(out + ".calls.jsonl", JSON.stringify({ queryId: id, order, model: judgeModel, sampling: SAMPLING, cliVersion, ...call, createdAt: new Date().toISOString() }) + "\n") });
    if (r.rateLimited) { console.error(`RATE LIMITED at ${id}/${order}: ${r.error}. Stopped; rerun resumes.`); stopped = true; process.exitCode = 3; return; }
    const verdict = r.json?.structured_output; const ok = r.ok && verdict != null;
    if (!ok) { console.error(`API/verdict ERROR at ${id}/${order}: ${r.error ?? "no structured_output"}. Stopped (no retry); rerun resumes.`); stopped = true; process.exitCode = 4; return; }
    const row = { queryId: id, category: q.category, order, ok, verdict, mapped: mapVerdict(verdict, boarIsA), system,
                  reference: `${basename(dirname(refPath))} ${basename(refPath, ".jsonl")}`, runId: tr.runId, commit: tr.engine?.commit, arm: tr.engine?.arm,
                  judgeModel: r.json ? Object.keys(r.json.modelUsage ?? {})[0] : undefined, requestedModel: judgeModel, judgeVersion: JUDGE_VERSION, sampling: SAMPLING, seed,
                  durationMs: r.json?.duration_ms, listPriceEquivalentUsd: r.json?.total_cost_usd, cliVersion, tracesSha256: tracesSha,
                  refsSha256: refsSha, questionsSha256: qSha, createdAt: new Date().toISOString() };
    appendFileSync(out, JSON.stringify(row) + "\n");
    console.log(`${id} ${order} ${verdict.winner}->${row.mapped.winner} ${((row.durationMs ?? 0) / 1000).toFixed(1)}s elapsed=${((Date.now() - t0) / 1000).toFixed(0)}s`);
  }
}
await Promise.all(Array.from({ length: concurrency }, () => worker()));
if (stopped) return;

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
                  judgeModel: "none (floor)", requestedModel: judgeModel, judgeVersion: JUDGE_VERSION, sampling: SAMPLING, seed, tracesSha256: tracesSha, refsSha256: refsSha, questionsSha256: qSha, createdAt: new Date().toISOString() };
    appendFileSync(out, JSON.stringify(row) + "\n"); n++;
  }
  console.log(`floor-errored: ${n} rows for ${floorIds.length} errored items (${floorIds.join(",")})`);
}
console.log(`done ${out}`);
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  main().catch(() => { console.error("judge failed (details withheld to protect held-out content)"); process.exitCode = 4; });
}
