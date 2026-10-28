# bench/heldout: the retired held-out sets (public since 2026-10-27)

> **Content note.** Several of these sets are safety evaluation probes: medical emergencies, danger, drugs, suicide and self-harm (crisis1 includes method-seeking prompts that a good answer must refuse). AI-reviewed, not clinically reviewed. Nothing here is medical advice. If you are in crisis, contact local emergency services.

TL;DR: while the project ran, these sets were held out (nobody tuned on them; one claim run per build). On 2026-10-27, after the project was submitted, the author retired them and opened everything that is not private to him or to the app maintainer. They are **public development data now**: a number measured on them again validates nothing. A final held-out number for a later system needs a set written after this date.

Each folder has a `CARD.md` (status, writer, licence, content note, how to verify). The `README.md` inside a folder, where there is one, is the card written at the time, kept byte for byte (it still says "blind"). Runs, judgments, hand reads and round reports on these sets are in `boar-research` `rnd/heldout/`, and the raw `.jsonl` traces are in the Hugging Face dataset `r4topunk/boar-traces` at the same paths.

| folder | what | items | writer | content note |
|---|---|---:|---|---|
| `bench-v02/` | bench v0.2 (the burnt dev set): items, two writers' drafts, rewrite rounds, card, plan and addenda, reference answers | 110 | two blind Claude Opus writers | yes (danger items) |
| `vpara1/` | **V-para**: paraphrases of the public example questions that inspired the bounty, venue gold (OSM), references | 58 | fresh Claude Opus subagent | yes (3 health items) |
| `health-fresh1/`, `health-fresh2/`, `health-fresh3/` | health-safety probes (danger + hard negatives, EN/PT/ES) | 120 / 150 / 120 | fresh Opus / Sonnet / Opus subagents | yes |
| `chat-v3/` | synthetic multi-turn chats | 64 | fresh Opus subagent | yes (7 safety items) |
| `meta-fresh1/` | questions about the app itself | 36 | fresh Sonnet subagent | no |
| `es-fresh1/`, `es-fresh2/` | Spanish items | 32 / 32 | fresh Sonnet subagents | no |
| `crisis1/` | suicide / self-harm crisis detector set (30 crisis, 30 hard negatives) | 60 | Veil lane (Claude agent) | **yes** |
| `hm-fresh/`, `hm-fresh2/`, `hm-fresh3/`, `hm-loc1/` | danger / health-question detector sets (`hm-loc1`: location-anchored, public places) | 16 / 40 / 74 / 45 | Veil lane | yes |
| `h1-fresh/` | health-coverage items | 24 | Veil lane | yes |
| `h2-fresh/`, `h2-pool/` | answer-position items (where in the article the answer sits) | 24 / 64 | Veil lane | no |
| `o2-blind-items/`, `o2v2c-fresh/` | o2 (instant-tier) items, with errata | 30 / 45 | Veil lane | no |

The v0.4 ruler (75 items, candidate, rejects, both reference halves, drafts, critiques, fact-checks, disagreements, changelog, round-2 writer prompts) is in `bench/v0.4/`.

## Licence

Items, rubrics and cards: **CC BY 4.0** (BOAR bench, r4to), written by Claude-family agents (the writer is named in each card); the v0.4 ruler also by OpenAI gpt-5.6-sol through the Codex CLI. Short attributed quotations of public guidance stay under their sources' terms; **NHS wording is not redistributed** (75 quotations in crisis1, hm-fresh2, hm-fresh3 and hm-loc1 were withheld: org and URL kept). OpenStreetMap venue data: ODbL 1.0, (c) OpenStreetMap contributors. Reference answers are frontier-model + live-web outputs and may quote their cited pages. V-para and the four V-exact anchors of v0.4 paraphrase or quote public example questions by Vitalik Buterin (named as the inspiration of the bounty only).

## Integrity

`HASHES.md` explains which hashes still verify, which changed on the way out and why; `HASHES.tsv` lists original and released sha256 for every file here. `python3 tools/verify-pins.py` (repo root) checks every pin and reports the documented exceptions as KNOWN.

## What changed on the way out

Local paths and hosts neutral; usage, token, price and plan fields dropped from reference-answer rows and manifests; competitor names replaced by `competitor`; NHS quotations withheld (above). Item ids, set names, questions, rubrics and answers are otherwise unchanged. No row in any set came from the app maintainer (checked by origin field and by content).
