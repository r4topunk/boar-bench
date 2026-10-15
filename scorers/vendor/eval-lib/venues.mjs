// Objective scoring for "best vegan restaurants in <city>" answers: how many named venues exist in the
// OpenStreetMap gold snapshot for that city. Pure functions (unit-tested).

const GENERIC = new Set(["vegan", "vegetarian", "cafe", "café", "restaurant", "bistro", "kitchen", "bar", "the", "food", "veggie", "green", "garden", "house", "home", "coffee", "bakery", "deli", "grill"]);

export function normalize(s) {
  return String(s ?? "")
    .normalize("NFKD")
    .replace(/[̀-ͯ]/g, "")
    .toLowerCase()
    .replace(/[’'`]/g, "")
    .replace(/[^\p{L}\p{N}]+/gu, " ")
    .trim();
}

/** A gold name is matchable if, once normalized, it is not just generic words and has at least 4 letters. */
export function matchable(name) {
  const n = normalize(name);
  if (n.replace(/\s/g, "").length < 4) return false;
  return n.split(" ").some((w) => !GENERIC.has(w));
}

/** Distinct gold venues whose name (or name:en) appears as a whole phrase in the answer. */
export function matchVenues(answer, venues) {
  const text = ` ${normalize(answer)} `;
  const seen = new Map();
  for (const v of venues) {
    for (const name of [v.name, v.nameEn].filter(Boolean)) {
      if (!matchable(name)) continue;
      const n = normalize(name);
      if (text.includes(` ${n} `) && !seen.has(n)) seen.set(n, { name, osm: v.osm, vegan: v.vegan });
    }
  }
  return [...seen.values()];
}

/** True when the answer declines or defers instead of naming places (e.g. "I don't have information"). */
export function deflects(answer) {
  return /(do(es)? not|don't|doesn't|cannot|can't|unable to)\s+(have|contain|provide|access|find|know)|no (specific )?information|not (in|included in) the (context|provided)|check (online|google|happycow)|i('m| am) not able/i.test(answer ?? "");
}

export function scoreFoodAnswer(answer, gold, { minRealVenues = 3 } = {}) {
  const pool = gold.diet === "vegan" ? gold.osm.venues.filter((v) => v.vegan === "only" || v.vegan === "yes") : gold.osm.venues;
  const matched = matchVenues(answer, gold.osm.venues);
  const matchedDiet = matchVenues(answer, pool);
  return {
    verifiedVenues: matched.length,
    verifiedDietVenues: matchedDiet.length,
    pass: matchedDiet.length >= minRealVenues,
    // Only a deflection when nothing verifiable was named ("check HappyCow" inside a good list is fine).
    deflects: matched.length === 0 && deflects(answer),
    matched: matched.map((m) => m.name),
  };
}
