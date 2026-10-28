# bench v0.4 ruler: changelog

Every edit between the candidate (items.candidate.jsonl, boar-eval a8c3b04, 70 items) and the frozen set (items.jsonl). items.candidate.jsonl is kept unchanged. Each edited item also carries a `changelog` field.

## 2026-10-20 r2 (approved by r4to 2026-10-20)

### 4a. Disputed points resolved (DISAGREEMENTS.md suggested resolutions)
| id | change | re-verified (Claude / Codex, live web) |
|---|---|---|
| cw-002 | P4 reworded: "Vajrayana (Drukpa Kagyu) Buddhism is the dominant religion and constitutionally the country's 'spiritual heritage' (there is no declared state religion); national language Dzongkha" | supported / supported (Constitution 2008 Art. 1(8), Art. 3(1): constituteproject.org; parliament.gov.bt) |
| cw-032 | P1-P3 rewritten: land border (incl. Aranyaprathet-Poipet) closed since June 2025, dated status, no reopening announced as of October 2026; alternative = fly Bangkok-Siem Reap; recheck an official advisory. P4 (e-visa, scams) and P5 (Angkor pass) kept with their original fact-check. Question text unchanged (the user asks overland). time_sensitive=true. reference_sources: Poipet/Aranyaprathet Wikipedia pages replaced by Smartraveller Cambodia | P1-P3 supported / supported (pixidia.com 2026-10-07 status, cambodiakingdom.com; visit-thailand.org, flightconnections BKK-SAI, smartraveller.gov.au) |
| cx-012 | P1 reworded: "truthful bidding is a dominant strategy in a standard private-values second-price auction, and fake identities and shill bids break the conditions behind it" | **contradicted by both** (Codex first; Claude withdrew its "supported" on review): in a one-item second-price auction a fixed seller shill bid raises the price but truthful bidding stays weakly dominant, and fake bidder identities do not break it. **cx-012 dropped** (moved to REJECTED.jsonl, stage "r2 fact-check"), per the rule "unresolved point: drop the item rather than guess" |

### 4b. V-exact anchors
cx-001 (Tell me about Japan), cx-007 (Which signature algorithms are quantum resistant?), cx-014 (Explain Mozi's views on universal love.), cx-015 (Why does Gríma kill Saruman in The Lord of the Rings?) tagged `anchor_vexact=true` with `anchor_vexact_question`; reported separately and excluded from the headline U. All other items carry `anchor_vexact=false`.

### 4c. Balance round
Same pipeline as the original round: Codex (codex-cli 0.144.3, gpt-5.6-sol, high reasoning, read-only sandbox, fresh dir with only blueprint + bounty text + prompt, web disabled) wrote cx-037..cx-039; Claude (coordinator session, claude-opus-5-5) wrote cw-037..cw-039 and the cw-034 replacement. Cross-critique: Claude on cx-*, Codex (web disabled) on cw-*. Fact-check: both families on the open web (Codex web_search=live). Merge rule: a point stays if at least one family supports and neither contradicts. Writers saw no packs, traces or scores. Raw files in drafts/r2/.

| id | writer | family / type | region / situation | critique |
|---|---|---|---|---|
| cw-034 (replaced) | claude | humanities / multiturn, shape context carry | europe / travel | codex keep |
| cw-037 | claude | travel / reasoning (Camino Portugues days at 20 km/day) | europe / travel | codex fix (dropped the credential/Compostela point as off-question) |
| cw-038 | claude | place / lookup ("Tell me about Moldova") | europe / at home | codex keep |
| cw-039 | claude | science / synthesis (caffeine and sleep) | global / at home | codex keep |
| cx-037 | codex | humanities / comparison (Spinoza vs Leibniz on freedom) | europe / at home | claude keep |
| cx-038 | codex | travel / reasoning (Venice islands by vaporetto, singles vs 24 h pass; device location) | europe / travel | claude fix (P4 states the expected conclusion: 24-hour pass cheaper) |
| cx-039 | codex | place / synthesis (Republic of Ragusa and Dubrovnik) | europe / at home | claude keep (duplicate output line removed) |

cw-034 before: drill-down "what were the main schools of thought in ancient china" (3 turns, region asia). Replaced because context carry was 0/8 and classical Chinese philosophy was over-represented (cw-017, cw-034, cx-014).

### Drops and fact-check outcome
- cx-012 dropped (see 4a). No new item dropped: all 32 points on the 7 new/replaced items supported by both families, none contradicted.
- Claude's fact-check initially marked the cx-012 rewording supported; revised to contradicted after reading Codex's note and re-deriving the single-item case (drafts/r2/factcheck-claude.jsonl note).

### Freeze
items.jsonl frozen 2026-10-20 16:42 -0300, sha256 f9ad2f2f0fc367811ea03690bc9b05e52d85b1ee5fb662600efa818587d33594 (75 items). items.candidate.jsonl (sha256 23b6febf66372f5b21bd94a2316cfd5da3187dbb37b493b2fd7e8a512e4c2993) kept unchanged as the pre-r2 record. Assembly script: drafts/r2/assemble_r2.py (merges critiques and both fact-checks; no item text written there).

