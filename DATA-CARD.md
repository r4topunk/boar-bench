# Data card: every dataset folder in this repository

TL;DR: five dataset folders, none of them a held-out set in plaintext. `bench/v0.1` (60 public questions, the only set with frontier references), `bench/v0.3` and `bench/v0.4` (plans and commitments, no items), `bench/selftest` (14 pack self-test sets) and `bench/slices` (6 dev slices). Each folder has its own `DATA-CARD.md`; v0.1, v0.3 and v0.4 also keep their detailed `DATASET_CARD.md`.

| Folder | Items | Status | Held out? | Reference side | Licence | Card |
|---|---:|---|---|---|---|---|
| `bench/v0.1/` | 60 public + 12 safety-track | dev set, frozen; public | no (a separate v0.1 held-out split exists as a hash only) | frozen Claude Opus + live web answers (`refs/refs.jsonl`) | CC BY 4.0 wrapper; OSM gold ODbL; Wikipedia-derived parts CC BY-SA | `bench/v0.1/DATA-CARD.md` |
| `bench/v0.3/` | 0 | pre-registered plan, schema, scripts | yes (plaintext held offline) | n/a | CC BY 4.0 / MIT | `bench/v0.3/DATA-CARD.md` |
| `bench/v0.4/` | 0 published (75 committed by hash) | the claim "ruler" | yes | n/a (references private) | n/a | `bench/v0.4/DATA-CARD.md` |
| `bench/selftest/` | 290 (13 sets x 20 + 30) | dev only | no | agent-written gold from public pack passages | per source: CC0, public domain, CC BY-SA 2.5/3.0/4.0 | `bench/selftest/DATA-CARD.md` |
| `bench/slices/` | 6 slices (150, 54, 80 questions in 10 sessions, 30 chats, 26, 20) | dev only | no | per slice | CC BY 4.0 (per-slice NOTICE) | `bench/slices/DATA-CARD.md` |

Common rules
- Health, first-aid and safety content is AI-reviewed, not clinically reviewed; it is not medical advice.
- English only (the one Portuguese slice, `citation-pt`, is a translation check).
- Integrity: `python3 tools/verify-pins.py` checks every published hash; `python3 bench/v0.1/validate.py --skip-heldout` checks the v0.1 data.
- Held-out policy: README, "Held-out policy". Anything not in plaintext here is private on purpose.
- Redaction applied to the whole tree: no personal names of third parties, no emails, no machine paths or hostnames, no account or spend details, no credentials. Origin fields that start with `rnd/` point at the private working tree.
