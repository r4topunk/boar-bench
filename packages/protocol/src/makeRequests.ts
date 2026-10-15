/**
 * Build EvalRequest jsonl from a questions jsonl and a run config.
 *
 *   pnpm -C packages/protocol exec tsx src/makeRequests.ts --questions q.jsonl --config cfg.json --run-id ID > requests.jsonl
 *
 * questions.jsonl: one `{ id, question, lang?, context? }` per line; other fields are ignored.
 *   A multi-turn item gives `turns: [{role, text}, …]` instead of `question` (chat-slice format): the last turn (a user
 *   turn) becomes `question`, the earlier ones `history.turns`. A one-turn `turns` is a plain single-turn item.
 *   Lines with `duplicate_of` are skipped unless --keep-duplicates (bench files mark repeated items that way).
 * cfg.json: an EngineConfig plus `seed` (default 42) and an optional `temperature` (0 = greedy gate mode):
 *   { "commit": "0cfd4a77", "arm": "main", "modelId": "qwen2.5-1.5b-instruct-q4km",
 *     "settings": { "quickFirst": true, "alwaysComplete": false },
 *     "kit": [{ "id": "boar-crypto", "sha256": "…" }], "device": { "platform": "ios", "ramGb": 4 },
 *     "seed": 42, "temperature": 0 }
 * Every line written is EvalRequest.parse()d; a bad question or config fails the whole build (nothing partial).
 */
import { readFileSync } from "node:fs";
import { pathToFileURL } from "node:url";
import { z } from "zod";
import { EngineConfig, EvalItem, EvalRequest, PROTOCOL_VERSION } from "./index";

export const RunConfig = EngineConfig.extend({
  seed: z.number().int().default(42),
  temperature: z.number().min(0).optional(),
});
export type RunConfig = z.infer<typeof RunConfig>;

export interface MakeOptions {
  runId: string;
  keepDuplicates?: boolean;
}

/** Parses questions jsonl text (blank lines ignored) and returns validated requests, in file order. */
export function makeRequests(questionsJsonl: string, config: unknown, opts: MakeOptions): EvalRequest[] {
  if (!opts.runId) throw new Error("runId is required");
  const cfg = RunConfig.parse(config);
  const { seed, temperature, ...engine } = cfg;
  const seen = new Set<string>();
  const out: EvalRequest[] = [];
  questionsJsonl.split("\n").forEach((line, i) => {
    if (!line.trim()) return;
    let raw: Record<string, unknown>;
    try {
      raw = JSON.parse(line);
    } catch (e) {
      throw new Error(`questions line ${i + 1}: invalid JSON (${(e as Error).message})`);
    }
    if (raw.duplicate_of && !opts.keepDuplicates) return;
    // Dataset files use BCP-47 tags ("pt-BR", "en-US"); the protocol keeps the base language.
    const lang = typeof raw.lang === "string" ? raw.lang.toLowerCase().split(/[-_]/)[0] : raw.lang;
    const { question, history } = splitTurns(raw, i);
    const parsed = EvalItem.safeParse({ id: raw.id, question, lang, context: raw.context, history });
    if (!parsed.success) throw new Error(`questions line ${i + 1}: ${parsed.error.issues.map((x) => `${x.path.join(".")}: ${x.message}`).join("; ")}`);
    if (seen.has(parsed.data.id)) throw new Error(`questions line ${i + 1}: duplicate id ${parsed.data.id}`);
    seen.add(parsed.data.id);
    out.push(
      EvalRequest.parse({
        protocol: PROTOCOL_VERSION,
        runId: opts.runId,
        item: parsed.data,
        config: engine,
        seed,
        ...(temperature !== undefined ? { temperature } : {}),
      })
    );
  });
  if (!out.length) throw new Error("no questions");
  return out;
}

/** `question` as given, or a `turns` list split into the message (last turn, must be the user's) and its history. */
function splitTurns(raw: Record<string, unknown>, i: number): { question: unknown; history?: { turns: unknown[] } } {
  if (raw.turns === undefined) return { question: raw.question };
  if (raw.question !== undefined) throw new Error(`questions line ${i + 1}: give question or turns, not both`);
  const turns = raw.turns as { role?: unknown; text?: unknown }[];
  if (!Array.isArray(turns) || !turns.length) throw new Error(`questions line ${i + 1}: turns must be a non-empty array`);
  const last = turns[turns.length - 1];
  if (last?.role !== "user") throw new Error(`questions line ${i + 1}: the last turn must be a user turn`);
  const earlier = turns.slice(0, -1).map((t) => ({ role: t.role, text: t.text }));
  return { question: last.text, ...(earlier.length ? { history: { turns: earlier } } : {}) };
}

function cli(argv: string[]) {
  const get = (k: string) => (argv.includes(k) ? argv[argv.indexOf(k) + 1] : undefined);
  const questions = get("--questions");
  const config = get("--config");
  const runId = get("--run-id");
  if (!questions || !config || !runId) {
    process.stderr.write("usage: tsx src/makeRequests.ts --questions q.jsonl --config cfg.json --run-id ID [--keep-duplicates] > requests.jsonl\n");
    process.exit(2);
  }
  const reqs = makeRequests(readFileSync(questions, "utf8"), JSON.parse(readFileSync(config, "utf8")), {
    runId,
    keepDuplicates: argv.includes("--keep-duplicates"),
  });
  process.stdout.write(reqs.map((r) => JSON.stringify(r)).join("\n") + "\n");
  process.stderr.write(`${reqs.length} requests (runId ${runId}, commit ${reqs[0].config.commit}, arm ${reqs[0].config.arm})\n`);
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  try {
    cli(process.argv.slice(2));
  } catch (e) {
    process.stderr.write(`makeRequests: ${(e as Error).message}\n`);
    process.exit(1);
  }
}
