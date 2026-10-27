/**
 * Pure pieces of the llama-server generation backend (`--backend server`): request bodies, SSE parsing, the
 * reasoning/content split, and the RSS sampler. No I/O here except through injected functions (unit-tested).
 * Spec: rnd/research/anvil/specs/adapter-llama-server-backend.md.
 */

/** The app's literal (src/inference/LlamaEngine.ts THINKING_BUDGET_MESSAGE, not exported there). */
export const THINKING_BUDGET_MESSAGE = "\nI have thought enough; answering now.\n";

export interface GenOpts {
  messages?: { role: string; content: string }[];
  prompt?: string;
  nPredict?: number;
  thinkingBudget?: number;
  enableThinking?: boolean;
  stop?: string[];
  temperature?: number;
}

/** Same arithmetic as the node path (and llama.rn's n_predict). */
export function maxTokensFor(o: GenOpts) {
  return (o.nPredict ?? 512) + (o.enableThinking === false ? 0 : o.thinkingBudget ?? 0);
}

/** Sampler identical to the node path: request override, else the engine's, else 0.7; top_k 40, top_p 0.95, min_p 0.05. */
export function samplerFor(o: GenOpts, temp: number | undefined, seed: number) {
  return { temperature: temp ?? o.temperature ?? 0.7, top_k: 40, top_p: 0.95, min_p: 0.05, seed, ...samplerOverride() };
}
/**
 * DEEPSAMP: BOAR_SAMPLER_JSON='{"temperature":1,"top_k":20,"min_p":0,"presence_penalty":1.5}' overrides sampler fields on
 * the server backend only (frozen arms never set it; an explicit per-item temperature 0 for health stays 0 unless overridden).
 * The adapter records the override in versions["sampler.override"].
 */
export function samplerOverride(): Record<string, number> {
  const raw = process.env.BOAR_SAMPLER_JSON;
  if (!raw) return {};
  const o = JSON.parse(raw) as Record<string, unknown>;
  const allowed = ["temperature", "top_k", "top_p", "min_p", "presence_penalty", "repetition_penalty", "frequency_penalty"];
  const out: Record<string, number> = {};
  for (const [k, v] of Object.entries(o)) { if (!allowed.includes(k) || typeof v !== "number") throw new Error(`BOAR_SAMPLER_JSON: bad field ${k}`); out[k] = v; }
  return out;
}

/** POST /v1/chat/completions body (o.messages) or POST /completion body (o.prompt). */
export function requestFor(o: GenOpts, temp: number | undefined, seed: number): { path: string; body: Record<string, unknown> } {
  const sampler = samplerFor(o, temp, seed);
  if (o.messages) {
    const budget = o.enableThinking !== false && o.thinkingBudget ? o.thinkingBudget : undefined;
    return {
      path: "/v1/chat/completions",
      body: {
        messages: o.messages,
        stream: true,
        max_tokens: maxTokensFor(o),
        ...sampler,
        cache_prompt: false,
        ...(o.stop ? { stop: o.stop } : {}),
        // b11010 enforces this per request (server-common.cpp: thinking_budget_tokens -> reasoning budget sampler) when
        // the template exposes thinking tags, forcing the end tag like llama.rn does. Otherwise only the flag catches it.
        ...(budget ? { thinking_budget_tokens: budget, reasoning_budget_message: THINKING_BUDGET_MESSAGE } : {}),
        ...(o.enableThinking === false ? { chat_template_kwargs: { enable_thinking: false } }
          // BOAR_THINK_KWARG=1 (GEMMATHINK): templates whose default is thinking OFF (Gemma 4) need the explicit kwarg to
          // think at all; Qwen3 templates default ON, so the frozen Qwen arms never set it (request bodies unchanged).
          : budget && process.env.BOAR_THINK_KWARG === "1" ? { chat_template_kwargs: { enable_thinking: true } } : {}),
      },
    };
  }
  return {
    path: "/completion",
    body: { prompt: o.prompt ?? "", stream: true, n_predict: maxTokensFor(o), ...sampler, cache_prompt: false,
            stop: o.stop ?? ["\nUser:", "\nQuestion:"] },
  };
}

/** Split an SSE buffer into complete `data:` payloads; `rest` is the trailing partial line. */
export function sseData(buf: string): { datas: string[]; rest: string } {
  const lines = buf.split("\n");
  const rest = lines.pop() ?? "";
  const datas: string[] = [];
  for (const raw of lines) {
    const line = raw.replace(/\r$/, "");
    if (line.startsWith("data:")) datas.push(line.slice(5).trimStart());
  }
  return { datas, rest };
}

export interface ServerTimings { promptTokens: number; promptMs: number; predictedTokens: number; predictedMs: number }

