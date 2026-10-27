# chat-fu-v1: multi-turn intent / anchor probe set (CHATFAIL S0)

License: CC BY 4.0. Written by a BOAR R&D agent on 2026-10-18 (agent-written DEV data, never a claim set, never a held-out set).

- 30 chats x 4-6 turns (159 turns): 24 intent-change chats + 6 control chats; topics the claim kit covers (crypto/Ethereum, travel, first aid, general science); English.
- Chat c01 is the live boar-ios chat of 2026-10-18 (smart contract -> "can you write it?").
- Per-turn labels: `expected_intent` (lookup | chat | code | format | translate | compare), `expected_anchor` (1-based turn whose subject applies; the turn itself when it names a new subject), `capability_request` (the user asks the assistant to produce or transform something: code, example program, table, shorter, translation).
- Labels were written before any replay and are not tuned to the engine. Control chats keep lookup intent and include non-technical "look like" / "an example of" asks that a code-intent rule must not capture.
- Use: deterministic routing replay (classify + follow-up planner, no model) and, later, generation probes. Not for scoring answer quality.
- Source: arms/chatfail/tools/chats.src.mjs in boar-rnd (generates chats.jsonl).
