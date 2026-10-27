/**
 * Route gate for the desktop adapter (GATEFID, step 1). The phone engine (src/inference/LlamaEngine.ts nextTokenProbs, llama.rn):
 * one forward over the gate messages in the model's chat template, n_predict 1, n_probs 20, no text; routeGate.ts reads the labels
 * "SEARCH" and "ANS" from the top probabilities. Desktop: node-llama-cpp controlledEvaluate on the ChatML render (identical to the
 * GGUF jinja render for Qwen2.5/Qwen3 instruct), raw softmax at the last prompt token; the 0.5 decision on p(SEARCH)/(p(SEARCH)+p(ANS))
 * is the same as on llama.rn's post-sampling probabilities (the ratio keeps the sign of the logit gap).
 * Off by default (old committed runs stay reproducible). BOAR_ROUTE_GATE=1 turns it on; BOAR_RUNNER_PROFILE=ship (the be-ship runner
 * of the CUT4/SPEEDPACK/CUT5/GATEFID runs) makes it default ON, and BOAR_ROUTE_GATE=0 turns it off again.
 */
export interface GateMessage { role: string; content: string }
export interface GateProb { token: string; prob: number }

export const gateEnabled = (env: Record<string, string | undefined> = process.env): boolean =>
  env.BOAR_ROUTE_GATE === "1" ? true : env.BOAR_ROUTE_GATE === "0" ? false : env.BOAR_RUNNER_PROFILE === "ship";

/** ChatML with the assistant turn opened, no thinking block (Qwen2.5 / Qwen3-Instruct-2507 templates). */
export function renderChatML(messages: GateMessage[]): string {
  return messages.map((m) => `<|im_start|>${m.role}\n${m.content}<|im_end|>\n`).join("") + "<|im_start|>assistant\n";
}

/** Top-n entries of a token-id -> probability map, highest first, tokens decoded with `detok`. */
export function topProbs(probs: Map<number, number>, n: number, detok: (id: number) => string): GateProb[] {
  return [...probs.entries()].sort((a, b) => b[1] - a[1]).slice(0, n).map(([t, p]) => ({ token: detok(t), prob: p }));
}

/** p(SEARCH) / (p(SEARCH) + p(ANS)) as routeGateVerdict computes it; null when neither label is in the list. */
export function searchScore(probs: readonly GateProb[]): number | null {
  const s = probs.find((p) => p.token === "SEARCH")?.prob ?? 0;
  const a = probs.find((p) => p.token === "ANS")?.prob ?? 0;
  return s + a > 0 ? s / (s + a) : null;
}

/** "SEARCH:1.000,ANS:0.000" for the trace event. */
export const gateTop = (probs: readonly GateProb[] | undefined | null, k = 2): string | null =>
  probs ? probs.slice(0, k).map((p) => `${p.token}:${p.prob.toFixed(3)}`).join(",") : null;
