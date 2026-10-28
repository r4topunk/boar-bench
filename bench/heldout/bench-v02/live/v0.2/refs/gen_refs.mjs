#!/usr/bin/env node
// Frozen "frontier + web" reference answers for the 110 items of boar-eval bench v0.2-new (origin "veil-v0.2").
// Copied from bench/v0.1/refs/gen_refs.mjs; recipe unchanged (reference.v1, opus, WebSearch + WebFetch, 5 s gap, same
// retry/stop rules). Only changed: the input file, the origin filter, the spend tag, and the freeze check (v0.2 has no
// SHA256SUMS yet: a row counts as done only if its question text equals the current item's, so a rewritten item is
// regenerated). build_manifest.py writes refs.jsonl + MANIFEST.jsonl/MANIFEST.json (hashes only are committed).
// Same recipe as rnd/bench/refs/gen_refs.mjs (v0): the shared claude -p helper (clean env: no API key),
// system prompt reference.v1 (sha256 d5144343…), tools WebSearch + WebFetch, sequential with a 5 s gap, resumable,
// rate limit -> stop (exit 3), other error -> 1 retry after 60 s, second failure -> stop (exit 4).
// Output text is gitignored (refs/*.jsonl).
// Usage (from <workspace>/boar-eval): node bench/v0.2/refs/gen_refs.mjs [--ids a,b] [--limit N] [--chunk-ms 290000] [--gap-ms 5000]
import { appendFileSync, existsSync, readFileSync } from "node:fs";
import { createHash } from "node:crypto";
import { execFileSync } from "node:child_process";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
// Shared helper, imported read-only by absolute path (clean env: strips API keys).
import { cleanEnv, isRateLimited, logSpend, runClaude, sleep, totalSpend, usageSummary } from "<workspace>/wt/eval/eval/scripts/lib/claude-cli.mjs";

const REFS_DIR = dirname(fileURLToPath(import.meta.url));
const BENCH = dirname(REFS_DIR);
const QUESTIONS = join(BENCH, "questions.v02-new.jsonl");
const NEW_ORIGIN = "veil-v0.2";
const PROMPT_VERSION = "reference.v1";
const PROMPT_FILE = `<workspace>/wt/eval/eval/prompts/${PROMPT_VERSION}.md`;
const PROMPT_SHA256 = "d51443438dfebcc7d2c3a0136340c70a68f495e1214c00a3a8c56bcdbc755972";
const TOOLS = ["WebSearch", "WebFetch"];
const RETRY_WAIT_MS = 60_000;
const CALL_TIMEOUT_MS = 300_000; // same default as the helper

const a = process.argv.slice(2);
const get = (k, d) => (a.includes(k) ? a[a.indexOf(k) + 1] : d);
const model = "opus";
const ids = get("--ids")?.split(",");
const limit = Number(get("--limit", "0"));
const gapMs = Number(get("--gap-ms", "5000"));
const chunkMs = Number(get("--chunk-ms", "0"));
const SPEND = join(REFS_DIR, "spend.jsonl");
const FAILS = join(REFS_DIR, "failures.jsonl");
const out = join(REFS_DIR, `claude-code__${model}.new.jsonl`);

const sha256 = (buf) => createHash("sha256").update(buf).digest("hex");

// Freeze check: a frozen MANIFEST.json blocks regeneration. (No SHA256SUMS before the v0.2 freeze; see header.)
const qBuf = readFileSync(QUESTIONS);
const QUESTIONS_SHA256 = sha256(qBuf);
const manPath = join(REFS_DIR, "MANIFEST.json");
if (existsSync(manPath) && JSON.parse(readFileSync(manPath, "utf8")).frozen === true) {
  console.error("ABORT: refs/MANIFEST.json is frozen. Regenerate as a new bench version.");
  process.exit(2);
}

const systemPrompt = readFileSync(PROMPT_FILE, "utf8");
const promptSha256 = sha256(systemPrompt);
if (promptSha256 !== PROMPT_SHA256) { console.error(`ABORT: ${PROMPT_FILE} sha256 ${promptSha256} != reference.v1`); process.exit(2); }
const cliVersion = execFileSync("claude", ["--version"], { env: cleanEnv(), encoding: "utf8" }).trim();

const all = qBuf.toString("utf8").trim().split("\n").map((l) => JSON.parse(l)).filter((q) => q.origin === NEW_ORIGIN);
let questions = ids ? all.filter((q) => ids.includes(q.id)) : all;

