# Data card: bench/v0.4 (the "ruler")

Card: `DATASET_CARD.md`.

- **What:** a 75-item cross-family ruler (casual lookup and research questions in the families of the bounty post's own test questions; English). Written by a Claude agent and by OpenAI gpt-5.6-sol via the Codex CLI, cross-critiqued and fact-checked live on the web by both families, frozen 2026-10-20 before any system answered.
- **Published (v1.1, 2026-10-27):** everything: `items.jsonl` (75), `items.candidate.jsonl` (70), `REJECTED.jsonl` (3), `refs/v2/` (both reference halves and call logs), `drafts/` (round-1 and round-2 drafts, critiques, fact-checks, Codex prompts and logs), `DISAGREEMENTS.md`, `CHANGELOG.md`.
- **Held out:** no longer. It was held out until the project was submitted; it is development data now.
- **Licence:** CC BY 4.0 for items and records; reference answers and drafts may quote their cited pages (see the card).
- **Limits:** see the card (writer imbalance, 19 time-sensitive items, four of six multi-turn shapes with one conversation).
- **Verify:** `python3 tools/verify-pins.py` checks both item files against `SHA256SUMS` (unchanged since v1.0) and the reference pins.
