#!/usr/bin/env node
// Calibration anchors: Claude models answering bench items from memory (NO tools, NO web) as systems under test, so a
// BOAR quality ratio can be read against "frontier model without web". Same recipe as the frozen Opus+web references
// (bench/v0.1/refs/gen_refs.mjs: claude -p on the subscription via the vendored eval-lib runClaude, user prompt = the
// bare question, system prompt reference.v1) with the web removed: system prompt anchor.v1 = reference.v1 minus its
// three web lines ("with web search", "Search the web…", "End with a line Sources:…"), tools []. The only differences
// vs the reference are web access and the model. One answer per item per model, written as EvalTrace v1
// (runtime.adapter "reference-cli", config.device null) so harness/judge.mjs judges it exactly like a BOAR run.
// Item set = judge.mjs's: venue-list items excluded, items without an ok reference excluded.
// Resumable (done = items already in --out without error); rate limit -> stop (exit 3); other error -> stop (exit 4).
//
// Usage: node harness/anchors.mjs --model haiku [--bench bench/v0.1] [--out runs/anchors-2026-10-02/haiku.traces.jsonl]
//          [--ids a,b] [--limit N] [--gap-ms 5000]
import { appendFileSync, existsSync, mkdirSync, readFileSync } from "node:fs";
import { createHash } from "node:crypto";
import { execFileSync } from "node:child_process";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const HERE = dirname(fileURLToPath(import.meta.url));
const REPO = join(HERE, "..");
const LIB = process.env.BOAR_EVAL_LIB ?? join(REPO, "scorers", "vendor", "eval-lib");
const { cleanEnv, isRateLimited, logSpend, runClaude, sleep, totalSpend, usageSummary } = await import(join(LIB, "claude-cli.mjs"));

