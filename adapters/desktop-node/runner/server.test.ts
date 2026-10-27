import { describe, expect, it } from "vitest";
import {
  applyData,
  budgetExceeded,
  maxTokensFor,
  modelGuard,
  newHiddenState,
  newStreamState,
  nodeBudgets,
  nodeChatOptions,
  nodeHidden,
  parsePsRss,
  requestFor,
  rssSampler,
  serverVersion,
  sseData,
  THINKING_BUDGET_MESSAGE,
} from "./server";

const chunk = (delta: Record<string, string>, extra: Record<string, unknown> = {}) =>
  JSON.stringify({ choices: [{ index: 0, delta, finish_reason: null }], object: "chat.completion.chunk", ...extra });

describe("request bodies", () => {
  const messages = [{ role: "system", content: "s" }, { role: "user", content: "q" }];
  it("chat: node-path arithmetic and sampler, no prompt cache, thinking off when the engine says so", () => {
    const { path, body } = requestFor({ messages, nPredict: 512, enableThinking: false, thinkingBudget: 256 }, 0, 42);
    expect(path).toBe("/v1/chat/completions");
    expect(body).toMatchObject({ messages, stream: true, max_tokens: 512, temperature: 0, top_k: 40, top_p: 0.95, min_p: 0.05, seed: 42,
                                 cache_prompt: false, chat_template_kwargs: { enable_thinking: false } });
    expect(body).not.toHaveProperty("thinking_budget_tokens");
  });
  it("chat: a thinking budget raises max_tokens and is sent per request with the app's message", () => {
    const { body } = requestFor({ messages, nPredict: 512, thinkingBudget: 256 }, undefined, 7);
    expect(body).toMatchObject({ max_tokens: 768, temperature: 0.7, seed: 7, thinking_budget_tokens: 256, reasoning_budget_message: THINKING_BUDGET_MESSAGE });
    expect(body).not.toHaveProperty("chat_template_kwargs");
  });
  it("chat: BOAR_THINK_KWARG=1 asks a thinking-off-by-default template (Gemma 4) to think, only with a budget", () => {
    process.env.BOAR_THINK_KWARG = "1";
    try {
      expect(requestFor({ messages, nPredict: 512, thinkingBudget: 256 }, undefined, 7).body).toMatchObject({ chat_template_kwargs: { enable_thinking: true }, thinking_budget_tokens: 256 });
      expect(requestFor({ messages, nPredict: 512 }, undefined, 7).body).not.toHaveProperty("chat_template_kwargs");
      expect(requestFor({ messages, nPredict: 512, enableThinking: false, thinkingBudget: 256 }, undefined, 7).body).toMatchObject({ chat_template_kwargs: { enable_thinking: false } });
    } finally { delete process.env.BOAR_THINK_KWARG; }
  });
  it("request temperature overrides the engine's; engine's overrides the default", () => {
    expect(requestFor({ messages, temperature: 0.2 }, 0, 1).body.temperature).toBe(0);
    expect(requestFor({ messages, temperature: 0.2 }, undefined, 1).body.temperature).toBe(0.2);
  });
  it("completion: prompt + the node path's stop fallback", () => {
    const { path, body } = requestFor({ prompt: "Q: x\nA:" }, 0, 42);
    expect(path).toBe("/completion");
    expect(body).toMatchObject({ prompt: "Q: x\nA:", n_predict: 512, stop: ["\nUser:", "\nQuestion:"], cache_prompt: false });
  });
  it("maxTokensFor", () => {
    expect(maxTokensFor({})).toBe(512);
    expect(maxTokensFor({ nPredict: 200, thinkingBudget: 128 })).toBe(328);
    expect(maxTokensFor({ nPredict: 200, thinkingBudget: 128, enableThinking: false })).toBe(200);
  });
});

