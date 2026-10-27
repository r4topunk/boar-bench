# cmpsplit (QUEUE #3): comparison entity split retrieval — night 2026-10-01

TL;DR: **v1 FAILS the card's criterion (a)** on both kits, so per the card: stop (v2 = #3b, section below). Retrieval does recover sides (vital5 kit: sides in `retrieval.raw` 17/24 → 22/24), but the prompt barely moves (13/24 → 16/24; both sides 3/12 → 4/12 items, +8 pp vs the +30 pp bar) because context assembly drops the recovered side. Gate PASS on every pair, 0 false fires, 0 errors.

- Arm: `adapters/desktop-node/arms/cmpsplit.patch` sha256 `9928cd28…847e` on `upstream/main` 0cfd4a77; README (frozen criterion, gold sides, kit coverage note): `adapters/desktop-node/arms/cmpsplit.README.md`.
- Adapter: desktop-node, iPhone profile (4 GB iOS, qwen2.5-1.5b, quick mode). Scripts: `arms/cmpsplit-slice.py` (a/b/c/e), `harness/gate.py`, `harness/diff.py`; outputs in `runs/night-2026-10-01/` (`cmpsplit-*-slice.txt`, `diff-main-cmpsplit-*.md`).
- "Prompt" = the `sources` event (`answer.shown`), emitted before generation, so sampling doesn't move it (main s42 vs s43: identical).

## Verdict per criterion (v1)

| Criterion (frozen) | night kit t0 (7 items) | night kit s42 / s43 | vital5 kit t0 (12 items) | Verdict |
|---|---|---|---|---|
| (a) both sides in context +≥ 30 pp | 1/7 → 1/7 (+0) | +0 / +0 | 3/12 → 4/12 (+8 pp) | **FAIL** |
| (b) citation-check declines on the slice −≥ 3 | 1 → 0 | 1 → 1 / 3 → 2 | 1 → 1 | FAIL (−1 at most) |
| (c) non-comparison items with changed retrieval | 0/65 | 0/65 / 0/65 | 0/66 | PASS (0 false fires) |
| (d) confident-wrong / safety | gate PASS (0 new safety hits, 0 health-memory) | PASS / PASS | PASS | safety PASS; CW needs the judge (not run) |
| (e) retrieval p50 +≤ 50 ms (desktop) | 81 → 141 (+60) | +97 / +47 | 109 → 202 (+93) | FAIL (2 extra embeddings + searches, M4 CPU) |

Paired diff (`harness/diff.py`): identical answer text 68/72 (t0), 68/72 (s42), 69/72 (s43), 71/78 (vital5); worse 0 / 1 / 0 / 0 (s42: vit-cry-005 declined after an EIP-7503 passage displaced a Tornado Cash one), better 1 / 1 / 1 / 2 (vit-sci-002 now answers with Wikivoyage: Japan). Gates re-run with `--safety-version v0.4` and the multi-run base (`--base main-s42 main-s43 --cand cmpsplit-s42 cmpsplit-s43`): PASS (`runs/night-2026-10-01/gate-cmpsplit-v1-*.md`). Quality (judge ratio) not measured: arm runs not judged, so no quality effect is claimed. Sonar's key-in-context on the vital5 pair: raw gained 1 (vit-fa-022), pre-answer 0 gained / 0 lost.

## Why the prompt doesn't move (reason codes)

1. **Kit coverage (night kit):** most gold sides have no article in essential corpus + crypto + Wikivoyage (no Mozi, Confucianism, Polar/Grizzly bear, Moose, Bison, crocodiles, Privacy Pools). At most 2 of 7 items can move there.
2. **k = 3:** comparisons route `task:lookup` → retrieval k = 3; two side slots leave one for the question's own hits (lan-cmp-001: encyclopedia "Russia" cut by the k, replaced by Wikivoyage: Russia).
3. **The side's slot goes to a travel guide:** `titles: [side]` fires the Wikivoyage named path first ("Wikivoyage: Japan", "Wikivoyage: Germany").
4. **Compression drops the second side:** `compressContext`'s relative floor (0.5 × top sentence) cuts the side that shares fewer question words: vit-sci-002 `context:624->161` keeps only Wikivoyage: Japan; lan-cmp-001 `context:398->235` drops Wikivoyage: Russia. `onSubject` drops one more on lan-cmp-005.

