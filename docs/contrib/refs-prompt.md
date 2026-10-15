# Bench v0.3 reference answers: web-UI recipe (reference.v1, non-Claude model + web)

TL;DR: the instructions are reference.v1 **verbatim** (sha256 `d51443438dfebcc7d2c3a0136340c70a68f495e1214c00a3a8c56bcdbc755972`, the v0.1/v0.2 recipe), pasted once into the web UI's custom-instructions slot. Each item is one fresh chat whose only message is the item's question, unchanged. Save each reply as a text file. The coordinator's import script turns the files into `refs.jsonl` and `MANIFEST.jsonl`/`MANIFEST.json` (hashes). Budget: about 2.5 min per item, 110 items ≈ 4.6 h (60 items ≈ 2.5 h).

## 1. One-time setup (10 min)
- Same vendor and model as the writer chats (spec §9 D1), on the same account. Write down the model name exactly as the model picker shows it.
- Settings: memory and "reference chat history" OFF; model-training opt-out ON; web search ON (or the model's "search" tool forced on).
- Create one container for the instructions: a ChatGPT **Project** (project instructions, project-only memory) or a Gemini **Gem** (instructions). Name it `ref-v1`. Paste the block in §2 as its instructions. Nothing else goes in it: no files, no item list, no writer chats.

## 2. Instructions (paste exactly; this is reference.v1, do not edit a character)
```text
You are a research assistant with web search. Answer the user's question accurately and completely, the way an expert would explain it to a curious traveler or student.

Rules:
- Search the web to verify facts before answering. Prefer primary or authoritative sources (encyclopedias, official bodies, peer-reviewed or medical guidance).
- Answer in the same language as the question.
- Keep the answer under 250 words. Lead with the direct answer, then the key supporting points.
- For first-aid or safety questions, give the standard recommended steps and say when to seek professional help.
- If the question has a false premise or no single answer, say so.
- End with a line "Sources:" followed by one URL per line (1 to 5 URLs you actually used).
```
The block above, with its final newline, hashes to `d5144343…` (checked 2026-10-07 against `wt/eval/eval/prompts/reference.v1.md`). The web UI adds its own hidden system prompt; we record the channel as `reference.v1-webui`, not `reference.v1`.

## 3. Per item (≈ 2.5 min)
1. The coordinator gives you `bench/v0.3/work/refs/todo.txt` (one line per item: `id<TAB>question`), written once the question text is final (after the G1 + G2 pre-pass, spec §7). If a question is changed later by a gate fix, its reference is regenerated, as v0.2's gen_refs.mjs did for rewritten items.
2. Open a **new chat inside `ref-v1`**. Paste the question text only, exactly as in todo.txt (no id, no "please", no context).
3. Wait for the full answer. Do not reply, regenerate or edit, except under the retry rule (§4).
4. Copy the answer with the UI's copy button (markdown is fine) and save it as `bench/v0.3/work/refs/raw/<id>.md` with this header:
```text
id: v03-explanation-01
model: <model name exactly as in the picker>
vendor_ui: <chatgpt.com | gemini.google.com>
date: 2026-10-18
web: <yes if the reply shows web citations, else no>
attempt: 1
---
<pasted answer, including the Sources: lines>
```
5. Do not read the answer for quality and do not fix it. Facts were already checked on the gold answer; the reference is whatever the frontier model plus web says.

## 4. Retry rule (same spirit as gen_refs.mjs: one retry, then stop)
- Retry once in a new chat (header `attempt: 2`, keep the attempt-1 file as `<id>.attempt1.md`) only if: the reply is empty or cut off, it asks a clarifying question instead of answering, it shows no web use (`web: no`), or it has no URL at all.
- A reply over 250 words is **not** retried; the import script flags it, and the count is reported in the manifest.
- If attempt 2 fails the same way, keep it and tell the coordinator. No third attempt.

## 5. What the coordinator does with the files (scripts written before 10-18)
- `bench/v0.3/refs/import_web_refs.py` (reads the `raw/` folder in private/, script-only): parses the header; splits the trailing `Sources:` block exactly as `splitSources()` in v0.2 `gen_refs.mjs` (falls back to any URL in the text); strips tracking parameters (`utm_source=...`); checks that the question in todo.txt equals the item's question; writes `refs/web__<model-slug>.new.jsonl` rows with the v0.2 row fields that exist in a web UI: `id, category, lang, question, ok, answer, sources, rawResult, requestedModel=actualModelId=<picker name>, via="web-ui (manual paste)", promptVersion="reference.v1-webui", promptSha256=d5144343…, questionsSha256, generatedAt=<date>, attempt, words, webUsed`.
- `bench/v0.3/refs/build_manifest.py` (copy of v0.2, RAW path and ACCOUNT_TERMS changed): `refs.jsonl` (text, blind only) plus `MANIFEST.jsonl` rows `{id, sha256, model_id, cli_version: "web-ui <vendor_ui>", prompt_version: "reference.v1-webui", prompt_sha256, generated_at, web_search, tools: ["web-ui search"], account_terms: "consumer web UI, training opt-out on", source: "generated for v0.3-ext (manual paste)"}` and `MANIFEST.json` with totals, word-count median/max, the number over 250 words, the retry count, and `frozen: true` only at 110/110 (or 60/60).
- Only the MANIFEST files (hashes) go to `boar-eval/bench/v0.3/refs/`. Reference text never leaves private/.
