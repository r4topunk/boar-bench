# Data card: every dataset folder in this repository

TL;DR (v1.1): six dataset folders. `bench/v0.1` (60 public questions with frontier references), `bench/v0.4` (the 75-item ruler with both reference halves, public since v1.1), `bench/heldout` (the retired held-out sets, public development data since v1.1), `bench/v0.3` (plan, schema and tooling; no items were ever written), `bench/selftest` (14 pack self-test sets) and `bench/slices` (6 dev slices). Each folder has its own `DATA-CARD.md`; v0.1, v0.3 and v0.4 also keep their detailed `DATASET_CARD.md`.

| Folder | Items | Status | Held out? | Reference side | Licence | Card |
|---|---:|---|---|---|---|---|
| `bench/v0.1/` | 60 public + 12 safety-track | dev set, frozen; public | no (a separate v0.1 held-out split exists as a hash only) | frozen Claude Opus + live web answers (`refs/refs.jsonl`) | CC BY 4.0 wrapper; OSM gold ODbL; Wikipedia-derived parts CC BY-SA | `bench/v0.1/DATA-CARD.md` |
| `bench/v0.3/` | 0 (no items were ever written; OF-3 dropped) | pre-registered plan, schema, scripts | n/a (nothing exists to hold out) | n/a | CC BY 4.0 / MIT | `bench/v0.3/DATA-CARD.md` |
| `bench/v0.4/` | 75 (+70 candidate, 3 rejected) | the claim "ruler"; retired 2026-10-27 | no longer (public since v1.1) | Claude Opus + web and Codex gpt-5.6-sol + web (`refs/v2/`) | CC BY 4.0; cited pages keep their terms | `bench/v0.4/DATA-CARD.md` |
| `bench/heldout/` | 19 sets (1,144 items, plus the v0.2 drafts) | retired held-out sets; dev data | no longer (public since v1.1) | v0.2 and V-para: Claude Opus + web | CC BY 4.0; quotations under their sources' terms (NHS withheld); OSM ODbL | `bench/heldout/README.md`, one `CARD.md` per set |
| `bench/selftest/` | 290 (13 sets x 20 + 30) | dev only | no | agent-written gold from public pack passages | per source: CC0, public domain, CC BY-SA 2.5/3.0/4.0 | `bench/selftest/DATA-CARD.md` |
| `bench/slices/` | 6 slices (150, 54, 80 questions in 10 sessions, 30 chats, 26, 20) | dev only | no | per slice | CC BY 4.0 (per-slice NOTICE) | `bench/slices/DATA-CARD.md` |

Common rules
- Health, first-aid and safety content is AI-reviewed, not clinically reviewed; it is not medical advice.
- English only (the one Portuguese slice, `citation-pt`, is a translation check).
- Integrity: `python3 tools/verify-pins.py` checks every published hash; `python3 bench/v0.1/validate.py --skip-heldout` checks the v0.1 data.
- Held-out policy: README, "Held-out policy". Since v1.1 every held-out set of the project is public (`bench/heldout/`, `bench/v0.4/`).
- Content note: `bench/heldout/` contains safety evaluation probes (medical emergencies, crisis and self-harm); AI-reviewed, not clinically reviewed; if you are in crisis, contact local emergency services.
- Redaction applied to the whole tree: no personal names of third parties, no emails, no machine paths or hostnames, no account or spend details, no credentials. Origin fields that start with `rnd/` resolve in the sibling repository `boar-research` (same layout); paths that were withheld are listed in its `docs/EXCLUDED.md`.
