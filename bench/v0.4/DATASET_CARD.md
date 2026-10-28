# BOAR bench v0.4 "ruler": dataset card

**Status (v1.1, 2026-10-27): retired, public development data.** The ruler was held out from its freeze (2026-10-20 16:42 -0300) until the project was submitted; it was answered by the claim systems for the final device run and then opened by the author. A number measured on it from now on validates nothing. The item files are byte-identical to the frozen files: `items.jsonl` (75 items) sha256 `f9ad2f2f0fc367811ea03690bc9b05e52d85b1ee5fb662600efa818587d33594`, `items.candidate.jsonl` (70 items, pre-r2) `23b6febf66372f5b21bd94a2316cfd5da3187dbb37b493b2fd7e8a512e4c2993`, both in `SHA256SUMS` and public since v1.0. The text below is the card written at the freeze; its rule "engine work must never use these items" applied while the ruler was held out. Every edit from the candidate to the frozen set is in `CHANGELOG.md`.

**Licence.** Items, rubrics (checklists), critiques and fact-check records: CC BY 4.0 (BOAR bench, r4to). Written by Claude Opus 5.5 (cw-*) and OpenAI gpt-5.6-sol through the Codex CLI (cx-*). The 4 V-exact anchors copy or near-copy public test questions by Vitalik Buterin (the post that inspired the bounty), quoted with attribution; he is named as the inspiration only. Reference answers (`refs/v2/`) and drafts are model + live-web outputs and may quote the pages they cite, which keep their own terms. 11 items are ordinary health or safety questions; no acute-emergency scenario is in the set.

**Changed on the way out.** `refs/v2/claude.jsonl` and `codex.jsonl`: per-call `usage` (token counts, list-price equivalent, cost basis) dropped and the plan label in `via` neutralised; answers byte-identical. Their sha256 and the `refs/v2/MANIFEST.json` pin changed: old and new values in `../heldout/HASHES.md`. Draft logs: a local scratch path, a login-method flag and rate-limit wording neutralised. The round-1 writer prompts are described in the blueprint (`boar-research` `rnd/research/coordinator/BENCH-ITEMS-BLUEPRINT-2026-10-20.md`); the round-2 Codex prompts are in `drafts/r2/`.

## Purpose
A cross-family ruler for poidh bounty #31 ("offline research assistant > 50 % as good as internet + frontier AI"): casual lookup and research questions a curious person asks with the phone offline or on a trip, in the families of Vitalik's own test questions (place overview, technical research, humanities, science and everyday health, travel). English only (our choice).

## Blueprint
rnd/research/coordinator/BENCH-ITEMS-BLUEPRINT-2026-10-20.md (revision r2 supersedes r1 quotas). Bounty text: BOUNTY_31.md.

