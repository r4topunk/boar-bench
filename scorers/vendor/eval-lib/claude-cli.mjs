// Runs `claude -p` headless on the user's own Claude Code CLI login (no API key, no gateway).
// Isolation: empty temp cwd, no settings sources, no MCP, no session persistence, fixed system prompt.
import { spawn } from "node:child_process";
import { appendFileSync, existsSync, mkdtempSync, readFileSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

// Env vars that would route calls to a paid API or tie the child to the parent session.
const STRIP_ENV = /^(ANTHROPIC_API_KEY|ANTHROPIC_AUTH_TOKEN|ANTHROPIC_BASE_URL|AI_GATEWAY_API_KEY|OPENAI_API_KEY|CLAUDE_CODE_(SESSION_ID|CHILD_SESSION|MESSAGING_SOCKET|MESSAGING_TOKEN|ENTRYPOINT|SESSION_ATTENDED|USE_BEDROCK|USE_VERTEX))$/;

export function cleanEnv() {
  return Object.fromEntries(Object.entries(process.env).filter(([k]) => !STRIP_ENV.test(k)));
}

/**
 * @param {{ prompt: string, systemPrompt: string, model: string, tools: string[], jsonSchema?: object, timeoutMs?: number, maxBudgetUsd?: number, effort?: string }} o
 * @returns {Promise<{ ok: boolean, json?: any, toolCalls: Array<{ name: string, input: any }>, stderr: string, wallMs: number, error?: string }>}
 */
export function runClaude({ prompt, systemPrompt, model, tools, jsonSchema, timeoutMs = 300_000, maxBudgetUsd = 1, effort }) {
  const cwd = mkdtempSync(join(tmpdir(), "boar-eval-claude-"));
  const toolList = tools.join(",");
  const argv = [
    "-p", prompt,
    "--model", model,
    ...(effort ? ["--effort", effort] : []),
    "--system-prompt", systemPrompt,
    "--tools", toolList,
    ...(tools.length ? ["--allowedTools", toolList] : []),
    "--setting-sources", "",
    "--strict-mcp-config",
    "--no-session-persistence",
    "--max-budget-usd", String(maxBudgetUsd),
    ...(jsonSchema ? ["--json-schema", JSON.stringify(jsonSchema)] : []),
    "--output-format", "stream-json",
    "--verbose",
  ];
  const start = performance.now();
  return new Promise((resolve) => {
    const child = spawn("claude", argv, { cwd, env: cleanEnv(), stdio: ["ignore", "pipe", "pipe"] });
    let out = "", err = "";
    child.stdout.on("data", (d) => (out += d));
    child.stderr.on("data", (d) => (err += d));
    const timer = setTimeout(() => child.kill("SIGTERM"), timeoutMs);
    child.on("close", (code) => {
      clearTimeout(timer);
      rmSync(cwd, { recursive: true, force: true });
      const wallMs = performance.now() - start;
      const events = out.split("\n").filter(Boolean).flatMap((l) => { try { return [JSON.parse(l)]; } catch { return []; } });
      const json = events.findLast((e) => e.type === "result");
      // WebSearch/WebFetch run client-side in Claude Code, so usage.server_tool_use stays 0; count tool_use blocks instead.
      const toolCalls = events
        .filter((e) => e.type === "assistant")
        .flatMap((e) => e.message?.content ?? [])
        .filter((c) => c.type === "tool_use")
        .map((c) => ({ name: c.name, input: c.input }));
      if (!json) return resolve({ ok: false, toolCalls, stderr: err, wallMs, error: `exit ${code}: ${(err || out).slice(0, 500)}` });
      resolve({ ok: code === 0 && !json.is_error, json, toolCalls, stderr: err, wallMs, error: json.is_error ? String(json.result ?? json.subtype) : undefined });
    });
  });
}

/** Usage summary kept per item: tokens, tool calls and the CLI's reported call usage. */
export function usageSummary(json) {
  const [modelId, mu] = Object.entries(json.modelUsage ?? {})[0] ?? [];
  return {
    modelId,
    inputTokens: json.usage?.input_tokens,
    cacheReadTokens: json.usage?.cache_read_input_tokens,
    cacheCreationTokens: json.usage?.cache_creation_input_tokens,
    outputTokens: json.usage?.output_tokens,
    thinkingTokens: json.usage?.output_tokens_details?.thinking_tokens,
    numTurns: json.num_turns,
    durationMs: json.duration_ms,
    durationApiMs: json.duration_api_ms,
    listPriceEquivalentUsd: json.total_cost_usd,
    costBasis: mu?.costBasis,
  };
}

// Stop signals: a rate/usage limit ends the run (no retry loop).
export const isRateLimited = (r) => /rate.?limit|usage limit|429|overloaded|too many requests/i.test(`${r.error ?? ""} ${r.stderr ?? ""} ${r.json?.api_error_status ?? ""}`);

export const sleep = (ms) => new Promise((res) => setTimeout(res, ms));

/** Appends one consumption row to results/spend.jsonl (call usage ledger). */
export function logSpend(file, purpose, r) {
  if (!r.json) return;
  const u = usageSummary(r.json);
  appendFileSync(file, JSON.stringify({ at: new Date().toISOString(), purpose, via: "claude-code", model: u.modelId, listPriceEquivalentUsd: u.listPriceEquivalentUsd, costBasis: u.costBasis, inputTokens: u.inputTokens, cacheReadTokens: u.cacheReadTokens, cacheCreationTokens: u.cacheCreationTokens, outputTokens: u.outputTokens, durationMs: u.durationMs }) + "\n");
}

export function totalSpend(file) {
  if (!existsSync(file)) return 0;
  return readFileSync(file, "utf8").trim().split("\n").filter(Boolean).reduce((a, l) => a + (JSON.parse(l).listPriceEquivalentUsd ?? 0), 0);
}