### vital5 kit, t0 (decides; main = `ios-main-v5-t0`)

| item | sides | raw main→arm | prompt main→arm | shown main→arm | declined main→arm | cite-decline main→arm | retrievalMs main→arm |
|---|---|---|---|---|---|---|---|
| vit-hum-002 | mozi|mohis · confucian | ●○→●○ | ●○→●○ | 1→1 | False→False | False→False | 181→411 |
| lan-cmp-001 | brazil · russia | ●●→●● | ●●→●○ | 3→2 | False→False | False→False | 114→239 |
| lan-cmp-002 | polar bear · grizzly|brown bear | ●●→●● | ●●→●● | 3→3 | False→False | False→False | 95→147 |
| vit-sci-002 | japan · german | ○●→●● | ○●→●○ | 2→1 | True→False | True→False | 108→211 |
| lan-cmp-004 | moose · bison | ●●→●● | ●●→●● | 2→2 | False→False | False→False | 160→371 |
| lan-cmp-005 | saltwater crocodile · nile crocodile | ●●→●● | ○●→○● | 2→1 | False→False | False→False | 58→131 |
| vit-cry-005 | privacy pool · tornado | ○●→○● | ○●→○● | 4→4 | False→False | False→False | 129→193 |
| vit-fa-004 | japan · nigeria | ○●→●● | ○●→●● | 2→3 | False→False | False→False | 111→191 |
| vit-fa-005 | rhino · elephant | ●●→●● | ○●→○● | 1→1 | False→False | False→False | 61→189 |
| vit-fa-006 | blue whale · dinosaur|sauropod|argentinosaurus | ●○→●● | ●○→●○ | 3→2 | False→False | False→False | 136→299 |
| vit-fa-021 | lion · tiger | ●○→●● | ○○→●● | 0→2 | True→True | False→True | 61→155 |
| vit-fa-022 | elephant · rhino | ○●→●● | ○○→●○ | 1→2 | False→False | False→False | 84→236 |

### night kit, t0 (main = `ios-main-t0`)

| item | sides | raw main→arm | prompt main→arm | shown main→arm | declined main→arm | cite-decline main→arm | retrievalMs main→arm |
|---|---|---|---|---|---|---|---|
| vit-hum-002 | mozi|mohis · confucian | ○○→○○ | ○○→○○ | 0→0 | True→True | False→False | 99→163 |
| lan-cmp-001 | brazil · russia | ●●→●● | ●●→●● | 3→3 | False→False | False→False | 82→141 |
| lan-cmp-002 | polar bear · grizzly|brown bear | ○○→○○ | ○○→○○ | 3→3 | False→False | False→False | 58→108 |
| vit-sci-002 | japan · german | ○●→●● | ○○→●○ | 1→1 | True→False | True→False | 72→121 |
| lan-cmp-004 | moose · bison | ○○→○○ | ○○→○○ | 1→1 | False→False | False→False | 101→189 |
| lan-cmp-005 | saltwater crocodile · nile crocodile | ○○→○○ | ○○→○○ | 1→2 | False→False | False→False | 46→89 |
| vit-cry-005 | privacy pool · tornado | ○●→○● | ○●→○● | 4→4 | False→False | False→False | 81→148 |


## v2 (QUEUE #3b): pin one passage per side — night 2026-10-01

TL;DR: **v2 meets the card's v2 retrieval criteria on the deciding vital5 pair** ((a') 5/6, (c') 0 lost, (e') +86 tokens max) **but FAILS the coordinator's condition: the full gate on questions72 (night kit, t0) FAILS** on lan-cmp-004 (lost all shown sources → memory answer). (b) is not met (unreachable on this pair). Not adopted as is; a one-line fix is identified (below), not run.

- Arm: `adapters/desktop-node/arms/cmpsplit-v2.patch` sha256 `27d8dd79…1290` (v1 + v2 vs 0cfd4a77); README with the card's v2 criterion: `adapters/desktop-node/arms/cmpsplit-v2.README.md`.
- Runs: `ios-cmpsplit-v2-v5-t0` (vs `ios-main-v5-t0`, 78 items, vital5 kit) and `ios-cmpsplit-v2-t0` (vs `ios-main-t0`, questions72, night kit). Gates with `--safety-version v0.4`.

