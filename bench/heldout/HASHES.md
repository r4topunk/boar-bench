# Hashes of the opened sets: what still verifies, what changed, and why

TL;DR: every **item file** of every opened set is byte-identical to the file that was hashed while it was held out, except four Veil-lane safety sets, where verbatim NHS quotations were withheld (the CARD of each set gives both hashes). Reference answers, plan files and a few scripts were redacted on the way out (local paths, usage and plan fields, competitor names), so their released hashes differ from the hashes committed during the project. Every row is in `HASHES.tsv` (released path, lab path, original sha256, released sha256, `same`/`changed`, whether the hash was committed before, privately or publicly).

## Still byte-identical to a public commitment

| file | sha256 | committed in |
|---|---|---|
| `bench/v0.4/items.jsonl` (75 items) | `f9ad2f2f0fc367811ea03690bc9b05e52d85b1ee5fb662600efa818587d33594` | `bench/v0.4/SHA256SUMS` (public since v1.0) |
| `bench/v0.4/items.candidate.jsonl` (70 items) | `23b6febf66372f5b21bd94a2316cfd5da3187dbb37b493b2fd7e8a512e4c2993` | `bench/v0.4/SHA256SUMS` |
| `heldout/bench-v02/live/v0.2/questions.v02-new.jsonl` (110 items) | `c883053b05959b4d987afe7458b6ba02c3e1bbda656c8a86514edc9b5885d5e2` | `SHA256SUMS.items`; 12-hex prefix in public arm criteria |
| `heldout/vpara1/items.jsonl` (58 items) | `aa604be6aa3f2e5de6af72478f9059a0ec478e61882846e3360a7cb53c74bebd` | set `SHA256SUMS`; 12-hex prefix in public deep-tier reports |
| `heldout/health-fresh1/items.jsonl` | `bf145565...` (full value in `HASHES.tsv`) | set `SHA256SUMS`; quoted in a public Sonar report |
| `heldout/o2-blind-items/o2-blind-items.jsonl`, `-b2.jsonl` | `46d5f5b7...`, `887ee740...` | `bench/v0.1/heldout.manifest.json` (public since the first release) |

chat-v3, es-fresh1/2, health-fresh2/3 and meta-fresh1 verify against their own `SHA256SUMS` (items and README, unchanged). h1-fresh, h2-fresh, h2-pool, hm-fresh and o2v2c-fresh had no earlier commitment; their files are identical to the lab files.

## Hashes published before the opening that no longer verify (redaction)

