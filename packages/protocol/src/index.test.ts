import { describe, expect, it } from "vitest";
import { EvalRequest, EvalTrace, PROTOCOL_VERSION } from "./index";

const config = { commit: "0cfd4a77", arm: "main", modelId: "qwen2.5-1.5b-instruct-q4km", settings: { quickFirst: true }, kit: [], device: { platform: "ios", ramGb: 4 } };

describe("protocol v1", () => {
  it("parses a request", () => {
    const r = EvalRequest.parse({ protocol: PROTOCOL_VERSION, runId: "r1", item: { id: "q1", question: "What is the capital of Australia?" }, config });
    expect(r.seed).toBe(42);
    expect(r.item.lang).toBe("en");
  });
  it("parses a minimal trace and fills defaults", () => {
    const t = EvalTrace.parse({
      protocol: PROTOCOL_VERSION, runId: "r1", itemId: "q1", question: "What is the capital of Australia?",
      engine: { commit: "0cfd4a77", arm: "main" },
      runtime: { adapter: "desktop-node", host: "Apple M4 cpu x4", model: "qwen2.5-1.5b-instruct-q4km", sampler: { temperature: 0, seed: 42 } },
      config,
      route: { task: "lookup", tier: "fast", outcome: "success", reasonCodes: ["task:lookup"] },
      retrieval: { raw: [{ title: "Canberra" }], kept: [{ title: "Canberra" }], dropped: [] },
      answer: { text: "Canberra [1].", cited: ["Canberra"], shown: ["Canberra"], declined: false, weakSources: false },
      timing: { ttftMs: 900, totalMs: 1500, retrievalMs: 80, prefillMs: 600, decodeTokPerSec: 55, promptTokens: 300, outputTokens: 6 },
      createdAt: "2026-10-01T22:00:00Z",
    });
    expect(t.resources).toBeNull();
    expect(t.retrieval.raw[0].section).toBeNull();
    expect("firstVisibleMs" in t.timing).toBe(false);
  });
  it("keeps the optional server-backend fields (llama-server: hidden reasoning, budget flag, peak RSS)", () => {
    const base = EvalTrace.parse({
      protocol: PROTOCOL_VERSION, runId: "r1", itemId: "q1", question: "q",
      engine: { commit: "0cfd4a77", arm: "main" },
      runtime: { adapter: "desktop-node", backend: "llama-server", host: "h", model: "m", sampler: {}, versions: { "llama-server": "b11010 (4bc272f; 0.4.1-dev build 1)" } },
      config,
      route: { task: null, tier: "fast", outcome: "success", reasonCodes: [], thinkingBudgetExceeded: true },
      retrieval: { raw: [], kept: [], dropped: [] },
      answer: { text: "x", cited: [], shown: [], declined: false, weakSources: false },
      timing: { ttftMs: 900, totalMs: 1500, retrievalMs: 80, prefillMs: 600, decodeTokPerSec: 55, promptTokens: 300, outputTokens: 6,
                firstVisibleMs: 2100, reasoningMs: 1200, reasoningTokens: 300 },
      resources: { peakRssMb: 3100.5, thermal: null, sustainedRatio: null },
      createdAt: "2026-10-02T03:00:00Z",
    });
    expect(base.runtime.backend).toBe("llama-server");
    expect(base.route.thinkingBudgetExceeded).toBe(true);
    expect(base.timing).toMatchObject({ firstVisibleMs: 2100, reasoningMs: 1200, reasoningTokens: 300 });
    expect(base.resources?.peakRssMb).toBe(3100.5);
  });
  it("keeps route.mode and timing.retrievalMs2 (MP4B / DEEPITER) and rejects an unknown mode", () => {
    const t = {
      protocol: PROTOCOL_VERSION, runId: "r1", itemId: "q1", question: "q",
      engine: { commit: "0cfd4a77", arm: "main" },
      runtime: { adapter: "desktop-node", host: "h", model: "m", sampler: {}, versions: {} },
      config,
      route: { task: null, tier: "deep", outcome: "success", reasonCodes: [], mode: "multipass" },
      retrieval: { raw: [], kept: [], dropped: [] },
      answer: { text: "x", cited: [], shown: [], declined: false, weakSources: false },
      timing: { ttftMs: null, totalMs: 1500, retrievalMs: null, prefillMs: 600, decodeTokPerSec: 55, promptTokens: 300, outputTokens: 6, retrievalMs2: 42.5 },
      createdAt: "2026-10-11T03:00:00Z",
    };
    const p = EvalTrace.parse(t);
    expect(p.route.mode).toBe("multipass");
    expect(p.timing.retrievalMs2).toBe(42.5);
    expect(EvalTrace.safeParse({ ...t, route: { ...t.route, mode: "triple" } }).success).toBe(false);
  });
  it("accepts a reference-cli anchor trace (no device) and still requires a device object or null", () => {
    const anchor = {
      protocol: PROTOCOL_VERSION, runId: "anchors-haiku", itemId: "q1", question: "q",
      engine: { commit: "n/a-anchor", arm: "anchor-haiku" },
      runtime: { adapter: "reference-cli", host: "claude-code-subscription", model: "claude-haiku-4-5-20251001", sampler: {} },
      config: { ...config, commit: "n/a-anchor", arm: "anchor-haiku", modelId: "claude-haiku-4-5-20251001", device: null },
      route: { task: null, tier: null, outcome: "answered", reasonCodes: [] },
      retrieval: { raw: [], kept: [], dropped: [] },
      answer: { text: "x", cited: [], shown: [], declined: false, weakSources: false },
      timing: { ttftMs: null, totalMs: null, retrievalMs: null, prefillMs: null, decodeTokPerSec: null, promptTokens: null, outputTokens: null },
      createdAt: "2026-10-02T12:00:00Z",
    };
    const t = EvalTrace.parse(anchor);
    expect(t.runtime.adapter).toBe("reference-cli");
    expect(t.config.device).toBeNull();
    const { device: _d, ...noDevice } = anchor.config;
    expect(() => EvalTrace.parse({ ...anchor, config: noDevice })).toThrow();
    expect(() => EvalTrace.parse({ ...anchor, runtime: { ...anchor.runtime, adapter: "web-cli" } })).toThrow();
  });
  it("rejects a wrong protocol version", () => {
    expect(() => EvalRequest.parse({ protocol: "0.9", runId: "r", item: { id: "q", question: "x" }, config })).toThrow();
  });
});
