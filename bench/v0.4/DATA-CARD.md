# Data card: bench/v0.4 (the "ruler")

Public derived card: `DATASET_CARD.md`.

- **What:** a 75-item cross-family ruler (casual lookup and research questions in the families of the bounty post's own test questions; English). Written by a Claude agent and by OpenAI gpt-5.6-sol via the Codex CLI, cross-critiqued and fact-checked live on the web by both families, frozen 2026-10-20 before any system answered.
- **Published:** only commitments: `SHA256SUMS` (items `f9ad2f2f0fc3...`, candidate `23b6febf66...`), `refs/v2/MANIFEST.json`, counts and pipeline in the card. No item, reference, draft, critique or topic list is published.
- **Held out:** yes. Engine, prompt, pack and retrieval work must never use these items. Whether the plaintext is ever published is the author's decision; unsealing turns the set into development data.
- **Limits:** see the card (writer imbalance, 19 time-sensitive items, four of six multi-turn shapes with one conversation).
- **Verify:** `python3 tools/verify-pins.py` reports the two item files as WITHHELD, as intended.