export const PROMPT_VERSION = "anchor.v1";
/** reference.v1 (sha256 d5144343…, prompts/reference.v1.md) minus the web lines. */
export const ANCHOR_SYSTEM = `You are a research assistant. Answer the user's question accurately and completely, the way an expert would explain it to a curious traveler or student.

Rules:
- Answer in the same language as the question.
- Keep the answer under 250 words. Lead with the direct answer, then the key supporting points.
- For first-aid or safety questions, give the standard recommended steps and say when to seek professional help.
- If the question has a false premise or no single answer, say so.
`;
// A refusal = the answer gives up on the question (not a "false premise" correction). Hand-checked in the report.
const REFUSAL = /\b(I (?:can(?:no|')t|am unable to|'m unable to|don't have (?:reliable |enough |specific |access|up-to-date|current|real-time))|I do not have (?:reliable|access|current|real-time))/i;

const a = process.argv.slice(2);
const get = (k, d) => (a.includes(k) ? a[a.indexOf(k) + 1] : d);
const model = get("--model");
if (!model) throw new Error("--model is required (haiku | sonnet | opus | fable)");
const benchDir = resolve(get("--bench", join(REPO, "bench", "v0.1")));
const out = resolve(get("--out", join(REPO, "runs", "anchors-2026-10-02", `${model}.traces.jsonl`)));
const limit = Number(get("--limit", "0")); const gapMs = Number(get("--gap-ms", "5000"));
const onlyIds = get("--ids") ? new Set(get("--ids").split(",")) : null;
const readJsonl = (p) => (existsSync(p) ? readFileSync(p, "utf8").split("\n").filter((l) => l.trim()).map((l) => JSON.parse(l)) : []);
const sha = (s) => createHash("sha256").update(s).digest("hex");

const man = JSON.parse(readFileSync(join(benchDir, "bench.json"), "utf8"));
const questions = readJsonl(join(benchDir, man.questions ?? "questions.public.jsonl"));
const refOk = new Set(readJsonl(join(benchDir, man.refs ?? "refs/refs.jsonl")).filter((r) => r.ok).map((r) => r.id));
const items = questions.filter((q) => q.grading?.type !== "venue-list" && refOk.has(q.id) && (!onlyIds || onlyIds.has(q.id)));

mkdirSync(dirname(out), { recursive: true });
const SPEND = join(dirname(out), "spend.jsonl");
const done = new Set(readJsonl(out).filter((t) => !t.error).map((t) => t.itemId));
const todo = items.filter((q) => !done.has(q.id));
console.log(`anchors ${model}: ${items.length} items, ${todo.length} to do -> ${out}`);

/** Same post-processing as the references (gen_refs.mjs splitSources): a trailing "Sources:" block is cut off. */
function splitSources(text) {
  const m = text.match(/\n\**Sources:?\**\s*\n([\s\S]*)$/i);
  return m ? text.slice(0, m.index).trim() : text.trim();
}

const cliVersion = execFileSync("claude", ["--version"], { env: cleanEnv(), encoding: "utf8" }).trim();
const promptSha = sha(ANCHOR_SYSTEM);
const runId = `anchors-2026-10-02-${model}`;
let n = 0;
for (const q of todo) {
  if (limit && n >= limit) { console.log(`limit ${limit} reached`); break; }
  if (n++) await sleep(gapMs);
  const startedAt = new Date().toISOString();
  const r = await runClaude({ prompt: q.question, systemPrompt: ANCHOR_SYSTEM, model, tools: [], timeoutMs: 300_000 });
  logSpend(SPEND, `boar-eval-anchor:${model}`, r);
  if (isRateLimited(r)) { console.error(`RATE LIMITED at ${q.id}: ${r.error ?? r.stderr}. Stopped; rerun resumes.`); process.exit(3); }
  const raw = r.json?.result ?? "";
  const text = splitSources(raw);
  if (!r.ok || !text) { console.error(`API ERROR at ${q.id}: ${r.error ?? "empty answer"}. Stopped (no retry); rerun resumes.`); process.exit(4); }
  if (r.toolCalls.length) { console.error(`TOOL CALL at ${q.id} (${r.toolCalls.map((c) => c.name)}): tools must be off. Stopped.`); process.exit(5); }
  const usage = usageSummary(r.json);
  const resolved = Object.keys(r.json.modelUsage ?? {}).find((k) => k.includes(model)) ?? usage.modelId;
  const trace = {
    protocol: "1.0.0", runId, itemId: q.id, question: q.question,
    engine: { commit: "n/a-anchor", arm: `anchor-${model}`, dirty: false },
    runtime: { adapter: "reference-cli", host: "claude-code-subscription (claude -p, cleanEnv: no API key)", model: resolved, sampler: {},
               versions: { "claude-code": cliVersion, prompt: PROMPT_VERSION, promptSha256: promptSha, requestedModel: model, tools: "none" } },
    config: { commit: "n/a-anchor", arm: `anchor-${model}`, modelId: resolved, settings: { promptVersion: PROMPT_VERSION, tools: [], web: false }, kit: [], device: null },
    route: { task: null, tier: null, outcome: "answered", reasonCodes: [] },
    retrieval: { raw: [], kept: [], dropped: [] },
    answer: { text, cited: [], shown: [], declined: REFUSAL.test(text.slice(0, 300)), weakSources: false, warnings: text === raw.trim() ? [] : ["sources-block-stripped"] },
    timing: { ttftMs: null, totalMs: null, retrievalMs: null, prefillMs: null, decodeTokPerSec: null, promptTokens: null, outputTokens: null },
    resources: null,
    events: [{ tMs: 0, type: "other", kind: "anchor-usage", startedAt, wallMs: Math.round(r.wallMs), modelUsageIds: Object.keys(r.json.modelUsage ?? {}), ...usage }],
    error: null,
    createdAt: new Date().toISOString(),
  };
  appendFileSync(out, JSON.stringify(trace) + "\n");
  console.log(`${q.id} ok ${resolved} out=${usage.outputTokens}tok ${(r.wallMs / 1000).toFixed(1)}s declined=${trace.answer.declined} listUsd=${usage.listPriceEquivalentUsd?.toFixed(4)}`);
}
const now = new Set(readJsonl(out).filter((t) => !t.error).map((t) => t.itemId));
console.log(`progress ${items.filter((q) => now.has(q.id)).length}/${items.length}; cumulative list-price equivalent ${totalSpend(SPEND).toFixed(2)} USD (${SPEND}; subscription, not a charge)`);
