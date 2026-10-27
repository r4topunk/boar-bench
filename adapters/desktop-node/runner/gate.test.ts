import { describe, expect, it } from "vitest";
import { gateEnabled, gateTop, renderChatML, searchScore, topProbs } from "./gate";

// The gate's system prompt is fixed; five fixed prompts as the engine builds them (system + one user message).
const SYS = "You are BOAR's router. ... Reply with exactly one word: SEARCH or ANSWER.";
const PROMPTS = ["oi!", "who made you?", "capital da Austrália", "is it safe to swim after eating?", "make that shorter"];
const vocab = ["SEARCH", "ANS", "The", "I", "Sorry"];
/** Fake model: label mass depends on the prompt, the rest is spread over other tokens. */
const fake = (q: string): Map<number, number> =>
  new Map(q === "oi!" || q === "make that shorter" || q === "who made you?" ? [[1, 0.9], [0, 0.05], [2, 0.03], [3, 0.02]] : [[0, 0.95], [1, 0.02], [2, 0.02], [4, 0.01]]);

describe("desktop route gate helpers", () => {
  it("renders ChatML with the assistant turn open", () => {
    expect(renderChatML([{ role: "system", content: "s" }, { role: "user", content: "q" }])).toBe("<|im_start|>system\ns<|im_end|>\n<|im_start|>user\nq<|im_end|>\n<|im_start|>assistant\n");
  });
  it("on 5 fixed gate prompts returns a sorted probability list holding the SEARCH and ANS labels", () => {
    const out = PROMPTS.map((q) => {
      expect(renderChatML([{ role: "system", content: SYS }, { role: "user", content: q }])).toContain(q);
      return topProbs(fake(q), 20, (i) => vocab[i]);
    });
    for (const probs of out) {
      expect(probs.map((p) => p.token)).toEqual(expect.arrayContaining(["SEARCH", "ANS"]));
      expect([...probs].sort((a, b) => b.prob - a.prob)).toEqual(probs);
    }
    expect(out.map((p) => (searchScore(p)! >= 0.5 ? "search" : "answer"))).toEqual(["answer", "answer", "search", "search", "answer"]);
  });
  it("searchScore is null without labels; gateTop formats the top two", () => {
    expect(searchScore([{ token: "The", prob: 1 }])).toBeNull();
    expect(gateTop([{ token: "SEARCH", prob: 0.9996 }, { token: "ANS", prob: 0.0004 }])).toBe("SEARCH:1.000,ANS:0.000");
  });
  it("be-ship profile: default on, BOAR_ROUTE_GATE=0 turns it off", () => {
    expect(gateEnabled({ BOAR_RUNNER_PROFILE: "ship" })).toBe(true);
    expect(gateEnabled({ BOAR_RUNNER_PROFILE: "ship", BOAR_ROUTE_GATE: "0" })).toBe(false);
  });
  it("is off unless BOAR_ROUTE_GATE=1", () => {
    expect(gateEnabled({})).toBe(false);
    expect(gateEnabled({ BOAR_ROUTE_GATE: "0" })).toBe(false);
    expect(gateEnabled({ BOAR_ROUTE_GATE: "1" })).toBe(true);
  });
});