export interface StreamState {
  content: string;
  reasoning: string;
  /** reasoning_content chunks (llama-server streams one token per chunk, so ≈ tokens). */
  reasoningTokens: number;
  firstReasoningMs: number | null;
  /** First chunk whose visible content is not whitespace (the node path's firstTextMs). */
  firstTextMs: number | null;
  timings: ServerTimings | null;
  finishReason: string | null;
  done: boolean;
}

export const newStreamState = (): StreamState => ({
  content: "", reasoning: "", reasoningTokens: 0, firstReasoningMs: null, firstTextMs: null, timings: null, finishReason: null, done: false,
});

/**
 * Apply one SSE `data:` payload at time tMs. Chat chunks: choices[0].delta.{reasoning_content,content};
 * /completion chunks: {content, stop}. Visible text goes to onText; reasoning never does. Returns false on non-JSON.
 */
export function applyData(st: StreamState, data: string, tMs: number, onText?: (c: string) => void): boolean {
  if (data === "[DONE]") {
    st.done = true;
    return true;
  }
  let j: any;
  try {
    j = JSON.parse(data);
  } catch {
    return false;
  }
  if (j.error) throw new Error(`llama-server: ${j.error.message ?? JSON.stringify(j.error)}`);
  const choice = j.choices?.[0];
  const reasoning: string | undefined = choice?.delta?.reasoning_content ?? undefined;
  const content: string | undefined = choice ? choice.delta?.content ?? undefined : typeof j.content === "string" ? j.content : undefined;
  if (reasoning) {
    if (st.firstReasoningMs === null) st.firstReasoningMs = tMs;
    st.reasoning += reasoning;
    st.reasoningTokens++;
  }
  if (content) {
    if (st.firstTextMs === null && content.trim() !== "") st.firstTextMs = tMs;
    st.content += content;
    onText?.(content);
  }
  if (choice?.finish_reason) st.finishReason = choice.finish_reason;
  if (j.stop === true) st.done = true;
  const t = j.timings;
  if (t && typeof t.prompt_n === "number") {
    st.timings = { promptTokens: t.prompt_n, promptMs: t.prompt_ms, predictedTokens: t.predicted_n, predictedMs: t.predicted_ms };
  }
  return true;
}

/** Reasoning beyond the per-item budget = the item is not app-faithful (the app forces the end tag at the budget). */
export function budgetExceeded(reasoningTokens: number, budget: number | undefined, enableThinking: boolean | undefined) {
  return enableThinking !== false && !!budget && reasoningTokens > budget;
}

/** `llama-server --version` output -> "4bc272f (0.4.1-dev build 1)", prefixed by a git tag when known. */
export function serverVersion(versionText: string, tag?: string | null) {
  const m = /version:\s*(\S+)\s*\(build\s*(\d+),\s*commit\s*([0-9a-f]+)\)/.exec(versionText);
  if (!m) return versionText.trim().split("\n").pop() ?? "unknown";
  return `${tag ? `${tag} ` : ""}(${m[3]}; ${m[1]} build ${m[2]})`;
}

/**
 * Peak RSS of a process, sampled every intervalMs while started (ps -o rss= -p <pid>, KiB). readRssKb and the timer
 * functions are injected so the sampler is testable without a process.
 */
export function rssSampler(
  readRssKb: () => Promise<number | null>,
  intervalMs = 250,
  timers: { set: (f: () => void, ms: number) => unknown; clear: (h: unknown) => void } = {
    set: (f, ms) => setInterval(f, ms),
    clear: (h) => clearInterval(h as NodeJS.Timeout),
  },
) {
  let handle: unknown = null;
  let windowPeakKb = 0;
  let runPeakKb = 0;
  let inflight: Promise<void> | null = null;
  const sample = () => {
    if (inflight) return inflight;
    inflight = readRssKb()
      .then((kb) => {
        if (kb && kb > 0) {
          windowPeakKb = Math.max(windowPeakKb, kb);
          runPeakKb = Math.max(runPeakKb, kb);
        }
      })
      .catch(() => {})
      .finally(() => (inflight = null));
    return inflight;
  };
  return {
    /** Start a window (one generate). Takes a first sample immediately. */
    start() {
      windowPeakKb = 0;
      void sample();
      if (handle === null) handle = timers.set(() => void sample(), intervalMs);
    },
    /** Stop the window; one last sample; returns the window's peak in bytes (null if nothing was read). */
    async stop(): Promise<number | null> {
      if (handle !== null) timers.clear(handle);
      handle = null;
      await sample();
      return windowPeakKb ? windowPeakKb * 1024 : null;
    },
    sample,
    get runPeakBytes() {
      return runPeakKb ? runPeakKb * 1024 : null;
    },
  };
}

