import { describe, expect, it } from "vitest";
import { answerContext, capTokenEvents, invalidateTiming, parseShard, citedTitles, droppedOf, mapEvent, shownTitles, sourceRef, taskOf, warningCodes, type TraceEvent } from "./trace";

const A = sourceRef({ title: "Canberra", section: "History", source: "wikipedia", similarity: 0.8, text: "long passage" } as never);
const B = sourceRef({ title: "Canberra", section: "Climate" });
const C = sourceRef({ title: "Sydney" });

describe("retrieval bookkeeping", () => {
  it("keeps only the ref fields, nulls for missing ones", () => {
    expect(A).toEqual({ title: "Canberra", section: "History", source: "wikipedia", similarity: 0.8 });
    expect(C).toEqual({ title: "Sydney", section: null, source: null, similarity: null });
  });
  it("dropped = raw - kept by title + section", () => {
    expect(droppedOf([A, B, C], [B])).toEqual([A, C]);
    expect(droppedOf([A], [{ ...A, similarity: 0.1 }])).toEqual([]);
  });
});

describe("events", () => {
  it("drops answerId/at, maps unknown types to other, strips passage text", () => {
    expect(mapEvent({ type: "stage", answerId: "ans-1", stage: "retrieving", tier: "instant", at: 123456 }, 5)).toEqual({
      tMs: 5, type: "other", kind: "stage", stage: "retrieving", tier: "instant",
    });
    const s = mapEvent({ type: "sources", answerId: "x", tier: "fast", sources: [{ title: "T", text: "body", relevance: 0.5, score: 3 }] }, 1);
    expect(s).toEqual({ tMs: 1, type: "sources", tier: "fast", sources: [{ title: "T", section: null, source: null, similarity: null, relevance: 0.5 }] });
    expect(mapEvent({ type: "done", answerId: "x", tier: "fast", cited: [1] }, 9).type).toBe("done");
    const withText = mapEvent({ type: "sources", tier: "fast", sources: [{ title: "T", body: "kept sentence." }] }, 2, true);
    expect((withText.sources as { text?: string }[])[0].text).toBe("kept sentence.");
  });
  it("caps token events keeping head/tail and one marker", () => {
    const ev: TraceEvent[] = [{ tMs: 0, type: "sources", sources: [] }, ...Array.from({ length: 10 }, (_, i) => ({ tMs: i + 1, type: "token" as const, text: `t${i}` })), { tMs: 20, type: "done" }];
    const out = capTokenEvents(ev, 4);
    expect(out.filter((e) => e.type === "token").map((e) => e.text)).toEqual(["t0", "t1", "t8", "t9"]);
    expect(out.find((e) => e.kind === "tokens-elided")).toMatchObject({ count: 6, chars: 12, tMs: 3 });
    expect(out.map((e) => e.type)).toEqual(["sources", "token", "token", "other", "token", "token", "done"]);
    expect(capTokenEvents(ev, 0)).toBe(ev);
    expect(capTokenEvents(ev, 64)).toBe(ev);
  });
  it("derives warnings, shown and cited titles", () => {
    const ev: TraceEvent[] = [
      { tMs: 0, type: "sources", sources: [A] },
      { tMs: 1, type: "warning", code: "weak_sources", declined: true },
      { tMs: 2, type: "sources", sources: [B, C] },
    ];
    expect(warningCodes(ev)).toEqual(["weak_sources:declined"]);
    expect(shownTitles(ev)).toEqual(["Canberra", "Sydney"]);
    expect(shownTitles([])).toEqual([]);
    expect(citedTitles([2, 5], [A, C])).toEqual(["Sydney"]);
    expect(taskOf(["retrieve:yes", "task:lookup"])).toBe("lookup");
    expect(taskOf([])).toBeNull();
  });
});

describe("multi-turn history", () => {
  const ctx = { systemPrompt: "sys", styleReminder: "style", maxTokens: 512 };
  it("single-turn: the context object is passed through untouched", () => {
    expect(answerContext(ctx, { })).toBe(ctx);
  });
  it("multi-turn: earlier turns become AnswerContext.history (summary null, oldest first)", () => {
    const turns = [{ role: "user" as const, text: "me fala de Lisboa" }, { role: "assistant" as const, text: "Capital de Portugal [1]." }];
    const c = answerContext(ctx, { history: { turns } });
    expect(c).toEqual({ ...ctx, history: { summary: null, turns } });
    expect(ctx).not.toHaveProperty("history");
  });
});

describe("parallel mode", () => {
  it("parses i/N shards and rejects bad ones", () => {
    expect(parseShard("0/1")).toEqual({ i: 0, n: 1 });
    expect(parseShard("2/3")).toEqual({ i: 2, n: 3 });
    for (const bad of ["3/3", "1/0", "a/2", "1"]) expect(() => parseShard(bad)).toThrow(/--shard/);
  });
  it("nulls latency fields, keeps token counts, moves raw values to an invalid timing-raw event", () => {
    const events: TraceEvent[] = [];
    const t = invalidateTiming({ ttftMs: 900, totalMs: 1500, retrievalMs: 80, prefillMs: 600, decodeTokPerSec: 55, promptTokens: 300, outputTokens: 6 }, events);
    expect(t).toEqual({ ttftMs: null, totalMs: null, retrievalMs: null, prefillMs: null, decodeTokPerSec: null, promptTokens: 300, outputTokens: 6 });
    expect(events).toEqual([{ tMs: 0, type: "other", kind: "timing-raw", origin: "adapter", valid: false, ttftMs: 900, totalMs: 1500, retrievalMs: 80, prefillMs: 600, decodeTokPerSec: 55 }]);
  });
  it("nulls retrievalMs2 too when present (DEEPITER / multi-pass), and adds nothing when absent", () => {
    const events: TraceEvent[] = [];
    expect(invalidateTiming({ retrievalMs: 80, retrievalMs2: 40, outputTokens: 6 }, events)).toEqual({ retrievalMs: null, retrievalMs2: null, outputTokens: 6 });
    expect(events[0]).toMatchObject({ retrievalMs: 80, retrievalMs2: 40 });
    expect("retrievalMs2" in invalidateTiming({ retrievalMs: 80 }, [])).toBe(false);
  });
});
