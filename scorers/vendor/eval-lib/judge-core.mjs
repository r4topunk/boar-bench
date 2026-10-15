// Blind pairwise judging: prompt, blinding, seeded order, verdict mapping and aggregate stats.
// Pure functions (no process spawning) so they are unit-testable; the CLI call lives in judge.mjs.

/** Removes cues that reveal which system wrote an answer; content words are untouched. */
export function blind(text) {
  return String(text ?? "")
    .replace(/<think>[\s\S]*?<\/think>/g, "")
    .replace(/\n\**Sources:?\**\s*\n[\s\S]*$/i, "") // trailing source list
    .replace(/\(\s*\[[^\]]*\]\([^)]*\)\s*\)/g, "") // ([site](url)) source parentheticals
    .replace(/\[([^\]]+)\]\((https?:[^)]+)\)/g, "$1") // markdown links -> text
    .replace(/https?:\/\/[^\s)]+/g, "")
    .replace(/\(\s*\)/g, "") // parentheses left empty by the URL removal
    .replace(/\s*\[\d+(?:\s*[,–-]\s*\d+)*\]/g, "") // [1], [1, 2], [1-3]
    .replace(/(\*\*|__)(.*?)\1/g, "$2")
    .replace(/^\s*Answer:\s*/i, "")
    .replace(/[ \t]+([.,;:])/g, "$1")
    .replace(/[ \t]+\n/g, "\n")
    .replace(/[ \t]{2,}/g, " ")
    .trim();
}

