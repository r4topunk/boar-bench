import { readFileSync } from "node:fs";
import { EvalTrace } from "@boar-eval/protocol";

export function readTraces(path: string): EvalTrace[] {
  return readFileSync(path, "utf8").split("\n").filter((l) => l.trim()).map((l) => EvalTrace.parse(JSON.parse(l)));
}

/** The run's headline counts (the ones exp-06/08b report). */
export function summarize(traces: EvalTrace[]) {
  const tiers: Record<string, number> = {};
  for (const t of traces) tiers[String(t.route.tier)] = (tiers[String(t.route.tier)] ?? 0) + 1;
  return {
    n: traces.length,
    errors: traces.filter((t) => t.error).length,
    declined: traces.filter((t) => t.answer.declined).length,
    weakSources: traces.filter((t) => t.answer.weakSources).length,
    noShownSources: traces.filter((t) => !t.answer.shown.length).length,
    tiers,
    rawSources: traces.reduce((s, t) => s + t.retrieval.raw.length, 0),
    keptSources: traces.reduce((s, t) => s + t.retrieval.kept.length, 0),
    droppedSources: traces.reduce((s, t) => s + t.retrieval.dropped.length, 0),
  };
}

/** Keys that measure time or host state: ignored when two runs are compared for determinism. */
const VOLATILE = /^(tMs|createdAt|loadAvg1m|ms|at)$|Ms$|TokPerSec$|tokPerSec$/;

/** A deep copy without volatile keys (timing, createdAt, loadAvg). */
export function stable(v: unknown): unknown {
  if (Array.isArray(v)) return v.map(stable);
  if (v && typeof v === "object") {
    return Object.fromEntries(Object.entries(v).filter(([k]) => !VOLATILE.test(k)).map(([k, x]) => [k, stable(x)]));
  }
  return v;
}

/** First differing path between two values, or null. */
export function firstDiff(a: unknown, b: unknown, path = ""): string | null {
  if (JSON.stringify(a) === JSON.stringify(b)) return null;
  if (a && b && typeof a === "object" && typeof b === "object") {
    const keys = [...new Set([...Object.keys(a), ...Object.keys(b)])];
    for (const k of keys) {
      const d = firstDiff((a as any)[k], (b as any)[k], `${path}.${k}`);
      if (d) return d;
    }
  }
  return path || "(root)";
}
