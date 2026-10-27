# QUEUE #17: big-pack relevance gate G1+ (Sonar), step 1 replay

TL;DR: **FAIL; the 3 judged seeds were not spent.** On both profiles, exact key-in-context at `pre`: net **+3 (+7 gained / −4 lost)** and **2 items lose all shown sources** (bar: net ≥ +5, ≤ 1 lost, 0 emptied). Of the card's 5 predicted fixes, 2 happen (lan-ref-001, saf-008). Ordering verified candidates first creates the card's two warned risks: mediocre verified chunks displace a working unverified source (1 new loss), and the sole surviving unverified source gets displaced (2 emptied). Android retrieval p50 is 2.17× base (bar ≤ 2×).

Arm: `adapters/desktop-node/arms/bigpack-g1plus.{patch,README.md}` (patch sha256 `a3ffcd69…70e3`; frozen criterion in the README). Pack: fixed top-100k `9123b372…94e7`. Tool: `rnd/research/sonar/tools/key_in_context.py … --vital5` (bench v0.1 public keys, 52 keyed items).

| Pair (s42, `--event-source-text`) | key in `pre` | gained | lost | emptied | verdict |
|---|---|---|---|---|---|
| iPhone `ios-main-v5-s42-kic` → `g1plus/ios-g1plus-s42-kic` | 13 → 16 | 7 | 4 | 2 | FAIL |
| Android `g1plus/and-main-v5-s42-kic` (new) → `g1plus/and-g1plus-s42-kic` | 13 → 16 | 7 | 4 | 2 | FAIL |
| reference: #6b `ios-enwiki-namedcap-s42-kic` (same tool, old pack) | 13 → 16 | 7 | 4 | 3 | FAIL |

- **Gained (7):** lan-exp-003 (Kenya, new vs #6b), lan-ref-004, lan-ref-005, lan-rsn-001, vit-cry-010, vit-hum-001, vit-hum-004. Not a gain any more: vit-hlt-003. Lead-verified Wikivoyage: Dengue fever ×2 now fills the slots, and only the guide survives the downstream filters, not the article.
- **Lost (4):**
  - **lan-exp-006 (new, caused by G1+):** vital5's Olympus Mons 0.74 / Pico de Orizaba 0.73 (verified, mediocre) take k = 3 and push out Wikivoyage: Volcanoes. Both are then dropped as off-topic. This is the card's "verified candidates are mediocre" risk;
  - **lan-rsn-007 (predicted fixed, not fixed):** named big-pack Berlin Wall goes first, and the lead-verified Wikivoyage: Berlin Wall (0.797) is dropped downstream. `pre` = Berlin Wall only, and compression cuts 1961/1989;
  - **vit-cry-004 (predicted fixed, not fixed):** G1+ does restore the right pages (EIP-7594 + PeerDAS ×2, as base). The key is then cut by compression (context 584→346 vs base 695→490);
  - **vit-cry-011:** key-proxy artifact (Terra/Do Kwon), as the card predicted.
- **Emptied (2):**
  - lan-hlt-003: Wikivoyage: China was base's sole survivor. Verified vital5 Mosquito-borne disease ×2 displace it, and all are dropped. #6b emptied this item too;
  - vit-sci-002: named Population density ×2 plus verified Tokyo displace Wikivoyage: German Empire ×2, and all are dropped.
  - Both are exactly the card's G1′ case ("when all k slots would be verified, keep the single best unverified hit as slot k"), declared as the fallback "not run unless needed".
- **Fixed vs #6b:** lan-ref-001 (Ishiguro back in `pre`), saf-008 (Wikivoyage: Jellyfish kept). saf-003 is not a loss in either run under this tool version; `pre` still shows Redback spider.
- **Latency, retrieval p50:** Android 888 / 410 ms = **2.17×** (back-to-back pair, loaded host). iPhone 498 / 137 ms = 3.6×, but that base is from another session and not comparable. #6 measured 1.94×.

Next options (coordinator / Sonar to decide):
- G1′ fixes the 2 emptied items by construction. Projected net +3 with 0 emptied, still short of +5;
- the remaining losses are downstream (onSubject / compression: lan-rsn-007, vit-cry-004), not ordering.

UNKNOWN: whether G1′ also recovers lan-exp-006 (it keeps one unverified slot, Volcanoes would be the best unverified hit).
