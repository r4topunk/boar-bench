// judge.v1_1 (wording W2, used only if W1 fails decline validity) = judge.v1 (../eval-lib/judge-core.mjs, bytes unchanged) + ONE added rule line (explicit true zero), inserted before
// the "- Do not use tools." rule. Everything else (rubric, schema, user prompt, blinding, orders, mapping) is re-exported from judge.v1 unchanged.
// Use: BOAR_EVAL_LIB=<abs path of this dir> node harness/judge.mjs ...  (rows still carry judgeVersion "judge.v1-<effort>": relabel after the run).
import { JUDGE_SYSTEM as V1_SYSTEM } from "../eval-lib/judge-core.mjs";
export * from "../eval-lib/judge-core.mjs";
export const TRUE_ZERO_RULE =
  "- True zero (this rule overrides the others): an answer that declines, defers, redirects the user to other sources, says it cannot answer, " +
  "or makes no specific checkable claim that answers the question scores exactly 1 on correctness, 1 on completeness and 1 on usefulness. " +
  "Asserting nothing is not the same as being correct: correctness rewards only true claims the answer actually makes. " +
  "A partial answer is scored on what it asserts.\n";
const ANCHOR = "- Do not use tools.";
if (V1_SYSTEM.split(ANCHOR).length !== 2) throw new Error("judge.v1_1: anchor not found exactly once in judge.v1 JUDGE_SYSTEM");
export const JUDGE_SYSTEM = V1_SYSTEM.replace(ANCHOR, TRUE_ZERO_RULE + ANCHOR);
export const JUDGE_VERSION_TAG = "judge.v1_1b";
