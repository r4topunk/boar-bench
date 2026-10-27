// The tree's src/rag/retrieve.ts as src/services/orchestrator.ts sees it (MP4B): every export unchanged, except `retrieve`,
// which goes through globalThis.__boarEvalOrchestratorRetrieve when the runner sets it (it logs a `retrieve` event and
// calls the real one). Only orchestrator.ts's "../rag/retrieve" import is redirected here (adapter.ts resolve hook);
// "boar-eval:tree-retrieve" resolves to the tree's own module, the same instance the runner and answer.ts use.
export * from "boar-eval:tree-retrieve";
import { retrieve as treeRetrieve } from "boar-eval:tree-retrieve";
export function retrieve(...args) {
  const hook = globalThis.__boarEvalOrchestratorRetrieve;
  return hook ? hook(treeRetrieve, ...args) : treeRetrieve(...args);
}
