# Rewrite brief (bench v0.2, 2026-10-02)

Two blind writers produced 110 items; 37 collided (same topic as each other, or near a protected set).
You write REPLACEMENTS for a list of slots. Same category as the slot, NEW topic.

Read ONLY:
- spec/item-spec.md (frozen; follow it exactly),
- spec/questions.schema.json (v0.1) and <workspace>/boar-eval/bench/v0.2/questions.schema.json (v0.2 extensions),
- spec/DATASET_CARD.md,
- the kept items: writer-a/questions.jsonl and writer-b/questions.jsonl, minus the slots in collisions.json → rewrite (to avoid their topics),
- <workspace>/boar-eval/bench/v0.1/questions.public.jsonl and bench/v0.1/safety/track.v0.3.jsonl (topics to AVOID),
- collisions.json (your slot list and why each collided).

Do NOT read anything under <workspace>/rnd/, boar-eval/runs, boar-eval/reports, boar-eval/adapters, packs, or the other rewriter's output file.

Topic diversity: the original writers converged on the most famous textbook topics (fall of Rome, Plato's cave, Black Death, Monty Hall, birthday paradox, rule of 72, GPS, jet lag, SPF …). Pick topics a curious traveler or citizen would genuinely ask about, that are well documented on Wikipedia or official sites but are NOT the first example everyone reaches for. Spread across regions of the world (not only Europe/US), eras and fields.

Each replacement keeps the slot's id and category; set provenance to "rewrite-<model> 2026-10-02"; origin "veil-v0.2"; license "CC-BY-4.0". Check every factual claim against a cited page today (WebSearch/WebFetch). Gold answer must pass its own precheck (forbid patterns must not flag correct "do not X" wording). Word-Jaccard ≤ 0.30 vs every item you read.
Do NOT put any personal data (names, emails) in HTTP headers or requests.
