// judge.v1_1 (wording W3 = W1 minus the sentence "A partial answer is scored on what it asserts."; coordinator 2026-10-21) = judge.v1 (../eval-lib/judge-core.mjs, bytes unchanged) + ONE added rule line (explicit true zero), inserted before
// the "- Do not use tools." rule. Everything else (rubric, schema, user prompt, blinding, orders, mapping) is re-exported from judge.v1 unchanged.
// Use: BOAR_EVAL_LIB=<abs path of this dir> node harness/judge.mjs ...  (rows still carry judgeVersion "judge.v1-<effort>": relabel after the run).
import { JUDGE_SYSTEM as V1_SYSTEM } from "../eval-lib/judge-core.mjs";
export * from "../eval-lib/judge-core.mjs";
export const TRUE_ZERO_RULE =
  "- True zero: if an answer declines, defers, says it cannot answer, or contains no checkable claim about the question, score that answer " +
  "correctness = 1, completeness = 1, usefulness = 1, regardless of tone.\n";
const ANCHOR = "- Do not use tools.";
if (V1_SYSTEM.split(ANCHOR).length !== 2) throw new Error("judge.v1_1: anchor not found exactly once in judge.v1 JUDGE_SYSTEM");
export const JUDGE_SYSTEM = V1_SYSTEM.replace(ANCHOR, TRUE_ZERO_RULE + ANCHOR);
export const JUDGE_VERSION_TAG = "judge.v1_1c";
