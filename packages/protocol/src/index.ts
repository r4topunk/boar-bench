/**
 * boar-eval protocol v1: the only contract between the harness and a runtime adapter
 * (desktop-node, ios-app, android-app). See docs/ADR-001-engine-eval-harness.md.
 *
 * An adapter receives EvalRequest lines, runs the engine's real answer pipeline, and
 * writes one EvalTrace line per item. Everything downstream (scorers, report, diff,
 * gate) reads EvalTrace only, never adapter-specific rows.
 */
import { z } from "zod";

export const PROTOCOL_VERSION = "1.0.0";

export const PackRef = z.object({
  id: z.string(),
  sha256: z.string().regex(/^[0-9a-f]{64}$/),
});

/** One earlier chat message, as the engine's ConversationTurn (src/rag/pure.ts). */
export const ConversationTurn = z.object({ role: z.enum(["user", "assistant"]), text: z.string() });

export const EvalItem = z.object({
  id: z.string(),
  /** The message being answered (a multi-turn item's last user turn). */
  question: z.string().min(1),
  lang: z.enum(["en", "pt", "es"]).default("en"),
  /** Simulated device context, e.g. a GPS fix for "near me" items. */
  context: z.object({ lat: z.number(), lon: z.number() }).partial().optional(),
  /** Earlier turns of a multi-turn item, oldest first; passed as the engine's AnswerContext.history. Absent = single turn. */
  history: z.object({ turns: z.array(ConversationTurn).min(1) }).optional(),
});

export const EngineConfig = z.object({
  /** Full or abbreviated git sha of the engine under test. */
  commit: z.string().min(7),
  /** Label of an A/B arm, e.g. "main", "main+46". */
  arm: z.string().default("main"),
  modelId: z.string(),
  /** The engine's answer settings, as the app would pass them. */
  settings: z.record(z.string(), z.unknown()).default({}),
  kit: z.array(PackRef).default([]),
  device: z.object({ platform: z.enum(["ios", "android"]), ramGb: z.number().positive() }),
});

export const EvalRequest = z.object({
  protocol: z.literal(PROTOCOL_VERSION),
  runId: z.string(),
  item: EvalItem,
  config: EngineConfig,
  seed: z.number().int().default(42),
  /** Overrides every generation's temperature (0 = greedy, deterministic gate mode). */
  temperature: z.number().min(0).optional(),
});

/** The engine's own emit() events, carried unchanged (extra fields allowed). */
export const EvalEvent = z
  .object({
    tMs: z.number().nonnegative(),
    type: z.enum(["route", "retrieve", "sources", "token", "instant", "warning", "done", "other"]),
  })
  .passthrough();

export const SourceRef = z.object({
  title: z.string(),
  section: z.string().nullable().default(null),
  source: z.string().nullable().default(null),
  similarity: z.number().nullable().default(null),
});

export const EvalTrace = z.object({
  protocol: z.literal(PROTOCOL_VERSION),
  runId: z.string(),
  itemId: z.string(),
  question: z.string(),
  engine: z.object({ commit: z.string(), arm: z.string(), dirty: z.boolean().default(false) }),
  runtime: z.object({
    /** "reference-cli": optional extension for calibration anchors (claude -p, no tools; harness/anchors.mjs), not an engine run. */
    adapter: z.enum(["desktop-node", "ios-app", "android-app", "reference-cli"]),
    /** e.g. "Apple M4 cpu x4", "iPhone14,5 iOS 26.6.2" */
    host: z.string(),
    model: z.string(),
    sampler: z.object({ temperature: z.number(), seed: z.number().int() }).partial(),
    /** Versions of the native runtime pieces (node-llama-cpp 3.21.1, llama.rn 0.13.0-rc.6…). */
    versions: z.record(z.string(), z.string()).default({}),
    loadAvg1m: z.number().optional(),
    /** Generation backend when not the adapter's default (desktop-node: "llama-server"). */
    backend: z.string().optional(),
  }),
  /** Requests always carry a device; a trace may say null = no device (reference-cli anchor answering from memory). */
  config: EngineConfig.extend({ device: EngineConfig.shape.device.nullable() }),
  route: z.object({
    task: z.string().nullable(),
    tier: z.string().nullable(),
    outcome: z.string().nullable(),
    reasonCodes: z.array(z.string()),
    /** Hidden reasoning went past the item's thinking budget (the app would have forced the end tag): not app-faithful. */
    thinkingBudgetExceeded: z.boolean().optional(),
    /** Always-complete configs (desktop-node): "multipass" when the engine ran its multi-pass Deep Research, else "single". */
    mode: z.enum(["single", "multipass"]).optional(),
  }),
  retrieval: z.object({
    /** What the retriever returned, before the engine's gates and filters. */
    raw: z.array(SourceRef),
    /** What survived into the answer's sources. */
    kept: z.array(SourceRef),
    /** raw minus kept, by title + section. Makes source losses visible. */
    dropped: z.array(SourceRef),
  }),
  answer: z.object({
    text: z.string(),
    /** Titles the final text cites ([n] markers resolved). */
    cited: z.array(z.string()),
    /** Titles the chat shows under the answer. */
    shown: z.array(z.string()),
    declined: z.boolean(),
    weakSources: z.boolean(),
    warnings: z.array(z.string()).default([]),
  }),
  timing: z.object({
    ttftMs: z.number().nullable(),
    totalMs: z.number().nullable(),
    retrievalMs: z.number().nullable(),
    prefillMs: z.number().nullable(),
    decodeTokPerSec: z.number().nullable(),
    promptTokens: z.number().nullable(),
    outputTokens: z.number().nullable(),
    /** First non-blank VISIBLE text since the answer started (hidden reasoning excluded). Optional: backends that split it. */
    firstVisibleMs: z.number().nullable().optional(),
    /** Hidden reasoning time before that visible text (0 = none). */
    reasoningMs: z.number().nullable().optional(),
    /** Hidden reasoning tokens over the answer's generations. */
    reasoningTokens: z.number().nullable().optional(),
    /** Retrieval outside retrievalMs (the first search): follow-up searches (DEEPITER) or multi-pass sub-question searches. */
    retrievalMs2: z.number().nullable().optional(),
  }),
  /** Device adapters; desktop-node only with --backend server (llama-server's peak RSS, a desktop number, not a phone one). */
  resources: z.object({ peakRssMb: z.number().nullable(), thermal: z.string().nullable(), sustainedRatio: z.number().nullable() }).nullable().default(null),
  events: z.array(EvalEvent).default([]),
  error: z.object({ code: z.string(), message: z.string() }).nullable().default(null),
  createdAt: z.string(),
});

export type EvalRequest = z.infer<typeof EvalRequest>;
export type EvalTrace = z.infer<typeof EvalTrace>;
export type EvalEvent = z.infer<typeof EvalEvent>;
