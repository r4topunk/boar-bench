# BOAR bench v0.4 "ruler": public dataset card (derived)

TL;DR: v0.4 is a 75-item held-out ruler written by two model families for the claim runs of poidh bounty #31. **The items, the references and the drafting record stay private; this repository publishes only commitments (sha256 of the item files), counts, the pipeline and the limits.** If the author later publishes the plaintext, anyone can check that it hashes to the values below. Until then the set is held out: no tuning, no prompts, packs or retrieval work against it.

This card is derived from the internal card. It drops everything that would reveal item content (per-item topics, question text, region lists, near-duplicate pairs, time-sensitive examples, the writer prompts with their topic lists).

## Commitments

| File (private, held out) | Items | sha256 |
|---|---:|---|
| `items.jsonl` (frozen set) | 75 | `f9ad2f2f0fc367811ea03690bc9b05e52d85b1ee5fb662600efa818587d33594` |
| `items.candidate.jsonl` (pre-balance-round candidate) | 70 | `23b6febf66372f5b21bd94a2316cfd5da3187dbb37b493b2fd7e8a512e4c2993` |

Both are in `SHA256SUMS`. `refs/v2/MANIFEST.json` carries the commitment for the reference files (generator and prompt shas, row counts). The set was frozen on 2026-10-20 before any answering system saw an item.

## Purpose
A cross-family ruler for the bounty claim ("offline research assistant > 50 % as good as internet + frontier AI"): casual lookup and research questions a curious person asks with the phone offline or on a trip, in the families of the test questions in the post that inspired the bounty (place overview, technical research, humanities, science and everyday health, travel). English only (our choice).

## Headline and anchors
- **Headline U = 71 items** (every item with `tags.anchor_vexact = false`).
- **4 "V-exact" anchors**, reported separately and excluded from U: they copy or near-copy test questions that the bounty-inspiring post itself published, so any system may have been shaped on them. They link the ruler to those public questions; they are not evidence.
- Multi-turn conversations (8) are reported separately and also inside U.

## Writers and pipeline
| Step | Who | Notes |
|---|---|---|
| 1. Draft (36 each) | a Claude agent (Claude Opus) and OpenAI gpt-5.6-sol via the Codex CLI (reasoning high, web disabled) | from the blueprint and the bounty text only; no packs, kit, traces or scores |
| 2. Cross-critique | Codex critiqued the Claude items (36 fixes, mostly tags); Claude critiqued the Codex items (26 keep, 8 fix, 2 reject) | fix: fixed item; reject: logged with a reason (private) |
| 3. Fact-check, live web | both families on every point of every surviving item; current-place items: at least 3 real matching places checked by both | a point is kept if at least 1 family supported it and neither contradicted it; otherwise it goes to a disagreement log (private) |
| 4. Assembly | a Claude agent | no item invented or rewritten at assembly; no system output consulted |
| 5. Author decisions (2026-10-20) | r4to | apply the 3 suggested resolutions and re-verify; tag the V-exact anchors; add a balance round |
| 6. Balance round r2 | Codex wrote 3 new items in a fresh directory (blueprint and bounty text only, web disabled); a Claude agent wrote 3 items and replaced 1; cross-critique and fact-check by both families | 32/32 new points supported by both; 2 edited points supported by both; 1 Codex item contradicted by both and dropped |
| 7. Freeze | coordinator | sha256 of `items.jsonl` taken before any system answered |

Approvals recorded 2026-10-20: Codex as second writer and checker family; acute-emergency scenarios kept out of the scored set (none present; 11 items are ordinary health or safety questions); resolutions of step 5.

## Counts (75 items = 67 single-turn + 8 multi-turn; 3 rejected)
| | Claude | Codex | Total |
|---|---:|---:|---:|
| Accepted | 39 | 36 | 75 |
| Rejected | 0 | 3 | 3 |
| Headline U (non-anchor) | 39 | 32 | 71 |

- Single-turn by family: place 14, tech 13, humanities 14, science 12, travel 14.
- Single-turn by type: lookup 13, explanation 16, comparison 12, synthesis 12, reasoning 14.
- Multi-turn (8): correction 2, constraint change 2, context carry 1, drill-down 1, comparison follow-up 1, recall 1; 3 are 2-turn and 5 are 3-turn.
- Tags (all 75): over-refusal 4; "1B-fail candidate" 66 (single-turn 58/67); time-sensitive 19 (state as of the check date, 2026-10-20); health/safety 11, acute emergency 0; situation travel 23 / at home 52; device location supplied 7; V-exact anchor 4.
- Region, place-bound items: 39 of 46 (85 %) are centred outside Europe and North America (target at least 40 %).
- Fact-check points: 329 on accepted items, each supported by at least 1 family and contradicted by none; 0 pending.

## Known limits
- Uneven cells: tech single-turn 13 (target 14); place and travel 14 (target 12); reasoning 14 (target 12).
- Multi-turn shapes: four of the six shapes have one conversation each.
- Writer imbalance: Claude 39 vs Codex 36; headline U is 39 Claude / 32 Codex because all 4 anchors are Codex-written. Report every number per writer family.
- One Claude agent acted as writer, critic and fact-checker in the balance round; the cross-family rule still holds because Codex critiqued and checked every Claude item.
- 19 time-sensitive items carry facts dated 2026-10-20: report U with and without them; a later re-check may change the gold.
- Near-duplicate intents exist across the two writers (same or overlapping task shapes, all kept, none identical).
- Readers so far: the writer, critic and fact-check agents of both families, the assembly agent, the coordinator, and the author through a review page. No answering system has seen any item.

## Files
- Published here: this card, `SHA256SUMS`, `refs/v2/MANIFEST.json`.
- Private (held out): `items.jsonl`, `items.candidate.jsonl`, the reference files, the drafts, critiques and fact-checks, the rejected-items log, the disagreement log and the changelog.

## UNKNOWN
- Whether and when the plaintext and references are published (the author's decision; unsealing also turns the set into a development set).
- Whether the near-duplicate pairs should be thinned (no rule in the blueprint; kept, frozen as is).