| released file | sha256 published during the project | released sha256 | what changed |
|---|---|---|---|
| `bench/v0.4/refs/v2/claude.jsonl` | `b27eac37a88918ca5d74ad22e9e5265d241c118342098a45a9178eb5066ce4f6` (public `refs/v2/MANIFEST.json`, v1.0) | `d83e518688cdc636bbf7c221370deeae239b13f859830a9ee8ab337cf9f5209f` | per-call `usage` (token counts, list-price equivalent, cost basis) dropped; plan label in `via` neutralised. Answers byte-identical |
| `bench/v0.4/refs/v2/codex.jsonl` | `047cb199e267...` (12-hex, public judge scripts) | `f6ae6b8851dad811c2d0d7f28a6593ccf5a0623917317b8cc382415ee91c810e` | `usage` token counts dropped; plan label in `via` neutralised. Answers byte-identical |
| `bench/v0.4/refs/v2/MANIFEST.json` | `c6d58017b5a8a302cc49575901fa4372692a63ec2b8268ba723d35dfcc96f3f1` (boar-bench v1.0) | `41b38585a6a7dcc7addb1df53e3ce122acef892623f80fc19e6f2d15fcaa8eb6` | re-pinned to the released `claude.jsonl` |
| `heldout/bench-v02/live/v0.2/refs/refs.jsonl` | `1e2668c488a1ca2f7d61f20de171c659067954f73aa8f0e7949137b27bd1cf53` (12-hex in public DEEPTHINKV02 / DT512V02 criteria) | `bf7a8d5fe56e7d8a487267b4b8b7ad51bc6dbec914813740f9aefceffc18590a` | token, cache, price and cost-basis fields dropped; `promptFile` path neutral; plan label in `via` neutralised. Answers byte-identical |
| `heldout/vpara1/refs/refs.jsonl` | `952e2c44d9783175fb6624039bb0b66b798d3ff5912f7156122e8ff09e43df1d` (12-hex in public DEEPFULL / DEEPTHINK / DEEPTHINK2 / GEMMATHINK reports) | `2cbc0e080fc0c474c5f4571dd28fe2462758fbeea1bf0e4e1b9ce9b74525fab2` | same as above |
| `heldout/bench-v02/live/v0.2/plan/SHA256SUMS` (the v0.2 "combined plan sha") | `fe100e91c4d6e51bb0c18001ce5e341e3e290d05e251cd997a0c50faa252855e` (public: `bench/v0.3/plan/README.md`, audit timeline, reports) | `d1dcd9633c5a47a2dd69342d102fa691950a7e7f22cc82410115e5c1fb996e41` | re-pinned because the 4 plan files below changed |
| `.../plan/analysis-plan.md` | `375ff004c90ac11d2c20eae4508899524e6f70826f52bc564e7fd41f2e4be488` | `a72f1184df4710736f9e189e4324c8c44ced327104d6249f5e3492975201080d` | local path neutral. A different redaction of the same original is in `boar-research` `rnd/research/compass/exp/bench-v02/analysis-plan.md` (v1.0) |
| `.../plan/item-spec.draft.md` | `0311a22e645f74128f73eed8fca6d8273fafb8bc4bbb6ce869e8dc6497d3b231` | `2bfb92f854f383b39c7515f3b1719ef694b6373c24305364ed371fd5b366b0fb` | same |
| `.../plan/strata.py` | `4b2a4f4f7ad3f5da60a837f59bd73ad1f02a9a57983ce2756b5a95b0904b8d0b` | `1d5324ff15b8dd8a3bca05f7929b8e6b1b15565ddf994a49e91dafc7b9935bd7` | local paths |
| `.../plan/key_in_context.py` | `c9124e43f1696a7a5e82684f1a7d1bae4744ce04357d287995cf2344eb4db329` (public `bench/v0.3/plan/README.md`) | `84182b678c008a096518e5e2434d8fbeb5644fdc68c36b4f806f5e2bb887cd46` | local paths |
| crisis1, hm-fresh2, hm-fresh3, hm-loc1 item files | see each `CARD.md` (lab `rnd/veil/<set>.sha256`) | see each `CARD.md` | 75 NHS quotations withheld (`quote_withheld: true`, org and URL kept) |

What this means for the published numbers: the judge reads the `answer` field of a reference, and no answer changed, so every number computed against the original files holds for the released files. The item files that the numbers were computed on are byte-identical (except the four NHS sets, which carry detector labels, not judged answers).

## Chains that do not close on the released bytes (known, reported by `tools/verify-pins.py` as KNOWN)

| chain | why | what to do |
|---|---|---|
| `bench-v02/live/v0.2/SHA256SUMS.items`: `assemble.py`, `validate.py`, `similarity.py`, `similarity.json` | these four files live in `boar-research` `rnd/heldout/bench-v02/live/v0.2/`; `assemble.py`, `similarity.py` and `similarity.json` were redacted (paths; competitor name to `competitor`), `validate.py` is unchanged | compare with `HASHES.tsv` of `boar-research` (`docs/REDACTION-HASHES.tsv`) |
| `bench-v02/live/v0.2/COMBINED-FREEZE.sha256` (`aa4ff3300aba75ba...`, quoted in the public audit timeline) | the commit that made it says it covers items, refs manifest, card, scripts, plan and addenda 01/02, but the concatenation recipe was not recorded and three covered files were redacted | not reproducible from the released bytes; the component hashes are above and in `HASHES.tsv` |
| `plan/SHA256SUMS.addendum-01` | pre-existing in the lab: 8 lines (the coverage run record) were appended to `addendum-01-coverage-split.md` on 2026-10-02 after it was hashed and before any run | none; documented |
| `plan/SHA256SUMS.addendum-02..04` | they name `../../../scorers/vendor/safety/...` (the old eval-repo layout); the public re-issue of those rules (`scorers/vendor/safety/`) dropped NHS wording, so the rule files differ; `safety_check.*.py` and `tests.*.json` match the public copies | none; documented |
| `vpara1/refs-80w/refs.jsonl` rows carry `sourceRefsSha256 = 952e2c44...` | that is the pre-redaction `refs/refs.jsonl`; the released one is `2cbc0e08...` | read it as "derived from the V-para references" |

## Not published from these folders

The app maintainer's data (none was found in any set), two pull-request comment drafts addressed to him, run logs with spend, gateway caches, and a competitor team's 27 test questions (ids only; see the research repository `docs/EXCLUDED.md`).
