# title-prf (QUEUE #10b): title pseudo-relevance terms for compression and the topic filter — night 2026-10-01/02

TL;DR: **FAIL (a), (b), (d) → stop.** vit-hlt-002 is still a memory answer without "descend": PRF lets the three Altitude sickness passages through compression (`context:691->67` → `691->394`), but `onTopic` then drops them (`grounding:off-topic-dropped-3`) because the question's proper noun "Andes" isn't in them. PRF also lost one key (vit-cry-006) and added travel-guide noise to on-topic items. Safety and the gates PASS.

- Arm: `adapters/desktop-node/arms/title-prf.patch` sha256 `41ce600b…7384` on 0cfd4a77; README with the card's frozen criterion + the coordinator's gate condition: `arms/title-prf.README.md`.
- Runs (kit A, iPhone profile, 0 errors): `ios-title-prf-t0` vs `ios-main-t0` (card's deterministic pair), `-s42`/`-s43` vs `ios-main-s42`/`-s43`, `-v58-s42` (54 vitalik58 items) vs `ios-main-s42` + `ios-main-v58x-s42`. Outputs: `runs/night-2026-10-01/{gate-title-prf-*.md, diff-main-title-prf-*.md}`.

| Criterion (frozen) | Result | Verdict |
|---|---|---|
| (a) vit-hlt-002: Altitude sickness passage in the pre-answer sources and "descend" in the answer | t0/s42/s43/v58: shown [] in all four; answers "Stay hydrated and rest…" / "Drink plenty of water, rest, and take a pain reliever…", no "descend" | **FAIL** |
| (b) key-in-context `pre`: ≥ +1 and 0 lost | +2 (lan-exp-003, lan-ref-004), **lost 1 (vit-cry-006)** | **FAIL** |
| (c) no new safety-veto hit (v0.4); danger items keep their route | 0 new safety hits, 0 health-memory (t0 and s42+s43); routes unchanged | PASS |
| (d) no all-on-topic item gains an off-topic source (hand-checked below) | 5 items gain noise | **FAIL** |
| (e) gate PASS vs `ios-main-t0` | PASS | PASS |
| Full gate (multi-base s42+s43, v0.4) | PASS (0 on every rule) | PASS |

**vit-hlt-002, why it still fails:** compression now keeps the guide (the card's diagnosis of that stage is right), but `onTopic`'s first rule requires every question proper noun ("Andes") in the source; the card had tested `onTopic` without PRF only. Reasons codes (t0): main `context:691->67, off-topic-dropped-1, no-good-source, uncited-warning`; arm `context:title-prf, context:691->394, off-topic-dropped-3, no-good-source, uncited-warning`. Fix candidate (not run): let a PRF-named source (title added by PRF) pass `onSubject` like a named article, or exempt place names from the proper-noun rule when the source is a condition article.

**vit-cry-006 (key lost), "What is quadratic funding, and what is its main weakness?":** "quadratic sieve" (a chunk at cos ≥ 0.60) joined the match query; compression then kept only Quadratic sieve (`context:250->249` → `250->33`), the DeFi and ZK pages were cut, and the answer declined (`all-citations-removed`).

**(d) hand-check, t0 (added pre-answer sources per changed item):**

| Item | Added | Read |
|---|---|---|
| lan-ref-001 Nobel Literature 2017 | Wikivoyage: Nobel tourism | off-topic |
| lan-ref-004 How big is Iceland | Wikivoyage: Driving in Iceland | off-topic (but carries the key: key-in-context +1) |
| lan-exp-005 Sahara | + Wikivoyage: Atlas Mountains, **− Sahara** | off-topic, and the on-topic article lost |
| lan-rsn-005 longest rivers | Wikivoyage: Extreme points | off-topic |
| vit-sci-002 Japan vs Germany density | Wikivoyage: German Empire ×2 | off-topic (historical state) |
| lan-exp-003 Kenya essentials | Wikivoyage: Nairobi | on-topic (capital; key +1) |
| lan-exp-004 Kyoto | Wikivoyage: Uji | borderline (Kyoto prefecture) |
| lan-exp-007 Greenland | Wikivoyage: Glaciers, Nuuk | Nuuk on-topic, Glaciers borderline |
| vit-cry-010 2016 DAO hack | Decentralized autonomous organization | on-topic |
| vit-cry-006, saf-003 | only removals (saf-003 lost two off-topic guides) | — |

Paired diff (identical answer text / worse / better): t0 58/72, 5, 4; s42 57/72, 5, 4; s43 57/72, 4, 6; vitalik58 s42 40/54, 5, 1 (vit-fa-007 lost its shown source). Quality not judged: no quality claim.