| v2 criterion (frozen) | vital5 pair, t0 | Verdict |
|---|---|---|
| (a') both sides in the shown pre-answer sources, 6 two-sided comparison items, ≥ 5/6 | main 3/6 → **5/6** (gained vit-sci-002 Japan+Germany, lan-cmp-005 both crocodiles; vit-hum-002 still no Confucianism) | PASS |
| (b) citation-check declines on comparison items −≥ 3 | 6 items: 1 → 1; 12 items: 1 → 2 | FAIL (main has only 1 on the slice: −3 is unreachable on this pair) |
| (c') key-in-context `pre` on non-comparison items: 0 lost | paired pre: gained 2 (lan-cmp-005, vit-fa-022), lost 0 | PASS |
| (d) confident-wrong not up, safety unchanged | gate PASS (0 new safety hits, 0 health-memory); CW not judged | safety PASS |
| (e') prompt tokens on comparison items within +150 | median 519 → 533; max +86 (lan-cmp-005) | PASS |
| **Coordinator: full gate on questions72 must PASS** | night kit t0 vs `ios-main-t0`: **FAIL**, lost-shown-sources lan-cmp-004 | **FAIL** |

Wider slice (12 items incl. vitalik58): both sides in the prompt 3/12 → **8/12** (+42 pp; v1: 4/12); sides in prompt 13/24 → 20/24; `context:pinned-2` on every two-sided item. Retrieval p50 on the slice 109 → 236 ms desktop (2–4 extra searches per comparison: the encyclopedia-first side search adds one). Paired diff: identical answer text 72/78 (vital5) and 67/72 (night kit); worse 0 / 1, better 1 / 1. Quality not judged (no quality claim).

**lan-cmp-004 ("adult male moose or an adult male American bison", night kit):** neither side has an article in the night kit. v2's `bestForSide` fallback "any non-guide before a guide" picked **Economics of bitcoin** (the side search's only non-guide hit) for the bison side; it displaced Wikivoyage: North American wildlife, the topic filter then dropped everything (`grounding:off-topic-dropped-3`, `no-good-source`) and the model answered from memory (`uncited-warning`). Main showed North American wildlife and answered from it.
- Fix (v2.1, not run, needs a new frozen sha): when no hit is the side's own article, keep the side search's top hit (v1 rule) or add nothing; never prefer an unnamed non-guide. Only a named article should be preferred over the guide, which is what the card asked.

### vital5 kit, t0 (decides; main = `ios-main-v5-t0`)

| item | sides | raw main→arm | prompt main→arm | shown main→arm | declined main→arm | cite-decline main→arm | retrievalMs main→arm |
|---|---|---|---|---|---|---|---|
| vit-hum-002 | mozi|mohis · confucian | ●○→●○ | ●○→●○ | 1→1 | False→False | False→False | 181→449 |
| lan-cmp-001 | brazil · russia | ●●→●● | ●●→●● | 3→3 | False→False | False→False | 114→352 |
| lan-cmp-002 | polar bear · grizzly|brown bear | ●●→●● | ●●→●● | 3→3 | False→False | False→False | 95→137 |
| vit-sci-002 | japan · german | ○●→●● | ○●→●● | 2→2 | True→True | True→True | 108→291 |
| lan-cmp-004 | moose · bison | ●●→●● | ●●→●● | 2→2 | False→False | False→False | 160→282 |
| lan-cmp-005 | saltwater crocodile · nile crocodile | ●●→●● | ○●→●● | 2→3 | False→False | False→False | 58→163 |
| vit-cry-005 | privacy pool · tornado | ○●→○● | ○●→○● | 4→4 | False→False | False→False | 129→287 |
| vit-fa-004 | japan · nigeria | ○●→●● | ○●→●● | 2→3 | False→False | False→False | 111→171 |
| vit-fa-005 | rhino · elephant | ●●→●● | ○●→○● | 1→1 | False→False | False→False | 61→180 |
| vit-fa-006 | blue whale · dinosaur|sauropod|argentinosaurus | ●○→●● | ●○→●○ | 3→2 | False→False | False→False | 136→313 |
| vit-fa-021 | lion · tiger | ●○→●● | ○○→●● | 0→2 | True→True | False→True | 61→122 |
| vit-fa-022 | elephant · rhino | ○●→●● | ○○→●● | 1→3 | False→False | False→False | 84→190 |


## v2.1 (approved fix): verdict **PASS on every frozen v2 condition except (b), which this pair can't reach; full gate PASS**

- Arm: `adapters/desktop-node/arms/cmpsplit-v21.patch` sha256 `2430f5bf…01dcd` = v2 + `bestForSide` never prefers an unnamed non-guide (side search's top hit instead); README frozen before the runs: `arms/cmpsplit-v21.README.md`.
- Runs: `ios-cmpsplit-v21-v5-t0` (vs `ios-main-v5-t0`), `ios-cmpsplit-v21-s42`/`-s43` (questions72, night kit). 0 errors.

| Criterion (frozen) | Result | Verdict |
|---|---|---|
| (a') both sides in the shown pre-answer sources, 6 two-sided items, ≥ 5/6 | main 3/6 → **5/6** (miss: vit-hum-002, no Confucianism article reaches the prompt) | PASS |
| (b) citation-check declines on comparison items −≥ 3 | 6 items 1 → 1; 12 items 1 → 2 | FAIL (unreachable: main has 1) |
| (c') key-in-context `pre`, non-comparison items: 0 lost | gained 2 (lan-cmp-005, vit-fa-022), lost 0 | PASS |
| (d) safety unchanged; CW not up | gates: 0 new safety hits, 0 health-memory, new-cw 0; CW not judged | safety PASS |
| (e') prompt tokens on comparison items within +150 | median 519 → 533, max +86 | PASS |
| **Full gate on questions72 (multi-base s42+s43, v0.4)** | **PASS** (0 lost-shown-sources: lan-cmp-004 fixed; 0 health-memory; 0 new safety hits; 0 errors) | **PASS** |

Wider slice (12 items): both sides in the prompt 3/12 → 8/12 (+42 pp), sides 13/24 → 20/24. Desktop retrieval p50 on the slice 109 → 207 ms (v1's (e) bar is not in the v2 criterion; device cost UNKNOWN). Paired diff: identical answer text 70/78 (vital5 t0), 67/72 (s42), 68/72 (s43); worse 0 / 1 / 0 (s42: vit-cry-005 declined; v1 showed the same flip at s42 and not at s43 = seed noise on a changed prompt), better 1 / 1 / 1. Quality not judged: no quality claim.

### vital5 kit, t0 (main = `ios-main-v5-t0`)

| item | sides | raw main→arm | prompt main→arm | shown main→arm | declined main→arm | cite-decline main→arm | retrievalMs main→arm |
|---|---|---|---|---|---|---|---|
| vit-hum-002 | mozi|mohis · confucian | ●○→●○ | ●○→●○ | 1→1 | False→False | False→False | 181→429 |
| lan-cmp-001 | brazil · russia | ●●→●● | ●●→●● | 3→3 | False→False | False→False | 114→284 |
| lan-cmp-002 | polar bear · grizzly|brown bear | ●●→●● | ●●→●● | 3→3 | False→False | False→False | 95→209 |
| vit-sci-002 | japan · german | ○●→●● | ○●→●● | 2→2 | True→True | True→True | 108→173 |
| lan-cmp-004 | moose · bison | ●●→●● | ●●→●● | 2→2 | False→False | False→False | 160→244 |
| lan-cmp-005 | saltwater crocodile · nile crocodile | ●●→●● | ○●→●● | 2→3 | False→False | False→False | 58→165 |
| vit-cry-005 | privacy pool · tornado | ○●→○● | ○●→○● | 4→4 | False→False | False→False | 129→272 |
| vit-fa-004 | japan · nigeria | ○●→●● | ○●→●● | 2→3 | False→False | False→False | 111→204 |
| vit-fa-005 | rhino · elephant | ●●→●● | ○●→○● | 1→1 | False→False | False→False | 61→145 |
| vit-fa-006 | blue whale · dinosaur|sauropod|argentinosaurus | ●○→●● | ●○→●○ | 3→2 | False→False | False→False | 136→299 |
| vit-fa-021 | lion · tiger | ●○→●● | ○○→●● | 0→2 | True→True | False→True | 61→107 |
| vit-fa-022 | elephant · rhino | ○●→●● | ○○→●● | 1→3 | False→False | False→False | 84→177 |
