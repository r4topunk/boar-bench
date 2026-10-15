import { execFileSync } from "node:child_process";
import { mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";
import { EvalRequest } from "./index";
import { makeRequests } from "./makeRequests";

const HERE = fileURLToPath(new URL(".", import.meta.url));

const cfg = {
  commit: "0cfd4a77",
  arm: "main",
  modelId: "qwen2.5-1.5b-instruct-q4km",
  settings: { quickFirst: true, alwaysComplete: false },
  kit: [{ id: "boar-crypto", sha256: "a".repeat(64) }],
  device: { platform: "ios", ramGb: 4 },
};
const questions = [
  JSON.stringify({ id: "q1", question: "What is the capital of Australia?", category: "x", rubric: ["ignored"] }),
  "",
  JSON.stringify({ id: "q2", question: "Restaurants near me?", lang: "pt", context: { lat: 1, lon: 2, city_hint: "ignored" } }),
  JSON.stringify({ id: "q3", question: "dup", duplicate_of: "q1" }),
].join("\n");

describe("makeRequests", () => {
  it("builds one valid request per unique question, with seed and temperature", () => {
    const r = makeRequests(questions, { ...cfg, seed: 7, temperature: 0 }, { runId: "run-a" });
    expect(r.map((x) => x.item.id)).toEqual(["q1", "q2"]);
    for (const x of r) expect(EvalRequest.parse(x)).toEqual(x);
    expect(r[0]).toMatchObject({ runId: "run-a", seed: 7, temperature: 0, item: { lang: "en" }, config: { commit: "0cfd4a77", arm: "main" } });
    expect(r[1].item).toEqual({ id: "q2", question: "Restaurants near me?", lang: "pt", context: { lat: 1, lon: 2 } });
    expect(r[0].item).not.toHaveProperty("category");
  });
  it("keeps the base language of a BCP-47 tag (safety track items use pt-BR)", () => {
    const q = [JSON.stringify({ id: "s1", question: "O que eu faço?", lang: "pt-BR" }), JSON.stringify({ id: "s2", question: "What now?", lang: "en-US" })].join("\n");
    expect(makeRequests(q, cfg, { runId: "r" }).map((x) => x.item.lang)).toEqual(["pt", "en"]);
  });
  it("defaults seed 42 and leaves temperature unset", () => {
    const [r] = makeRequests(questions, cfg, { runId: "r" });
    expect(r.seed).toBe(42);
    expect(r.temperature).toBeUndefined();
  });
  it("keeps duplicates on request", () => {
    expect(makeRequests(questions, cfg, { runId: "r", keepDuplicates: true })).toHaveLength(3);
  });
  it("fails loudly on a bad config, a bad question or a repeated id", () => {
    expect(() => makeRequests(questions, { ...cfg, device: { platform: "web", ramGb: 4 } }, { runId: "r" })).toThrow();
    expect(() => makeRequests('{"id":"x"}', cfg, { runId: "r" })).toThrow(/line 1/);
    expect(() => makeRequests('{"id":"x","question":"a"}\n{"id":"x","question":"b"}', cfg, { runId: "r" })).toThrow(/duplicate id x/);
    expect(() => makeRequests("", cfg, { runId: "r" })).toThrow(/no questions/);
  });
  it("splits a multi-turn item: last user turn = question, earlier turns = history (chat-slice format)", () => {
    const q = [
      JSON.stringify({ id: "m1", lang: "pt", kind: "followup", expected_search: "yes", turns: [
        { role: "user", text: "o que é a dengue?" }, { role: "assistant", text: "Uma doença viral [1]." }, { role: "user", text: "e como previne?" }] }),
      JSON.stringify({ id: "m2", lang: "es", turns: [{ role: "user", text: "hola" }] }),
    ].join("\n");
    const [m1, m2] = makeRequests(q, cfg, { runId: "r" });
    expect(m1.item).toEqual({ id: "m1", question: "e como previne?", lang: "pt", history: { turns: [
      { role: "user", text: "o que é a dengue?" }, { role: "assistant", text: "Uma doença viral [1]." }] } });
    // One turn = a plain single-turn item: no history key at all.
    expect(m2.item).toEqual({ id: "m2", question: "hola", lang: "es" });
    for (const x of [m1, m2]) expect(EvalRequest.parse(x)).toEqual(x);
  });
  it("rejects a turns list that does not end on the user, or a question given twice", () => {
    expect(() => makeRequests(JSON.stringify({ id: "x", turns: [{ role: "user", text: "a" }, { role: "assistant", text: "b" }] }), cfg, { runId: "r" })).toThrow(/last turn/);
    expect(() => makeRequests(JSON.stringify({ id: "x", question: "a", turns: [{ role: "user", text: "a" }] }), cfg, { runId: "r" })).toThrow(/not both/);
    expect(() => makeRequests(JSON.stringify({ id: "x", turns: [{ role: "system", text: "s" }, { role: "user", text: "a" }] }), cfg, { runId: "r" })).toThrow(/history/);
  });
  it("CLI writes jsonl", () => {
    const d = mkdtempSync(join(tmpdir(), "mkreq-"));
    writeFileSync(join(d, "q.jsonl"), questions);
    writeFileSync(join(d, "c.json"), JSON.stringify({ ...cfg, temperature: 0 }));
    const out = execFileSync(join(HERE, "../node_modules/.bin/tsx"), [join(HERE, "makeRequests.ts"), "--questions", join(d, "q.jsonl"), "--config", join(d, "c.json"), "--run-id", "cli"], { encoding: "utf8", stdio: ["ignore", "pipe", "ignore"] });
    const lines = out.trim().split("\n").map((l) => EvalRequest.parse(JSON.parse(l)));
    expect(lines.map((l) => l.item.id)).toEqual(["q1", "q2"]);
    expect(lines[0].temperature).toBe(0);
  });
});