export const parsePsRss = (out: string): number | null => {
  const n = parseInt(out.trim(), 10);
  return Number.isFinite(n) && n > 0 ? n : null;
};

// ---------------------------------------------------------------- node backend (node-llama-cpp 3.21.1) thinking control
/**
 * node-llama-cpp's thought budget for one generate. On 3.21.1, enable_thinking=false through jinja render params does
 * NOT stop a thinking-capable model (MiniCPM5-1B: empty answers after ~19 s, Anvil); only the prompt option
 * `budgets.thoughtTokens` does. Off (enableThinking false) -> 0; a numeric per-item budget -> that budget; else none.
 */
export function nodeBudgets(o: GenOpts): { thoughtTokens: number } | undefined {
  if (o.enableThinking === false) return { thoughtTokens: 0 };
  if (typeof o.thinkingBudget === "number") return { thoughtTokens: o.thinkingBudget };
  return undefined;
}

export interface HiddenState { reasoningTokens: number; firstReasoningMs: number | null; sawThought: boolean }
export const newHiddenState = (): HiddenState => ({ reasoningTokens: 0, firstReasoningMs: null, sawThought: false });

/** One node-llama-cpp onResponseChunk: thought segments are hidden reasoning (main-text chunks are ignored here). */
export function trackThoughtChunk(st: HiddenState, chunk: { type?: string; segmentType?: string; tokens?: readonly unknown[] }, tMs: number) {
  if (chunk.type !== "segment" || chunk.segmentType !== "thought") return;
  st.sawThought = true;
  const n = chunk.tokens?.length ?? 0;
  if (n > 0 && st.firstReasoningMs === null) st.firstReasoningMs = tMs;
  st.reasoningTokens += n;
}

/**
 * Node backend: the hidden-reasoning record for a generate, or null when nothing was hidden (no budget asked, or 0 thought
 * tokens). The engine's fast tier asks every model for thinking (budget 256), so a non-thinking model such as
 * Qwen3-4B-Instruct-2507 gets budgets.thoughtTokens 256, emits an empty thought segment and 0 thought tokens: nothing
 * recorded, its traces keep their shape. A fully suppressed thought (budget 0) has no hidden time either. The flag:
 * thought tokens beyond the enforced limit (0 when off), i.e. the suppression or the cap leaked.
 */
export function nodeHidden(o: GenOpts, st: HiddenState) {
  const b = nodeBudgets(o);
  if (!b || st.reasoningTokens === 0) return null;
  return { reasoningTokens: st.reasoningTokens, firstReasoningMs: st.firstReasoningMs, budgetExceeded: st.reasoningTokens > b.thoughtTokens };
}

/** The LlamaChatSession.prompt options of the node path: sampler + thought budget + hidden-reasoning tracking. */
export function nodeChatOptions<S extends object>(o: GenOpts, sampling: S, hidden: HiddenState, elapsedMs: () => number, onTextChunk: (c: string) => void) {
  const budgets = nodeBudgets(o);
  return {
    ...sampling,
    ...(budgets ? { budgets } : {}),
    onResponseChunk: (c: { type?: string; segmentType?: string; tokens?: readonly unknown[] }) => trackThoughtChunk(hidden, c, elapsedMs()),
    onTextChunk,
  };
}

// ---------------------------------------------------------------- one backend model, several installed (--deep-model)
/**
 * The backend holds ONE GGUF, but the engine may believe it loaded another installed model (the fast 4B, a verifier):
 * its only signal is engine.load(filename, { meta: { modelId } }); generate carries no model. This guard tracks what
 * the engine believes is loaded (also what getModelInfo must report, or the engine skips the load) and refuses a
 * generate unless that is the backend's file, so a fast/verifier call can never run silently on the deep model.
 */
export function modelGuard(backendFilename: string, backendModelId: string) {
  let loaded = { filename: backendFilename, modelId: backendModelId };
  let violations: string[] = [];
  return {
    get loadedFilename() {
      return loaded.filename;
    },
    onLoad(filename: string, modelId?: string) {
      loaded = { filename, modelId: modelId ?? filename };
    },
    /** null when generate may run; else the violation (also recorded for the item). */
    check(): string | null {
      if (loaded.filename === backendFilename) return null;
      const v = `model-guard: generate for ${loaded.modelId} (${loaded.filename}) but the backend holds ${backendModelId}`;
      violations.push(v);
      return v;
    },
    /** The current item's violations; clears them for the next item. */
    take(): string[] {
      const v = violations;
      violations = [];
      return v;
    },
  };
}
