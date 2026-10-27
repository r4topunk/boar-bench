# Second judge: Fable 5.1 vs Opus 5.5 on the same answers (2026-10-02)

Same judge.v1 prompt, same frozen Opus+web references, both orders. Answers: iPhone 13 P1 r1/r2 and desktop ios-main-v5 s42/s43 (456 verdicts per judge).

| | Opus (official) | Fable |
|---|---|---|
| iPhone, two-level ratio | 0.394 (0.353–0.441) | 0.398 (0.355–0.447) |
| Desktop v5, two-level ratio | 0.395 (0.352–0.443) | 0.405 (0.360–0.454) |
| iPhone − desktop | −0.001 | −0.007 (MDE 0.036–0.043) |

Agreement on the 456 shared verdicts:
- same winner (BOAR / reference / tie): **453 / 456 (99%)**;
- Pearson r of BOAR's mean rubric score: **0.939**; means 1.94 (Opus) vs 1.97 (Fable);
- "BOAR correct" (correctness ≥ 4) Cohen's κ: **0.894** (both correct 95, both not 344, disagree 17).

Reading: the desktop ↔ device conclusion holds under both judges, and Fable scores BOAR marginally higher (+0.004 to +0.010, inside noise).
Caveat: both judges are Claude models judging against a Claude reference. This lowers judge-noise concerns, not the
self-preference concern; that still needs the cross-family judge (r4to's call) and the 40 human pairs (analysis plan §6).