const readJsonl = (f) => (existsSync(f) ? readFileSync(f, "utf8").trim().split("\n").filter(Boolean).map((l) => JSON.parse(l)) : []);
const qText = new Map(all.map((q) => [q.id, q.question]));
const done = new Set(readJsonl(out).filter((r) => r.ok && r.question === qText.get(r.id)).map((r) => r.id));
const priorFails = readJsonl(FAILS).reduce((m, r) => m.set(r.id, (m.get(r.id) ?? 0) + 1), new Map());

/** Same as v0: splits the trailing "Sources:" block off the answer; falls back to any URLs in the text. */
function splitSources(text) {
  const m = text.match(/\n\**Sources:?\**\s*\n([\s\S]*)$/i);
  const body = m ? text.slice(0, m.index).trim() : text.trim();
  const urls = [...new Set(((m ? m[1] : text).match(/https?:\/\/[^\s)\]>"']+/g) ?? []).map((u) => u.replace(/[.,;]+$/, "")))];
  return { answer: body, sources: urls };
}

/** The answering model: the modelUsage entry matching the requested alias; other entries are web-tool helper models. */
function actualModel(json) {
  const keys = Object.keys(json?.modelUsage ?? {});
  if (!keys.length) return {};
  return { actualModelId: keys.find((k) => k.includes(model)) ?? keys[0], modelUsageIds: keys };
}

const t0 = performance.now();
let first = true, n = 0;
for (const q of questions) {
  if (done.has(q.id)) continue;
  if (limit && n >= limit) break;
  if (chunkMs && performance.now() - t0 > chunkMs) { console.log("chunk time budget reached; rerun to resume"); break; }
  if ((priorFails.get(q.id) ?? 0) >= 2) { console.error(`ABORT: ${q.id} already failed twice (see failures.jsonl); not retrying.`); process.exit(4); }
  if (!first) await sleep(gapMs);
  first = false;
  n++;

  let r, startedAt;
  for (let attempt = 1; attempt <= 2; attempt++) {
    startedAt = new Date().toISOString();
    r = await runClaude({ prompt: q.question, systemPrompt, model, tools: TOOLS, timeoutMs: CALL_TIMEOUT_MS });
    logSpend(SPEND, "bench-reference:boar-eval-v0.2", r);
    const text = r.json?.result ?? "";
    if (r.ok && splitSources(text).answer.length > 0) break;
    appendFileSync(FAILS, JSON.stringify({ id: q.id, attempt, at: new Date().toISOString(), error: r.error, stderr: (r.stderr ?? "").slice(0, 500), rateLimited: isRateLimited(r) }) + "\n");
    if (isRateLimited(r)) { console.error(`RATE LIMITED at ${q.id}: ${r.error ?? r.stderr}. Stopping; rerun resumes from here.`); process.exit(3); }
    if (attempt === 2) { console.error(`FAIL twice at ${q.id}: ${r.error}. Stopping; inspect failures.jsonl.`); process.exit(4); }
    console.error(`FAIL at ${q.id}: ${r.error}. Retrying once in ${RETRY_WAIT_MS / 1000}s.`);
    await sleep(RETRY_WAIT_MS);
  }

  const text = r.json?.result ?? "";
  const { answer, sources } = splitSources(text);
  const row = {
    id: q.id,
    category: q.category,
    lang: q.lang,
    question: q.question,
    ok: true,
    answer,
    sources,
    rawResult: text,
    wallMs: Math.round(r.wallMs),
    ...(r.json ? usageSummary(r.json) : {}),
    ...actualModel(r.json),
    webSearches: r.toolCalls.filter((c) => c.name === "WebSearch").map((c) => c.input?.query),
    webFetches: r.toolCalls.filter((c) => c.name === "WebFetch").map((c) => c.input?.url),
    requestedModel: model,
    tools: TOOLS,
    via: "claude-code (claude -p, cleanEnv: no API key)",
    promptVersion: PROMPT_VERSION,
    promptFile: PROMPT_FILE,
    promptSha256,
    promptSha: promptSha256.slice(0, 12),
    cliVersion,
    questionsSha256: QUESTIONS_SHA256,
    startedAt,
    generatedAt: new Date().toISOString(),
  };
  appendFileSync(out, JSON.stringify(row) + "\n");
  console.log(`${q.id} ok wall=${(row.wallMs / 1000).toFixed(1)}s search=${row.webSearches.length} fetch=${row.webFetches.length} out=${row.outputTokens ?? "?"}tok model=${row.actualModelId}`);
}
const okNow = new Set(readJsonl(out).filter((r) => r.ok && r.question === qText.get(r.id)).map((r) => r.id));
console.log(`progress ${all.filter((q) => okNow.has(q.id)).length}/${all.length} new items ok in ${out}; this chunk ${((performance.now() - t0) / 1000).toFixed(0)}s`);