## Headline and anchors
- **Headline U = 71 items** (all items with `tags.anchor_vexact=false`).
- **V-exact anchors (4), reported separately and excluded from the headline U:** cx-001 (Tell me about Japan), cx-007 (Which signature algorithms are quantum resistant?), cx-014 (Explain Mozi's views on universal love.), cx-015 (Why does Gríma kill Saruman in The Lord of the Rings?). They copy or near-copy Vitalik's public test questions (`tags.anchor_vexact_question`), so any system may have been shaped on them; they serve as a link to V-exact, not as evidence.
- Multi-turn (8) reported separately as well as inside U.

## Writers and pipeline
| Step | Who | Notes |
|---|---|---|
| 1. Draft (36 each) | Claude agent (cw-*), Codex gpt-5.6-sol, reasoning high, web disabled (cx-*) | from the blueprint + bounty text only; no packs, kit, traces or scores |
| 2. Cross-critique | Codex critiqued cw-* (36 fix, mostly tags: situation, health_safety, time_sensitive); Claude critiqued cx-* (26 keep, 8 fix, 2 reject) | fix -> fixed_item; reject -> REJECTED.jsonl with reason |
| 3. Fact-check, live web | both families on every point of every surviving item; current-place items: >= 3 real matching places checked by both | merge rule: point kept if >= 1 family supported and neither contradicted; else DISAGREEMENTS.md |
| 4. Assembly | Claude agent | no item invented or rewritten at assembly; no system output consulted |
| 5. r4to decisions (2026-10-20) | r4to | 4a apply the 3 suggested resolutions + re-verify; 4b tag V-exact anchors; 4c balance round |
| 6. Balance round r2 | Codex wrote cx-037..039 (fresh dir: blueprint + bounty only, web disabled); Claude (coordinator, claude-opus-5-5) wrote cw-037..039 and replaced cw-034 (now context carry); cross-critique (Codex on cw-*: 1 fix, 3 keep; Claude on cx-*: 1 fix, 2 keep); fact-check by both on the open web (Codex web live) | 32/32 new points supported by both; edited points: cw-002 and cw-032 supported by both, cx-012 contradicted by both -> dropped |
| 7. Freeze | coordinator | sha256 of items.jsonl before any system answers |

User approvals recorded 2026-10-20: Codex as second writer/checker family; acute-emergency scenarios kept out of the scored set (none present; 11 items are ordinary health/safety); resolutions 4a-4c above.

## Counts (frozen: 75 items = 67 single-turn + 8 multi-turn; 3 rejected)
| | Claude | Codex | Total |
|---|---|---|---|
| Accepted | 39 | 36 | 75 |
| Rejected | 0 | 3 (cx-017, cx-025 at critique; cx-012 at r2 re-verification) | 3 |
| Headline U (non-anchor) | 39 | 32 | 71 |

Single-turn by family (r2 target in brackets): place 14 (12), tech 13 (14), humanities 14 (14), science 12 (12), travel 14 (12). Per writer: Claude 7/7/7/7/7, Codex 7/6/7/5/7.

Single-turn by type (target): lookup 13 (12), explanation 16 (16), comparison 12 (12), synthesis 12 (12), reasoning 14 (12). Per writer Claude 7/8/6/7/7, Codex 6/8/6/5/7.

Multi-turn (8): correction 2 (cw-033, cx-033), constraint change 2 (cw-035, cx-035), context carry 1 (cw-034), drill-down 1 (cx-034), comparison follow-up 1 (cw-036), recall 1 (cx-036). Turns: 2-turn 3, 3-turn 5. In the file the shape labels stay as drafted (e.g. "wrong premise correction", "recall of turn 1").

Tags (all 75): over-refusal 4; 1B-fail candidate 66 (single-turn 58/67 = 87 %); time-sensitive 19 (state as of the check date 2026-10-20); health/safety 11, acute emergency 0; situation travel 23 / at home 52 (31 %); device location supplied (context) 7; anchor_vexact 4.

Region: asia 17, africa 11, europe 7, latam 6, oceania 5, global 29. Place-bound items outside Europe/North America 39/46 (85 %, target >= 40 %). Europe items: cw-016, cw-034, cw-037, cw-038, cx-037, cx-038, cx-039.

Fact-check points: 329 on accepted items, all supported by >= 1 family and contradicted by none; 0 pending.

## Known limits
- Tech single-turn 13/14 (cx-012 dropped at r2); place and travel 14 vs 12 (balance round added Europe items there); reasoning 14 vs 12.
- Multi-turn shapes: context carry, drill-down, comparison follow-up and recall have 1 conversation each (blueprint r1 wanted 2 each of 6 shapes; r2 reduced to 8 conversations).
- Writer imbalance: Claude 39 vs Codex 36 (Codex lost 3 to rejection); headline U is 39 Claude / 32 Codex because all 4 anchors are Codex-written. Report every number per writer family.
- Claude wrote both the r2 Claude items and acted as Claude critic/fact-checker for r2 (one family member in several roles; the cross-family rule still holds: Codex critiqued and checked every Claude item).
- Time-sensitive items (19) carry facts dated 2026-10-20 (e.g. cw-032 border closed since June 2025; ACTV fares; EU status of Moldova; current venues). Report U with and without them (BENCH-RULER R-D4); a later re-check may change the gold.
- Near-duplicates across writers (same or overlapping intent; all kept, none identical):
  - cw-024 / cx-024 mineral vs chemical/organic sunscreen (near-identical intent)
  - cw-031 / cx-031 International Date Line "land before take-off" (near-identical intent)
  - cw-030 / cx-032 trans-Pacific flight to Santiago, real duration across time zones (same task shape)
  - cw-022 / cx-022 altitude sickness / acclimatization (overlapping)
  - cw-008 / cx-011 EIP-1559 (explanation vs synthesis, overlapping)
  - cw-007 / cx-007 quantum-resistant signatures (cx-007 is an anchor); cx-034 also covers lattice vs hash-based
  - related clusters, distinct intents: cw-017 / cx-014 (classical Chinese philosophy; cw-034 no longer in it); cw-025 / cx-021 (mosquito-borne disease); cw-011 (second-price auctions); cw-010 / cx-010 (consensus); cw-029 / cx-027 (same city, Marrakesh)
- Readers so far: writer, critic and fact-check agents of both families, the assembly agent, the coordinator, and r4to via the review artifact. No answering system has seen any item.

## Files
- items.jsonl: frozen set. Schema as the candidate (id, writer, family, type, turns, context, tags, checklist, reference_sources, notes, critique, factcheck) plus `tags.anchor_vexact` (all items), `tags.anchor_vexact_question` (anchors), `changelog` (edited/new items), `critique.round` / `factcheck.round` = "r2" on r2 items, `factcheck.r2_note` on re-verified items.
- items.candidate.jsonl: pre-r2 candidate (70), unchanged.
- SHA256SUMS: sha256 of items.jsonl and items.candidate.jsonl.
- CHANGELOG.md: every edit from the candidate to the frozen set.
- REJECTED.jsonl: 3 rejected items with stage, critic and reason.
- DISAGREEMENTS.md: the 5 disputed candidate points and their resolution.
- refs/v2/: reference answers by both families (Claude Opus + web, Codex gpt-5.6-sol + web), their call logs and `MANIFEST.json`.
- drafts/: round-1 raw drafts, critiques, fact-checks and Codex logs; drafts/r2/: balance-round drafts, critiques, both fact-checks, Codex prompts and run log, assemble_r2.py.

## UNKNOWN
- Claude writer, critic and fact-checker in round 1 = claude-opus-5-5, effort medium (workflow boar-ruler-items, run wf_39928fe0-dc8); r2 Claude roles = claude-opus-5-5 (coordinator-delegated agent); Codex = codex-cli 0.144.3, gpt-5.6-sol, high reasoning.
- Whether near-duplicate pairs should be thinned (blueprint has no rule; kept both, frozen as is).