describe("SSE parsing", () => {
  it("splits complete data lines and keeps the partial tail", () => {
    const { datas, rest } = sseData(`data: {"a":1}\r\n\ndata: {"b":2}\n: comment\ndata: {"c"`);
    expect(datas).toEqual([`{"a":1}`, `{"b":2}`]);
    expect(rest).toBe(`data: {"c"`);
  });
  it("reassembles a payload split across network chunks", () => {
    let buf = "";
    const got: string[] = [];
    for (const piece of [`data: {"x":`, `"y"}\n\nda`, `ta: [DONE]\n\n`]) {
      const r = sseData(buf + piece);
      buf = r.rest;
      got.push(...r.datas);
    }
    expect(got).toEqual([`{"x":"y"}`, "[DONE]"]);
  });
});

describe("reasoning / content split", () => {
  it("reasoning_content stays hidden, content streams, first-text skips whitespace, timings map", () => {
    const st = newStreamState();
    const shown: string[] = [];
    const on = (c: string) => shown.push(c);
    applyData(st, chunk({ role: "assistant", content: "" }), 1, on);
    applyData(st, chunk({ reasoning_content: "Let me" }), 10, on);
    applyData(st, chunk({ reasoning_content: " think." }), 20, on);
    applyData(st, chunk({ content: "\n\n" }), 30, on);
    applyData(st, chunk({ content: "Canberra" }), 40, on);
    applyData(st, chunk({ content: " [1]." }), 50, on);
    applyData(st, JSON.stringify({ choices: [{ delta: {}, finish_reason: "stop" }], timings: { prompt_n: 300, prompt_ms: 600.5, predicted_n: 6, predicted_ms: 100 } }), 60, on);
    applyData(st, "[DONE]", 61, on);
    expect(shown.join("")).toBe("\n\nCanberra [1].");
    expect(st.content).toBe("\n\nCanberra [1].");
    expect(st.reasoning).toBe("Let me think.");
    expect(st).toMatchObject({ reasoningTokens: 2, firstReasoningMs: 10, firstTextMs: 40, finishReason: "stop", done: true,
                               timings: { promptTokens: 300, promptMs: 600.5, predictedTokens: 6, predictedMs: 100 } });
  });
  it("no reasoning: firstReasoningMs stays null", () => {
    const st = newStreamState();
    applyData(st, chunk({ content: "Hi" }), 5);
    expect(st).toMatchObject({ reasoningTokens: 0, firstReasoningMs: null, firstTextMs: 5 });
  });
  it("/completion chunks: content + stop + timings", () => {
    const st = newStreamState();
    applyData(st, JSON.stringify({ content: "Can", stop: false }), 3);
    applyData(st, JSON.stringify({ content: "", stop: true, timings: { prompt_n: 10, prompt_ms: 20, predicted_n: 2, predicted_ms: 30 } }), 9);
    expect(st).toMatchObject({ content: "Can", firstTextMs: 3, done: true, timings: { promptTokens: 10, predictedTokens: 2 } });
  });
  it("a server error payload throws; non-JSON is ignored", () => {
    expect(() => applyData(newStreamState(), JSON.stringify({ error: { code: 500, message: "template error" } }), 1)).toThrow(/template error/);
    expect(applyData(newStreamState(), "not json", 1)).toBe(false);
  });
  it("budget flag: only above the budget, only when thinking is on", () => {
    expect(budgetExceeded(257, 256, undefined)).toBe(true);
    expect(budgetExceeded(256, 256, undefined)).toBe(false);
    expect(budgetExceeded(900, 256, false)).toBe(false);
    expect(budgetExceeded(900, undefined, undefined)).toBe(false);
  });
});