/** mulberry32: small seeded PRNG so orders and bootstrap resamples are reproducible. */
export function rng(seed) {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

/** Which order runs first for each question (both orders always run; this only fixes the sequence). */
export function firstOrders(ids, seed) {
  const r = rng(seed);
  return Object.fromEntries(ids.map((id) => [id, r() < 0.5 ? "boarA" : "boarB"]));
}

export const RUBRIC = [
  ["correctness", "Factual accuracy. Any wrong claim that matters to the question caps this at 2. A false premise that is not corrected caps it at 1."],
  ["completeness", "Covers the key points the question needs (see the author notes); not whether it is long."],
  ["usefulness", "Would this answer actually help the person asking (e.g. a traveler without internet)? Safety-relevant advice must be safe."],
];

const scoreSchema = {
  type: "object",
  properties: Object.fromEntries(RUBRIC.map(([k]) => [k, { type: "integer", minimum: 1, maximum: 5 }])),
  required: RUBRIC.map(([k]) => k),
  additionalProperties: false,
};
export const VERDICT_SCHEMA = {
  type: "object",
  properties: {
    scores_A: scoreSchema,
    scores_B: scoreSchema,
    winner: { type: "string", enum: ["A", "B", "tie"] },
    rationale: { type: "string" },
  },
  required: ["scores_A", "scores_B", "winner", "rationale"],
  additionalProperties: false,
};

export const JUDGE_SYSTEM =
  "You are an impartial grader comparing two answers to the same question. You do not know who wrote them; " +
  "they may come from very different systems. Grade substance only.\n" +
  "Rules:\n" +
  "- Do NOT reward length, formatting, confidence or tone. A short answer that is correct and covers the essentials can win or tie.\n" +
  "- Penalize factual errors heavily. A correct 'I am not sure' is better than a confident wrong answer.\n" +
  "- If the question contains a false premise, the answer must correct it.\n" +
  "- The author notes describe what a good answer contains; they may be incomplete, and may be outdated for time-sensitive facts.\n" +
  "- Declare 'tie' when the answers are of practically equal quality.\n" +
  "- Do not use tools. Return only the structured verdict.\n" +
  "Score each answer 1-5 on:\n" +
  RUBRIC.map(([k, d]) => `  ${k}: ${d}`).join("\n");

export function judgePrompt({ question, notes, answerA, answerB }) {
  return `Question:\n${question}\n\nAuthor notes (key points of a good answer):\n${notes || "(none)"}\n\n` +
    `=== Answer A ===\n${answerA || "(empty answer)"}\n\n=== Answer B ===\n${answerB || "(empty answer)"}\n\n` +
    "Return the scores for A and B, the winner (A, B or tie) and a one or two sentence rationale.";
}

/** Maps a positional verdict back to systems. */
export function mapVerdict(v, boarIsA) {
  const boar = boarIsA ? v.scores_A : v.scores_B;
  const ref = boarIsA ? v.scores_B : v.scores_A;
  const winner = v.winner === "tie" ? "tie" : (v.winner === "A") === boarIsA ? "boar" : "ref";
  return { winner, boar, ref };
}

export const meanScore = (s) => RUBRIC.reduce((a, [k]) => a + s[k], 0) / RUBRIC.length;

/** Combines the two orders of one pair: agreement keeps the verdict, disagreement is a tie. Scores are averaged. */
export function combineOrders(a, b) {
  const winner = a.winner === b.winner ? a.winner : "tie";
  const avg = (x, y) => Object.fromEntries(RUBRIC.map(([k]) => [k, (x[k] + y[k]) / 2]));
  return { winner, consistent: a.winner === b.winner, boar: avg(a.boar, b.boar), ref: avg(a.ref, b.ref) };
}

/** Win score: win = 1, tie = 0.5, loss = 0 (from BOAR's side). */
export const winPoints = (w) => (w === "boar" ? 1 : w === "tie" ? 0.5 : 0);

export function percentile(sorted, p) {
  if (!sorted.length) return NaN;
  const i = (sorted.length - 1) * p;
  const lo = Math.floor(i), hi = Math.ceil(i);
  return sorted[lo] + (sorted[hi] - sorted[lo]) * (i - lo);
}

/** Percentile bootstrap 95% CI of statFn over items (resampled with replacement, seeded). */
export function bootstrapCI(items, statFn, { seed = 1, n = 2000 } = {}) {
  if (!items.length) return [NaN, NaN];
  const r = rng(seed);
  const stats = [];
  for (let i = 0; i < n; i++) {
    const sample = Array.from({ length: items.length }, () => items[Math.floor(r() * items.length)]);
    stats.push(statFn(sample));
  }
  stats.sort((x, y) => x - y);
  return [percentile(stats, 0.025), percentile(stats, 0.975)];
}

/** Aggregates combined pairs: win/tie/loss rates, win score with CI, rubric means, BOAR/reference ratio with CI. */
export function summarize(pairs, { seed = 1 } = {}) {
  const n = pairs.length;
  const rate = (w) => pairs.filter((p) => p.winner === w).length / n;
  const winScore = (ps) => ps.reduce((a, p) => a + winPoints(p.winner), 0) / ps.length;
  const ratio = (ps) => ps.reduce((a, p) => a + meanScore(p.boar), 0) / ps.reduce((a, p) => a + meanScore(p.ref), 0);
  const rubric = (side) => Object.fromEntries(RUBRIC.map(([k]) => [k, pairs.reduce((a, p) => a + p[side][k], 0) / n]));
  return {
    n,
    boarWin: rate("boar"),
    tie: rate("tie"),
    refWin: rate("ref"),
    winScore: winScore(pairs),
    winScoreCI: bootstrapCI(pairs, winScore, { seed }),
    qualityRatio: ratio(pairs),
    qualityRatioCI: bootstrapCI(pairs, ratio, { seed: seed + 1 }),
    positionConsistency: pairs.filter((p) => p.consistent).length / n,
    rubricBoar: rubric("boar"),
    rubricRef: rubric("ref"),
  };
}

/** Cohen's kappa between two label arrays (e.g. hand labels vs judge winners). */
export function cohenKappa(a, b) {
  const labels = [...new Set([...a, ...b])];
  const n = a.length;
  const po = a.filter((x, i) => x === b[i]).length / n;
  const pe = labels.reduce((s, l) => s + (a.filter((x) => x === l).length / n) * (b.filter((x) => x === l).length / n), 0);
  return pe === 1 ? 1 : (po - pe) / (1 - pe);
}
