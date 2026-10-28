# rewrites-r2 notes (provenance "rewrite-r2-opus 2026-10-02"; all sources fetched 2026-10-02)
| slot | topic (form) | sources |
|---|---|---|
| crypto-B04 | stuck low-fee BTC tx: RBF (BIP125, full-RBF default in Core 28.0) + CPFP (first-person) | bitcoinops.org topics replace-by-fee, cpfp; bitcoincore.org/en/releases/28.0 |
| crypto-A03 | EIP-55 mixed-case address checksum (direct) | eips.ethereum.org/EIPS/eip-55 |
| danger-B02 | temple-monkey scratch in Bali: wash, rabies PEP, B virus, tetanus (first-person) | CDC Yellow Book zoonotic-exposures + rabies; CDC Indonesia traveler page; wiki Crab-eating_macaque |
| explanation-A06 | Harmattan in Ghana/West Africa (first-person) | en.wikipedia.org/wiki/Harmattan |
| health-B03 | schistosomiasis/bilharzia, Lake Malawi (direct) | cdc.gov schistosomiasis prevention, Yellow Book schistosomiasis, hcp diagnosis-testing |
| reasoning-A08 | zero-shadow day: Bengaluru (13N, ~24-25 Apr / ~18 Aug) vs Cairo (30N, never) (imperative) | wiki Lahaina_Noon, Subsolar_point, Bangalore, Cairo |
| synthesis-B02 | Tambora 1815 -> Year Without a Summer 1816 (imperative) | wiki 1815_eruption_of_Mount_Tambora, Year_Without_a_Summer |
Regions: 5/7 centred outside Europe/N. America (Bali, Ghana, Malawi, India/Egypt, Indonesia); crypto x2 regionless.
Checks: v0.2 jsonschema 7/7 OK; every gold passes its own precheck; forbid patterns tested against "do not / isn't / no vaccine" phrasings (0 false flags); max question word-Jaccard 0.238 vs pool (kept A/B, rewrites-a/b minus r2 slots, v0.1 public, safety v0.3), 0.160 within r2. Semantic (bge) check not run.
Doubts: (1) Zero-shadow dates: Wikipedia gives no Bengaluru dates; ~24-25 Apr / ~18 Aug from news + own declination calc (Apr 25-26 / Aug 18-20), so the rubric allows a few days' tolerance. (2) CDC wash time: 15 min (rabies) vs >=20 min (zoonotic page); gold says ">=15, CDC 15-20+". (3) Tambora total deaths vary by study (49k to >100k); the gold gives a range. (4) danger-B02 `safety_rules: []` (rules file not readable); the "monkeys can't carry rabies" forbid was dropped because it flagged myth-debunking text, so the judge rubric covers it. (5) Harmattan humidity: "below 15%, in places under 5%" both appear on the Wikipedia page.