describe("RSS sampling (stubbed ps + timers)", () => {
  it("per-window peak and run peak, in bytes; ignores failed reads", async () => {
    const reads = [1000, 3000, null, 2000, 500, 4000];
    let i = 0;
    let tick: (() => void) | null = null;
    const s = rssSampler(async () => reads[i++] ?? null, 250, { set: (f) => (tick = f), clear: () => (tick = null) });
    s.start(); // 1000
    await s.sample(); // in flight -> same promise
    tick!(); await Promise.resolve(); await new Promise((r) => setTimeout(r, 0)); // 3000
    tick!(); await new Promise((r) => setTimeout(r, 0)); // null
    expect(await s.stop()).toBe(3000 * 1024 * 1); // + final read 2000
    expect(tick).toBeNull();
    s.start(); // 500
    await new Promise((r) => setTimeout(r, 0));
    expect(await s.stop()).toBe(4000 * 1024); // final read 4000
    expect(s.runPeakBytes).toBe(4000 * 1024);
  });
  it("parses ps output", () => {
    expect(parsePsRss("  123456\n")).toBe(123456);
    expect(parsePsRss("")).toBeNull();
  });
});

describe("server version", () => {
  it("formats --version with the checkout's tag", () => {
    const v = "version: 0.4.1-dev (build 1, commit 4bc272f)\nbuilt with AppleClang 17.0.0.17000319 for Darwin arm64\n";
    expect(serverVersion(v, "b11010")).toBe("b11010 (4bc272f; 0.4.1-dev build 1)");
    expect(serverVersion(v)).toBe("(4bc272f; 0.4.1-dev build 1)");
  });
});

describe("node backend thought budget (stubbed LlamaChatSession.prompt)", () => {
  /** Stub of node-llama-cpp 3.21.1: a thinking model emits up to budgets.thoughtTokens thought tokens (default: all 50),
   *  then the answer. Render params (enable_thinking) are ignored, as Anvil found on MiniCPM5-1B. */
  function stubPrompt(thinks: boolean, opts: any) {
    const want = thinks ? 50 : 0;
    const allowed = Math.min(want, opts.budgets?.thoughtTokens ?? Infinity);
    if (thinks) opts.onResponseChunk({ type: "segment", segmentType: "thought", tokens: [], text: "", segmentStartTime: new Date() });
    for (let i = 0; i < allowed; i++) opts.onResponseChunk({ type: "segment", segmentType: "thought", tokens: [i], text: "t" });
    if (thinks) opts.onResponseChunk({ type: "segment", segmentType: "thought", tokens: [], text: "", segmentEndTime: new Date() });
    for (const c of ["Can", "berra"]) {
      opts.onResponseChunk({ type: undefined, segmentType: undefined, tokens: [1], text: c });
      opts.onTextChunk(c);
    }
    return "Canberra";
  }
  const run = (o: any, thinks: boolean) => {
    const st = newHiddenState();
    let clock = 0;
    const shown: string[] = [];
    const opts = nodeChatOptions(o, { temperature: 0, topK: 40 }, st, () => ++clock, (c) => shown.push(c));
    const text = stubPrompt(thinks, opts);
    return { opts, st, text, shown, rec: nodeHidden(o, st) };
  };

  it("budgets: off -> 0, numeric per-item budget -> it (0 included), none otherwise", () => {
    expect(nodeBudgets({ enableThinking: false, thinkingBudget: 256 })).toEqual({ thoughtTokens: 0 });
    expect(nodeBudgets({ thinkingBudget: 256 })).toEqual({ thoughtTokens: 256 });
    expect(nodeBudgets({ thinkingBudget: 0 })).toEqual({ thoughtTokens: 0 });
    expect(nodeBudgets({})).toBeUndefined();
  });
  it("thinking off: budgets.thoughtTokens 0 reaches prompt(), the stub thinks 0 tokens, record shows no leak", () => {
    const r = run({ messages: [], enableThinking: false }, true);
    expect(r.opts).toMatchObject({ temperature: 0, topK: 40, budgets: { thoughtTokens: 0 } });
    expect(r.shown.join("")).toBe("Canberra");
    expect(r.st.reasoningTokens).toBe(0);
    expect(r.rec).toBeNull(); // fully suppressed: nothing hidden to record
  });
  it("per-item budget caps hidden tokens; time of first thought recorded; text chunks are not counted", () => {
    const r = run({ messages: [], thinkingBudget: 16 }, true);
    expect(r.opts.budgets).toEqual({ thoughtTokens: 16 });
    expect(r.rec).toMatchObject({ reasoningTokens: 16, budgetExceeded: false });
    expect(r.rec!.firstReasoningMs).toBe(2);
  });
  it("a leak past the limit is flagged (thought tokens > budget)", () => {
    const st = newHiddenState();
    const opts = nodeChatOptions({ messages: [], enableThinking: false }, {}, st, () => 1, () => {});
    opts.onResponseChunk({ type: "segment", segmentType: "thought", tokens: [1, 2, 3] });
    expect(nodeHidden({ enableThinking: false }, st)).toMatchObject({ reasoningTokens: 3, budgetExceeded: true });
  });
  it("non-thinking model with thinking off (Qwen3-4B-Instruct): budgets sent, nothing recorded -> trace shape unchanged", () => {
    const r = run({ messages: [], enableThinking: false }, false);
    // its wrapper emits an empty thought segment: still nothing to record
    r.opts.onResponseChunk({ type: "segment", segmentType: "thought", tokens: [], segmentStartTime: new Date() } as any);
    expect(nodeHidden({ enableThinking: false }, r.st)).toBeNull();
    expect(r.opts.budgets).toEqual({ thoughtTokens: 0 });
    expect(r.rec).toBeNull();
    expect(nodeHidden({}, newHiddenState())).toBeNull(); // no budget asked: nothing recorded
    // the engine's fast tier: thinking on with budget 256 for every model; a non-thinker emits 0 thought tokens
    const fast = run({ messages: [], thinkingBudget: 256 }, false);
    expect(fast.opts.budgets).toEqual({ thoughtTokens: 256 });
    expect(fast.rec).toBeNull();
  });
});

