/**
 * Pure helpers that turn what the engine did (emit() events, retrieve() calls, the AnswerResult) into EvalTrace
 * pieces. No engine, node-llama-cpp or file-system imports: unit-tested on the MacBook (trace.test.ts) and imported
 * by adapter.ts on the mini.
 */

/** The parts of a RetrievedChunk / SourceChunk a trace keeps (never the passage text). */
export interface ChunkLike {
  title?: unknown;
  section?: unknown;
  source?: unknown;
  similarity?: unknown;
  relevance?: unknown;
}

export interface SourceRef {
  title: string;
  section: string | null;
  source: string | null;
  similarity: number | null;
}

const str = (v: unknown): string | null => (typeof v === "string" && v.length ? v : null);
const num = (v: unknown): number | null => (typeof v === "number" && Number.isFinite(v) ? v : null);

export function sourceRef(c: ChunkLike): SourceRef {
  return { title: String(c.title ?? ""), section: str(c.section), source: str(c.source), similarity: num(c.similarity) };
}

/** Identity of a source for raw/kept/dropped: title + section (the engine dedupes passages the same way). */
export const sourceKey = (s: { title: string; section: string | null }) => `${s.title}\u0000${s.section ?? ""}`;

/** raw − kept, by title + section. */
export function droppedOf(raw: SourceRef[], kept: SourceRef[]): SourceRef[] {
  const k = new Set(kept.map(sourceKey));
  return raw.filter((r) => !k.has(sourceKey(r)));
}

/** "task:research" -> "research". */
export function taskOf(reasonCodes: string[]): string | null {
  const c = reasonCodes.find((x) => x.startsWith("task:"));
  return c ? c.slice("task:".length) : null;
}

export type ProtocolEventType = "route" | "retrieve" | "sources" | "token" | "instant" | "warning" | "done" | "other";
export interface TraceEvent {
  tMs: number;
  type: ProtocolEventType;
  [k: string]: unknown;
}

const CARRIED = new Set(["sources", "token", "instant", "warning", "done"]);

/**
 * One engine AnswerEvent -> one protocol event, carried as is except:
 * - `answerId` (wall-clock based) and `at` (absolute performance.now()) are dropped: `tMs` replaces them;
 * - event types outside the protocol enum (stage, location, places, deep_available) become `type: "other"` with
 *   `kind: <engine type>`;
 * - source lists keep { title, section, source, similarity, relevance } per source, not the passage text (unless
 *   sourceText: then `text` = the passage body as the engine placed it, after compression).
 */
export function mapEvent(e: Record<string, unknown>, tMs: number, sourceText = false): TraceEvent {
  const { answerId: _id, at: _at, type, ...rest } = e;
  const t = String(type);
  const out: TraceEvent = CARRIED.has(t) ? { tMs, type: t as ProtocolEventType, ...rest } : { tMs, type: "other", kind: t, ...rest };
  if (Array.isArray(rest.sources)) {
    out.sources = (rest.sources as (ChunkLike & { body?: unknown })[]).map((c) => ({
      ...sourceRef(c),
      ...(num(c.relevance) !== null ? { relevance: num(c.relevance) } : {}),
      // --event-source-text: the passage as placed in the prompt (after compression), for exact key-in-context.
      ...(sourceText && typeof c.body === "string" ? { text: c.body } : {}),
    }));
  }
  return out;
}

/**
 * Caps token events: above `max`, keeps the first max/2 and the last max/2 and puts one
 * `{ type: "other", kind: "tokens-elided", count, chars }` where the elided run was. Text is never lost from the trace:
 * `answer.text` holds the final text. max <= 0 disables the cap.
 */
export function capTokenEvents(events: TraceEvent[], max: number): TraceEvent[] {
  const tokenIdx = events.flatMap((e, i) => (e.type === "token" ? [i] : []));
  if (max <= 0 || tokenIdx.length <= max) return events;
  const head = Math.ceil(max / 2);
  const tail = Math.floor(max / 2);
  const elided = new Set(tokenIdx.slice(head, tokenIdx.length - tail));
  const out: TraceEvent[] = [];
  let marker: TraceEvent | null = null;
  for (let i = 0; i < events.length; i++) {
    const e = events[i];
    if (!elided.has(i)) {
      out.push(e);
      continue;
    }
    if (!marker) {
      marker = { tMs: e.tMs, type: "other", kind: "tokens-elided", count: 0, chars: 0 };
      out.push(marker);
    }
    (marker.count as number)++;
    (marker.chars as number) += typeof e.text === "string" ? e.text.length : 0;
  }
  return out;
}

/** Warning events -> "code" or "code:declined". */
export function warningCodes(events: TraceEvent[]): string[] {
  return events.filter((e) => e.type === "warning").map((e) => `${String(e.code)}${e.declined ? ":declined" : ""}`);
}

/** Titles the chat shows under the answer: the last `sources` event (kept on a decline, as exp-06's shownSources). */
export function shownTitles(events: TraceEvent[]): string[] {
  const last = [...events].reverse().find((e) => e.type === "sources" && Array.isArray(e.sources));
  return last ? (last.sources as SourceRef[]).map((s) => s.title) : [];
}

/** [n] numbers of the done event -> titles of the answer's final sources. */
export function citedTitles(cited: number[] | undefined, kept: SourceRef[]): string[] {
  return (cited ?? []).map((i) => kept[i - 1]?.title).filter((t): t is string => !!t);
}

export const round1 = (n: number) => Math.round(n * 10) / 10;

/**
 * The engine's AnswerContext for one item: a multi-turn item's earlier turns go in as `history` (summary null, turns
 * verbatim, as ChatScreen sends them before a chat is long enough to summarise); a single-turn item gets `ctx` unchanged.
 */
export function answerContext<C extends object>(ctx: C, item: { history?: { turns: { role: "user" | "assistant"; text: string }[] } }): C | (C & { history: { summary: null; turns: { role: "user" | "assistant"; text: string }[] } }) {
  return item.history ? { ...ctx, history: { summary: null, turns: item.history.turns.map((t) => ({ role: t.role, text: t.text })) } } : ctx;
}

/** "--shard i/N" → { i, n } (0 ≤ i < n). */
export function parseShard(s: string): { i: number; n: number } {
  const m = /^(\d+)\/(\d+)$/.exec(s);
  const i = m ? Number(m[1]) : NaN, n = m ? Number(m[2]) : NaN;
  if (!m || n < 1 || i >= n) throw new Error(`--shard must be i/N with 0 <= i < N, got ${s}`);
  return { i, n };
}

/** Latency fields of a trace's timing (counts such as promptTokens/outputTokens stay valid under parallel load). */
export const LATENCY_FIELDS = ["ttftMs", "totalMs", "retrievalMs", "prefillMs", "decodeTokPerSec", "firstVisibleMs", "reasoningMs", "retrievalMs2"] as const;

/**
 * Parallel mode: items share the CPU, so latency is not comparable. The latency fields become null (any latency reader
 * skips them) and the raw values go into one `other/timing-raw` event with `valid: false`, appended to `events`.
 */
export function invalidateTiming<T extends Record<string, unknown>>(timing: T, events: TraceEvent[]): T {
  const raw: Record<string, unknown> = {};
  const out: Record<string, unknown> = { ...timing };
  for (const k of LATENCY_FIELDS) if (k in timing) { raw[k] = timing[k]; out[k] = null; }
  events.push({ tMs: 0, type: "other", kind: "timing-raw", origin: "adapter", valid: false, ...raw });
  return out as T;
}
