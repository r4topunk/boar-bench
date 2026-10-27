// llama.rn on node-llama-cpp, embedding contexts only (the app's EmbeddingEngine calls initLlama({ embedding: true })).
// BOAR_APP_EMBED=zero returns zero vectors without loading a model (import-graph smoke tests only).
let llama;
export async function initLlama(params) {
  if (!params.embedding) throw new Error("llama.rn shim: only embedding contexts are supported in the eval");
  if (process.env.BOAR_APP_EMBED === "zero") {
    return { embedding: async () => ({ embedding: new Array(384).fill(0) }), release: async () => {} };
  }
  const { getLlama } = await import("node-llama-cpp");
  llama ??= await getLlama({ gpu: process.env.BOAR_APP_GPU === "0" ? false : "auto" });
  const model = await llama.loadModel({ modelPath: params.model.replace(/^file:\/\//, "") });
  const ctx = await model.createEmbeddingContext({ contextSize: params.n_ctx ?? 512 });
  return {
    embedding: async (text) => ({ embedding: Array.from((await ctx.getEmbeddingFor(text)).vector) }),
    release: async () => { await ctx.dispose(); await model.dispose(); },
  };
}
export function getBackendDevicesInfo() { return []; }
// generation never goes through llama.rn here (the answerer passes its own node-llama-cpp engine);
// LlamaEngine.ts only needs these names to import.
export async function loadLlamaModelInfo() { return {}; }
export class LlamaContext {}
export default { initLlama, getBackendDevicesInfo, LlamaContext, loadLlamaModelInfo };