describe("model guard (--deep-model: the backend holds one GGUF)", () => {
  it("generate passes on the backend's model, fails (and records) after the engine loads another one", () => {
    const g = modelGuard("models/deep.gguf", "deep35");
    expect(g.check()).toBeNull();
    g.onLoad("models/deep.gguf", "deep35");
    expect(g.check()).toBeNull();
    g.onLoad("models/fast.gguf", "qwen4b");
    expect(g.loadedFilename).toBe("models/fast.gguf"); // what getModelInfo must report, so the engine reloads the deep one
    expect(g.check()).toMatch(/generate for qwen4b .* backend holds deep35/);
    expect(g.take()).toHaveLength(1);
    expect(g.take()).toEqual([]); // per item
    g.onLoad("models/deep.gguf", "deep35");
    expect(g.check()).toBeNull();
  });
});

describe("samplerOverride (DEEPSAMP)", () => {
  it("is empty by default and merges allowed numeric fields from BOAR_SAMPLER_JSON", async () => {
    const { samplerFor, samplerOverride } = await import("./server");
    delete process.env.BOAR_SAMPLER_JSON;
    expect(samplerOverride()).toEqual({});
    expect(samplerFor({ messages: [] } as any, undefined, 7)).toEqual({ temperature: 0.7, top_k: 40, top_p: 0.95, min_p: 0.05, seed: 7 });
    process.env.BOAR_SAMPLER_JSON = JSON.stringify({ temperature: 1, top_k: 20, min_p: 0, presence_penalty: 1.5 });
    try {
      expect(samplerFor({ messages: [] } as any, undefined, 7)).toEqual({ temperature: 1, top_k: 20, top_p: 0.95, min_p: 0, presence_penalty: 1.5, seed: 7 });
      process.env.BOAR_SAMPLER_JSON = JSON.stringify({ mirostat: 2 });
      expect(() => samplerOverride()).toThrow(/bad field/);
    } finally { delete process.env.BOAR_SAMPLER_JSON; }
  });
});

